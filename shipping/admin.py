from django.contrib import admin
from shipping.models import ShippingZone, ShippingMethod, Fulfillment


class ShippingMethodInline(admin.TabularInline):
    model = ShippingMethod
    extra = 1


@admin.register(ShippingZone)
class ShippingZoneAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "created_at")
    inlines = [ShippingMethodInline]


@admin.register(Fulfillment)
class FulfillmentAdmin(admin.ModelAdmin):
    list_display = ("sub_order", "carrier", "tracking_number", "status", "shipped_at")
    list_filter = ("status", "carrier")
