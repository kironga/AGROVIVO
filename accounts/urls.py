from django.urls import path
from django.contrib.auth.decorators import login_required
from .views import account,register
urlpatterns=[path("",login_required(account),name="account"),path("register/",register,name="register")]
