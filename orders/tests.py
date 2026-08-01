from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from catalog.models import Category, ProductType, Product, ProductVariant
from vendors.models import Vendor
from cart.models import Cart, CartItem
from orders.models import Order

User = get_user_model()


class OrderAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="buyer@example.com",
            password="Password123!",
            is_active=True,
        )
        self.vendor_user = User.objects.create_user(
            email="seller@example.com",
            password="Password123!",
            is_active=True,
        )
        self.vendor = Vendor.objects.create(
            owner=self.vendor_user,
            store_name="Gear Shop",
            slug="gear-shop",
            status=Vendor.Status.ACTIVE,
            commission_rate="10.00",
        )
        self.category = Category.add_root(name="Gear", slug="gear")
        self.product_type = ProductType.objects.create(name="Gear Item", slug="gear-item")
        self.product = Product.objects.create(
            vendor=self.vendor,
            product_type=self.product_type,
            category=self.category,
            name="Smart Watch",
            slug="smart-watch",
            status=Product.Status.ACTIVE,
        )
        self.variant = ProductVariant.objects.create(
            product=self.product,
            sku="SW-01",
            price="200.00",
        )
        self.cart, _ = Cart.objects.get_or_create(user=self.user)
        CartItem.objects.create(cart=self.cart, variant=self.variant, quantity=3)

    def test_checkout_flow(self):
        self.client.force_authenticate(user=self.user)
        url = "/api/v1/orders/checkout/"
        data = {
            "shipping_address": {"recipient_name": "Buyer", "street_address_1": "123 Main St", "city": "NYC"},
            "billing_address": {"recipient_name": "Buyer", "street_address_1": "123 Main St", "city": "NYC"},
            "notes": "Handle with care.",
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["status"], Order.Status.PENDING_PAYMENT)
        self.assertEqual(float(response.data["grand_total"]), 600.00)

        # Check multi-vendor sub-orders & commission
        order = Order.objects.get(id=response.data["id"])
        sub_order = order.sub_orders.first()
        self.assertEqual(float(sub_order.subtotal), 600.00)
        self.assertEqual(float(sub_order.commission_amount), 60.00)  # 10% of 600
        self.assertEqual(float(sub_order.vendor_payout), 540.00)

        # Cart should be emptied
        self.assertEqual(self.cart.items.count(), 0)
