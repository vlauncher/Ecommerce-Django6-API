from decimal import Decimal
from django.test import TestCase
from promotions.models import Coupon
from promotions.engine import calculate_coupon_discount, InvalidCouponError


class PromotionsTestCase(TestCase):
    def setUp(self):
        self.coupon_pct = Coupon.objects.create(
            code="SAVE20",
            discount_type=Coupon.DiscountType.PERCENTAGE,
            value=Decimal("20.00"),
            min_order_value=Decimal("50.00"),
        )
        self.coupon_fixed = Coupon.objects.create(
            code="TAKE10",
            discount_type=Coupon.DiscountType.FIXED_AMOUNT,
            value=Decimal("10.00"),
            min_order_value=Decimal("20.00"),
        )

    def test_percentage_coupon_discount(self):
        discount = calculate_coupon_discount(self.coupon_pct, cart_subtotal=Decimal("100.00"))
        self.assertEqual(discount, Decimal("20.00"))

    def test_fixed_coupon_discount(self):
        discount = calculate_coupon_discount(self.coupon_fixed, cart_subtotal=Decimal("50.00"))
        self.assertEqual(discount, Decimal("10.00"))

    def test_min_order_value_validation(self):
        with self.assertRaises(InvalidCouponError):
            calculate_coupon_discount(self.coupon_pct, cart_subtotal=Decimal("30.00"))
