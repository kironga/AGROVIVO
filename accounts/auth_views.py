from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse

from catalog.models import Product
from cart.models import CartItem


class StaffAwareLoginView(LoginView):
    template_name = "registration/login.html"

    def get_role_redirect_url(self):
        if self.request.user.is_authenticated and self.request.user.is_staff:
            return reverse("dashboard_home")
        return reverse("account")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(self.get_role_redirect_url())
        return super().dispatch(request, *args, **kwargs)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["username"].label = "Email or username"
        form.fields["username"].widget.attrs.update({"autocomplete": "username", "autocapitalize": "none"})
        return form

    def form_valid(self, form):
        response = super().form_valid(form)
        pending = self.request.session.pop("pending_cart_add", {})
        added = False
        unavailable = False
        for product_id, requested in pending.items():
            product = Product.objects.filter(pk=product_id, active=True).first()
            if not product:
                unavailable = True
                continue
            try:
                requested = max(1, min(50, int(requested)))
                existing = CartItem.objects.filter(user=self.request.user, product=product).first()
                current = existing.quantity if existing else 0
            except (TypeError, ValueError):
                requested, current = 1, 0
            quantity = min(product.stock, current + requested)
            if quantity > current:
                CartItem.objects.update_or_create(user=self.request.user, product=product, defaults={"quantity": quantity})
                added = True
            else:
                unavailable = True
        if added:
            messages.success(self.request, "Your selected product has been added to your cart.")
        if unavailable:
            messages.warning(self.request, "One or more requested products are no longer available in that quantity.")
        return response

    def get_success_url(self):
        # Always land in the correct dashboard after authentication, even when
        # the login form was opened with a stale or unrelated `next` value.
        return self.get_role_redirect_url()
