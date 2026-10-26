from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import get_user_model, password_validation
from django.contrib.auth.hashers import make_password
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from urllib.parse import urlencode

from .forms import DualOtpForm, EmailAddressForm, RegistrationForm, SetNewPasswordForm
from .models import AccountVerification, CustomerProfile
from .otp import RESEND_WAIT, issue_codes, valid_codes

User = get_user_model()
SIGNUP_SESSION_KEY = "signup_verification_id"
RESET_SESSION_KEY = "password_reset_verification_id"
VERIFIED_RESET_SESSION_KEY = "verified_password_reset_id"


def account(request):
    if request.user.is_staff:
        return redirect("dashboard_home")
    profile = CustomerProfile.objects.filter(user=request.user).first()
    return render(request, "accounts/account.html", {"profile": profile, "orders": request.user.orders.prefetch_related("items__product").order_by("-created_at")})


def register(request):
    next_url = request.POST.get("next", request.GET.get("next", ""))
    form = RegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        AccountVerification.objects.filter(expires_at__lt=timezone.now() - timedelta(days=1)).delete()
        email = form.cleaned_data["email"]
        phone = form.cleaned_data["phone"]
        if User.objects.filter(email__iexact=email).exists() or User.objects.filter(username__iexact=email).exists():
            form.add_error("email", "An account already uses this email. Please sign in or reset your password.")
        elif CustomerProfile.objects.filter(phone=phone).exists():
            form.add_error("phone", "An account already uses this phone number.")
        else:
            recent = AccountVerification.objects.filter(purpose=AccountVerification.Purpose.SIGNUP, email=email, created_at__gte=timezone.now() - RESEND_WAIT).first()
            if recent:
                form.add_error(None, "A verification code was sent recently. Check your email and phone, or wait one minute before requesting another.")
            else:
                AccountVerification.objects.filter(purpose=AccountVerification.Purpose.SIGNUP, email=email).delete()
                challenge = AccountVerification.objects.create(
                    purpose=AccountVerification.Purpose.SIGNUP,
                    email=email,
                    phone=phone,
                    first_name=form.cleaned_data["first_name"].strip(),
                    last_name=form.cleaned_data["last_name"].strip(),
                    password_hash=make_password(form.cleaned_data["password"]),
                    email_code_hash="pending",
                    phone_code_hash="pending",
                    expires_at=timezone.now(),
                    last_sent_at=timezone.now() - RESEND_WAIT,
                )
                request.session[SIGNUP_SESSION_KEY] = challenge.pk
                request.session["signup_next"] = next_url
                delivered = issue_codes(challenge)
                if delivered:
                    messages.success(request, "We sent one verification code to your email and another to your phone. Enter both codes to finish creating your account.")
                else:
                    messages.warning(request, "Your verification request is saved, but one of the codes could not be delivered. Check the delivery settings or try resending in one minute.")
                return redirect("signup_verify")
    return render(request, "registration/register.html", {"form": form, "next": next_url})


def signup_verify(request):
    challenge = _session_challenge(request, SIGNUP_SESSION_KEY, AccountVerification.Purpose.SIGNUP)
    if not challenge:
        messages.info(request, "Start account creation to request new verification codes.")
        return redirect("register")
    form = DualOtpForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        if not valid_codes(challenge, form.cleaned_data["email_code"], form.cleaned_data["phone_code"]):
            messages.error(request, "The codes are incorrect, expired, or have used all attempts. Request fresh codes and try again.")
        else:
            if User.objects.filter(email__iexact=challenge.email).exists() or User.objects.filter(username__iexact=challenge.email).exists() or CustomerProfile.objects.filter(phone=challenge.phone).exists():
                challenge.delete()
                request.session.pop(SIGNUP_SESSION_KEY, None)
                messages.error(request, "That email or phone number has since been used. Please sign in or use different details.")
                return redirect("register")
            try:
                with transaction.atomic():
                    user = User.objects.create(
                        username=challenge.email,
                        email=challenge.email,
                        first_name=challenge.first_name,
                        last_name=challenge.last_name,
                        password=challenge.password_hash,
                    )
                    CustomerProfile.objects.create(user=user, phone=challenge.phone, email_verified=True, phone_verified=True)
                    challenge.delete()
            except IntegrityError:
                challenge.delete()
                request.session.pop(SIGNUP_SESSION_KEY, None)
                messages.error(request, "Those account details have already been registered. Please sign in or use another email and phone number.")
                return redirect("register")
            next_url = request.session.pop("signup_next", "")
            request.session.pop(SIGNUP_SESSION_KEY, None)
            messages.success(request, "Your email and phone are verified. Sign in with your email and password.")
            return redirect(f"{reverse('login')}?{urlencode({'next': next_url})}" if next_url else "login")
    return render(request, "registration/verify_otp.html", {"form": form, "purpose": "signup", "email_hint": _masked_email(challenge.email), "phone_hint": _masked_phone(challenge.phone)})


def password_reset_start(request):
    form = EmailAddressForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        AccountVerification.objects.filter(expires_at__lt=timezone.now() - timedelta(days=1)).delete()
        email = form.cleaned_data["email"]
        request.session.pop(VERIFIED_RESET_SESSION_KEY, None)
        challenge = None
        user = User.objects.filter(email__iexact=email, is_active=True).first()
        if user:
            profile = CustomerProfile.objects.filter(user=user).first()
            phone = profile.phone if profile else _phone_from_order_history(user)
            if phone:
                recent = AccountVerification.objects.filter(purpose=AccountVerification.Purpose.PASSWORD_RESET, user=user, created_at__gte=timezone.now() - RESEND_WAIT).first()
                if not recent:
                    AccountVerification.objects.filter(purpose=AccountVerification.Purpose.PASSWORD_RESET, user=user).delete()
                    challenge = AccountVerification.objects.create(
                        purpose=AccountVerification.Purpose.PASSWORD_RESET,
                        user=user,
                        email=user.email,
                        phone=phone,
                        email_code_hash="pending",
                        phone_code_hash="pending",
                        expires_at=timezone.now(),
                        last_sent_at=timezone.now() - RESEND_WAIT,
                    )
                    issue_codes(challenge)
                else:
                    challenge = recent
        if challenge:
            request.session[RESET_SESSION_KEY] = challenge.pk
        else:
            request.session.pop(RESET_SESSION_KEY, None)
        messages.info(request, "If the email belongs to a verified customer account, verification codes have been sent to its email and phone.")
        return redirect("customer_password_reset_verify")
    return render(request, "registration/password_reset_form.html", {"form": form})


def password_reset_verify(request):
    challenge = _session_challenge(request, RESET_SESSION_KEY, AccountVerification.Purpose.PASSWORD_RESET)
    form = DualOtpForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        if not challenge or not valid_codes(challenge, form.cleaned_data["email_code"], form.cleaned_data["phone_code"]):
            messages.error(request, "The codes are incorrect, expired, or unavailable. Start a new password reset request and try again.")
        else:
            challenge.verified_at = timezone.now()
            challenge.save(update_fields=["verified_at"])
            request.session[VERIFIED_RESET_SESSION_KEY] = challenge.pk
            return redirect("customer_password_reset_new")
    return render(request, "registration/verify_otp.html", {"form": form, "purpose": "password_reset", "email_hint": _masked_email(challenge.email) if challenge else "your registered email", "phone_hint": _masked_phone(challenge.phone) if challenge else "your registered phone"})


def password_reset_new(request):
    challenge_id = request.session.get(VERIFIED_RESET_SESSION_KEY)
    challenge = AccountVerification.objects.filter(pk=challenge_id, purpose=AccountVerification.Purpose.PASSWORD_RESET, verified_at__isnull=False, expires_at__gt=timezone.now(), user__is_active=True).first() if challenge_id else None
    if not challenge:
        request.session.pop(VERIFIED_RESET_SESSION_KEY, None)
        messages.info(request, "Verify both OTP codes before choosing a new password.")
        return redirect("customer_password_reset")
    form = SetNewPasswordForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            password_validation.validate_password(form.cleaned_data["password"], challenge.user)
        except ValidationError as error:
            form.add_error("password", error)
        else:
            challenge.user.set_password(form.cleaned_data["password"])
            challenge.user.save(update_fields=["password"])
            challenge.delete()
            request.session.pop(RESET_SESSION_KEY, None)
            request.session.pop(VERIFIED_RESET_SESSION_KEY, None)
            messages.success(request, "Your password has been reset. Sign in with your new password.")
            return redirect("login")
    return render(request, "registration/password_reset_new.html", {"form": form})


def resend_otp(request, purpose):
    if request.method != "POST":
        return redirect("register")
    if purpose == "signup":
        session_key, target, expected = SIGNUP_SESSION_KEY, "signup_verify", AccountVerification.Purpose.SIGNUP
    else:
        session_key, target, expected = RESET_SESSION_KEY, "customer_password_reset_verify", AccountVerification.Purpose.PASSWORD_RESET
    challenge = _session_challenge(request, session_key, expected)
    if challenge and challenge.created_at > timezone.now() - timedelta(days=1):
        wait_until = challenge.last_sent_at + RESEND_WAIT
        if timezone.now() < wait_until:
            seconds = max(1, int((wait_until - timezone.now()).total_seconds()))
            messages.warning(request, f"Please wait {seconds} seconds before requesting new codes.")
        elif issue_codes(challenge):
            messages.success(request, "Fresh verification codes have been sent to your email and phone.")
        else:
            messages.error(request, "At least one verification code could not be delivered. Check the delivery settings and try again later.")
    else:
        messages.error(request, "This verification request has expired. Start again to request new codes.")
    return redirect(target)


def _session_challenge(request, session_key, purpose):
    challenge_id = request.session.get(session_key)
    if not challenge_id:
        return None
    return AccountVerification.objects.filter(pk=challenge_id, purpose=purpose).first()


def _masked_email(email):
    name, separator, domain = email.partition("@")
    return f"{name[:1]}{'*' * max(1, len(name) - 1)}@{domain}" if separator else "your email"


def _masked_phone(phone):
    return f"{phone[:4]}{'*' * max(0, len(phone) - 7)}{phone[-3:]}"


def _phone_from_order_history(user):
    order = user.orders.exclude(customer_phone="").order_by("-created_at").only("customer_phone").first()
    if not order:
        return ""
    phone = "".join(character for character in order.customer_phone if character.isdigit() or character == "+")
    if phone.startswith("07") and len(phone) == 10:
        phone = "+254" + phone[1:]
    elif phone.startswith("2547") and len(phone) == 12:
        phone = "+" + phone
    return phone if len(phone) == 13 and phone.startswith("+2547") else ""
