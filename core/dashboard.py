from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import user_passes_test
from django.db import transaction
from django.db.models import Count, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.text import slugify
from django.views.decorators.http import require_POST

from catalog.models import CropStage, Product
from orders.models import Order, OrderStatus
from orders.services import cancel_order as cancel_order_service, OrderCancellationError

from .dashboard_forms import OrderAdminForm, ProductAdminForm
from accounts.forms import AdminSetPasswordForm, AdminUserCreateForm
from accounts.models import CustomerProfile
from cart.models import CartItem

User = get_user_model()
superuser_required = user_passes_test(lambda user: user.is_authenticated and user.is_superuser)


@staff_member_required
def dashboard_home(request):
    today = timezone.localdate()
    orders = Order.objects.all()
    context = {
        "today_orders": orders.filter(created_at__date=today).count(),
        "open_orders": orders.filter(status__in=[OrderStatus.PENDING, OrderStatus.PAYMENT_PENDING, OrderStatus.PROCESSING]).count(),
        "paid_revenue": orders.filter(status__in=[OrderStatus.PAID, OrderStatus.SHIPPED, OrderStatus.DELIVERED]).aggregate(total=Sum("total_kes"))["total"] or 0,
        "product_count": Product.objects.filter(active=True).count(),
        "active_carts": CartItem.objects.filter(user__is_staff=False).values("user_id").distinct().count(),
        "unassigned_deliveries": orders.filter(status=OrderStatus.SHIPPED, delivery_agent_phone="").count(),
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
    form = ProductAdminForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        product = form.save()
        messages.success(request, f"{product.name} has been added to the catalogue.")
        return redirect("dashboard_products")
    return render(request, "dashboard/product_form.html", {"form": form, "page_title": "Add product"})


@staff_member_required
def product_edit(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    form = ProductAdminForm(request.POST or None, request.FILES or None, instance=product)
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


@staff_member_required
@require_POST
def order_cancel(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    try:
        cancel_order_service(order.pk, request.user)
    except OrderCancellationError as error:
        messages.error(request, str(error))
    else:
        if order.payment_ref or order.status == OrderStatus.PAID:
            messages.warning(request, f"Order {order.order_number} cancelled and stock returned. Any paid M-Pesa amount must be refunded separately.")
        else:
            messages.success(request, f"Order {order.order_number} cancelled and its stock returned to inventory.")
    return redirect("dashboard_order_detail", order_id=order.pk)


@staff_member_required
def user_list(request):
    query = request.GET.get("q", "").strip()
    users = User.objects.all() if request.user.is_superuser else User.objects.filter(is_staff=False)
    if query:
        users = users.filter(Q(username__icontains=query) | Q(email__icontains=query) | Q(first_name__icontains=query) | Q(last_name__icontains=query) | Q(customer_profile__phone__icontains=query)).distinct()
    return render(request, "dashboard/users.html", {"users": users.order_by("-date_joined"), "query": query, "customer_count": User.objects.filter(is_staff=False).count(), "staff_count": User.objects.filter(is_staff=True).count() if request.user.is_superuser else None})


@superuser_required
def user_create(request):
    form = AdminUserCreateForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        data = form.cleaned_data
        with transaction.atomic():
            user = User.objects.create_user(
                username=data["email"], email=data["email"],
                first_name=data["first_name"].strip(), last_name=data["last_name"].strip(),
                password=data["password"], is_staff=(data["role"] == "staff"),
            )
            if data["role"] == "customer":
                CustomerProfile.objects.create(user=user, phone=data["phone"])
        messages.success(request, f"{data['role'].title()} account created for {user.get_full_name()}.")
        return redirect("dashboard_users")
    return render(request, "dashboard/user_form.html", {"form": form, "page_title": "Create a user"})


@superuser_required
def user_password_reset(request, user_id):
    target = get_object_or_404(User, pk=user_id)
    if target.is_superuser and target.pk == request.user.pk:
        messages.info(request, "Use your own account password reset flow to change your administrator password.")
        return redirect("dashboard_users")
    form = AdminSetPasswordForm(request.POST or None, user=target)
    if request.method == "POST" and form.is_valid():
        target.set_password(form.cleaned_data["password"])
        target.save(update_fields=["password"])
        messages.success(request, f"Password updated for {target.get_full_name() or target.email}. Share the new password with them securely.")
        return redirect("dashboard_users")
    return render(request, "dashboard/user_password.html", {"form": form, "target_user": target})


@staff_member_required
def cart_list(request):
    items = CartItem.objects.filter(user__is_staff=False).select_related("user", "product").order_by("-updated_at")
    query = request.GET.get("q", "").strip()
    if query:
        items = items.filter(
            Q(user__email__icontains=query) | Q(user__first_name__icontains=query)
            | Q(user__last_name__icontains=query) | Q(user__customer_profile__phone__icontains=query)
            | Q(product__name__icontains=query)
        )
    customers = {}
    for item in items:
        customer = customers.setdefault(item.user_id, {"user": item.user, "items": 0, "subtotal": 0, "updated_at": item.updated_at})
        customer["items"] += item.quantity
        customer["subtotal"] += item.product.price_kes * item.quantity
        if item.updated_at > customer["updated_at"]:
            customer["updated_at"] = item.updated_at
    return render(request, "dashboard/carts.html", {"customers": sorted(customers.values(), key=lambda row: row["updated_at"], reverse=True), "query": query, "cart_count": len(customers), "item_count": sum(row["items"] for row in customers.values())})


@staff_member_required
def cart_detail(request, user_id):
    customer = get_object_or_404(User, pk=user_id, is_staff=False)
    items = CartItem.objects.filter(user=customer).select_related("product").order_by("updated_at")
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "clear":
            items.delete()
            messages.success(request, f"Cleared {customer.get_full_name() or customer.email}’s cart.")
            return redirect("dashboard_carts")
        item = get_object_or_404(items, pk=request.POST.get("item_id"))
        if action == "remove":
            item.delete()
            messages.success(request, f"Removed {item.product.name} from the customer’s cart.")
        elif action == "quantity":
            try:
                quantity = int(request.POST.get("quantity", "1"))
            except (TypeError, ValueError):
                quantity = -1
            if quantity < 0:
                messages.error(request, "Enter a valid quantity.")
            elif quantity == 0:
                item.delete()
                messages.success(request, f"Removed {item.product.name} from the customer’s cart.")
            elif quantity > item.product.stock:
                messages.error(request, f"Only {item.product.stock} units of {item.product.name} are in stock.")
            else:
                item.quantity = quantity
                item.save(update_fields=["quantity", "updated_at"])
                messages.success(request, "Cart quantity updated.")
        return redirect("dashboard_cart_detail", user_id=customer.pk)
    return render(request, "dashboard/cart_detail.html", {"customer": customer, "items": items, "subtotal": sum(item.product.price_kes * item.quantity for item in items), "item_count": sum(item.quantity for item in items)})
