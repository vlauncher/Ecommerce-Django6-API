from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from orders.models import Order
from payments.models import PaymentTransaction

User = get_user_model()


class PaymentAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="payer@example.com",
            password="Password123!",
            is_active=True,
        )
        self.order = Order.objects.create(
            order_number="ORD-TEST-001",
            user=self.user,
            status=Order.Status.PENDING_PAYMENT,
            subtotal="100.00",
            grand_total="100.00",
        )

    def test_initiate_stripe_payment(self):
        self.client.force_authenticate(user=self.user)
        url = "/api/v1/payments/initiate/"
        data = {
            "order_number": self.order.order_number,
            "gateway": "stripe",
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["gateway"], "stripe")
        self.assertTrue(response.data["client_secret"].startswith("pi_stripe_"))

        # Verify database record
        tx = PaymentTransaction.objects.get(id=response.data["transaction_id"])
        self.assertEqual(tx.status, PaymentTransaction.Status.PENDING)
