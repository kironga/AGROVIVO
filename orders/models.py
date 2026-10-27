from django.conf import settings
from django.db import models
from catalog.models import Product
class OrderStatus(models.TextChoices):
 PENDING="PENDING","Pending"
 PAYMENT_PENDING="PAYMENT_PENDING","Payment pending"
 PAID="PAID","Paid"
 PROCESSING="PROCESSING","Processing"
 SHIPPED="SHIPPED","Shipped"
 DELIVERED="DELIVERED","Delivered"
 CANCELLED="CANCELLED","Cancelled"
class PaymentMethod(models.TextChoices):
 MPESA="MPESA","M-Pesa"
 CARD="CARD","Card"
 COD="COD","Cash on delivery"
class Order(models.Model):
 order_number=models.CharField(max_length=24,unique=True)
 user=models.ForeignKey(settings.AUTH_USER_MODEL,null=True,blank=True,on_delete=models.SET_NULL,related_name="orders")
 customer_name=models.CharField(max_length=160)
 customer_phone=models.CharField(max_length=16)
 customer_email=models.EmailField(blank=True)
 county=models.CharField(max_length=80)
 town=models.CharField(max_length=120)
 delivery_area=models.CharField(max_length=160,blank=True)
 delivery_address=models.CharField(max_length=255,blank=True)
 landmark=models.CharField(max_length=180,blank=True)
 delivery_notes=models.TextField(blank=True)
 delivery_agent_name=models.CharField(max_length=160,blank=True)
 delivery_agent_phone=models.CharField(max_length=16,blank=True)
 subtotal_kes=models.PositiveIntegerField()
 delivery_kes=models.PositiveIntegerField(default=0)
 total_kes=models.PositiveIntegerField()
 status=models.CharField(max_length=24,choices=OrderStatus.choices,default=OrderStatus.PENDING)
 payment_method=models.CharField(max_length=8,choices=PaymentMethod.choices)
 payment_ref=models.CharField(max_length=160,blank=True)
 mpesa_checkout_request_id=models.CharField(max_length=100,blank=True,db_index=True)
 mpesa_merchant_request_id=models.CharField(max_length=100,blank=True)
 mpesa_account_reference=models.CharField(max_length=12,blank=True)
 created_at=models.DateTimeField(auto_now_add=True)
 updated_at=models.DateTimeField(auto_now=True)
 @property
 def customer_can_cancel(self):
  if self.payment_ref or self.status in (OrderStatus.PAID, OrderStatus.SHIPPED, OrderStatus.DELIVERED, OrderStatus.CANCELLED):
   return False
  if self.status in (OrderStatus.PENDING, OrderStatus.PAYMENT_PENDING):
   return True
  return self.payment_method == PaymentMethod.COD and self.status == OrderStatus.PROCESSING
 def __str__(self): return self.order_number
class OrderItem(models.Model):
 order=models.ForeignKey(Order,on_delete=models.CASCADE,related_name="items")
 product=models.ForeignKey(Product,on_delete=models.PROTECT,related_name="order_items")
 quantity=models.PositiveIntegerField()
 unit_price_kes=models.PositiveIntegerField()
