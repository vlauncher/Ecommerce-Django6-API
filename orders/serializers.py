from rest_framework import serializers
from orders.models import Order, VendorSubOrder, OrderItem, OrderLog, ReturnRequest, ReturnItem
from vendors.serializers import VendorPublicSerializer


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = (
            "id",
            "product_name",
            "variant_name",
            "sku",
            "variant_attributes",
            "unit_price",
            "quantity",
            "line_total",
            "download_url",
            "download_expires_at",
        )


class VendorSubOrderSerializer(serializers.ModelSerializer):
    vendor = VendorPublicSerializer(read_only=True)
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = VendorSubOrder
        fields = (
            "id",
            "vendor",
            "status",
            "subtotal",
            "commission_amount",
            "vendor_payout",
            "tracking_number",
            "tracking_url",
            "items",
            "created_at",
        )


class OrderLogSerializer(serializers.ModelSerializer):
    performed_by_email = serializers.CharField(source="performed_by.email", read_only=True)

    class Meta:
        model = OrderLog
        fields = ("id", "from_status", "to_status", "performed_by_email", "notes", "created_at")


class OrderListSerializer(serializers.ModelSerializer):
    items_count = serializers.IntegerField(source="items.count", read_only=True)

    class Meta:
        model = Order
        fields = (
            "id",
            "order_number",
            "status",
            "grand_total",
            "currency",
            "items_count",
            "created_at",
            "paid_at",
        )


class OrderDetailSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    sub_orders = VendorSubOrderSerializer(many=True, read_only=True)
    logs = OrderLogSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = (
            "id",
            "order_number",
            "status",
            "shipping_address",
            "billing_address",
            "subtotal",
            "shipping_total",
            "tax_total",
            "discount_total",
            "grand_total",
            "currency",
            "notes",
            "items",
            "sub_orders",
            "logs",
            "created_at",
            "paid_at",
            "shipped_at",
            "delivered_at",
        )


class CheckoutSerializer(serializers.Serializer):
    shipping_address = serializers.DictField()
    billing_address = serializers.DictField()
    notes = serializers.CharField(required=False, allow_blank=True)


class ReturnRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReturnRequest
        fields = ("id", "order", "status", "reason", "admin_notes", "refund_amount", "created_at")
        read_only_fields = ("status", "admin_notes", "refund_amount", "order")
