from unittest.mock import patch
from django.test import TestCase
from django.test import Client
from apps.users.models import User, UserProfile


class DjangoNinjaUsersApiTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.register_url = "/api/v1/auth/register"
        self.verify_otp_url = "/api/v1/auth/verify-otp"
        self.login_url = "/api/v1/auth/login"
        self.profile_url = "/api/v1/users/profile"

        self.user_data = {
            "first_name": "Jane",
            "last_name": "Doe",
            "email": "jane@example.com",
            "password": "Password123!",
            "confirm_password": "Password123!",
        }

    @patch("apps.users.services.send_mail")
    def test_register_and_verify_otp(self, mock_send_mail):
        # 1. Register
        response = self.client.post(
            self.register_url,
            data=self.user_data,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)

        user = User.objects.get(email="jane@example.com")
        self.assertFalse(user.is_verified)
        self.assertTrue(UserProfile.objects.filter(user=user).exists())

        # Extract OTP sent in test
        call_message = mock_send_mail.call_args[1]["message"]
        otp = call_message.split("is: ")[1].split(".")[0]

        # 2. Verify OTP (only OTP passed)
        verify_res = self.client.post(
            self.verify_otp_url,
            data={"otp": otp},
            content_type="application/json",
        )
        self.assertEqual(verify_res.status_code, 200)

        user.refresh_from_db()
        self.assertTrue(user.is_verified)

    @patch("apps.users.services.send_mail")
    def test_login_and_get_profile(self, mock_send_mail):
        # Register & Verify
        self.client.post(
            self.register_url,
            data=self.user_data,
            content_type="application/json",
        )
        call_message = mock_send_mail.call_args[1]["message"]
        otp = call_message.split("is: ")[1].split(".")[0]
        self.client.post(
            self.verify_otp_url,
            data={"otp": otp},
            content_type="application/json",
        )

        # Login
        login_res = self.client.post(
            self.login_url,
            data={"email": "jane@example.com", "password": "Password123!"},
            content_type="application/json",
        )
        self.assertEqual(login_res.status_code, 200)
        data = login_res.json()
        self.assertIn("access", data)
        self.assertIn("refresh", data)

        # Profile GET
        access_token = data["access"]
        profile_res = self.client.get(
            self.profile_url,
            HTTP_AUTHORIZATION=f"Bearer {access_token}",
        )
        self.assertEqual(profile_res.status_code, 200)
        prof_data = profile_res.json()
        self.assertEqual(prof_data["user"]["email"], "jane@example.com")
