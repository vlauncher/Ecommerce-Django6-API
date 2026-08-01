from django.db import models
from common.models import TimeStampedModel


class PaymentTransaction(TimeStampedModel):
    """Transaction audit log for all payment processing attempts."""

    class Gateway(models.TextChoices):
        STRIPE = "stripe", "Stripe"
        PAYPAL = "paypal", "PayPal"
        FLUTTERWAVE = "flutterwave", "Flutterwave"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        AUTHORIZED = "authorized", "Authorized"
        CAPTURED = "captured", "Captured"
        FAILED = "failed", "Failed"
        REFUNDED = "refunded", "Refunded"

    order = models.ForeignKey(
        "orders.Order", on_delete=models.CASCADE, related_name="payments"
    )
    gateway = models.CharField(max_length=20, choices=Gateway.choices)
    gateway_transaction_id = models.CharField(max_length=255, db_index=True)
    gateway_response = models.JSONField(default=dict)

    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default="USD")
    status = models.CharField(
        max_length=25, choices=Status.choices, default=Status.PENDING
    )

    idempotency_key = models.CharField(max_length=255, unique=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.gateway.upper()} transaction {self.gateway_transaction_id} — {self.amount} {self.currency} ({self.status})"
