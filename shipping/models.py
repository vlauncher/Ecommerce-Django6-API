from django.db import models
from common.models import TimeStampedModel


class ShippingZone(TimeStampedModel):
    """Geographic shipping zone."""

    name = models.CharField(max_length=255)
    countries = models.JSONField(default=list, help_text='List of ISO country codes, e.g. ["US", "CA", "GB"]')
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class ShippingMethod(TimeStampedModel):
    """Shipping method offered within a shipping zone."""

    class RateType(models.TextChoices):
        FLAT_RATE = "flat_rate", "Flat Rate"
        WEIGHT_BASED = "weight_based", "Weight-Based Tier"
        PRICE_BASED = "price_based", "Price-Based Tier"

    zone = models.ForeignKey(
        ShippingZone, on_delete=models.CASCADE, related_name="methods"
    )
    name = models.CharField(max_length=255)
    rate_type = models.CharField(
        max_length=20, choices=RateType.choices, default=RateType.FLAT_RATE
    )
    base_rate = models.DecimalField(max_digits=12, decimal_places=2)
    free_shipping_threshold = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    estimated_days = models.CharField(
        max_length=50, blank=True, help_text='Estimated delivery window, e.g. "3-5 business days"'
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["base_rate"]

    def __str__(self):
        return f"{self.name} ({self.zone.name}) — {self.base_rate}"


class Fulfillment(TimeStampedModel):
    """Shipment dispatch tracking for a vendor sub-order."""

    class Status(models.TextChoices):
        PREPARING = "preparing", "Preparing Package"
        DISPATCHED = "dispatched", "Dispatched / In Transit"
        DELIVERED = "delivered", "Delivered"
        FAILED = "failed", "Delivery Failed"

    sub_order = models.OneToOneField(
        "orders.VendorSubOrder", on_delete=models.CASCADE, related_name="fulfillment"
    )
    warehouse = models.ForeignKey(
        "inventory.Warehouse", on_delete=models.PROTECT, related_name="fulfillments"
    )
    carrier = models.CharField(max_length=100, help_text='Carrier name, e.g. "FedEx", "DHL", "UPS"')
    tracking_number = models.CharField(max_length=100)
    tracking_url = models.URLField(blank=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PREPARING
    )
    shipped_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.carrier} {self.tracking_number} ({self.status})"
