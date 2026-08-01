from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from catalog.models import Category, ProductType, Product, ProductVariant
from vendors.models import Vendor

User = get_user_model()


class CartAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="customer@example.com",
            password="Password123!",
            is_active=True,
        )
        self.vendor_user = User.objects.create_user(
            email="vendor@example.com",
            password="Password123!",
            is_active=True,
        )
        self.vendor = Vendor.objects.create(
            owner=self.vendor_user,
            store_name="Tech Store",
            slug="tech-store",
            status=Vendor.Status.ACTIVE,
        )
        self.category = Category.add_root(name="Tech", slug="tech")
        self.product_type = ProductType.objects.create(name="Device", slug="device")
        self.product = Product.objects.create(
            vendor=self.vendor,
            product_type=self.product_type,
            category=self.category,
            name="Laptop Pro",
            slug="laptop-pro",
            status=Product.Status.ACTIVE,
        )
        self.variant = ProductVariant.objects.create(
            product=self.product,
            sku="LAP-001",
            price="1200.00",
        )

    def test_add_and_get_cart_items(self):
        self.client.force_authenticate(user=self.user)
        add_url = "/api/v1/cart/items/"
        data = {"variant_id": str(self.variant.id), "quantity": 2}
        response = self.client.post(add_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total_quantity"], 2)
        self.assertEqual(float(response.data["subtotal"]), 2400.00)

        # Get Cart
        get_response = self.client.get("/api/v1/cart/")
        self.assertEqual(get_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(get_response.data["items"]), 1)
