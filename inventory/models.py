from django.db import models
from django.conf import settings
from common.models import TimeStampedModel


class Warehouse(TimeStampedModel):
    """Fulfillment warehouse location."""

    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, unique=True)
    address = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.code})"


class StockRecord(TimeStampedModel):
    """Per-variant, per-warehouse stock level tracking."""

    variant = models.ForeignKey(
        "catalog.ProductVariant",
        on_delete=models.CASCADE,
        related_name="stock_records",
    )
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.CASCADE,
        related_name="stock_records",
    )
    quantity = models.PositiveIntegerField(default=0)
    reserved = models.PositiveIntegerField(default=0)
    low_stock_threshold = models.PositiveIntegerField(default=5)

    class Meta:
        unique_together = [("variant", "warehouse")]
        ordering = ["-updated_at"]

    def __str__(self):
        return f"{self.variant.sku} @ {self.warehouse.code}: {self.available_quantity} available"

    @property
    def available_quantity(self):
        return max(0, self.quantity - self.reserved)


class StockMovement(TimeStampedModel):
    """Immutable stock movement audit ledger."""

    class MovementType(models.TextChoices):
        PURCHASE_RECEIPT = "purchase_receipt", "Purchase Receipt"
        CUSTOMER_ORDER = "customer_order", "Customer Order"
        RESERVATION_HOLD = "reservation_hold", "Reservation Hold"
        RESERVATION_RELEASE = "reservation_release", "Reservation Release"
        RETURN_RESTOCK = "return_restock", "Return Restock"
        MANUAL_ADJUSTMENT = "manual_adjustment", "Manual Adjustment"
        DAMAGE_LOSS = "damage_loss", "Damage / Loss"

    variant = models.ForeignKey(
        "catalog.ProductVariant",
        on_delete=models.CASCADE,
        related_name="stock_movements",
    )
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.CASCADE,
        related_name="stock_movements",
    )
    movement_type = models.CharField(max_length=30, choices=MovementType.choices)
    quantity_delta = models.IntegerField()
    reference_id = models.CharField(max_length=255, blank=True)
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.movement_type}: {self.quantity_delta} for {self.variant.sku}"
