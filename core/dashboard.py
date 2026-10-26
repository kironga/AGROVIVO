from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.text import slugify
from django.views.decorators.http import require_POST

from catalog.models import CropStage, Product
from orders.models import Order, OrderStatus

from .dashboard_forms import OrderAdminForm, ProductAdminForm


@staff_member_required
def dashboard_home(request):
    today = timezone.localdate()
    orders = Order.objects.all()
    context = {
        "today_orders": orders.filter(created_at__date=today).count(),
        "open_orders": orders.filter(status__in=[OrderStatus.PENDING, OrderStatus.PAYMENT_PENDING, OrderStatus.PROCESSING]).count(),
        "paid_revenue": orders.filter(status__in=[OrderStatus.PAID, OrderStatus.SHIPPED, OrderStatus.DELIVERED]).aggregate(total=Sum("total_kes"))["total"] or 0,
        "product_count": Product.objects.filter(active=True).count(),
        "low_stock": Product.objects.filter(active=True, stock__lte=5).order_by("stock", "name")[:6],
        "recent_orders": orders.order_by("-created_at")[:8],
    }
    return render(request, "dashboard/home.html", context)


@staff_member_required
def product_list(request):
    products = Product.objects.all()
    query = request.GET.get("q", "").strip()
    status = request.GET.get("status", "active")
    if query:
        products = products.filter(Q(name__icontains=query) | Q(primary_role__icontains=query) | Q(formulation__icontains=query))
    if status == "active":
        products = products.filter(active=True)
    elif status == "archived":
        products = products.filter(active=False)
    products = products.order_by("name")
    return render(request, "dashboard/products.html", {"products": products, "query": query, "status": status})


@staff_member_required
def product_create(request):
    form = ProductAdminForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        product = form.save()
        messages.success(request, f"{product.name} has been added to the catalogue.")
        return redirect("dashboard_products")
    return render(request, "dashboard/product_form.html", {"form": form, "page_title": "Add product"})


@staff_member_required
def product_edit(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    form = ProductAdminForm(request.POST or None, instance=product)
    if request.method == "POST" and form.is_valid():
        product = form.save()
        messages.success(request, f"Changes to {product.name} have been saved.")
        return redirect("dashboard_products")
    return render(request, "dashboard/product_form.html", {"form": form, "product": product, "page_title": f"Edit {product.name}"})


@staff_member_required
@require_POST
def product_archive(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    product.active = not product.active
    product.save(update_fields=["active", "updated_at"])
    action = "published" if product.active else "archived"
    messages.success(request, f"{product.name} has been {action}.")
    return redirect("dashboard_products")


@staff_member_required
def order_list(request):
    orders = Order.objects.all().annotate(item_count=Count("items"))
    query = request.GET.get("q", "").strip()
    status = request.GET.get("status", "")
    if query:
        orders = orders.filter(Q(order_number__icontains=query) | Q(customer_name__icontains=query) | Q(customer_phone__icontains=query))
    if status in OrderStatus.values:
        orders = orders.filter(status=status)
    return render(request, "dashboard/orders.html", {"orders": orders.order_by("-created_at"), "query": query, "status": status, "statuses": OrderStatus.choices})


@staff_member_required
def order_detail(request, order_id):
    order = get_object_or_404(Order.objects.prefetch_related("items__product"), pk=order_id)
    form = OrderAdminForm(request.POST or None, instance=order)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, f"Order {order.order_number} has been updated.")
        return redirect("dashboard_order_detail", order_id=order.pk)
    return render(request, "dashboard/order_detail.html", {"order": order, "form": form})
