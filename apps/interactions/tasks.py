from datetime import timedelta

from django.utils import timezone

from apps.shops.models import ShopInvitation
from .models import Offer


def expire_offers():
    """Expire submitted and countered offers whose response window elapsed."""
    return Offer.objects.filter(
        status__in=(Offer.Status.SUBMITTED, Offer.Status.COUNTERED),
        expires_at__lte=timezone.now(),
    ).update(status=Offer.Status.EXPIRED)


def revoke_expired_invitations():
    """Revoke invitations that can no longer be accepted."""
    return ShopInvitation.objects.filter(
        expires_at__lte=timezone.now(),
        accepted_at__isnull=True,
        revoked_at__isnull=True,
    ).update(revoked_at=timezone.now())
