from rest_framework import generics, permissions, status
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
from shipping.models import ShippingZone, ShippingMethod, Fulfillment
from shipping.serializers import (
    ShippingZoneSerializer,
    ShippingMethodSerializer,
    FulfillmentSerializer,
)
from orders.models import VendorSubOrder
from vendors.permissions import IsActiveVendor


@extend_schema(tags=["Shipping"])
class PublicShippingMethodListView(generics.ListAPIView):
    """List available shipping methods for a given country code."""

    permission_classes = [permissions.AllowAny]
    serializer_class = ShippingMethodSerializer

    def get_queryset(self):
        country_code = self.request.query_params.get("country", "US").upper()
        return ShippingMethod.objects.filter(
            is_active=True,
            zone__is_active=True,
            zone__countries__contains=[country_code],
        )


@extend_schema(tags=["Shipping - Admin"])
class AdminShippingZoneListCreateView(generics.ListCreateAPIView):
    """Manage geographic shipping zones (Admin only)."""

    permission_classes = [permissions.IsAdminUser]
    serializer_class = ShippingZoneSerializer
    queryset = ShippingZone.objects.prefetch_related("methods").all()


@extend_schema(tags=["Shipping - Vendor Dashboard"])
class VendorFulfillmentCreateView(generics.CreateAPIView):
    """Vendor dashboard: Create shipment tracking fulfillment for sub-order."""

    permission_classes = [permissions.IsAuthenticated, IsActiveVendor]
    serializer_class = FulfillmentSerializer

    def create(self, request, *args, **kwargs):
        sub_order_id = request.data.get("sub_order")
        sub_order = generics.get_object_or_404(
            VendorSubOrder, id=sub_order_id, vendor=request.user.vendor_profile
        )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        fulfillment = serializer.save()

        # Update sub-order tracking info and status
        sub_order.tracking_number = fulfillment.tracking_number
        sub_order.tracking_url = fulfillment.tracking_url
        sub_order.status = VendorSubOrder.Status.SHIPPED
        sub_order.save(update_fields=["tracking_number", "tracking_url", "status"])

        return Response(FulfillmentSerializer(fulfillment).data, status=status.HTTP_201_CREATED)
