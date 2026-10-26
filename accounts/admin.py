from django.contrib import admin

from .models import CustomerProfile


@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "phone", "email_verified", "phone_verified", "created_at")
    search_fields = ("user__email", "user__first_name", "user__last_name", "phone")
    list_filter = ("email_verified", "phone_verified")
    readonly_fields = ("created_at",)
