from django.conf import settings
from django.db import models

from apps.commerce.models import Order, SellerOrder
from apps.shops.models import Shop


class Payment(models.Model):
    class Status(models.TextChoices):
        INITIALIZED = "initialized", "Initialized"
        PENDING = "pending", "Pending"
        SUCCESS = "success", "Success"
        FAILED = "failed", "Failed"
        REFUNDED = "refunded", "Refunded"
        PARTIALLY_REFUNDED = "partially_refunded", "Partially refunded"

    order = models.OneToOneField(Order, on_delete=models.PROTECT, related_name="payment")
    provider = models.CharField(max_length=30, default="paystack")
    reference = models.CharField(max_length=100, unique=True)
    provider_id = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.INITIALIZED)
    amount_minor = models.PositiveBigIntegerField()
    currency = models.CharField(max_length=3, default="NGN")
    raw_data = models.JSONField(default=dict, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class PaymentEvent(models.Model):
    provider = models.CharField(max_length=30, default="paystack")
    event_id = models.CharField(max_length=150, unique=True)
    event_type = models.CharField(max_length=100)
    payload = models.JSONField(default=dict)
    processed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class Refund(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        NEEDS_ATTENTION = "needs_attention", "Needs attention"
        PROCESSED = "processed", "Processed"
        FAILED = "failed", "Failed"

    payment = models.ForeignKey(Payment, on_delete=models.PROTECT, related_name="refunds")
    reference = models.CharField(max_length=100, unique=True)
    amount_minor = models.PositiveBigIntegerField()
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.PENDING)
    reason = models.TextField(blank=True)
    raw_data = models.JSONField(default=dict, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)


class LedgerEntry(models.Model):
    class EntryType(models.TextChoices):
        PAYMENT = "payment", "Payment"
        COMMISSION = "commission", "Commission"
        SELLER_PAYABLE = "seller_payable", "Seller payable"
        REFUND = "refund", "Refund"
        HOLD = "hold", "Hold"
        RELEASE = "release", "Release"
        WITHDRAWAL = "withdrawal", "Withdrawal"
        ADJUSTMENT = "adjustment", "Adjustment"

    shop = models.ForeignKey(Shop, null=True, on_delete=models.PROTECT, related_name="ledger_entries")
    seller_order = models.ForeignKey(SellerOrder, null=True, blank=True, on_delete=models.PROTECT, related_name="ledger_entries")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name="ledger_entries")
    entry_type = models.CharField(max_length=30, choices=EntryType.choices)
    amount_minor = models.BigIntegerField()
    currency = models.CharField(max_length=3, default="NGN")
    reference = models.CharField(max_length=150, unique=True)
    available_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class PayoutRecipient(models.Model):
    shop = models.OneToOneField(Shop, on_delete=models.CASCADE, related_name="payout_recipient")
    bank_code = models.CharField(max_length=30)
    account_number = models.CharField(max_length=30)
    account_name = models.CharField(max_length=150, blank=True)
    recipient_code = models.CharField(max_length=100, blank=True)
    is_verified = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)


class Withdrawal(models.Model):
    class Status(models.TextChoices):
        REQUESTED = "requested", "Requested"
        APPROVED = "approved", "Approved"
        PROCESSING = "processing", "Processing"
        SUCCESS = "success", "Success"
        FAILED = "failed", "Failed"
        REVERSED = "reversed", "Reversed"
        REJECTED = "rejected", "Rejected"

    shop = models.ForeignKey(Shop, on_delete=models.PROTECT, related_name="withdrawals")
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    amount_minor = models.PositiveBigIntegerField()
    currency = models.CharField(max_length=3, default="NGN")
    reference = models.CharField(max_length=100, unique=True)
    transfer_code = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.REQUESTED)
    reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
