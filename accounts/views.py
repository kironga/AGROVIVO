from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import get_user_model, password_validation, login
from django.core.exceptions import ValidationError
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme

from cart.models import CartItem
from catalog.models import Product
from .forms import DualOtpForm, EmailAddressForm, RegistrationForm, SetNewPasswordForm
from .models import AccountVerification, CustomerProfile
from .otp import RESEND_WAIT, issue_codes, valid_codes

User = get_user_model()
RESET_SESSION_KEY = "password_reset_verification_id"
VERIFIED_RESET_SESSION_KEY = "verified_password_reset_id"


def account(request):
    if request.user.is_staff:
        return redirect("dashboard_home")
    profile = CustomerProfile.objects.filter(user=request.user).first()
    orders = request.user.orders.prefetch_related("items__product").order_by("-created_at")
    cart_items = CartItem.objects.filter(user=request.user, product__active=True).select_related("product")
    cart_total = sum(item.product.price_kes * item.quantity for item in cart_items)
    return render(request, "accounts/account.html", {
        "profile": profile,
        "orders": orders[:6],
        "order_count": orders.count(),
        "active_order_count": orders.exclude(status__in=["DELIVERED", "CANCELLED"]).count(),
        "cart_items": cart_items[:3],
        "cart_count": sum(item.quantity for item in cart_items),
        "cart_total": cart_total,
        "latest_order": orders.first(),
    })


def register(request):
    next_url = request.POST.get("next", request.GET.get("next", ""))
    form = RegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        email = form.cleaned_data["email"]
        phone = form.cleaned_data["phone"]
        user = User.objects.create_user(
            username=email, email=email,
            first_name=form.cleaned_data["first_name"].strip(),
            last_name=form.cleaned_data["last_name"].strip(),
            password=form.cleaned_data["password"],
        )
        CustomerProfile.objects.create(user=user, phone=phone)
        login(request, user)
        pending = request.session.pop("pending_cart_add", {})
        added = False
        for product_id, requested in pending.items():
            product = Product.objects.filter(pk=product_id, active=True).first()
            if not product or not product.stock:
                continue
            try:
                requested = max(1, min(50, int(requested)))
            except (TypeError, ValueError):
                requested = 1
            item, _ = CartItem.objects.get_or_create(user=user, product=product, defaults={"quantity": 0})
            item.quantity = min(product.stock, item.quantity + requested)
            if item.quantity:
                item.save(update_fields=["quantity", "updated_at"])
                added = True
            else:
                item.delete()
        if added:
            messages.info(request, "The product you selected before signup is waiting in your cart.")
        messages.success(request, "Your customer account is ready. You are now signed in.")
        if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
            return redirect(next_url)
        return redirect("account")
    return render(request, "registration/register.html", {"form": form, "next": next_url})


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


def resend_otp(request):
    if request.method != "POST":
        return redirect("customer_password_reset")
    challenge = _session_challenge(request, RESET_SESSION_KEY, AccountVerification.Purpose.PASSWORD_RESET)
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
    return redirect("customer_password_reset_verify")


def _session_challenge(request, session_key, purpose):
    challenge_id = request.session.get(session_key)
    if not challenge_id:
        return None
    return AccountVerification.objects.filter(pk=challenge_id, purpose=purpose).first()


def _masked_email(email):
    name, separator, domain = email.partition("@")
    return f"{name[:1]}{'*' * max(1, len(name) - 1)}@{domain}" if separator else "your email"


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
