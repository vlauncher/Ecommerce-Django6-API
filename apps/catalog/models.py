from django.conf import settings
from django.db import models

from apps.shops.models import Shop


class Attribute(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, unique=True)
    input_type = models.CharField(max_length=20, default="text")

    def __str__(self):
        return self.name


class Category(models.Model):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name="categories")
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.CASCADE, related_name="children")
    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=160)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=("shop", "slug"), name="unique_shop_category_slug")]
        ordering = ("name",)


class Collection(models.Model):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name="collections")
    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=160)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    starts_at = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=("shop", "slug"), name="unique_shop_collection_slug")]


class Product(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PENDING = "pending", "Pending review"
        PUBLISHED = "published", "Published"
        ARCHIVED = "archived", "Archived"

    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name="products")
    category = models.ForeignKey(Category, null=True, blank=True, on_delete=models.SET_NULL, related_name="products")
    collections = models.ManyToManyField(Collection, blank=True, related_name="products")
    name = models.CharField(max_length=250)
    slug = models.SlugField(max_length=270)
    description = models.TextField(blank=True)
    product_type = models.CharField(max_length=50, default="physical")
    brand = models.CharField(max_length=120, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    is_digital = models.BooleanField(default=False)
    requires_shipping = models.BooleanField(default=True)
    seo_title = models.CharField(max_length=250, blank=True)
    seo_description = models.CharField(max_length=320, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="created_products")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=("shop", "slug"), name="unique_shop_product_slug")]
        indexes = [models.Index(fields=("shop", "status")), models.Index(fields=("name",))]


class ProductAttributeValue(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="attribute_values")
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE, related_name="product_values")
    value = models.CharField(max_length=500)

    class Meta:
        constraints = [models.UniqueConstraint(fields=("product", "attribute"), name="unique_product_attribute")]


class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants")
    name = models.CharField(max_length=250, blank=True)
    sku = models.CharField(max_length=100)
    barcode = models.CharField(max_length=100, blank=True)
    option_values = models.JSONField(default=dict, blank=True)
    price_minor = models.PositiveBigIntegerField()
    compare_at_price_minor = models.PositiveBigIntegerField(null=True, blank=True)
    currency = models.CharField(max_length=3, default="NGN")
    weight_grams = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=("product", "sku"), name="unique_product_variant_sku")]
        indexes = [models.Index(fields=("sku",)), models.Index(fields=("product", "is_active"))]


class BundleComponent(models.Model):
    bundle = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, related_name="bundle_components")
    component = models.ForeignKey(ProductVariant, on_delete=models.PROTECT, related_name="used_in_bundles")
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        constraints = [models.UniqueConstraint(fields=("bundle", "component"), name="unique_bundle_component")]


class Warehouse(models.Model):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name="warehouses")
    name = models.CharField(max_length=150)
    code = models.SlugField(max_length=80)
    address = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=("shop", "code"), name="unique_shop_warehouse_code")]


class StockItem(models.Model):
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, related_name="stock_items")
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name="stock_items")
    on_hand = models.IntegerField(default=0)
    reserved = models.IntegerField(default=0)
    reorder_level = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=("variant", "warehouse"), name="unique_variant_warehouse_stock")]

    @property
    def available(self):
        return max(self.on_hand - self.reserved, 0)


class InventoryLedgerEntry(models.Model):
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, related_name="inventory_entries")
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name="inventory_entries")
    quantity_delta = models.IntegerField()
    reason = models.CharField(max_length=40)
    reference = models.CharField(max_length=120, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)


class PriceRule(models.Model):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name="price_rules")
    name = models.CharField(max_length=150)
    variant = models.ForeignKey(ProductVariant, null=True, blank=True, on_delete=models.CASCADE, related_name="price_rules")
    percentage = models.PositiveIntegerField(null=True, blank=True)
    fixed_price_minor = models.PositiveBigIntegerField(null=True, blank=True)
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)


class Promotion(models.Model):
    class Kind(models.TextChoices):
        PERCENTAGE = "percentage", "Percentage"
        FIXED = "fixed", "Fixed amount"
        BUY_GET = "buy_get", "Buy X get Y"
        FREE_SHIPPING = "free_shipping", "Free shipping"

    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name="promotions")
    name = models.CharField(max_length=150)
    code = models.CharField(max_length=80, blank=True)
    kind = models.CharField(max_length=30, choices=Kind.choices)
    value = models.PositiveBigIntegerField(default=0)
    minimum_subtotal_minor = models.PositiveBigIntegerField(default=0)
    usage_limit = models.PositiveIntegerField(null=True, blank=True)
    per_customer_limit = models.PositiveIntegerField(null=True, blank=True)
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField(null=True, blank=True)
    is_automatic = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    products = models.ManyToManyField(Product, blank=True, related_name="promotions")
    categories = models.ManyToManyField(Category, blank=True, related_name="promotions")

    class Meta:
        indexes = [models.Index(fields=("shop", "is_active", "starts_at", "ends_at"))]


class Coupon(models.Model):
    promotion = models.OneToOneField(Promotion, on_delete=models.CASCADE, related_name="coupon")
    code = models.CharField(max_length=80, unique=True)
    usage_limit = models.PositiveIntegerField(null=True, blank=True)
    per_customer_limit = models.PositiveIntegerField(null=True, blank=True)
    used_count = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)


class CouponRedemption(models.Model):
    coupon = models.ForeignKey(Coupon, on_delete=models.PROTECT, related_name="redemptions")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="coupon_redemptions")
    order = models.ForeignKey("commerce.Order", on_delete=models.PROTECT, related_name="coupon_redemptions")
    amount_minor = models.PositiveBigIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=("coupon", "order"), name="unique_coupon_order_redemption")]
