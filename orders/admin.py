from django.contrib import admin
from .models import Order,OrderItem
class OrderItemInline(admin.TabularInline):
 model=OrderItem
 extra=0
 readonly_fields=("product","quantity","unit_price_kes")
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
 list_display=("order_number","customer_name","total_kes","status","payment_method","created_at")
 list_filter=("status","payment_method","created_at")
 search_fields=("order_number","customer_name","customer_phone")
 inlines=[OrderItemInline]
