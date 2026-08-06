import hashlib
import secrets
from datetime import timedelta

from asgiref.sync import sync_to_async
from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify
from ninja.errors import HttpError

from apps.users.models import User

from .models import Shop, ShopInvitation, ShopMembership

VALID_ROLES = {choice.value for choice in ShopMembership.Role}
MANAGER_ROLES = {ShopMembership.Role.OWNER, ShopMembership.Role.MANAGER}


def _shop_dict(shop):
    return {"id": shop.id, "name": shop.name, "slug": shop.slug, "description": shop.description, "is_active": shop.is_active}


def _membership_dict(membership):
    user = membership.user
    return {"id": membership.id, "user_id": user.id, "email": user.email, "first_name": user.first_name, "last_name": user.last_name, "role": membership.role, "is_active": membership.is_active}


@sync_to_async(thread_sensitive=True)
def create_shop(user, data):
    with transaction.atomic():
        slug = data.get("slug") or slugify(data["name"])
        if not slug:
            raise HttpError(400, "Shop name must produce a valid slug.")
        if Shop.objects.filter(slug=slug).exists():
            raise HttpError(400, "A shop with this slug already exists.")
        shop = Shop.objects.create(name=data["name"], slug=slug, description=data.get("description", ""), created_by=user)
        ShopMembership.objects.create(shop=shop, user=user, role=ShopMembership.Role.OWNER)
        return _shop_dict(shop)


@sync_to_async(thread_sensitive=True)
def update_shop(shop, data):
    for field in ("name", "description", "is_active"):
        if data.get(field) is not None:
            setattr(shop, field, data[field])
    shop.save(update_fields=[field for field in ("name", "description", "is_active", "updated_at") if data.get(field) is not None or field == "updated_at"])
    return _shop_dict(shop)


@sync_to_async(thread_sensitive=True)
def list_memberships(shop):
    return [_membership_dict(item) for item in ShopMembership.objects.select_related("user").filter(shop=shop)]


@sync_to_async(thread_sensitive=True)
def change_membership(shop, acting_membership, user_id, role=None, remove=False):
    try:
        membership = ShopMembership.objects.select_related("user").get(shop=shop, user_id=user_id)
    except ShopMembership.DoesNotExist:
        raise HttpError(404, "Membership not found.")
    if membership.role == ShopMembership.Role.OWNER and acting_membership.role != ShopMembership.Role.OWNER:
        raise HttpError(403, "Only an owner can manage another owner.")
    if remove:
        if membership.role == ShopMembership.Role.OWNER and ShopMembership.objects.filter(shop=shop, role=ShopMembership.Role.OWNER, is_active=True).count() == 1:
            raise HttpError(400, "A shop must have at least one owner.")
        membership.delete()
        return None
    if role not in VALID_ROLES:
        raise HttpError(400, "Invalid membership role.")
    if role == ShopMembership.Role.OWNER and acting_membership.role != ShopMembership.Role.OWNER:
        raise HttpError(403, "Only an owner can assign the owner role.")
    membership.role = role
    membership.save(update_fields=("role", "updated_at"))
    return _membership_dict(membership)


@sync_to_async(thread_sensitive=True)
def create_invitation(shop, inviter, email, role):
    email = email.lower().strip()
    if role not in VALID_ROLES or role == ShopMembership.Role.OWNER:
        raise HttpError(400, "Invitations may only assign manager, staff, or customer roles.")
    user = User.objects.filter(email__iexact=email).first()
    if user and ShopMembership.objects.filter(shop=shop, user=user, is_active=True).exists():
        raise HttpError(400, "This user is already a member of the shop.")

    raw_token = secrets.token_urlsafe(32)
    expiry = timezone.now() + timedelta(days=getattr(settings, "SHOP_INVITATION_EXPIRY_DAYS", 7))
    invitation = ShopInvitation.objects.create(
        shop=shop,
        email=email,
        role=role,
        token_hash=hashlib.sha256(raw_token.encode()).hexdigest(),
        expires_at=expiry,
        created_by=inviter,
    )
    send_mail(
        subject=f"Invitation to join {shop.name}",
        message=f"You have been invited to join {shop.name} as {role}. Accept with invitation token: {raw_token}",
        from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@ecommerce.com"),
        recipient_list=[email],
        fail_silently=False,
    )
    return {"detail": "Invitation sent successfully.", "expires_at": invitation.expires_at}


@sync_to_async(thread_sensitive=True)
def accept_invitation(user, raw_token):
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    try:
        invitation = ShopInvitation.objects.select_related("shop").get(token_hash=token_hash)
    except ShopInvitation.DoesNotExist:
        raise HttpError(400, "Invalid invitation.")
    if not invitation.is_usable or invitation.email.lower() != user.email.lower():
        raise HttpError(400, "This invitation is invalid, expired, or belongs to another email address.")
    with transaction.atomic():
        membership, _ = ShopMembership.objects.update_or_create(
            shop=invitation.shop,
            user=user,
            defaults={"role": invitation.role, "is_active": True},
        )
        invitation.accepted_at = timezone.now()
        invitation.save(update_fields=("accepted_at",))
    return {"detail": f"You joined {invitation.shop.name} successfully."}


@sync_to_async(thread_sensitive=True)
def list_user_shops(user):
    return [{"id": membership.shop_id, "name": membership.shop.name, "slug": membership.shop.slug, "role": membership.role, "is_active": membership.shop.is_active} for membership in ShopMembership.objects.select_related("shop").filter(user=user, is_active=True)]


@sync_to_async(thread_sensitive=True)
def deactivate_shop(shop):
    shop.is_active = False
    shop.save(update_fields=("is_active", "updated_at"))
    return {"detail": "Shop deactivated successfully."}
