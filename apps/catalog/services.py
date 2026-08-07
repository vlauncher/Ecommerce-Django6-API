from asgiref.sync import sync_to_async
from django.db import transaction
from ninja.errors import HttpError

from django.utils.dateparse import parse_datetime

from .models import Category, Coupon, InventoryLedgerEntry, Product, ProductVariant, Promotion, StockItem, Warehouse


def product_dict(product):
    return {
        "id": product.id,
        "name": product.name,
        "slug": product.slug,
        "description": product.description,
        "status": product.status,
        "category_id": product.category_id,
        "variants": [
            {
                "id": variant.id,
                "sku": variant.sku,
                "name": variant.name,
                "option_values": variant.option_values,
                "price_minor": variant.price_minor,
                "compare_at_price_minor": variant.compare_at_price_minor,
                "currency": variant.currency,
                "weight_grams": variant.weight_grams,
            }
            for variant in product.variants.all()
        ],
    }


@sync_to_async(thread_sensitive=True)
def create_product(shop, user, data):
    with transaction.atomic():
        product = Product.objects.create(
            shop=shop,
            created_by=user,
            name=data["name"],
            slug=data["slug"],
            description=data.get("description", ""),
            category_id=data.get("category_id"),
            product_type=data.get("product_type", "physical"),
            is_digital=data.get("is_digital", False),
            requires_shipping=data.get("requires_shipping", True),
        )
        ProductVariant.objects.bulk_create([
            ProductVariant(product=product, **variant) for variant in data["variants"]
        ])
        return product_dict(Product.objects.prefetch_related("variants").get(pk=product.pk))


@sync_to_async(thread_sensitive=True)
def create_category(shop, data):
    if data.get("parent_id") and not Category.objects.filter(pk=data["parent_id"], shop=shop).exists():
        raise HttpError(400, "Parent category does not belong to this shop.")
    category = Category.objects.create(shop=shop, **data)
    return category


@sync_to_async(thread_sensitive=True)
def adjust_stock(shop, user, data):
    try:
        warehouse = Warehouse.objects.get(pk=data["warehouse_id"], shop=shop)
        variant = ProductVariant.objects.select_related("product").get(pk=data["variant_id"], product__shop=shop)
    except (Warehouse.DoesNotExist, ProductVariant.DoesNotExist):
        raise HttpError(404, "Warehouse or variant not found.")
    with transaction.atomic():
        stock, _ = StockItem.objects.select_for_update().get_or_create(warehouse=warehouse, variant=variant)
        if stock.on_hand + data["quantity_delta"] < 0:
            raise HttpError(400, "Stock cannot become negative.")
        stock.on_hand += data["quantity_delta"]
        stock.save(update_fields=("on_hand", "updated_at"))
        InventoryLedgerEntry.objects.create(variant=variant, warehouse=warehouse, quantity_delta=data["quantity_delta"], reason=data["reason"], created_by=user)
        if stock.available <= stock.reorder_level:
            from apps.interactions.models import Notification
            from apps.shops.models import ShopMembership
            recipients = ShopMembership.objects.filter(shop=shop, is_active=True).exclude(role=ShopMembership.Role.CUSTOMER).values_list("user_id", flat=True)
            Notification.objects.bulk_create([Notification(user_id=user_id, kind="inventory.low_stock", title="Low stock alert", body=f"{variant.product.name} ({variant.sku}) is low on stock.", payload={"variant_id": variant.id, "warehouse_id": warehouse.id, "available": stock.available}) for user_id in recipients])
        return {"variant_id": variant.id, "warehouse_id": warehouse.id, "on_hand": stock.on_hand, "reserved": stock.reserved, "available": stock.available}


@sync_to_async(thread_sensitive=True)
def create_coupon(shop, data):
    if data["kind"] not in {choice.value for choice in Promotion.Kind}:
        raise HttpError(400, "Invalid promotion type.")
    starts_at = parse_datetime(data["starts_at"])
    ends_at = parse_datetime(data["ends_at"]) if data.get("ends_at") else None
    if not starts_at or (ends_at and ends_at <= starts_at):
        raise HttpError(400, "Invalid promotion dates.")
    promotion = Promotion.objects.create(shop=shop, name=f"Coupon {data['code']}", code=data["code"].upper(), kind=data["kind"], value=data["value"], minimum_subtotal_minor=data["minimum_subtotal_minor"], starts_at=starts_at, ends_at=ends_at)
    coupon = Coupon.objects.create(promotion=promotion, code=data["code"].upper(), usage_limit=data.get("usage_limit"), per_customer_limit=data.get("per_customer_limit"))
    return {"id": coupon.id, "code": coupon.code, "promotion_id": promotion.id, "kind": promotion.kind, "value": promotion.value}
