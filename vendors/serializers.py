from rest_framework import serializers
from django.utils.text import slugify
from vendors.models import Vendor


class VendorRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendor
        fields = (
            "store_name",
            "description",
            "business_email",
            "phone_number",
            "business_address",
            "tax_id",
            "bank_name",
            "bank_account_number",
            "bank_routing_number",
        )

    def validate_store_name(self, value):
        slug = slugify(value)
        if Vendor.objects.filter(slug=slug).exists():
            raise serializers.ValidationError("A vendor with this store name already exists.")
        return value

    def create(self, validated_data):
        user = self.context["request"].user
        if hasattr(user, "vendor_profile"):
            raise serializers.ValidationError("User already has a vendor profile.")
        
        slug = slugify(validated_data["store_name"])
        vendor = Vendor.objects.create(
            owner=user,
            slug=slug,
            **validated_data
        )
        return vendor


class VendorPublicSerializer(serializers.ModelSerializer):
    owner_name = serializers.CharField(source="owner.full_name", read_only=True)

    class Meta:
        model = Vendor
        fields = (
            "id",
            "store_name",
            "slug",
            "description",
            "logo",
            "banner",
            "is_verified",
            "owner_name",
            "created_at",
        )


class VendorDetailSerializer(serializers.ModelSerializer):
    owner_email = serializers.CharField(source="owner.email", read_only=True)
    owner_name = serializers.CharField(source="owner.full_name", read_only=True)

    class Meta:
        model = Vendor
        fields = (
            "id",
            "store_name",
            "slug",
            "description",
            "logo",
            "banner",
            "business_email",
            "phone_number",
            "business_address",
            "tax_id",
            "status",
            "commission_rate",
            "is_verified",
            "bank_name",
            "bank_account_number",
            "bank_routing_number",
            "owner_email",
            "owner_name",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("status", "commission_rate", "is_verified", "slug")
