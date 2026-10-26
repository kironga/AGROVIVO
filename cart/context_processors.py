from .models import CartItem

def cart_summary(request):
 if not request.user.is_authenticated:
  return {"cart_count":0}
 return {"cart_count":sum(CartItem.objects.filter(user=request.user,product__active=True).values_list("quantity",flat=True))}
