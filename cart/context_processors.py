def cart_summary(request):
 return {"cart_count":sum(int(q) for q in request.session.get("cart",{}).values())}
