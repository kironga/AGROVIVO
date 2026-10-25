from django.shortcuts import get_object_or_404,render,redirect
from django.views.decorators.http import require_POST
from django.contrib import messages
from catalog.models import Product
def cart_page(request):
 cart=request.session.get("cart",{})
 products=Product.objects.filter(id__in=cart.keys(),active=True)
 lines=[{"product":p,"quantity":int(cart.get(str(p.id),0))} for p in products]
 subtotal=sum(x["product"].price_kes*x["quantity"] for x in lines)
 return render(request,"cart/cart.html",{"lines":lines,"subtotal":subtotal})
@require_POST
def add_to_cart(request,product_id):
 product=get_object_or_404(Product,pk=product_id,active=True)
 try: quantity=max(1,min(50,int(request.POST.get("quantity",1))))
 except ValueError: quantity=1
 cart=request.session.get("cart",{}); key=str(product_id)
 cart[key]=min(product.stock,int(cart.get(key,0))+quantity) if product.stock else 0
 request.session["cart"]=cart
 if not cart[key]: messages.error(request,"This product is currently out of stock.")
 else: messages.success(request,f"{product.name} added to your cart.")
 return redirect("cart")
@require_POST
def update_cart(request,product_id):
 product=get_object_or_404(Product,pk=product_id,active=True)
 try: quantity=max(0,min(product.stock,int(request.POST.get("quantity",1))))
 except ValueError: quantity=1
 cart=request.session.get("cart",{})
 if quantity: cart[str(product_id)]=quantity
 else: cart.pop(str(product_id),None)
 request.session["cart"]=cart
 return redirect("cart")
@require_POST
def remove_from_cart(request,product_id):
 cart=request.session.get("cart",{}); cart.pop(str(product_id),None); request.session["cart"]=cart
 return redirect("cart")
