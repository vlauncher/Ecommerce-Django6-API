from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from notifications.models import Notification
from notifications.dispatchers import MultiChannelNotificationEngine

User = get_user_model()


class NotificationAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(email="user@example.com", password="Password123!", is_active=True)

    def test_multi_channel_engine_and_notification_list(self):
        MultiChannelNotificationEngine.notify_user(
            user=self.user,
            title="Order Shipped",
            message="Your order #ORD-123 has been shipped!",
        )

        # Check in-app notification DB record
        self.assertEqual(Notification.objects.filter(user=self.user).count(), 1)
        notif = Notification.objects.get(user=self.user)
        self.assertEqual(notif.title, "Order Shipped")
        self.assertFalse(notif.is_read)

        # API list
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/v1/notifications/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

        # Mark read
        read_response = self.client.post(f"/api/v1/notifications/{notif.id}/read/")
        self.assertEqual(read_response.status_code, status.HTTP_200_OK)
        self.assertTrue(read_response.data["is_read"])
