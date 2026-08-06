from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from apps.commerce.models import Cart, CartItem
from apps.shops.models import Shop
from apps.users.models import User

from .discounts import calculate_discount
from .models import Coupon, Product, ProductVariant, Promotion


class CouponDiscountTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="buyer@example.com", password="Password123!", first_name="Buyer", last_name="One")
        self.shop = Shop.objects.create(name="Discount Shop", slug="discount-shop", created_by=self.user)
        self.product = Product.objects.create(shop=self.shop, name="Test item", slug="test-item", status=Product.Status.PUBLISHED)
        self.variant = ProductVariant.objects.create(product=self.product, sku="TEST-1", price_minor=10000)
        self.cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=self.cart, variant=self.variant, quantity=1, price_minor_snapshot=10000)

    def test_coupon_percentage_discount_and_minimum_spend(self):
        promotion = Promotion.objects.create(shop=self.shop, name="Ten percent", kind=Promotion.Kind.PERCENTAGE, value=10, starts_at=timezone.now() - timedelta(minutes=1))
        Coupon.objects.create(promotion=promotion, code="SAVE10")
        result = calculate_discount(list(self.cart.items.all()), self.user, "SAVE10")
        self.assertEqual(result["amount_minor"], 1000)

    def test_invalid_coupon_is_rejected(self):
        with self.assertRaises(Exception):
            calculate_discount(list(self.cart.items.all()), self.user, "MISSING")
