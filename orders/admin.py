from django.contrib import admin
from orders.models import Order, VendorSubOrder, OrderItem, OrderLog, ReturnRequest, ReturnItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("product_name", "variant_name", "sku", "unit_price", "quantity", "line_total")


class VendorSubOrderInline(admin.StackedInline):
    model = VendorSubOrder
    extra = 0


class OrderLogInline(admin.TabularInline):
    model = OrderLog
    extra = 0
    readonly_fields = ("from_status", "to_status", "performed_by", "notes", "created_at")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("order_number", "user", "status", "grand_total", "currency", "created_at", "paid_at")
    list_filter = ("status", "created_at")
    search_fields = ("order_number", "user__email")
    inlines = [VendorSubOrderInline, OrderItemInline, OrderLogInline]


@admin.register(ReturnRequest)
class ReturnRequestAdmin(admin.ModelAdmin):
    list_display = ("order", "user", "status", "refund_amount", "created_at")
    list_filter = ("status", "created_at")
