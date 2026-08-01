from rest_framework import serializers
from django.utils.text import slugify
from drf_spectacular.utils import extend_schema_field, OpenApiTypes
from catalog.models import (
    Category,
    ProductType,
    AttributeGroup,
    Attribute,
    AttributeOption,
    Product,
    ProductVariant,
    VariantAttributeValue,
    ProductAttributeValue,
    ProductImage,
)
from vendors.serializers import VendorPublicSerializer


# ─── CATEGORY SERIALIZERS ──────────────────────────────────

class CategoryTreeSerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()
    full_path = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = (
            "id",
            "name",
            "slug",
            "description",
            "image",
            "full_path",
            "children",
        )

    @extend_schema_field(OpenApiTypes.STR)
    def get_full_path(self, obj):
        return obj.full_path

    @extend_schema_field(OpenApiTypes.OBJECT)
    def get_children(self, obj):
        children = obj.get_children().filter(is_active=True)
        return CategoryTreeSerializer(children, many=True).data


class CategoryDetailSerializer(serializers.ModelSerializer):
    ancestors = serializers.SerializerMethodField()
    full_path = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = (
            "id",
            "name",
            "slug",
            "description",
            "image",
            "is_active",
            "meta_title",
            "meta_description",
            "full_path",
            "ancestors",
        )

    @extend_schema_field(OpenApiTypes.STR)
    def get_full_path(self, obj):
        return obj.full_path


    @extend_schema_field(OpenApiTypes.OBJECT)
    def get_ancestors(self, obj):
        ancestors = obj.get_ancestors()
        return [
            {"id": str(node.id), "name": node.name, "slug": node.slug}
            for node in ancestors
        ]



# ─── ATTRIBUTE SERIALIZERS ─────────────────────────────────

class AttributeOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttributeOption
        fields = ("id", "value", "color_hex", "sort_order")


class AttributeSerializer(serializers.ModelSerializer):
    options = AttributeOptionSerializer(many=True, read_only=True)
    group_name = serializers.CharField(source="group.name", read_only=True)

    class Meta:
        model = Attribute
        fields = (
            "id",
            "group",
            "group_name",
            "name",
            "slug",
            "value_type",
            "is_filterable",
            "is_required",
            "sort_order",
            "options",
        )


class AttributeGroupSerializer(serializers.ModelSerializer):
    attributes = AttributeSerializer(many=True, read_only=True)

    class Meta:
        model = AttributeGroup
        fields = ("id", "name", "sort_order", "attributes")


# ─── PRODUCT TYPE SERIALIZERS ──────────────────────────────

class ProductTypeSerializer(serializers.ModelSerializer):
    attribute_groups = AttributeGroupSerializer(many=True, read_only=True)
    variation_attributes = AttributeSerializer(many=True, read_only=True)

    class Meta:
        model = ProductType
        fields = (
            "id",
            "name",
            "slug",
            "kind",
            "requires_shipping",
            "is_digital",
            "attribute_groups",
            "variation_attributes",
        )


# ─── PRODUCT MEDIA & VARIANT SERIALIZERS ───────────────────

class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ("id", "image", "alt_text", "is_primary", "variant", "sort_order")


class VariantAttributeValueSerializer(serializers.ModelSerializer):
    attribute_name = serializers.CharField(source="attribute.name", read_only=True)
    option_value = serializers.CharField(source="attribute_option.value", read_only=True, default=None)
    color_hex = serializers.CharField(source="attribute_option.color_hex", read_only=True, default=None)

    class Meta:
        model = VariantAttributeValue
        fields = (
            "id",
            "attribute",
            "attribute_name",
            "attribute_option",
            "option_value",
            "color_hex",
            "value_text",
        )


class ProductVariantSerializer(serializers.ModelSerializer):
    attribute_values = VariantAttributeValueSerializer(many=True, read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)

    class Meta:
        model = ProductVariant
        fields = (
            "id",
            "sku",
            "barcode",
            "name",
            "price",
            "compare_at_price",
            "weight",
            "length",
            "width",
            "height",
            "digital_file",
            "download_limit",
            "download_expiry_days",
            "is_active",
            "sort_order",
            "attribute_values",
            "images",
        )


class ProductVariantCreateUpdateSerializer(serializers.ModelSerializer):
    attribute_values = serializers.ListField(
        child=serializers.DictField(), write_only=True, required=False
    )

    class Meta:
        model = ProductVariant
        fields = (
            "id",
            "sku",
            "barcode",
            "name",
            "price",
            "compare_at_price",
            "cost_price",
            "weight",
            "length",
            "width",
            "height",
            "digital_file",
            "download_limit",
            "download_expiry_days",
            "is_active",
            "sort_order",
            "attribute_values",
        )

    def create(self, validated_data):
        attr_values_data = validated_data.pop("attribute_values", [])
        variant = ProductVariant.objects.create(**validated_data)

        for attr_data in attr_values_data:
            VariantAttributeValue.objects.create(
                variant=variant,
                attribute_id=attr_data["attribute_id"],
                attribute_option_id=attr_data.get("attribute_option_id"),
                value_text=attr_data.get("value_text", ""),
            )
        return variant


class ProductAttributeValueSerializer(serializers.ModelSerializer):
    attribute_name = serializers.CharField(source="attribute.name", read_only=True)
    option_value = serializers.CharField(source="attribute_option.value", read_only=True, default=None)

    class Meta:
        model = ProductAttributeValue
        fields = (
            "id",
            "attribute",
            "attribute_name",
            "attribute_option",
            "option_value",
            "value_text",
            "value_integer",
            "value_decimal",
            "value_boolean",
        )


# ─── PRODUCT SERIALIZERS ───────────────────────────────────

class ProductListSerializer(serializers.ModelSerializer):
    vendor = VendorPublicSerializer(read_only=True)
    category_name = serializers.CharField(source="category.name", read_only=True)
    primary_image = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = (
            "id",
            "name",
            "slug",
            "short_description",
            "status",
            "is_featured",
            "min_price",
            "max_price",
            "average_rating",
            "review_count",
            "total_sold",
            "vendor",
            "category_name",
            "primary_image",
            "created_at",
        )

    @extend_schema_field(ProductImageSerializer)
    def get_primary_image(self, obj):
        primary = obj.images.filter(is_primary=True).first() or obj.images.first()
        if primary:
            return ProductImageSerializer(primary).data
        return None



class ProductDetailSerializer(serializers.ModelSerializer):
    vendor = VendorPublicSerializer(read_only=True)
    category = CategoryDetailSerializer(read_only=True)
    product_type = ProductTypeSerializer(read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    attribute_values = ProductAttributeValueSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = (
            "id",
            "name",
            "slug",
            "description",
            "short_description",
            "status",
            "is_featured",
            "min_price",
            "max_price",
            "meta_title",
            "meta_description",
            "average_rating",
            "review_count",
            "total_sold",
            "vendor",
            "category",
            "product_type",
            "variants",
            "images",
            "attribute_values",
            "created_at",
            "updated_at",
            "published_at",
        )


class ProductCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = (
            "id",
            "product_type",
            "category",
            "name",
            "description",
            "short_description",
            "status",
            "is_featured",
            "meta_title",
            "meta_description",
        )

    def validate_name(self, value):
        slug = slugify(value)
        existing = Product.objects.filter(slug=slug)
        if self.instance:
            existing = existing.exclude(pk=self.instance.pk)
        if existing.exists():
            raise serializers.ValidationError("A product with a similar name already exists.")
        return value

    def create(self, validated_data):
        vendor = self.context["request"].user.vendor_profile
        slug = slugify(validated_data["name"])
        product = Product.objects.create(
            vendor=vendor,
            slug=slug,
            **validated_data
        )
        return product
