from django.contrib import admin
from django.urls import include,path
from django.contrib.sitemaps.views import sitemap
from django.http import JsonResponse
from core.views import HomeView,AboutView,ContactView,RobotsView,ResourcesView,PartnersView,LegalView,DifferenceView
from core.sitemaps import StaticViewSitemap
from catalog.views import product_list,product_detail,programme_list,programme_detail
from cart.views import cart_page,add_to_cart,update_cart,remove_from_cart
from orders.views import checkout,confirmation
sitemaps={"pages":StaticViewSitemap}
urlpatterns=[
 path("healthz",lambda request:JsonResponse({"status":"ok"}),name="healthz"),
 path("admin/",admin.site.urls),path("",HomeView.as_view(),name="home"),path("about/",AboutView.as_view(),name="about"),path("difference/",DifferenceView.as_view(),name="difference"),path("resources/",ResourcesView.as_view(),name="resources"),path("partners/",PartnersView.as_view(),name="partners"),path("privacy/",LegalView.as_view(),{"title":"Privacy policy"},name="privacy"),path("terms/",LegalView.as_view(),{"title":"Terms of use"},name="terms"),path("contact/",ContactView.as_view(),name="contact"),
 path("products/",product_list,name="products"),path("products/<slug:slug>/",product_detail,name="product_detail"),
 path("crop-programmes/",programme_list,name="programmes"),path("crop-programmes/<slug:slug>/",programme_detail,name="programme_detail"),
 path("cart/",cart_page,name="cart"),path("cart/add/<int:product_id>/",add_to_cart,name="cart_add"),path("cart/update/<int:product_id>/",update_cart,name="cart_update"),path("cart/remove/<int:product_id>/",remove_from_cart,name="cart_remove"),
 path("checkout/",checkout,name="checkout"),path("order/<str:order_number>/confirmation/",confirmation,name="confirmation"),
 path("accounts/",include("django.contrib.auth.urls")),path("account/",include("accounts.urls")),
 path("payments/",include("payments.urls")),
 path("sitemap.xml",sitemap,{"sitemaps":sitemaps},name="sitemap"),path("robots.txt",RobotsView.as_view(),name="robots")]
