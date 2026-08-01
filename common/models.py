import uuid
from django.db import models
from django.conf import settings


class TimeStampedModel(models.Model):
    """Abstract base model with UUID primary key and timestamp audit fields."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Address(TimeStampedModel):
    """User shipping and billing address book entries."""

    class AddressType(models.TextChoices):
        SHIPPING = "shipping", "Shipping Address"
        BILLING = "billing", "Billing Address"
        BOTH = "both", "Shipping & Billing"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="addresses",
    )
    address_type = models.CharField(
        max_length=20,
        choices=AddressType.choices,
        default=AddressType.SHIPPING,
    )
    recipient_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=30)
    street_address_1 = models.CharField(max_length=255)
    street_address_2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20)
    country_code = models.CharField(
        max_length=2,
        default="US",
        help_text="ISO 3166-1 alpha-2 country code (e.g. US, NG, GB)",
    )
    is_default = models.BooleanField(default=False)

    class Meta:
        ordering = ["-is_default", "-created_at"]
        verbose_name_plural = "addresses"

    def __str__(self):
        return f"{self.recipient_name} — {self.street_address_1}, {self.city}"

    def save(self, *args, **kwargs):
        if self.is_default:
            # Set all other addresses for this user to is_default=False
            Address.objects.filter(
                user=self.user,
                address_type=self.address_type,
            ).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)
