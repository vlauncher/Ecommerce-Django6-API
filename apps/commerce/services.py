import uuid
from collections import defaultdict

from asgiref.sync import sync_to_async
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from ninja.errors import HttpError

from apps.catalog.models import ProductVariant, StockItem
from apps.catalog.discounts import calculate_discount

from .models import Cart, CartItem, Order, OrderItem, SellerOrder


def _cart_dict(cart):
    items = []
    subtotal = 0
    for item in cart.items.select_related("variant__product", "variant__product__shop"):
        total = item.quantity * item.price_minor_snapshot
        subtotal += total
        items.append({"variant_id": item.variant_id, "product_name": item.variant.product.name, "shop_slug": item.variant.product.shop.slug, "quantity": item.quantity, "unit_price_minor": item.price_minor_snapshot, "total_minor": total})
    discount = calculate_discount(list(cart.items.all()), cart.user, cart.coupon_code) if cart.coupon_code else {"amount_minor": 0}
    return {"id": cart.id, "currency": cart.currency, "subtotal_minor": subtotal, "discount_minor": discount["amount_minor"], "coupon_code": cart.coupon_code, "items": items}


@sync_to_async(thread_sensitive=True)
def get_or_create_cart(user):
    cart, _ = Cart.objects.get_or_create(user=user, defaults={"currency": "NGN"})
    return _cart_dict(cart)


@sync_to_async(thread_sensitive=True)
def add_to_cart(user, data):
    variant = ProductVariant.objects.select_related("product").get(pk=data["variant_id"], is_active=True, product__status=ProductVariant.product.field.related_model.Status.PUBLISHED)
    cart, _ = Cart.objects.get_or_create(user=user, defaults={"currency": variant.currency})
    item, created = CartItem.objects.get_or_create(cart=cart, variant=variant, defaults={"quantity": 0, "price_minor_snapshot": variant.price_minor})
    item.quantity += data["quantity"]
    item.price_minor_snapshot = variant.price_minor
    item.save(update_fields=("quantity", "price_minor_snapshot"))
    return _cart_dict(cart)


@sync_to_async(thread_sensitive=True)
def apply_coupon(user, code):
    cart = Cart.objects.prefetch_related("items__variant__product").filter(user=user).first()
    if not cart or not cart.items.exists():
        raise HttpError(400, "Cart is empty.")
    calculate_discount(list(cart.items.all()), user, code)
    cart.coupon_code = code.strip().upper()
    cart.save(update_fields=("coupon_code", "updated_at"))
    return _cart_dict(cart)


@sync_to_async(thread_sensitive=True)
def checkout(user, data):
    with transaction.atomic():
        cart = Cart.objects.select_for_update().prefetch_related("items__variant__product__shop").filter(user=user).first()
        if not cart or not cart.items.exists():
            raise HttpError(400, "Cart is empty.")
        tip_minor = data.get("tip_minor", 0)
        order = Order.objects.create(number=f"ORD-{uuid.uuid4().hex[:12].upper()}", user=user, currency=cart.currency, shipping_address=data["shipping_address"], billing_address=data.get("billing_address") or data["shipping_address"], tip_minor=tip_minor)
        grouped = defaultdict(list)
        subtotal = 0
        for item in cart.items.all():
            variant = ProductVariant.objects.select_related("product__shop").get(pk=item.variant_id)
            stock = StockItem.objects.select_for_update().filter(variant=variant, warehouse__is_active=True).order_by("id").first()
            if stock and stock.available < item.quantity:
                raise HttpError(409, f"Insufficient stock for {variant.sku}.")
            if stock:
                stock.reserved += item.quantity
                stock.save(update_fields=("reserved", "updated_at"))
            total = item.quantity * item.price_minor_snapshot
            subtotal += total
            grouped[variant.product.shop_id].append((item, variant, total))
        discount = calculate_discount(list(cart.items.all()), user, data.get("coupon_code") or cart.coupon_code)
        discount_minor = discount["amount_minor"]
        order.subtotal_minor = subtotal
        order.discount_minor = discount_minor
        order.total_minor = max(subtotal - discount_minor, 0) + tip_minor
        order.save(update_fields=("subtotal_minor", "discount_minor", "tip_minor", "total_minor", "updated_at"))
        if discount["promotion"]:
            try:
                coupon = discount["promotion"].coupon
            except discount["promotion"]._meta.get_field("coupon").related_model.DoesNotExist:
                coupon = None
        else:
            coupon = None
        if coupon:
            coupon.used_count += 1
            coupon.save(update_fields=("used_count",))
            from apps.catalog.models import CouponRedemption
            CouponRedemption.objects.create(coupon=coupon, user=user, order=order, amount_minor=discount_minor)
        for shop_id, entries in grouped.items():
            seller_total = sum(total for _, _, total in entries)
            commission = seller_total * settings.PLATFORM_COMMISSION_PERCENT // 100
            seller_order = SellerOrder.objects.create(order=order, shop_id=shop_id, subtotal_minor=seller_total, commission_minor=commission, seller_net_minor=seller_total - commission)
            OrderItem.objects.bulk_create([OrderItem(seller_order=seller_order, variant=variant, product_name=variant.product.name, variant_name=variant.name, sku=variant.sku, quantity=item.quantity, unit_price_minor=item.price_minor_snapshot, total_minor=total) for item, variant, total in entries])
        cart.items.all().delete()
        return {"order_id": order.id, "order_number": order.number, "total_minor": order.total_minor, "currency": order.currency}
