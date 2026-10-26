from django.shortcuts import render,redirect
from django.contrib import messages
from .forms import RegistrationForm
def account(request):
 if request.user.is_staff:
  return redirect("dashboard_home")
 return render(request,"accounts/account.html",{"orders":request.user.orders.prefetch_related("items__product").order_by("-created_at")})
def register(request):
 if request.method=="POST":
  form=RegistrationForm(request.POST)
  if form.is_valid():
   form.save(); messages.success(request,"Your account is ready. Please sign in."); return redirect("login")
 else: form=RegistrationForm()
 return render(request,"registration/register.html",{"form":form})
