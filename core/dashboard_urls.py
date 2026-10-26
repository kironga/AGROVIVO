from django.urls import path

from . import dashboard

urlpatterns = [
    path("", dashboard.dashboard_home, name="dashboard_home"),
    path("products/", dashboard.product_list, name="dashboard_products"),
    path("products/new/", dashboard.product_create, name="dashboard_product_create"),
    path("products/<int:product_id>/edit/", dashboard.product_edit, name="dashboard_product_edit"),
    path("products/<int:product_id>/archive/", dashboard.product_archive, name="dashboard_product_archive"),
    path("orders/", dashboard.order_list, name="dashboard_orders"),
    path("orders/<int:order_id>/", dashboard.order_detail, name="dashboard_order_detail"),
]
