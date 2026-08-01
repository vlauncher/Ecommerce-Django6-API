from rest_framework import serializers
from shipping.models import ShippingZone, ShippingMethod, Fulfillment


class ShippingMethodSerializer(serializers.ModelSerializer):
    zone_name = serializers.CharField(source="zone.name", read_only=True)

    class Meta:
        model = ShippingMethod
        fields = (
            "id",
            "zone",
            "zone_name",
            "name",
            "rate_type",
            "base_rate",
            "free_shipping_threshold",
            "estimated_days",
            "is_active",
        )


class ShippingZoneSerializer(serializers.ModelSerializer):
    methods = ShippingMethodSerializer(many=True, read_only=True)

    class Meta:
        model = ShippingZone
        fields = ("id", "name", "countries", "is_active", "methods")


class FulfillmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Fulfillment
        fields = (
            "id",
            "sub_order",
            "warehouse",
            "carrier",
            "tracking_number",
            "tracking_url",
            "status",
            "shipped_at",
            "delivered_at",
        )
