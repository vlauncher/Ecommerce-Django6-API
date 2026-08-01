from unittest.mock import patch
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from accounts.models import OTP

User = get_user_model()


class AuthenticationTests(APITestCase):

    def setUp(self):
        self.register_url = reverse("accounts:register")
        self.verify_otp_url = reverse("accounts:verify-otp")
        self.resend_otp_url = reverse("accounts:resend-otp")
        self.login_url = reverse("accounts:login")
        self.google_login_url = reverse("accounts:google-login")
        self.token_refresh_url = reverse("accounts:token-refresh")
        self.profile_url = reverse("accounts:user-profile")

        self.user_data = {
            "email": "testuser@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "password": "StrongPassword123!",
            "password_confirm": "StrongPassword123!",
        }

    def test_registration_creates_inactive_user_and_otp(self):
        response = self.client.post(self.register_url, self.user_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        user = User.objects.get(email=self.user_data["email"])
        self.assertFalse(user.is_active)
        self.assertEqual(user.first_name, "John")
        self.assertEqual(user.last_name, "Doe")

        otp = OTP.objects.filter(user=user).first()
        self.assertIsNotNone(otp)
        self.assertEqual(len(otp.code), 6)
        self.assertFalse(otp.is_used)

    def test_verify_otp_activates_user_and_returns_jwt(self):
        self.client.post(self.register_url, self.user_data)
        user = User.objects.get(email=self.user_data["email"])
        otp = OTP.objects.filter(user=user).first()

        response = self.client.post(
            self.verify_otp_url,
            {"email": user.email, "otp": otp.code},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("tokens", response.data)
        self.assertIn("access", response.data["tokens"])
        self.assertIn("refresh", response.data["tokens"])

        user.refresh_from_db()
        self.assertTrue(user.is_active)

        otp.refresh_from_db()
        self.assertTrue(otp.is_used)

    def test_verify_invalid_otp_fails(self):
        self.client.post(self.register_url, self.user_data)
        response = self.client.post(
            self.verify_otp_url,
            {"email": self.user_data["email"], "otp": "000000"},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_verify_expired_otp_fails(self):
        self.client.post(self.register_url, self.user_data)
        user = User.objects.get(email=self.user_data["email"])
        otp = OTP.objects.filter(user=user).first()
        
        # Expire the OTP
        otp.expires_at = timezone.now() - timedelta(minutes=1)
        otp.save()

        response = self.client.post(
            self.verify_otp_url,
            {"email": user.email, "otp": otp.code},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_unverified_account_fails(self):
        self.client.post(self.register_url, self.user_data)
        response = self.client.post(
            self.login_url,
            {"email": self.user_data["email"], "password": self.user_data["password"]},
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_verified_account_succeeds(self):
        self.client.post(self.register_url, self.user_data)
        user = User.objects.get(email=self.user_data["email"])
        otp = OTP.objects.filter(user=user).first()
        self.client.post(self.verify_otp_url, {"email": user.email, "otp": otp.code})

        response = self.client.post(
            self.login_url,
            {"email": self.user_data["email"], "password": self.user_data["password"]},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_resend_otp_generates_new_code(self):
        self.client.post(self.register_url, self.user_data)
        user = User.objects.get(email=self.user_data["email"])
        old_otp = OTP.objects.filter(user=user).first()

        response = self.client.post(self.resend_otp_url, {"email": user.email})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        old_otp.refresh_from_db()
        self.assertTrue(old_otp.is_used)

        new_otp = OTP.objects.filter(user=user, is_used=False).first()
        self.assertIsNotNone(new_otp)
        self.assertNotEqual(old_otp.code, new_otp.code)

    def test_user_profile_endpoint(self):
        self.client.post(self.register_url, self.user_data)
        user = User.objects.get(email=self.user_data["email"])
        otp = OTP.objects.filter(user=user).first()
        verify_res = self.client.post(self.verify_otp_url, {"email": user.email, "otp": otp.code})
        access_token = verify_res.data["tokens"]["access"]

        # Request profile without token
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Request profile with token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], user.email)
        self.assertEqual(response.data["full_name"], "John Doe")

    @patch("accounts.services.GoogleOAuthService.verify_token")
    def test_google_oauth_login(self, mock_verify):
        mock_verify.return_value = {
            "email": "googleuser@example.com",
            "given_name": "Google",
            "family_name": "User",
        }

        response = self.client.post(
            self.google_login_url,
            {"id_token": "fake-google-id-token"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("tokens", response.data)
        self.assertTrue(response.data["created"])

        user = User.objects.get(email="googleuser@example.com")
        self.assertTrue(user.is_active)
        self.assertEqual(user.first_name, "Google")
        self.assertEqual(user.last_name, "User")

