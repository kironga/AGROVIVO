from django.views.generic import TemplateView
from django.views import View
from django.shortcuts import render,redirect
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.http import HttpResponse
from catalog.models import Product,CropProgramme
class HomeView(TemplateView):
 template_name="core/home.html"
 def get_context_data(self,**kwargs):
  data=super().get_context_data(**kwargs)
  data["featured_products"]=Product.objects.filter(active=True,featured=True)[:4]
  data["programmes"]=CropProgramme.objects.all()[:4]
  data["journey_stages"]=["Establish","Vegetative","Balanced nutrition","Flowering & set","Growth regulation","Fruit strength","Stress support","Micronutrients","Bulking & finish"]
  return data
class AboutView(TemplateView): template_name="core/about.html"
class DifferenceView(TemplateView): template_name="core/difference.html"
class ResourcesView(TemplateView): template_name="core/resources.html"
class PartnersView(TemplateView): template_name="core/partners.html"
class LegalView(TemplateView):
 template_name="core/legal.html"
 def get_context_data(self,**kwargs):
  data=super().get_context_data(**kwargs); data["title"]=self.kwargs.get("title","Information"); return data
class ContactView(View):
 def get(self,request): return render(request,"core/contact.html")
 def post(self,request):
  name=request.POST.get("name","").strip()
  email=request.POST.get("email","").strip()
  body=request.POST.get("message","").strip()
  if not name or not body:
   messages.error(request,"Please enter your name and message.")
   return redirect("contact")
  send_mail(f"Website enquiry from {name}",f"{body}\nPhone: {request.POST.get('phone','')}",settings.DEFAULT_FROM_EMAIL,[settings.DEFAULT_FROM_EMAIL],fail_silently=True)
  messages.success(request,"Thanks. Your message has been received.")
  return redirect("contact")
class RobotsView(View):
 def get(self,request):
  return HttpResponse("User-agent: *\nAllow: /\nSitemap: https://agrofields.example/sitemap.xml\n",content_type="text/plain")
