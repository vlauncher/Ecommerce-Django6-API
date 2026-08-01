from decimal import Decimal
from promotions.models import Coupon, CouponUsage


class InvalidCouponError(Exception):
    pass


def calculate_coupon_discount(coupon: Coupon, cart_subtotal: Decimal, user=None) -> Decimal:
    """Calculates valid discount amount for a given cart subtotal and user."""
    if not coupon.is_valid:
        raise InvalidCouponError("Coupon code is expired or invalid.")

    if cart_subtotal < coupon.min_order_value:
        raise InvalidCouponError(
            f"Minimum subtotal of ${coupon.min_order_value} required for this coupon."
        )

    if user and user.is_authenticated:
        user_usage = CouponUsage.objects.filter(coupon=coupon, user=user).count()
        if user_usage >= coupon.usage_limit_per_user:
            raise InvalidCouponError("You have reached the maximum usage limit for this coupon.")

    if coupon.discount_type == Coupon.DiscountType.PERCENTAGE:
        discount = (cart_subtotal * (coupon.value / Decimal("100.00"))).quantize(Decimal("0.01"))
        if coupon.max_discount_amount and discount > coupon.max_discount_amount:
            discount = coupon.max_discount_amount
        return discount

    elif coupon.discount_type == Coupon.DiscountType.FIXED_AMOUNT:
        return min(coupon.value, cart_subtotal)

    elif coupon.discount_type == Coupon.DiscountType.FREE_SHIPPING:
        return Decimal("0.00")  # Handled in shipping fee calculation

    return Decimal("0.00")
