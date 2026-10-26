def cart_summary(request):
 if not request.user.is_authenticated:
  return {"cart_count":0}
 return {"cart_count":sum(int(q) for q in request.session.get("cart",{}).values())}
