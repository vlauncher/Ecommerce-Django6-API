from django.conf import settings
from django.db import models

from apps.catalog.models import ProductVariant
from apps.shops.models import Shop


class CustomerProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="customer_profile")
    phone = models.CharField(max_length=30, blank=True)
    marketing_opt_in = models.BooleanField(default=False)
    tags = models.JSONField(default=list, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class Address(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="addresses")
    label = models.CharField(max_length=80, default="default")
    recipient_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=30, blank=True)
    line1 = models.CharField(max_length=250)
    line2 = models.CharField(max_length=250, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=2, default="NG")
    postal_code = models.CharField(max_length=30, blank=True)


class ShippingZone(models.Model):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name="shipping_zones")
    name = models.CharField(max_length=100)
    countries = models.JSONField(default=list, blank=True)
    states = models.JSONField(default=list, blank=True)
    is_active = models.BooleanField(default=True)


class ShippingRate(models.Model):
    zone = models.ForeignKey(ShippingZone, on_delete=models.CASCADE, related_name="rates")
    name = models.CharField(max_length=100)
    amount_minor = models.PositiveBigIntegerField()
    currency = models.CharField(max_length=3, default="NGN")
    min_subtotal_minor = models.PositiveBigIntegerField(default=0)
    estimated_days = models.PositiveIntegerField(default=3)


class TaxRate(models.Model):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name="tax_rates")
    name = models.CharField(max_length=100)
    percentage = models.DecimalField(max_digits=5, decimal_places=2)
    country = models.CharField(max_length=2, default="NG")
    state = models.CharField(max_length=100, blank=True)
    is_inclusive = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)


class Cart(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.CASCADE, related_name="carts")
    guest_token = models.CharField(max_length=100, blank=True, db_index=True)
    currency = models.CharField(max_length=3, default="NGN")
    coupon_code = models.CharField(max_length=80, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, related_name="cart_items")
    quantity = models.PositiveIntegerField()
    price_minor_snapshot = models.PositiveBigIntegerField()
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=("cart", "variant"), name="unique_cart_variant")]


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING_PAYMENT = "pending_payment", "Pending payment"
        PAID = "paid", "Paid"
        PROCESSING = "processing", "Processing"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"
        REFUNDED = "refunded", "Refunded"

    number = models.CharField(max_length=40, unique=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="orders")
    guest_email = models.EmailField(blank=True)
    guest_token = models.CharField(max_length=100, blank=True, db_index=True)
    currency = models.CharField(max_length=3, default="NGN")
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.PENDING_PAYMENT)
    subtotal_minor = models.PositiveBigIntegerField(default=0)
    discount_minor = models.PositiveBigIntegerField(default=0)
    shipping_minor = models.PositiveBigIntegerField(default=0)
    tax_minor = models.PositiveBigIntegerField(default=0)
    tip_minor = models.PositiveBigIntegerField(default=0)
    total_minor = models.PositiveBigIntegerField(default=0)
    shipping_address = models.JSONField(default=dict)
    billing_address = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class SellerOrder(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        SHIPPED = "shipped", "Shipped"
        DELIVERED = "delivered", "Delivered"
        CANCELLED = "cancelled", "Cancelled"
        DISPUTED = "disputed", "Disputed"

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="seller_orders")
    shop = models.ForeignKey(Shop, on_delete=models.PROTECT, related_name="seller_orders")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    subtotal_minor = models.PositiveBigIntegerField(default=0)
    commission_minor = models.PositiveBigIntegerField(default=0)
    seller_net_minor = models.PositiveBigIntegerField(default=0)
    delivered_at = models.DateTimeField(null=True, blank=True)
    hold_until = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=("order", "shop"), name="unique_order_shop")]


class OrderItem(models.Model):
    seller_order = models.ForeignKey(SellerOrder, on_delete=models.CASCADE, related_name="items")
    variant = models.ForeignKey(ProductVariant, null=True, on_delete=models.SET_NULL, related_name="order_items")
    product_name = models.CharField(max_length=250)
    variant_name = models.CharField(max_length=250, blank=True)
    sku = models.CharField(max_length=100)
    quantity = models.PositiveIntegerField()
    unit_price_minor = models.PositiveBigIntegerField()
    discount_minor = models.PositiveBigIntegerField(default=0)
    tax_minor = models.PositiveBigIntegerField(default=0)
    total_minor = models.PositiveBigIntegerField()
    metadata = models.JSONField(default=dict, blank=True)


class Shipment(models.Model):
    seller_order = models.ForeignKey(SellerOrder, on_delete=models.CASCADE, related_name="shipments")
    carrier = models.CharField(max_length=100, blank=True)
    tracking_number = models.CharField(max_length=150, blank=True)
    status = models.CharField(max_length=30, default="pending")
    shipped_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)


class ReturnRequest(models.Model):
    class Status(models.TextChoices):
        REQUESTED = "requested", "Requested"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        RECEIVED = "received", "Received"
        REFUNDED = "refunded", "Refunded"

    order = models.ForeignKey(Order, on_delete=models.PROTECT, related_name="return_requests")
    seller_order = models.ForeignKey(SellerOrder, on_delete=models.PROTECT, related_name="return_requests")
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="return_requests")
    reason = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.REQUESTED)
    resolution = models.TextField(blank=True)
    refund_amount_minor = models.PositiveBigIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class CheckoutAttempt(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="checkout_attempts")
    idempotency_key = models.CharField(max_length=120)
    response = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=("user", "idempotency_key"), name="unique_user_checkout_idempotency_key")]


class WishlistItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="wishlist_items")
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, related_name="wishlists")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=("user", "variant"), name="unique_wishlist_variant")]


class GiftCard(models.Model):
    code = models.CharField(max_length=80, unique=True)
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name="gift_cards")
    purchaser = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="purchased_gift_cards")
    recipient_email = models.EmailField(blank=True)
    initial_amount_minor = models.PositiveBigIntegerField()
    balance_minor = models.PositiveBigIntegerField()
    currency = models.CharField(max_length=3, default="NGN")
    expires_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)


class GiftCardTransaction(models.Model):
    gift_card = models.ForeignKey(GiftCard, on_delete=models.PROTECT, related_name="transactions")
    order = models.ForeignKey(Order, null=True, blank=True, on_delete=models.PROTECT)
    amount_minor = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
