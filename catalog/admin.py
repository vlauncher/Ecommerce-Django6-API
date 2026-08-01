from django.contrib import admin
from treebeard.admin import TreeAdmin
from treebeard.forms import movenodeform_factory
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


@admin.register(Category)
class CategoryAdmin(TreeAdmin):
    form = movenodeform_factory(Category)
    list_display = ("name", "slug", "is_active")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(ProductType)
class ProductTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "kind", "requires_shipping", "is_digital")
    prepopulated_fields = {"slug": ("name",)}
    filter_horizontal = ("attribute_groups", "variation_attributes")


class AttributeOptionInline(admin.TabularInline):
    model = AttributeOption
    extra = 1


@admin.register(AttributeGroup)
class AttributeGroupAdmin(admin.ModelAdmin):
    list_display = ("name", "sort_order")


@admin.register(Attribute)
class AttributeAdmin(admin.ModelAdmin):
    list_display = ("name", "group", "value_type", "is_filterable", "is_required", "sort_order")
    list_filter = ("group", "value_type", "is_filterable")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [AttributeOptionInline]


class ProductVariantInline(admin.StackedInline):
    model = ProductVariant
    extra = 1


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "vendor", "product_type", "category", "status", "min_price", "max_price", "is_featured", "created_at")
    list_filter = ("status", "is_featured", "product_type", "category")
    search_fields = ("name", "slug", "description", "vendor__store_name")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [ProductVariantInline, ProductImageInline]


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ("sku", "product", "name", "price", "compare_at_price", "is_active")
    search_fields = ("sku", "barcode", "name", "product__name")
    list_filter = ("is_active",)
