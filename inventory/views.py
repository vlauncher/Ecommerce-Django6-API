from rest_framework import generics, permissions, status
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
from inventory.models import Warehouse, StockRecord, StockMovement
from inventory.serializers import (
    WarehouseSerializer,
    StockRecordSerializer,
    StockMovementSerializer,
    StockAdjustmentSerializer,
)
from catalog.models import ProductVariant
from vendors.permissions import IsActiveVendor
from common.pagination import StandardResultsSetPagination


@extend_schema(tags=["Inventory - Admin Warehouses"])
class WarehouseListCreateView(generics.ListCreateAPIView):
    """Manage fulfillment warehouses (Admin only)."""

    permission_classes = [permissions.IsAdminUser]
    serializer_class = WarehouseSerializer
    queryset = Warehouse.objects.all()


@extend_schema(tags=["Inventory - Vendor Dashboard"])
class VendorStockRecordListView(generics.ListAPIView):
    """Vendor dashboard: List vendor's variant stock levels."""

    permission_classes = [permissions.IsAuthenticated, IsActiveVendor]
    serializer_class = StockRecordSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return StockRecord.objects.none()
        vendor = self.request.user.vendor_profile
        return StockRecord.objects.filter(
            variant__product__vendor=vendor
        ).select_related("variant", "warehouse")


@extend_schema(tags=["Inventory - Vendor Dashboard"])
class VendorStockAdjustmentView(generics.GenericAPIView):
    """Vendor dashboard: Manually adjust stock count (e.g. new shipment or loss)."""

    permission_classes = [permissions.IsAuthenticated, IsActiveVendor]
    serializer_class = StockAdjustmentSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        variant_id = serializer.validated_data["variant_id"]
        warehouse_id = serializer.validated_data["warehouse_id"]
        quantity_delta = serializer.validated_data["quantity_delta"]
        notes = serializer.validated_data.get("notes", "")

        variant = generics.get_object_or_404(
            ProductVariant, id=variant_id, product__vendor=request.user.vendor_profile
        )
        warehouse = generics.get_object_or_404(Warehouse, id=warehouse_id)

        stock_record, created = StockRecord.objects.get_or_create(
            variant=variant, warehouse=warehouse,
            defaults={"quantity": 0},
        )
        stock_record.quantity += quantity_delta
        if stock_record.quantity < 0:
            stock_record.quantity = 0
        stock_record.save(update_fields=["quantity"])

        movement = StockMovement.objects.create(
            variant=variant,
            warehouse=warehouse,
            movement_type=StockMovement.MovementType.MANUAL_ADJUSTMENT,
            quantity_delta=quantity_delta,
            performed_by=request.user,
            notes=notes,
        )

        return Response(StockRecordSerializer(stock_record).data, status=status.HTTP_200_OK)


@extend_schema(tags=["Inventory - Vendor Dashboard"])
class VendorStockMovementListView(generics.ListAPIView):
    """Vendor dashboard: View stock movement audit trail."""

    permission_classes = [permissions.IsAuthenticated, IsActiveVendor]
    serializer_class = StockMovementSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return StockMovement.objects.none()
        vendor = self.request.user.vendor_profile
        return StockMovement.objects.filter(
            variant__product__vendor=vendor
        ).select_related("variant", "warehouse")
