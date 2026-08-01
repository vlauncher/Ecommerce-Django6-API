from django.contrib import admin
from inventory.models import Warehouse, StockRecord, StockMovement


@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "is_active", "created_at")
    search_fields = ("name", "code")


@admin.register(StockRecord)
class StockRecordAdmin(admin.ModelAdmin):
    list_display = ("variant", "warehouse", "quantity", "reserved", "available_quantity", "low_stock_threshold")
    list_filter = ("warehouse",)
    search_fields = ("variant__sku", "variant__product__name")


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ("variant", "warehouse", "movement_type", "quantity_delta", "performed_by", "created_at")
    list_filter = ("movement_type", "warehouse", "created_at")
    search_fields = ("variant__sku", "reference_id")
