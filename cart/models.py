from django.db import models
from django.conf import settings
from common.models import TimeStampedModel


class Cart(TimeStampedModel):
    """Shopping cart supporting authenticated users and guest sessions."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="cart",
    )
    session_key = models.CharField(
        max_length=40,
        null=True,
        blank=True,
        db_index=True,
        help_text="For anonymous/guest session carts",
    )

    def __str__(self):
        if self.user:
            return f"Cart for User: {self.user.email}"
        return f"Guest Cart: {self.session_key}"

    @property
    def total_quantity(self):
        return sum(item.quantity for item in self.items.all())

    @property
    def subtotal(self):
        return sum(item.subtotal for item in self.items.all())


class CartItem(TimeStampedModel):
    """Individual item in a shopping cart."""

    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name="items",
    )
    variant = models.ForeignKey(
        "catalog.ProductVariant",
        on_delete=models.CASCADE,
        related_name="cart_items",
    )
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = [("cart", "variant")]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.quantity}x {self.variant.product.name} ({self.variant.sku})"

    @property
    def subtotal(self):
        return self.variant.price * self.quantity


class SavedForLater(TimeStampedModel):
    """Items saved for later purchase by authenticated users."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="saved_items",
    )
    variant = models.ForeignKey(
        "catalog.ProductVariant",
        on_delete=models.CASCADE,
        related_name="saved_by_users",
    )

    class Meta:
        unique_together = [("user", "variant")]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.email} saved {self.variant.sku}"
