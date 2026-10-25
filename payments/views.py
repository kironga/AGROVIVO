import json
from django.conf import settings
from django.http import JsonResponse,HttpResponseBadRequest
from django.shortcuts import get_object_or_404,redirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from orders.models import Order,OrderStatus
def mpesa_start(request,order_number):
 order=get_object_or_404(Order,order_number=order_number)
 if settings.DEBUG:
  order.status=OrderStatus.PAID
  order.payment_ref="DEMO-"+order.order_number
  order.save(update_fields=["status","payment_ref","updated_at"])
  return redirect("confirmation",order_number=order_number)
 return JsonResponse({"error":"M-Pesa credentials and Daraja STK service are not configured."},status=503)
@csrf_exempt
@require_POST
def mpesa_callback(request):
 try: data=json.loads(request.body); callback=data["Body"]["stkCallback"]
 except (ValueError,KeyError,TypeError): return HttpResponseBadRequest("Invalid callback")
 if callback.get("ResultCode")==0:
  meta={x["Name"]:x.get("Value") for x in callback.get("CallbackMetadata",{}).get("Item",[])}
  order=Order.objects.filter(order_number=meta.get("AccountReference")).first()
  if order:
   order.status=OrderStatus.PAID; order.payment_ref=str(meta.get("MpesaReceiptNumber","")); order.save(update_fields=["status","payment_ref","updated_at"])
 return JsonResponse({"ResultCode":0,"ResultDesc":"Accepted"})
def stripe_start(request,order_number):
 return JsonResponse({"error":"Stripe checkout is not configured."},status=503)
@csrf_exempt
@require_POST
def stripe_webhook(request):
 return JsonResponse({"received":True})
