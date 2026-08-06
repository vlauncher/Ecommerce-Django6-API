from django.db.models import Q
from django.utils import timezone
from ninja.errors import HttpError

from .models import Promotion


def _active_promotions(shop_ids, code=""):
    now = timezone.now()
    query = Promotion.objects.filter(shop_id__in=shop_ids, is_active=True, starts_at__lte=now).filter(Q(ends_at__isnull=True) | Q(ends_at__gte=now))
    if code:
        query = query.filter(coupon__code__iexact=code, coupon__is_active=True)
    else:
        query = query.filter(is_automatic=True)
    return query.prefetch_related("products", "categories", "coupon")


def calculate_discount(items, user, code=""):
    shop_ids = {item.variant.product.shop_id for item in items}
    subtotal = sum(item.quantity * item.price_minor_snapshot for item in items)
    best = None
    for promotion in _active_promotions(shop_ids, code):
        if subtotal < promotion.minimum_subtotal_minor:
            continue
        try:
            coupon = promotion.coupon
        except promotion._meta.get_field("coupon").related_model.DoesNotExist:
            coupon = None
        if coupon:
            if coupon.usage_limit is not None and coupon.used_count >= coupon.usage_limit:
                continue
            if coupon.per_customer_limit is not None and coupon.redemptions.filter(user=user).count() >= coupon.per_customer_limit:
                continue
        eligible = [item for item in items if item.variant.product.shop_id == promotion.shop_id and (not promotion.products.exists() and not promotion.categories.exists() or promotion.products.filter(pk=item.variant.product_id).exists() or promotion.categories.filter(pk=item.variant.product.category_id).exists())]
        eligible_total = sum(item.quantity * item.price_minor_snapshot for item in eligible)
        if not eligible_total:
            continue
        amount = eligible_total * promotion.value // 100 if promotion.kind == Promotion.Kind.PERCENTAGE else min(promotion.value, eligible_total)
        if promotion.kind == Promotion.Kind.FREE_SHIPPING:
            amount = 0
        if not best or amount > best["amount_minor"]:
            best = {"promotion": promotion, "amount_minor": amount}
    if code and not best:
        raise HttpError(400, "Coupon is invalid, expired, or not applicable to this cart.")
    return best or {"promotion": None, "amount_minor": 0}
