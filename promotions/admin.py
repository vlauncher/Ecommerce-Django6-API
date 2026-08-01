from django.contrib import admin
from promotions.models import Coupon, CouponUsage, FlashSale, TieredPrice


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ("code", "discount_type", "value", "min_order_value", "times_used", "is_active", "valid_to")
    list_filter = ("discount_type", "is_active")
    search_fields = ("code",)


@admin.register(FlashSale)
class FlashSaleAdmin(admin.ModelAdmin):
    list_display = ("title", "discount_percentage", "start_time", "end_time", "is_active")
    list_filter = ("is_active",)


@admin.register(TieredPrice)
class TieredPriceAdmin(admin.ModelAdmin):
    list_display = ("variant", "min_quantity", "unit_price")
