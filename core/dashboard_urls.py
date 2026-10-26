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
    path("users/", dashboard.user_list, name="dashboard_users"),
    path("users/new/", dashboard.user_create, name="dashboard_user_create"),
    path("users/<int:user_id>/password/", dashboard.user_password_reset, name="dashboard_user_password_reset"),
]
