from django.shortcuts import get_object_or_404,render,redirect
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.urls import reverse
from urllib.parse import urlencode
from catalog.models import Product
from .models import CartItem
def cart_page(request):
 items=CartItem.objects.filter(user=request.user,product__active=True).select_related("product") if request.user.is_authenticated else []
 lines=[{"product":item.product,"quantity":item.quantity,"line_total":item.product.price_kes*item.quantity} for item in items]
 subtotal=sum(line["line_total"] for line in lines)
 threshold=10000
 return render(request,"cart/cart.html",{"lines":lines,"subtotal":subtotal,"delivery_threshold":threshold,"delivery":0 if subtotal>=threshold else 350,"delivery_remaining":max(0,threshold-subtotal),"delivery_progress":min(100,int(subtotal*100/threshold)) if subtotal else 0,"cart_count":sum(line["quantity"] for line in lines)})
@require_POST
def add_to_cart(request,product_id):
 product=get_object_or_404(Product,pk=product_id,active=True)
 try: quantity=max(1,min(50,int(request.POST.get("quantity",1))))
 except ValueError: quantity=1
 if not request.user.is_authenticated:
  pending=request.session.get("pending_cart_add",{})
  key=str(product_id)
  try: pending[key]=min(50,int(pending.get(key,0))+quantity)
  except (TypeError,ValueError): pending[key]=quantity
  request.session["pending_cart_add"]=pending
  messages.info(request,"Create an account or sign in to add this product to your cart.")
  return redirect(f"{reverse('login')}?{urlencode({'next':reverse('cart')})}")
 item,_=CartItem.objects.get_or_create(user=request.user,product=product,defaults={"quantity":0})
 item.quantity=min(product.stock,item.quantity+quantity) if product.stock else 0
 if item.quantity: item.save(update_fields=["quantity","updated_at"])
 else: item.delete()
 if not item.quantity: messages.error(request,"This product is currently out of stock.")
 else: messages.success(request,f"{product.name} added to your cart.")
 return redirect("cart")
@require_POST
def update_cart(request,product_id):
 if not request.user.is_authenticated:
  messages.info(request,"Sign in to manage your cart.")
  return redirect(f"{reverse('login')}?{urlencode({'next':reverse('cart')})}")
 product=get_object_or_404(Product,pk=product_id,active=True)
 try: quantity=max(0,min(product.stock,int(request.POST.get("quantity",1))))
 except ValueError: quantity=1
 if quantity: CartItem.objects.update_or_create(user=request.user,product=product,defaults={"quantity":quantity})
 else: CartItem.objects.filter(user=request.user,product=product).delete()
 return redirect("cart")
@require_POST
def remove_from_cart(request,product_id):
 if not request.user.is_authenticated:
  messages.info(request,"Sign in to manage your cart.")
  return redirect(f"{reverse('login')}?{urlencode({'next':reverse('cart')})}")
 CartItem.objects.filter(user=request.user,product_id=product_id).delete()
 return redirect("cart")
