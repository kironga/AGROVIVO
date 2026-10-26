from django.conf import settings
from django.db import models


class CustomerProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="customer_profile")
    phone = models.CharField(max_length=16, unique=True)
    email_verified = models.BooleanField(default=False)
    phone_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} ({self.phone})"


class AccountVerification(models.Model):
    class Purpose(models.TextChoices):
        SIGNUP = "signup", "Sign up"
        PASSWORD_RESET = "password_reset", "Password reset"

    purpose = models.CharField(max_length=20, choices=Purpose.choices)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.CASCADE, related_name="account_verifications")
    email = models.EmailField()
    phone = models.CharField(max_length=16)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    password_hash = models.CharField(max_length=256, blank=True)
    email_code_hash = models.CharField(max_length=256)
    phone_code_hash = models.CharField(max_length=256)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    last_sent_at = models.DateTimeField()
    verified_at = models.DateTimeField(null=True, blank=True)
    attempts = models.PositiveSmallIntegerField(default=0)

    def __str__(self):
        return f"{self.get_purpose_display()} for {self.email}"
