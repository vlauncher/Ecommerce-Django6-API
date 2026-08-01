from rest_framework import serializers
from inventory.models import Warehouse, StockRecord, StockMovement


class WarehouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Warehouse
        fields = ("id", "name", "code", "address", "is_active", "created_at")


class StockRecordSerializer(serializers.ModelSerializer):
    warehouse_name = serializers.CharField(source="warehouse.name", read_only=True)
    sku = serializers.CharField(source="variant.sku", read_only=True)
    available_quantity = serializers.IntegerField(read_only=True)

    class Meta:
        model = StockRecord
        fields = (
            "id",
            "variant",
            "sku",
            "warehouse",
            "warehouse_name",
            "quantity",
            "reserved",
            "available_quantity",
            "low_stock_threshold",
            "updated_at",
        )


class StockMovementSerializer(serializers.ModelSerializer):
    performed_by_email = serializers.CharField(source="performed_by.email", read_only=True, default=None)

    class Meta:
        model = StockMovement
        fields = (
            "id",
            "variant",
            "warehouse",
            "movement_type",
            "quantity_delta",
            "reference_id",
            "performed_by_email",
            "notes",
            "created_at",
        )


class StockAdjustmentSerializer(serializers.Serializer):
    variant_id = serializers.UUIDField()
    warehouse_id = serializers.UUIDField()
    quantity_delta = serializers.IntegerField()
    notes = serializers.CharField(required=False, allow_blank=True)
