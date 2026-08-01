from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from catalog.models import ProductVariant


@receiver(post_save, sender=ProductVariant)
@receiver(post_delete, sender=ProductVariant)
def update_product_price_range(sender, instance, **kwargs):
    """Automatically recalculate product min/max price when variants change."""
    instance.product.update_price_range()
