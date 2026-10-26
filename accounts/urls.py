from django.urls import path
from django.contrib.auth.decorators import login_required
from .views import account, password_reset_new, password_reset_start, password_reset_verify, register, resend_otp
urlpatterns=[
 path("",login_required(account),name="account"),
 path("register/",register,name="register"),
 path("password-reset/",password_reset_start,name="customer_password_reset"),
 path("password-reset/verify/",password_reset_verify,name="customer_password_reset_verify"),
 path("password-reset/resend/",resend_otp,name="resend_otp"),
 path("password-reset/new/",password_reset_new,name="customer_password_reset_new"),
]
