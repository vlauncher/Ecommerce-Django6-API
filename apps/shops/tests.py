from unittest.mock import patch

from django.test import Client, TestCase

from apps.users.models import User

from .models import Shop, ShopMembership
from apps.users.auth import create_jwt_token


class ShopApiTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.owner = User.objects.create_user(
            email="owner@example.com",
            password="Password123!",
            first_name="Shop",
            last_name="Owner",
            is_verified=True,
        )
        self.member = User.objects.create_user(
            email="member@example.com",
            password="Password123!",
            first_name="Shop",
            last_name="Member",
            is_verified=True,
        )

    def auth_headers(self, user):
        token = create_jwt_token(user.id)["access"]
        return {"HTTP_AUTHORIZATION": f"Bearer {token}"}

    def test_authenticated_user_creates_shop_and_becomes_owner(self):
        response = self.client.post(
            "/api/v1/shops/",
            data={"name": "My Store", "description": "A test store"},
            content_type="application/json",
            **self.auth_headers(self.owner),
        )

        self.assertEqual(response.status_code, 201)
        shop = Shop.objects.get(slug="my-store")
        self.assertTrue(ShopMembership.objects.filter(shop=shop, user=self.owner, role="owner").exists())
        self.assertEqual(response.json()["slug"], "my-store")

    def test_non_member_cannot_access_shop(self):
        shop = Shop.objects.create(name="Private Store", slug="private-store", created_by=self.owner)
        ShopMembership.objects.create(shop=shop, user=self.owner, role="owner")

        response = self.client.get(
            "/api/v1/shops/private-store",
            **self.auth_headers(self.member),
        )

        self.assertEqual(response.status_code, 403)

    @patch("apps.shops.services.send_mail")
    def test_owner_can_invite_and_member_can_accept(self, mock_send_mail):
        shop = Shop.objects.create(name="Invite Store", slug="invite-store", created_by=self.owner)
        ShopMembership.objects.create(shop=shop, user=self.owner, role="owner")

        invite_response = self.client.post(
            "/api/v1/shops/invite-store/invitations",
            data={"email": self.member.email, "role": "staff"},
            content_type="application/json",
            **self.auth_headers(self.owner),
        )
        self.assertEqual(invite_response.status_code, 200)
        raw_token = mock_send_mail.call_args.kwargs["message"].split("token: ", 1)[1]

        accept_response = self.client.post(
            f"/api/v1/invitations/{raw_token}/accept",
            content_type="application/json",
            **self.auth_headers(self.member),
        )
        self.assertEqual(accept_response.status_code, 200)
        self.assertEqual(
            ShopMembership.objects.get(shop=shop, user=self.member).role,
            ShopMembership.Role.STAFF,
        )

    def test_last_owner_cannot_be_removed(self):
        shop = Shop.objects.create(name="Owner Store", slug="owner-store", created_by=self.owner)
        ShopMembership.objects.create(shop=shop, user=self.owner, role="owner")

        response = self.client.delete(
            f"/api/v1/shops/owner-store/members/{self.owner.id}",
            **self.auth_headers(self.owner),
        )

        self.assertEqual(response.status_code, 400)
