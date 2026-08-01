from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from vendors.models import Vendor
from catalog.models import Category, ProductType, Product, ProductVariant

User = get_user_model()


class CatalogAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="vendor@example.com",
            password="Password123!",
            first_name="Jane",
            last_name="Doe",
            is_active=True,
        )
        self.vendor = Vendor.objects.create(
            owner=self.user,
            store_name="Gadget Store",
            slug="gadget-store",
            business_email="gadgets@example.com",
            status=Vendor.Status.ACTIVE,
        )
        self.root_category = Category.add_root(
            name="Electronics",
            slug="electronics",
        )
        self.sub_category = self.root_category.add_child(
            name="Smartphones",
            slug="smartphones",
        )
        self.product_type = ProductType.objects.create(
            name="Smartphone",
            slug="smartphone",
            kind=ProductType.Kind.PHYSICAL,
        )
        self.client.force_authenticate(user=self.user)

    def test_category_tree(self):
        response = self.client.get("/api/v1/catalog/categories/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], "Electronics")
        self.assertEqual(len(response.data[0]["children"]), 1)
        self.assertEqual(response.data[0]["children"][0]["name"], "Smartphones")

    def test_vendor_create_product_and_variant(self):
        # Create Product
        url = "/api/v1/catalog/vendor/products/"
        data = {
            "product_type": str(self.product_type.id),
            "category": str(self.sub_category.id),
            "name": "Super Phone 15",
            "description": "The best smartphone ever made.",
            "short_description": "Super Phone 15",
            "status": Product.Status.ACTIVE,
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        product_id = response.data["id"]

        # Create Variant
        variant_url = f"/api/v1/catalog/vendor/products/{product_id}/variants/"
        variant_data = {
            "sku": "SP15-256-BLK",
            "name": "Super Phone 15 256GB Black",
            "price": "999.99",
            "compare_at_price": "1099.99",
        }
        response = self.client.post(variant_url, variant_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Check signal auto-computed product price range
        product = Product.objects.get(id=product_id)
        self.assertEqual(float(product.min_price), 999.99)
        self.assertEqual(float(product.max_price), 999.99)

    def test_public_product_list_and_detail(self):
        product = Product.objects.create(
            vendor=self.vendor,
            product_type=self.product_type,
            category=self.sub_category,
            name="Wireless Headphones",
            slug="wireless-headphones",
            status=Product.Status.ACTIVE,
        )
        ProductVariant.objects.create(
            product=product,
            sku="WH-001",
            price="149.99",
        )

        response = self.client.get("/api/v1/catalog/products/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

        detail_response = self.client.get("/api/v1/catalog/products/wireless-headphones/")
        self.assertEqual(detail_response.status_code, status.HTTP_200_OK)
        self.assertEqual(detail_response.data["name"], "Wireless Headphones")
