from django.db.models import Sum, Count, Avg
from rest_framework import generics, permissions, status, serializers
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, inline_serializer
from orders.models import Order, VendorSubOrder, OrderItem
from vendors.models import Vendor
from vendors.permissions import IsActiveVendor


@extend_schema(
    tags=["Analytics - Vendor Dashboard"],
    responses={
        200: inline_serializer(
            name="VendorSalesAnalyticsResponse",
            fields={
                "total_orders": serializers.IntegerField(),
                "total_sales": serializers.CharField(),
                "total_commission": serializers.CharField(),
                "total_payout": serializers.CharField(),
                "average_order_value": serializers.CharField(),
            },
        )
    },
)
class VendorSalesAnalyticsView(generics.GenericAPIView):
    """Vendor sales performance dashboard metrics."""

    permission_classes = [permissions.IsAuthenticated, IsActiveVendor]

    def get(self, request):
        vendor = request.user.vendor_profile
        sub_orders = VendorSubOrder.objects.filter(vendor=vendor)

        total_orders = sub_orders.count()
        aggregates = sub_orders.aggregate(
            total_sales=Sum("subtotal"),
            total_commission=Sum("commission_amount"),
            total_payout=Sum("vendor_payout"),
            aov=Avg("subtotal"),
        )

        return Response({
            "total_orders": total_orders,
            "total_sales": str(aggregates["total_sales"] or "0.00"),
            "total_commission": str(aggregates["total_commission"] or "0.00"),
            "total_payout": str(aggregates["total_payout"] or "0.00"),
            "average_order_value": str(aggregates["aov"] or "0.00"),
        }, status=status.HTTP_200_OK)


@extend_schema(
    tags=["Analytics - Vendor Dashboard"],
    responses={
        200: inline_serializer(
            name="VendorTopProductsResponse",
            fields={
                "product_name": serializers.CharField(),
                "sku": serializers.CharField(),
                "total_quantity": serializers.IntegerField(),
                "total_revenue": serializers.CharField(),
            },
            many=True,
        )
    },
)
class VendorTopProductsView(generics.GenericAPIView):
    """Best selling products for vendor."""

    permission_classes = [permissions.IsAuthenticated, IsActiveVendor]

    def get(self, request):
        vendor = request.user.vendor_profile
        top_items = (
            OrderItem.objects
            .filter(sub_order__vendor=vendor)
            .values("product_name", "sku")
            .annotate(total_quantity=Sum("quantity"), total_revenue=Sum("line_total"))
            .order_by("-total_quantity")[:10]
        )
        return Response(list(top_items), status=status.HTTP_200_OK)


@extend_schema(
    tags=["Analytics - Admin"],
    responses={
        200: inline_serializer(
            name="AdminPlatformAnalyticsResponse",
            fields={
                "total_active_vendors": serializers.IntegerField(),
                "total_orders": serializers.IntegerField(),
                "gross_revenue": serializers.CharField(),
                "platform_commission_earned": serializers.CharField(),
                "average_order_value": serializers.CharField(),
            },
        )
    },
)
class AdminPlatformAnalyticsView(generics.GenericAPIView):
    """Platform-wide financial and vendor performance metrics (Admin only)."""

    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        total_orders = Order.objects.count()
        total_vendors = Vendor.objects.filter(status=Vendor.Status.ACTIVE).count()

        order_aggs = Order.objects.aggregate(
            gross_revenue=Sum("grand_total"),
            average_order_value=Avg("grand_total"),
        )
        sub_order_aggs = VendorSubOrder.objects.aggregate(
            total_commission_earned=Sum("commission_amount"),
        )

        return Response({
            "total_active_vendors": total_vendors,
            "total_orders": total_orders,
            "gross_revenue": str(order_aggs["gross_revenue"] or "0.00"),
            "platform_commission_earned": str(sub_order_aggs["total_commission_earned"] or "0.00"),
            "average_order_value": str(order_aggs["average_order_value"] or "0.00"),
        }, status=status.HTTP_200_OK)

