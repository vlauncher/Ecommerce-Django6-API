import uuid
from datetime import timedelta
from collections import defaultdict

from asgiref.sync import sync_to_async
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from ninja.errors import HttpError

from apps.catalog.models import ProductVariant, StockItem
from apps.catalog.discounts import calculate_discount

from .models import Address, Cart, CartItem, CheckoutAttempt, GiftCard, GiftCardTransaction, Order, OrderItem, SellerOrder, ShippingRate, TaxRate


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
    if cart.currency != variant.currency:
        raise HttpError(400, "All items in a cart must use the same currency.")
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
def checkout(user, data, idempotency_key="", guest_token=""):
    with transaction.atomic():
        if idempotency_key and user:
            previous = CheckoutAttempt.objects.filter(user=user, idempotency_key=idempotency_key).first()
            if previous:
                return previous.response
        cart_query = Cart.objects.select_for_update().prefetch_related("items__variant__product__shop")
        cart = cart_query.filter(user=user).first() if user else cart_query.filter(guest_token=guest_token, user__isnull=True).first()
        if not cart or not cart.items.exists():
            raise HttpError(400, "Cart is empty.")
        if not user and not data.get("customer_email"):
            raise HttpError(400, "An email address is required for guest checkout.")
        if not user and (data.get("coupon_code") or cart.coupon_code):
            raise HttpError(400, "Coupons require an authenticated customer account.")
        tip_minor = data.get("tip_minor", 0)
        shipping_address = data["shipping_address"]
        if data.get("address_id"):
            try:
                saved_address = Address.objects.get(pk=data["address_id"], user=user)
            except Address.DoesNotExist:
                raise HttpError(400, "Shipping address not found.")
            shipping_address = {field: getattr(saved_address, field) for field in ("label", "recipient_name", "phone", "line1", "line2", "city", "state", "country", "postal_code")}
        order = Order.objects.create(number=f"ORD-{uuid.uuid4().hex[:12].upper()}", user=user, guest_email=data.get("customer_email", "") or "", guest_token=guest_token, currency=cart.currency, shipping_address=shipping_address, billing_address=data.get("billing_address") or shipping_address, tip_minor=tip_minor)
        grouped = defaultdict(list)
        subtotal = 0
        for item in cart.items.all():
            variant = ProductVariant.objects.select_related("product__shop").get(pk=item.variant_id)
            stocks = list(StockItem.objects.select_for_update().filter(variant=variant, warehouse__is_active=True).order_by("id"))
            available = sum(stock.available for stock in stocks)
            if not stocks or available < item.quantity:
                raise HttpError(409, f"Insufficient stock for {variant.sku}.")
            remaining = item.quantity
            for stock in stocks:
                reserve = min(remaining, stock.available)
                if reserve:
                    stock.reserved += reserve
                    stock.save(update_fields=("reserved", "updated_at"))
                    remaining -= reserve
                if not remaining:
                    break
            total = item.quantity * item.price_minor_snapshot
            subtotal += total
            grouped[variant.product.shop_id].append((item, variant, total))
        discount = calculate_discount(list(cart.items.all()), user, data.get("coupon_code") or cart.coupon_code)
        discount_minor = discount["amount_minor"]
        shipping_minor = 0
        tax_minor = 0
        rate_ids = data.get("shipping_rate_ids") or {}
        for shop_id, entries in grouped.items():
            rate_id = rate_ids.get(str(shop_id)) or rate_ids.get(shop_id)
            if rate_id:
                try:
                    rate = ShippingRate.objects.get(pk=rate_id, zone__shop_id=shop_id, zone__is_active=True)
                except ShippingRate.DoesNotExist:
                    raise HttpError(400, "Invalid shipping rate.")
                shipping_minor += rate.amount_minor
            seller_subtotal = sum(total for _, _, total in entries)
            tax_rate = TaxRate.objects.filter(shop_id=shop_id, is_active=True, country=shipping_address.get("country", "NG"), state__in=[shipping_address.get("state", ""), ""]).order_by("-state").first()
            if tax_rate:
                tax_minor += int(seller_subtotal * tax_rate.percentage / 100)
        order.subtotal_minor = subtotal
        order.discount_minor = discount_minor
        order.shipping_minor = shipping_minor
        order.tax_minor = tax_minor
        order.total_minor = max(subtotal - discount_minor, 0) + shipping_minor + tax_minor + tip_minor
        order.save(update_fields=("subtotal_minor", "discount_minor", "shipping_minor", "tax_minor", "tip_minor", "total_minor", "shipping_address", "billing_address", "updated_at"))
        gift_card_code = (data.get("gift_card_code") or "").strip().upper()
        if gift_card_code:
            try:
                gift_card = GiftCard.objects.select_for_update().get(code=gift_card_code, is_active=True, currency=cart.currency)
            except GiftCard.DoesNotExist:
                raise HttpError(400, "Gift card is invalid or inactive.")
            if gift_card.expires_at and gift_card.expires_at <= timezone.now():
                raise HttpError(400, "Gift card has expired.")
            gift_amount = min(gift_card.balance_minor, order.total_minor)
            gift_card.balance_minor -= gift_amount
            if gift_card.balance_minor == 0:
                gift_card.is_active = False
            gift_card.save(update_fields=("balance_minor", "is_active"))
            order.total_minor -= gift_amount
            order.save(update_fields=("total_minor", "updated_at"))
            GiftCardTransaction.objects.create(gift_card=gift_card, order=order, amount_minor=-gift_amount)
        if discount["promotion"]:
            try:
                coupon = discount["promotion"].coupon
            except discount["promotion"]._meta.get_field("coupon").related_model.DoesNotExist:
                coupon = None
        else:
            coupon = None
        if coupon:
            from apps.catalog.models import Coupon
            coupon = Coupon.objects.select_for_update().get(pk=coupon.pk)
            if coupon.usage_limit is not None and coupon.used_count >= coupon.usage_limit:
                raise HttpError(400, "Coupon usage limit has been reached.")
            if coupon.per_customer_limit is not None and coupon.redemptions.filter(user=user).count() >= coupon.per_customer_limit:
                raise HttpError(400, "You have already used this coupon the maximum number of times.")
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
        if user:
            from apps.interactions.models import Notification
            Notification.objects.create(user=user, kind="order.created", title="Order placed", body=f"Your order {order.number} has been created.", payload={"order_id": order.id, "order_number": order.number})
        response = {"order_id": order.id, "order_number": order.number, "total_minor": order.total_minor, "currency": order.currency}
        if idempotency_key and user:
            CheckoutAttempt.objects.create(user=user, idempotency_key=idempotency_key, response=response)
        return response


@sync_to_async(thread_sensitive=True)
def get_guest_cart(guest_token):
    cart, _ = Cart.objects.get_or_create(guest_token=guest_token, user=None, defaults={"currency": "NGN", "expires_at": timezone.now() + timedelta(days=7)})
    return _cart_dict(cart)


@sync_to_async(thread_sensitive=True)
def add_guest_to_cart(guest_token, data):
    variant = ProductVariant.objects.select_related("product").get(pk=data["variant_id"], is_active=True, product__status=ProductVariant.product.field.related_model.Status.PUBLISHED)
    cart, _ = Cart.objects.get_or_create(guest_token=guest_token, user=None, defaults={"currency": variant.currency, "expires_at": timezone.now() + timedelta(days=7)})
    if cart.currency != variant.currency:
        raise HttpError(400, "All items in a cart must use the same currency.")
    item, _ = CartItem.objects.get_or_create(cart=cart, variant=variant, defaults={"quantity": 0, "price_minor_snapshot": variant.price_minor})
    item.quantity += data["quantity"]
    item.price_minor_snapshot = variant.price_minor
    item.save(update_fields=("quantity", "price_minor_snapshot"))
    return _cart_dict(cart)
