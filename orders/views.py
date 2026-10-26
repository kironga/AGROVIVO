import re
from uuid import uuid4
from django.shortcuts import render,redirect,get_object_or_404
from django.urls import reverse
from urllib.parse import urlencode
from django.contrib import messages
from django.db import transaction
from django.core.mail import send_mail
from django.conf import settings
from catalog.models import Product
from .models import Order,OrderItem,OrderStatus,PaymentMethod
COUNTIES=["Baringo","Bomet","Bungoma","Busia","Elgeyo-Marakwet","Embu","Garissa","Homa Bay","Isiolo","Kajiado","Kakamega","Kericho","Kiambu","Kilifi","Kirinyaga","Kisii","Kisumu","Kitui","Kwale","Laikipia","Lamu","Machakos","Makueni","Mandera","Marsabit","Meru","Migori","Mombasa","Murang'a","Nairobi","Nakuru","Nandi","Narok","Nyamira","Nyandarua","Nyeri","Samburu","Siaya","Taita-Taveta","Tana River","Tharaka-Nithi","Trans Nzoia","Turkana","Uasin Gishu","Vihiga","Wajir","West Pokot"]
def checkout(request):
 if not request.user.is_authenticated:
  request.session["cart"]={}
  messages.info(request,"Sign in or create an account before checking out.")
  return redirect(f"{reverse('login')}?{urlencode({'next':reverse('products')})}")
 cart=request.session.get("cart",{})
 products=Product.objects.filter(id__in=cart.keys(),active=True)
 lines=[(p,int(cart.get(str(p.id),0))) for p in products]
 subtotal=sum(p.price_kes*q for p,q in lines)
 if not lines:
  messages.info(request,"Your cart is empty.")
  return redirect("products")
 delivery=0 if subtotal>=10000 else 350
 if request.method=="POST":
  data=request.POST
  phone=re.sub(r"[\s()-]","",data.get("phone",""))
  if re.fullmatch(r"07\d{8}",phone):
   phone="+254"+phone[1:]
  elif re.fullmatch(r"2547\d{8}",phone):
   phone="+"+phone
  if not re.fullmatch(r"\+2547\d{8}",phone):
   messages.error(request,"Enter a Kenyan mobile number, for example 0712345678 or +254712345678.")
  elif not data.get("name","").strip() or not data.get("town","").strip() or not data.get("county"):
   messages.error(request,"Complete your name and delivery location.")
  else:
   with transaction.atomic():
    locked={p.id:Product.objects.select_for_update().get(id=p.id) for p,q in lines}
    if any(locked[p.id].stock<q for p,q in lines):
     messages.error(request,"Some cart quantities are no longer available. Please update your cart.")
     return redirect("cart")
    method=data.get("payment_method","MPESA")
    if method not in PaymentMethod.values: method="MPESA"
    order=Order.objects.create(order_number=f"AP-{uuid4().hex[:16].upper()}",user=request.user if request.user.is_authenticated else None,customer_name=data["name"].strip(),customer_phone=phone,customer_email=data.get("email","").strip(),county=data["county"],town=data["town"].strip(),delivery_notes=data.get("delivery_notes","").strip(),subtotal_kes=subtotal,delivery_kes=delivery,total_kes=subtotal+delivery,payment_method=method,status=OrderStatus.PROCESSING if method=="COD" else OrderStatus.PAYMENT_PENDING)
    for p,q in lines:
     Product.objects.filter(pk=p.pk).update(stock=locked[p.id].stock-q)
     OrderItem.objects.create(order=order,product=p,quantity=q,unit_price_kes=p.price_kes)
   request.session["cart"]={}
   if order.customer_email:
    send_mail(f"AgroVivo order {order.order_number}",f"Thank you {order.customer_name}. Total: KES {order.total_kes:,}.",settings.DEFAULT_FROM_EMAIL,[order.customer_email],fail_silently=True)
   if method=="MPESA": return redirect("mpesa_start",order_number=order.order_number)
   if method=="CARD": return redirect("stripe_start",order_number=order.order_number)
   return redirect("confirmation",order_number=order.order_number)
 return render(request,"orders/checkout.html",{"lines":lines,"subtotal":subtotal,"delivery":delivery,"total":subtotal+delivery,"counties":COUNTIES})
def confirmation(request,order_number):
 order=get_object_or_404(Order,order_number=order_number)
 if order.user_id and request.user!=order.user: return redirect("home")
 return render(request,"orders/confirmation.html",{"order":order})
