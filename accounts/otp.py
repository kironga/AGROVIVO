import logging
import secrets
from datetime import timedelta

import requests
from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.core.mail import send_mail
from django.utils import timezone

from .models import AccountVerification

logger = logging.getLogger(__name__)
OTP_LIFETIME = timedelta(minutes=10)
RESEND_WAIT = timedelta(seconds=60)
MAX_ATTEMPTS = 5


def new_code():
    return f"{secrets.randbelow(1_000_000):06d}"


def issue_codes(challenge):
    email_code, phone_code = new_code(), new_code()
    challenge.email_code_hash = make_password(email_code)
    challenge.phone_code_hash = make_password(phone_code)
    challenge.expires_at = timezone.now() + OTP_LIFETIME
    challenge.last_sent_at = timezone.now()
    challenge.attempts = 0
    challenge.verified_at = None
    challenge.save(update_fields=["email_code_hash", "phone_code_hash", "expires_at", "last_sent_at", "attempts", "verified_at"])
    email_ok = send_email_code(challenge, email_code)
    phone_ok = send_phone_code(challenge, phone_code)
    return email_ok and phone_ok


def send_email_code(challenge, code):
    purpose = "create your AgroVivo account" if challenge.purpose == AccountVerification.Purpose.SIGNUP else "reset your AgroVivo password"
    try:
        return bool(send_mail(
            "Your AgroVivo verification code",
            f"Your code to {purpose} is {code}. It expires in 10 minutes. If you did not request this, ignore this email.",
            settings.DEFAULT_FROM_EMAIL,
            [challenge.email],
            fail_silently=False,
        ))
    except Exception:
        logger.exception("Could not send AgroVivo email verification code")
        return False


def send_phone_code(challenge, code):
    username = settings.AFRICASTALKING_USERNAME
    api_key = settings.AFRICASTALKING_API_KEY
    if not username or not api_key:
        if settings.DEBUG:
            logger.warning("Development phone OTP for %s: %s", challenge.phone, code)
            return True
        logger.error("Africa's Talking credentials are not configured")
        return False

    host = "https://api.sandbox.africastalking.com" if settings.AFRICASTALKING_ENV == "sandbox" else "https://api.africastalking.com"
    payload = {"username": username, "to": challenge.phone, "message": f"Your AgroVivo verification code is {code}. It expires in 10 minutes."}
    if settings.AFRICASTALKING_SENDER_ID:
        payload["from"] = settings.AFRICASTALKING_SENDER_ID
    try:
        response = requests.post(f"{host}/version1/messaging", data=payload, headers={"apiKey": api_key, "Accept": "application/json"}, timeout=12)
        response.raise_for_status()
        body = response.json()
        recipients = body.get("SMSMessageData", {}).get("Recipients", [])
        return bool(recipients and recipients[0].get("status") == "Success")
    except (requests.RequestException, ValueError, TypeError):
        logger.exception("Could not send AgroVivo phone verification code")
        return False


def valid_codes(challenge, email_code, phone_code):
    if challenge.attempts >= MAX_ATTEMPTS or challenge.expires_at <= timezone.now():
        return False
    challenge.attempts += 1
    challenge.save(update_fields=["attempts"])
    return check_password(email_code, challenge.email_code_hash) and check_password(phone_code, challenge.phone_code_hash)
