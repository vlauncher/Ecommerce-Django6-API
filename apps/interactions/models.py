from django.conf import settings
from django.db import models

from apps.catalog.models import Product, ProductVariant
from apps.commerce.models import Order, SellerOrder
from apps.shops.models import Shop


class Conversation(models.Model):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name="conversations")
    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="buyer_conversations")
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="seller_conversations")
    product = models.ForeignKey(Product, null=True, blank=True, on_delete=models.SET_NULL, related_name="conversations")
    order = models.ForeignKey(Order, null=True, blank=True, on_delete=models.SET_NULL, related_name="conversations")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    body = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)


class Offer(models.Model):
    class Status(models.TextChoices):
        SUBMITTED = "submitted", "Submitted"
        COUNTERED = "countered", "Countered"
        ACCEPTED = "accepted", "Accepted"
        REJECTED = "rejected", "Rejected"
        EXPIRED = "expired", "Expired"
        CANCELLED = "cancelled", "Cancelled"

    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name="offers")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="offers")
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, related_name="offers")
    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="offers")
    conversation = models.ForeignKey(Conversation, null=True, blank=True, on_delete=models.SET_NULL, related_name="offers")
    amount_minor = models.PositiveBigIntegerField()
    quantity = models.PositiveIntegerField(default=1)
    round_number = models.PositiveIntegerField(default=1)
    expires_at = models.DateTimeField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SUBMITTED)
    created_at = models.DateTimeField(auto_now_add=True)


class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="reviews")
    variant = models.ForeignKey(ProductVariant, null=True, blank=True, on_delete=models.SET_NULL)
    order = models.ForeignKey(Order, on_delete=models.PROTECT, related_name="reviews")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reviews")
    rating = models.PositiveSmallIntegerField()
    title = models.CharField(max_length=150, blank=True)
    body = models.TextField(blank=True)
    is_verified_purchase = models.BooleanField(default=True)
    is_published = models.BooleanField(default=False)
    seller_reply = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=("product", "order", "author"), name="unique_order_product_review")]


class Dispute(models.Model):
    class Status(models.TextChoices):
        OPEN = "open", "Open"
        SELLER_RESPONSE = "seller_response", "Seller response"
        SUPPORT_REVIEW = "support_review", "Support review"
        ESCALATED = "escalated", "Escalated"
        RESOLVED = "resolved", "Resolved"
        REJECTED = "rejected", "Rejected"

    order = models.ForeignKey(Order, on_delete=models.PROTECT, related_name="disputes")
    seller_order = models.ForeignKey(SellerOrder, null=True, on_delete=models.PROTECT, related_name="disputes")
    shop = models.ForeignKey(Shop, on_delete=models.PROTECT, related_name="disputes")
    opened_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="opened_disputes")
    reason = models.CharField(max_length=100)
    description = models.TextField()
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.OPEN)
    resolution = models.TextField(blank=True)
    due_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    kind = models.CharField(max_length=80)
    title = models.CharField(max_length=200)
    body = models.TextField()
    payload = models.JSONField(default=dict, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class AuditLog(models.Model):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="audit_logs")
    shop = models.ForeignKey(Shop, null=True, blank=True, on_delete=models.SET_NULL, related_name="audit_logs")
    action = models.CharField(max_length=100)
    resource = models.CharField(max_length=100)
    object_id = models.CharField(max_length=80, blank=True)
    payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
