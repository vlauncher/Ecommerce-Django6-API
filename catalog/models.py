import uuid
from django.db import models
from treebeard.mp_tree import MP_Node
from common.models import TimeStampedModel


# ─── CATEGORIES ────────────────────────────────────────────

class Category(MP_Node):
    """
    Hierarchical product categories using Materialized Path (django-treebeard).
    Supports unlimited nesting: Electronics > Phones > Smartphones > Android
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, db_index=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to="categories/", blank=True, null=True)
    is_active = models.BooleanField(default=True)
    meta_title = models.CharField(max_length=255, blank=True)
    meta_description = models.TextField(blank=True)

    node_order_by = ["name"]

    class Meta:
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name

    @property
    def full_path(self):
        """Returns breadcrumb path: 'Electronics > Phones > Smartphones'"""
        ancestors = self.get_ancestors()
        if ancestors:
            return " > ".join([node.name for node in ancestors] + [self.name])
        return self.name


# ─── PRODUCT TYPES ─────────────────────────────────────────

class ProductType(TimeStampedModel):
    """
    Defines the 'kind' of product and which attribute groups apply.
    Examples: 'T-Shirt', 'Laptop', 'eBook', 'Online Course'
    """
    class Kind(models.TextChoices):
        PHYSICAL = "physical", "Physical"
        DIGITAL = "digital", "Digital"

    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True)
    kind = models.CharField(max_length=10, choices=Kind.choices, default=Kind.PHYSICAL)
    requires_shipping = models.BooleanField(default=True)
    is_digital = models.BooleanField(default=False)

    attribute_groups = models.ManyToManyField(
        "AttributeGroup", blank=True, related_name="product_types"
    )
    variation_attributes = models.ManyToManyField(
        "Attribute", blank=True, related_name="variant_product_types",
        help_text="Attributes that create product variants (e.g., Size, Color)",
    )

    def __str__(self):
        return self.name


# ─── ATTRIBUTES (EAV-like system) ──────────────────────────

class AttributeGroup(TimeStampedModel):
    """Groups related attributes: 'Physical Specs', 'Display', 'Connectivity'"""
    name = models.CharField(max_length=255)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "name"]

    def __str__(self):
        return self.name


class Attribute(TimeStampedModel):
    """
    Dynamic product attributes: Size, Color, Material, RAM, Storage, etc.
    Used for both product specs AND variant-defining options.
    """
    class ValueType(models.TextChoices):
        TEXT = "text", "Text"
        INTEGER = "integer", "Integer"
        DECIMAL = "decimal", "Decimal"
        BOOLEAN = "boolean", "Boolean"
        SELECT = "select", "Single Select"
        MULTI_SELECT = "multi_select", "Multi Select"
        COLOR = "color", "Color (Hex)"

    group = models.ForeignKey(
        AttributeGroup, on_delete=models.CASCADE, related_name="attributes"
    )
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    value_type = models.CharField(max_length=20, choices=ValueType.choices)
    is_filterable = models.BooleanField(default=False, help_text="Show in faceted filters")
    is_required = models.BooleanField(default=False)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "name"]

    def __str__(self):
        return f"{self.group.name} → {self.name}"


class AttributeOption(TimeStampedModel):
    """Predefined values for SELECT/MULTI_SELECT/COLOR attributes."""
    attribute = models.ForeignKey(
        Attribute, on_delete=models.CASCADE, related_name="options"
    )
    value = models.CharField(max_length=255)
    color_hex = models.CharField(
        max_length=7, blank=True, help_text="Hex color code for COLOR type (e.g., #FF5733)"
    )
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order"]
        unique_together = [("attribute", "value")]

    def __str__(self):
        return f"{self.attribute.name}: {self.value}"


# ─── PRODUCTS ──────────────────────────────────────────────

class Product(TimeStampedModel):
    """
    Parent product template. Contains shared info (title, description, category).
    Actual purchasable items are ProductVariant records.
    """
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PENDING_REVIEW = "pending_review", "Pending Review"
        ACTIVE = "active", "Active"
        INACTIVE = "inactive", "Inactive"
        ARCHIVED = "archived", "Archived"

    vendor = models.ForeignKey(
        "vendors.Vendor", on_delete=models.CASCADE, related_name="products"
    )
    product_type = models.ForeignKey(
        ProductType, on_delete=models.PROTECT, related_name="products"
    )
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True, related_name="products"
    )

    name = models.CharField(max_length=500)
    slug = models.SlugField(max_length=500, unique=True, db_index=True)
    description = models.TextField(blank=True)
    short_description = models.CharField(max_length=500, blank=True)

    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.DRAFT, db_index=True
    )
    is_featured = models.BooleanField(default=False, db_index=True)

    min_price = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True,
        help_text="Lowest variant price (auto-computed)",
    )
    max_price = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True,
        help_text="Highest variant price (auto-computed)",
    )

    meta_title = models.CharField(max_length=255, blank=True)
    meta_description = models.TextField(blank=True)

    average_rating = models.DecimalField(
        max_digits=3, decimal_places=2, default=0.00
    )
    review_count = models.PositiveIntegerField(default=0)
    total_sold = models.PositiveIntegerField(default=0)

    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "is_featured"]),
            models.Index(fields=["vendor", "status"]),
            models.Index(fields=["category", "status"]),
            models.Index(fields=["-average_rating"]),
            models.Index(fields=["-total_sold"]),
        ]

    def __str__(self):
        return self.name

    def update_price_range(self):
        """Calculates min_price and max_price from active variants."""
        variants = self.variants.filter(is_active=True)
        if variants.exists():
            prices = variants.values_list("price", flat=True)
            self.min_price = min(prices)
            self.max_price = max(prices)
        else:
            self.min_price = None
            self.max_price = None
        self.save(update_fields=["min_price", "max_price"])


class ProductVariant(TimeStampedModel):
    """
    Purchasable SKU — a specific configuration of a Product.
    Example: "Nike Air Max 90 - Size 10, Black" is a variant of "Nike Air Max 90".
    """
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="variants"
    )
    sku = models.CharField(max_length=100, unique=True, db_index=True)
    barcode = models.CharField(max_length=100, blank=True, db_index=True)
    name = models.CharField(
        max_length=255, blank=True,
        help_text="Auto-generated from variant options if blank",
    )

    price = models.DecimalField(max_digits=12, decimal_places=2)
    compare_at_price = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True,
        help_text="Original price before discount (strikethrough price)",
    )
    cost_price = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True,
        help_text="Cost of goods sold (hidden from customers)",
    )

    # Physical specs
    weight = models.DecimalField(
        max_digits=8, decimal_places=3, null=True, blank=True, help_text="Weight in kg"
    )
    length = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    width = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    height = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)

    # Digital product specs
    digital_file = models.FileField(upload_to="digital_products/", blank=True, null=True)
    download_limit = models.PositiveIntegerField(
        null=True, blank=True, help_text="Max download count (null = unlimited)"
    )
    download_expiry_days = models.PositiveIntegerField(
        null=True, blank=True, help_text="Days until download link expires"
    )

    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "created_at"]

    def __str__(self):
        return f"{self.product.name} — {self.name or self.sku}"


class VariantAttributeValue(TimeStampedModel):
    """Links a variant to its defining attribute values (Size=XL, Color=Navy)."""
    variant = models.ForeignKey(
        ProductVariant, on_delete=models.CASCADE, related_name="attribute_values"
    )
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE)
    attribute_option = models.ForeignKey(
        AttributeOption, on_delete=models.CASCADE, null=True, blank=True
    )
    value_text = models.CharField(max_length=500, blank=True)

    class Meta:
        unique_together = [("variant", "attribute")]

    def __str__(self):
        display = self.attribute_option.value if self.attribute_option else self.value_text
        return f"{self.attribute.name}: {display}"


class ProductAttributeValue(TimeStampedModel):
    """Stores product-level spec attributes (Brand=Apple, Chipset=A16 Bionic)."""
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="attribute_values"
    )
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE)
    attribute_option = models.ForeignKey(
        AttributeOption, on_delete=models.CASCADE, null=True, blank=True
    )
    value_text = models.TextField(blank=True)
    value_integer = models.IntegerField(null=True, blank=True)
    value_decimal = models.DecimalField(
        max_digits=12, decimal_places=4, null=True, blank=True
    )
    value_boolean = models.BooleanField(null=True, blank=True)

    class Meta:
        unique_together = [("product", "attribute")]

    def __str__(self):
        return f"{self.product.name} → {self.attribute.name}"


# ─── PRODUCT MEDIA ─────────────────────────────────────────

class ProductImage(TimeStampedModel):
    """Product images with optional variant association."""
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="images"
    )
    variant = models.ForeignKey(
        ProductVariant, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="images",
    )
    image = models.ImageField(upload_to="products/images/")
    alt_text = models.CharField(max_length=255, blank=True)
    is_primary = models.BooleanField(default=False)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order"]

    def __str__(self):
        return f"Image for {self.product.name} (order: {self.sort_order})"

    def save(self, *args, **kwargs):
        if self.is_primary:
            ProductImage.objects.filter(
                product=self.product
            ).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)
