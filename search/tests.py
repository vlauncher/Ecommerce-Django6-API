from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from catalog.models import Category, ProductType, Product
from vendors.models import Vendor
from django.contrib.auth import get_user_model

User = get_user_model()


class SearchAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(email="seller@example.com", password="Password123!", is_active=True)
        self.vendor = Vendor.objects.create(owner=self.user, store_name="Gizmo Shop", slug="gizmo-shop", status=Vendor.Status.ACTIVE)
        self.category = Category.add_root(name="Audio", slug="audio")
        self.product_type = ProductType.objects.create(name="Headphones", slug="headphones")

        Product.objects.create(
            vendor=self.vendor,
            product_type=self.product_type,
            category=self.category,
            name="Noise Cancelling Earbuds",
            slug="noise-cancelling-earbuds",
            status=Product.Status.ACTIVE,
        )

    def test_search_products(self):
        response = self.client.get("/api/v1/search/products/?q=Noise")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["name"], "Noise Cancelling Earbuds")

    def test_search_suggestions(self):
        response = self.client.get("/api/v1/search/suggestions/?q=Earbuds")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["products"]), 1)
