from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.urls import reverse

from catalog.models import Product


class StaffAwareLoginView(LoginView):
    template_name = "registration/login.html"

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["username"].label = "Email or username"
        form.fields["username"].widget.attrs.update({"autocomplete": "username", "autocapitalize": "none"})
        return form

    def form_valid(self, form):
        response = super().form_valid(form)
        pending = self.request.session.pop("pending_cart_add", {})
        cart = self.request.session.get("cart", {})
        added = False
        unavailable = False
        for product_id, requested in pending.items():
            product = Product.objects.filter(pk=product_id, active=True).first()
            if not product:
                unavailable = True
                continue
            try:
                requested = max(1, min(50, int(requested)))
                current = max(0, int(cart.get(str(product.pk), 0)))
            except (TypeError, ValueError):
                requested, current = 1, 0
            quantity = min(product.stock, current + requested)
            if quantity > current:
                cart[str(product.pk)] = quantity
                added = True
            else:
                unavailable = True
        self.request.session["cart"] = cart
        if added:
            messages.success(self.request, "Your selected product has been added to your cart.")
        if unavailable:
            messages.warning(self.request, "One or more requested products are no longer available in that quantity.")
        return response

    def get_default_redirect_url(self):
        if self.request.user.is_authenticated and self.request.user.is_staff:
            return reverse("dashboard_home")
        return reverse("account")
