import base64
import json
import logging
import re
from datetime import datetime

import requests
from django.conf import settings
from django.contrib import messages
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from requests.auth import HTTPBasicAuth

from orders.models import Order, OrderStatus

logger = logging.getLogger(__name__)


def _safe_provider_error(response):
    """Return only Daraja's public error code/message, with secrets redacted."""
    try:
        data = response.json()
    except (ValueError, json.JSONDecodeError):
        return ""
    message = str(data.get("errorMessage") or data.get("ResponseDescription") or "")[:240]
    for secret in (
        settings.MPESA_CONSUMER_KEY,
        settings.MPESA_CONSUMER_SECRET,
        settings.MPESA_PASSKEY,
    ):
        if secret:
            message = message.replace(secret, "[redacted]")
    code = str(data.get("errorCode") or data.get("ResponseCode") or "")[:40]
    return f"code={code} message={message}" if code or message else ""


def _mpesa_base_url():
    if settings.MPESA_ENV == "production":
        return "https://api.safaricom.co.ke"
    return "https://sandbox.safaricom.co.ke"


def _callback_url():
    callback_url = settings.MPESA_CALLBACK_URL.strip()
    render_hostname = getattr(settings, "RENDER_EXTERNAL_HOSTNAME", "")
    if not callback_url and render_hostname:
        callback_url = f"https://{render_hostname}/payments/mpesa/callback/"
    if not callback_url.startswith("https://"):
        raise ValueError("Set MPESA_CALLBACK_URL to the public HTTPS callback URL.")
    return callback_url


def _get_access_token():
    response = requests.get(
        f"{_mpesa_base_url()}/oauth/v1/generate?grant_type=client_credentials",
        auth=HTTPBasicAuth(settings.MPESA_CONSUMER_KEY, settings.MPESA_CONSUMER_SECRET),
        timeout=20,
    )
    response.raise_for_status()
    token = response.json().get("access_token")
    if not token:
        raise ValueError("Daraja did not return an access token.")
    return token


def mpesa_start(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    if not request.user.is_authenticated or order.user_id != request.user.pk:
        return redirect("login")
    if order.status == OrderStatus.PAID:
        return redirect("confirmation", order_number=order_number)
    if order.payment_method != "MPESA":
        return redirect("confirmation", order_number=order_number)
    if not all((settings.MPESA_CONSUMER_KEY, settings.MPESA_CONSUMER_SECRET, settings.MPESA_SHORTCODE, settings.MPESA_PASSKEY)):
        messages.error(request, "M-Pesa checkout is not configured yet. Please contact us or choose another payment option.")
        return redirect("confirmation", order_number=order_number)

    phone = re.sub(r"\D", "", order.customer_phone)
    if phone.startswith("0"):
        phone = "254" + phone[1:]
    elif phone.startswith("+254"):
        phone = phone[1:]
    if not re.fullmatch(r"2547\d{8}", phone):
        messages.error(request, "The phone number on this order cannot receive an M-Pesa prompt. Please contact us.")
        return redirect("confirmation", order_number=order_number)

    stage = "callback URL validation"
    try:
        callback_url = _callback_url()
        stage = "OAuth token request"
        token = _get_access_token()
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        password = base64.b64encode(
            f"{settings.MPESA_SHORTCODE}{settings.MPESA_PASSKEY}{timestamp}".encode()
        ).decode()
        # Daraja's AccountReference is limited to 12 characters.
        account_reference = f"AG{order.pk:010d}"
        payload = {
            "BusinessShortCode": settings.MPESA_SHORTCODE,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": max(1, int(order.total_kes)),
            "PartyA": phone,
            "PartyB": settings.MPESA_SHORTCODE,
            "PhoneNumber": phone,
            "CallBackURL": callback_url,
            "AccountReference": account_reference,
            "TransactionDesc": "AgroVivo order",
        }
        stage = "STK Push request"
        response = requests.post(
            f"{_mpesa_base_url()}/mpesa/stkpush/v1/processrequest",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
            timeout=25,
        )
        response.raise_for_status()
        result = response.json()
        if str(result.get("ResponseCode")) != "0" or not result.get("CheckoutRequestID"):
            messages.error(request, result.get("CustomerMessage") or "Daraja could not start the M-Pesa prompt. Please try again.")
            return redirect("confirmation", order_number=order_number)

        order.mpesa_checkout_request_id = result["CheckoutRequestID"]
        order.mpesa_merchant_request_id = result.get("MerchantRequestID", "")
        order.mpesa_account_reference = account_reference
        order.status = OrderStatus.PAYMENT_PENDING
        order.save(update_fields=["mpesa_checkout_request_id", "mpesa_merchant_request_id", "mpesa_account_reference", "status", "updated_at"])
        messages.success(request, "M-Pesa prompt sent. Check your phone and enter your M-Pesa PIN to complete payment.")
    except requests.RequestException as exc:
        response = getattr(exc, "response", None)
        provider_error = _safe_provider_error(response) if response is not None else ""
        logger.error(
            "Daraja %s failed for order %s (exception=%s, http_status=%s, %s)",
            stage,
            order.order_number,
            type(exc).__name__,
            getattr(response, "status_code", "none"),
            provider_error or "no provider error body",
        )
        messages.error(request, "We could not reach M-Pesa just now. Please try again shortly.")
    except (ValueError, KeyError) as exc:
        logger.error(
            "Daraja %s failed for order %s (exception=%s)",
            stage,
            order.order_number,
            type(exc).__name__,
        )
        messages.error(request, "We could not reach M-Pesa just now. Please try again shortly.")
    return redirect("confirmation", order_number=order_number)


@csrf_exempt
@require_POST
def mpesa_callback(request):
    try:
        payload = json.loads(request.body)
        callback = payload["Body"]["stkCallback"]
        checkout_id = callback["CheckoutRequestID"]
        result_code = int(callback["ResultCode"])
    except (ValueError, KeyError, TypeError):
        return HttpResponseBadRequest("Invalid callback")

    order = Order.objects.filter(mpesa_checkout_request_id=checkout_id, payment_method="MPESA").first()
    if not order:
        # Acknowledge unknown/old callback IDs; never mark an order paid by AccountReference alone.
        return JsonResponse({"ResultCode": 0, "ResultDesc": "Accepted"})

    if result_code == 0 and order.status != OrderStatus.PAID:
        try:
            metadata = {
                item["Name"]: item.get("Value")
                for item in callback.get("CallbackMetadata", {}).get("Item", [])
                if "Name" in item
            }
            amount = int(metadata["Amount"])
            receipt = str(metadata["MpesaReceiptNumber"])
            paid_phone = str(metadata["PhoneNumber"])
            expected_phone = re.sub(r"\D", "", order.customer_phone).removeprefix("+")
        except (KeyError, TypeError, ValueError):
            return JsonResponse({"ResultCode": 0, "ResultDesc": "Accepted"})
        if amount == order.total_kes and paid_phone == expected_phone and receipt:
            order.status = OrderStatus.PAID
            order.payment_ref = receipt
            order.save(update_fields=["status", "payment_ref", "updated_at"])

    return JsonResponse({"ResultCode": 0, "ResultDesc": "Accepted"})


def stripe_start(request, order_number):
    return JsonResponse({"error": "Stripe checkout is not configured."}, status=503)


@csrf_exempt
@require_POST
def stripe_webhook(request):
    return JsonResponse({"received": True})
