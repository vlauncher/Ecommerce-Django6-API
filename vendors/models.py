from django.db import models
from django.conf import settings
from common.models import TimeStampedModel


class Vendor(TimeStampedModel):
    """Multi-vendor marketplace seller profile."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending Approval"
        ACTIVE = "active", "Active"
        SUSPENDED = "suspended", "Suspended"
        CLOSED = "closed", "Closed"

    owner = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="vendor_profile",
    )
    store_name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True, db_index=True)
    description = models.TextField(blank=True)
    logo = models.ImageField(upload_to="vendors/logos/", blank=True, null=True)
    banner = models.ImageField(upload_to="vendors/banners/", blank=True, null=True)

    # Contact & Business details
    business_email = models.EmailField()
    phone_number = models.CharField(max_length=30, blank=True)
    business_address = models.TextField(blank=True)
    tax_id = models.CharField(max_length=50, blank=True)

    # Platform relationship
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    commission_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=10.00,
        help_text="Platform commission percentage (e.g., 10.00 = 10%)",
    )
    is_verified = models.BooleanField(default=False)

    # Bank / payout details
    bank_name = models.CharField(max_length=255, blank=True)
    bank_account_number = models.CharField(max_length=50, blank=True)
    bank_routing_number = models.CharField(max_length=50, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "is_verified"]),
        ]

    def __str__(self):
        return self.store_name
