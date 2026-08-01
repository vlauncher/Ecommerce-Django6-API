from rest_framework import serializers
from promotions.models import Coupon, FlashSale, TieredPrice


class CouponSerializer(serializers.ModelSerializer):
    is_valid = serializers.BooleanField(read_only=True)

    class Meta:
        model = Coupon
        fields = (
            "id",
            "code",
            "discount_type",
            "value",
            "min_order_value",
            "max_discount_amount",
            "usage_limit_total",
            "usage_limit_per_user",
            "times_used",
            "valid_from",
            "valid_to",
            "is_active",
            "is_valid",
        )


class ApplyCouponSerializer(serializers.Serializer):
    code = serializers.CharField()


class FlashSaleSerializer(serializers.ModelSerializer):
    is_currently_active = serializers.BooleanField(read_only=True)

    class Meta:
        model = FlashSale
        fields = (
            "id",
            "title",
            "discount_percentage",
            "products",
            "start_time",
            "end_time",
            "is_active",
            "is_currently_active",
        )


class TieredPriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = TieredPrice
        fields = ("id", "variant", "min_quantity", "unit_price")
