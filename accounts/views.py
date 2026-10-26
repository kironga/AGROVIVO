from django.shortcuts import render,redirect
from django.urls import reverse
from urllib.parse import urlencode
from django.contrib import messages
from .forms import RegistrationForm
def account(request):
 if request.user.is_staff:
  return redirect("dashboard_home")
 return render(request,"accounts/account.html",{"orders":request.user.orders.prefetch_related("items__product").order_by("-created_at")})
def register(request):
 next_url=request.POST.get("next",request.GET.get("next",""))
 if request.method=="POST":
  form=RegistrationForm(request.POST)
  if form.is_valid():
   form.save(); messages.success(request,"Your account is ready. Please sign in.")
   login_url=reverse("login")
   return redirect(f"{login_url}?{urlencode({'next':next_url})}" if next_url else login_url)
 else: form=RegistrationForm()
 return render(request,"registration/register.html",{"form":form,"next":next_url})
