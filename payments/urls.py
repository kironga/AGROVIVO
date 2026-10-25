from django.urls import path
from .views import mpesa_start,mpesa_callback,stripe_start,stripe_webhook
urlpatterns=[path("mpesa/<str:order_number>/",mpesa_start,name="mpesa_start"),path("mpesa/callback/",mpesa_callback,name="mpesa_callback"),path("stripe/<str:order_number>/",stripe_start,name="stripe_start"),path("stripe/webhook/",stripe_webhook,name="stripe_webhook")]
