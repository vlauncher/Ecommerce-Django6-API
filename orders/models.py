from django.db import models
from django.conf import settings
from django_fsm import FSMField, transition
from common.models import TimeStampedModel
from django.utils import timezone


class Order(TimeStampedModel):
    """Master order with FSM-managed lifecycle."""

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PENDING_PAYMENT = "pending_payment", "Pending Payment"
        PAID = "paid", "Paid"
        PROCESSING = "processing", "Processing"
        PARTIALLY_SHIPPED = "partially_shipped", "Partially Shipped"
        SHIPPED = "shipped", "Shipped"
        DELIVERED = "delivered", "Delivered"
        CANCELLED = "cancelled", "Cancelled"
        REFUNDED = "refunded", "Refunded"

    order_number = models.CharField(max_length=30, unique=True, db_index=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="orders",
    )

    status = FSMField(
        default=Status.DRAFT,
        choices=Status.choices,
        db_index=True,
        protected=True,
    )

    shipping_address = models.JSONField(default=dict)
    billing_address = models.JSONField(default=dict)

    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    shipping_total = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    tax_total = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    discount_total = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    grand_total = models.DecimalField(max_digits=12, decimal_places=2)

    currency = models.CharField(max_length=3, default="USD")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    notes = models.TextField(blank=True)

    paid_at = models.DateTimeField(null=True, blank=True)
    shipped_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"Order #{self.order_number} ({self.user.email})"

    # FSM State Transitions
    @transition(field=status, source=Status.DRAFT, target=Status.PENDING_PAYMENT)
    def place_order(self):
        """Transition from draft to pending payment."""
        pass

    @transition(field=status, source=[Status.DRAFT, Status.PENDING_PAYMENT], target=Status.PAID)
    def mark_paid(self):
        """Transition to paid upon payment verification."""
        self.paid_at = timezone.now()

    @transition(field=status, source=Status.PAID, target=Status.PROCESSING)
    def start_processing(self):
        """Vendor starts fulfilling items."""
        pass

    @transition(field=status, source=[Status.PROCESSING, Status.PARTIALLY_SHIPPED], target=Status.SHIPPED)
    def mark_shipped(self):
        """Order dispatched."""
        self.shipped_at = timezone.now()

    @transition(field=status, source=Status.SHIPPED, target=Status.DELIVERED)
    def mark_delivered(self):
        """Order delivered to customer."""
        self.delivered_at = timezone.now()

    @transition(field=status, source=[Status.DRAFT, Status.PENDING_PAYMENT, Status.PAID], target=Status.CANCELLED)
    def cancel(self):
        """Cancel unfulfilled order."""
        pass


class VendorSubOrder(TimeStampedModel):
    """Vendor-specific sub-order for multi-vendor fulfillment isolation."""

    class Status(models.TextChoices):
        PROCESSING = "processing", "Processing"
        SHIPPED = "shipped", "Shipped"
        DELIVERED = "delivered", "Delivered"
        CANCELLED = "cancelled", "Cancelled"

    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="sub_orders"
    )
    vendor = models.ForeignKey(
        "vendors.Vendor", on_delete=models.PROTECT, related_name="sub_orders"
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PROCESSING
    )
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    commission_amount = models.DecimalField(max_digits=12, decimal_places=2)
    vendor_payout = models.DecimalField(max_digits=12, decimal_places=2)

    tracking_number = models.CharField(max_length=100, blank=True)
    tracking_url = models.URLField(blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Sub-Order #{self.order.order_number} — {self.vendor.store_name}"


class OrderItem(TimeStampedModel):
    """Line item snapshot — freezes product details at checkout time."""

    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="items"
    )
    sub_order = models.ForeignKey(
        VendorSubOrder, on_delete=models.CASCADE, related_name="items"
    )
    variant = models.ForeignKey(
        "catalog.ProductVariant", on_delete=models.PROTECT
    )

    # Point-in-time snapshot fields
    product_name = models.CharField(max_length=500)
    variant_name = models.CharField(max_length=255, blank=True)
    sku = models.CharField(max_length=100)
    variant_attributes = models.JSONField(default=dict)

    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    quantity = models.PositiveIntegerField()
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    line_total = models.DecimalField(max_digits=12, decimal_places=2)

    # Digital product delivery
    download_url = models.URLField(blank=True)
    download_count = models.PositiveIntegerField(default=0)
    download_expires_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.quantity}x {self.product_name} ({self.sku})"


class OrderLog(TimeStampedModel):
    """Immutable audit trail for order state changes."""

    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="logs"
    )
    from_status = models.CharField(max_length=30)
    to_status = models.CharField(max_length=30)
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"Order #{self.order.order_number}: {self.from_status} -> {self.to_status}"


class ReturnRequest(TimeStampedModel):
    """Return Merchandise Authorization (RMA)."""

    class Status(models.TextChoices):
        REQUESTED = "requested", "Requested"
        APPROVED = "approved", "Approved"
        RECEIVED = "received", "Received"
        REFUNDED = "refunded", "Refunded"
        REJECTED = "rejected", "Rejected"

    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="returns"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.REQUESTED
    )
    reason = models.TextField()
    admin_notes = models.TextField(blank=True)
    refund_amount = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )

    def __str__(self):
        return f"RMA for Order #{self.order.order_number} ({self.status})"


class ReturnItem(TimeStampedModel):
    """Items included in return request."""

    return_request = models.ForeignKey(
        ReturnRequest, on_delete=models.CASCADE, related_name="items"
    )
    order_item = models.ForeignKey(
        OrderItem, on_delete=models.CASCADE
    )
    quantity = models.PositiveIntegerField()
    reason = models.CharField(max_length=255, blank=True)
