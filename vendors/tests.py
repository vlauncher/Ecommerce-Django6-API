from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from vendors.models import Vendor

User = get_user_model()


class VendorAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="vendor@example.com",
            password="Password123!",
            first_name="Vendor",
            last_name="Owner",
            is_active=True,
        )
        self.client.force_authenticate(user=self.user)

    def test_register_vendor(self):
        url = "/api/v1/vendors/register/"
        data = {
            "store_name": "Tech Galaxy Store",
            "description": "Premium electronics seller",
            "business_email": "contact@techgalaxy.com",
            "phone_number": "+1234567890",
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["store_name"], "Tech Galaxy Store")
        self.assertEqual(response.data["slug"], "tech-galaxy-store")

        # Verify vendor exists in database
        vendor = Vendor.objects.get(owner=self.user)
        self.assertEqual(vendor.status, Vendor.Status.PENDING)

    def test_vendor_list_and_dashboard(self):
        vendor = Vendor.objects.create(
            owner=self.user,
            store_name="Active Store",
            slug="active-store",
            business_email="active@store.com",
            status=Vendor.Status.ACTIVE,
        )

        # Public list
        self.client.logout()
        response = self.client.get("/api/v1/vendors/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

        # Dashboard
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/v1/vendors/me/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["store_name"], "Active Store")
