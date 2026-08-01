from django.contrib import admin
from vendors.models import Vendor


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = (
        "store_name",
        "owner",
        "status",
        "commission_rate",
        "is_verified",
        "created_at",
    )
    list_filter = ("status", "is_verified", "created_at")
    search_fields = ("store_name", "business_email", "owner__email", "tax_id")
    prepopulated_fields = {"slug": ("store_name",)}
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        ("Basic Info", {"fields": ("owner", "store_name", "slug", "description", "logo", "banner")}),
        ("Contact & Business", {"fields": ("business_email", "phone_number", "business_address", "tax_id")}),
        ("Marketplace Settings", {"fields": ("status", "commission_rate", "is_verified")}),
        ("Banking & Payout", {"fields": ("bank_name", "bank_account_number", "bank_routing_number")}),
        ("Metadata", {"fields": ("created_at", "updated_at")}),
    )
