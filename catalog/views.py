from django.shortcuts import render,get_object_or_404
from .models import Product,CropProgramme
def product_list(request):
 products=Product.objects.filter(active=True)
 stage=request.GET.get("stage")
 if stage: products=products.filter(stage=stage)
 return render(request,"catalog/products.html",{"products":products,"stages":Product._meta.get_field("stage").choices})
def product_detail(request,slug):
 product=get_object_or_404(Product,slug=slug,active=True)
 return render(request,"catalog/product_detail.html",{"product":product,"related":Product.objects.filter(active=True,stage=product.stage).exclude(pk=product.pk)[:3]})
def programme_list(request):
 return render(request,"catalog/programmes.html",{"programmes":CropProgramme.objects.all()})
def programme_detail(request,slug):
 programme=get_object_or_404(CropProgramme,slug=slug)
 return render(request,"catalog/programme_detail.html",{"programme":programme})
