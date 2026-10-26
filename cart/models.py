from django.conf import settings
from django.db import models

from catalog.models import Product


class CartItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="cart_items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="cart_items")
    quantity = models.PositiveSmallIntegerField(default=1)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "product"], name="unique_user_cart_product")]
        ordering = ["updated_at"]

    def __str__(self):
        return f"{self.user} · {self.product} × {self.quantity}"
