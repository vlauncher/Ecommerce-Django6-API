from django.utils import timezone

from .models import Cart


def purge_expired_carts():
    """Remove abandoned guest carts and expired carts."""
    return Cart.objects.filter(expires_at__isnull=False, expires_at__lte=timezone.now()).delete()[0]
