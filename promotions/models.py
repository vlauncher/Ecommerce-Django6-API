from django.db import models
from django.conf import settings
from common.models import TimeStampedModel
from django.utils import timezone


class Coupon(TimeStampedModel):
    """Discount coupon code."""

    class DiscountType(models.TextChoices):
        PERCENTAGE = "percentage", "Percentage Discount"
        FIXED_AMOUNT = "fixed_amount", "Fixed Amount Discount"
        FREE_SHIPPING = "free_shipping", "Free Shipping"

    code = models.CharField(max_length=50, unique=True, db_index=True)
    discount_type = models.CharField(
        max_length=20, choices=DiscountType.choices, default=DiscountType.PERCENTAGE
    )
    value = models.DecimalField(
        max_digits=12, decimal_places=2, help_text="Percentage (e.g. 15.00 for 15%) or Fixed Amount ($10.00)"
    )

    min_order_value = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    max_discount_amount = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True,
        help_text="Cap for percentage discounts (null = uncapped)",
    )

    usage_limit_total = models.PositiveIntegerField(null=True, blank=True)
    usage_limit_per_user = models.PositiveIntegerField(default=1)
    times_used = models.PositiveIntegerField(default=0)

    valid_from = models.DateTimeField(default=timezone.now)
    valid_to = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Coupon {self.code} ({self.discount_type}: {self.value})"

    @property
    def is_valid(self):
        now = timezone.now()
        if not self.is_active:
            return False
        if self.valid_from and now < self.valid_from:
            return False
        if self.valid_to and now > self.valid_to:
            return False
        if self.usage_limit_total and self.times_used >= self.usage_limit_total:
            return False
        return True


class CouponUsage(TimeStampedModel):
    """Per-user coupon usage log."""

    coupon = models.ForeignKey(
        Coupon, on_delete=models.CASCADE, related_name="usages"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="coupon_usages"
    )
    order = models.ForeignKey(
        "orders.Order", on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        ordering = ["-created_at"]


class FlashSale(TimeStampedModel):
    """Time-limited product flash sale promotion."""

    title = models.CharField(max_length=255)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    products = models.ManyToManyField("catalog.Product", related_name="flash_sales")
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-start_time"]

    def __str__(self):
        return f"Flash Sale: {self.title} ({self.discount_percentage}%)"

    @property
    def is_currently_active(self):
        now = timezone.now()
        return self.is_active and self.start_time <= now <= self.end_time


class TieredPrice(TimeStampedModel):
    """Wholesale volume-based tiered pricing per variant."""

    variant = models.ForeignKey(
        "catalog.ProductVariant", on_delete=models.CASCADE, related_name="tiered_prices"
    )
    min_quantity = models.PositiveIntegerField(help_text="Minimum purchase quantity for tier")
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        unique_together = [("variant", "min_quantity")]
        ordering = ["min_quantity"]
