import re

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

from .models import CustomerProfile

User = get_user_model()


class RegistrationForm(forms.Form):
    first_name = forms.CharField(max_length=150, label="First name", widget=forms.TextInput(attrs={"autocomplete": "given-name"}))
    last_name = forms.CharField(max_length=150, label="Last name", widget=forms.TextInput(attrs={"autocomplete": "family-name"}))
    email = forms.EmailField(max_length=150, widget=forms.EmailInput(attrs={"autocomplete": "email"}))
    phone = forms.CharField(label="Phone number", max_length=16, widget=forms.TelInput(attrs={"autocomplete": "tel", "placeholder": "0712345678 or +254712345678"}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}), label="Password")
    password_confirm = forms.CharField(widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}), label="Confirm password")

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists() or User.objects.filter(username__iexact=email).exists():
            raise forms.ValidationError("An account already uses this email. Please sign in or reset your password.")
        return email

    def clean_phone(self):
        phone = re.sub(r"[\s()-]", "", self.cleaned_data["phone"])
        if re.fullmatch(r"07\d{8}", phone):
            phone = "+254" + phone[1:]
        elif re.fullmatch(r"2547\d{8}", phone):
            phone = "+" + phone
        if not re.fullmatch(r"\+2547\d{8}", phone):
            raise forms.ValidationError("Enter a Kenyan mobile number, for example 0712345678.")
        if CustomerProfile.objects.filter(phone=phone).exists():
            raise forms.ValidationError("An account already uses this phone number.")
        return phone

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("password") and cleaned.get("password_confirm") and cleaned["password"] != cleaned["password_confirm"]:
            self.add_error("password_confirm", "The passwords do not match.")
        if cleaned.get("password") and cleaned.get("email"):
            user = User(username=cleaned["email"], email=cleaned["email"], first_name=cleaned.get("first_name", ""), last_name=cleaned.get("last_name", ""))
            try:
                validate_password(cleaned["password"], user)
            except forms.ValidationError as error:
                self.add_error("password", error)
        return cleaned


class EmailAddressForm(forms.Form):
    email = forms.EmailField(max_length=254, widget=forms.EmailInput(attrs={"autocomplete": "email"}))

    def clean_email(self):
        return self.cleaned_data["email"].strip().lower()


class DualOtpForm(forms.Form):
    email_code = forms.CharField(label="Email OTP", min_length=6, max_length=6, widget=forms.TextInput(attrs={"inputmode": "numeric", "autocomplete": "one-time-code", "pattern": "[0-9]{6}"}))
    phone_code = forms.CharField(label="Phone OTP", min_length=6, max_length=6, widget=forms.TextInput(attrs={"inputmode": "numeric", "autocomplete": "one-time-code", "pattern": "[0-9]{6}"}))

    def clean_email_code(self):
        code = self.cleaned_data["email_code"].strip()
        if not code.isdigit():
            raise forms.ValidationError("Enter the 6-digit code from your email.")
        return code

    def clean_phone_code(self):
        code = self.cleaned_data["phone_code"].strip()
        if not code.isdigit():
            raise forms.ValidationError("Enter the 6-digit code sent to your phone.")
        return code


class SetNewPasswordForm(forms.Form):
    password = forms.CharField(widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}), label="New password")
    password_confirm = forms.CharField(widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}), label="Confirm new password")

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("password") and cleaned.get("password_confirm") and cleaned["password"] != cleaned["password_confirm"]:
            self.add_error("password_confirm", "The passwords do not match.")
        return cleaned
