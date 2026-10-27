from django.db import transaction
from django.db.models import F

from catalog.models import Product
from .models import Order, OrderStatus


class OrderCancellationError(Exception):
    pass


@transaction.atomic
def cancel_order(order_id, actor):
    order = Order.objects.select_for_update().get(pk=order_id)
    if order.status == OrderStatus.CANCELLED:
        raise OrderCancellationError("This order is already cancelled.")

    if actor.is_staff:
        if order.status == OrderStatus.DELIVERED:
            raise OrderCancellationError("A delivered order cannot be cancelled.")
    else:
        if order.user_id != actor.pk:
            raise OrderCancellationError("You can only cancel your own orders.")
        if not order.customer_can_cancel:
            raise OrderCancellationError("Customers can cancel only before payment and dispatch.")

    for item in order.items.all():
        Product.objects.filter(pk=item.product_id).update(stock=F("stock") + item.quantity)

    order.status = OrderStatus.CANCELLED
    order.save(update_fields=["status", "updated_at"])
    return order
