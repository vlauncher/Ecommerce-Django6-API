from rest_framework import generics, permissions, status
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
from orders.models import Order, VendorSubOrder, ReturnRequest
from orders.serializers import (
    CheckoutSerializer,
    OrderListSerializer,
    OrderDetailSerializer,
    VendorSubOrderSerializer,
    ReturnRequestSerializer,
)
from orders.services import create_order_from_cart
from cart.views import get_or_create_cart
from vendors.permissions import IsActiveVendor
from common.pagination import StandardResultsSetPagination


@extend_schema(tags=["Orders"])
class CheckoutView(generics.CreateAPIView):
    """Place an order from the current shopping cart."""

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CheckoutSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        cart = get_or_create_cart(request)
        if not cart.items.exists():
            return Response(
                {"detail": "Shopping cart is empty."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        order = create_order_from_cart(
            user=request.user,
            cart=cart,
            shipping_address=serializer.validated_data["shipping_address"],
            billing_address=serializer.validated_data["billing_address"],
            notes=serializer.validated_data.get("notes", ""),
        )

        return Response(
            OrderDetailSerializer(order).data,
            status=status.HTTP_201_CREATED,
        )


@extend_schema(tags=["Orders"])
class OrderListView(generics.ListAPIView):
    """List authenticated user's order history."""

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = OrderListSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)


@extend_schema(tags=["Orders"])
class OrderDetailView(generics.RetrieveAPIView):
    """Retrieve detailed order information."""

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = OrderDetailSerializer
    lookup_field = "order_number"

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).prefetch_related(
            "items", "sub_orders__vendor", "sub_orders__items", "logs"
        )


@extend_schema(tags=["Orders"])
class OrderCancelView(generics.GenericAPIView):
    """Cancel an unfulfilled order."""

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = OrderDetailSerializer

    @extend_schema(responses={200: OrderDetailSerializer})
    def post(self, request, order_number):

        order = generics.get_object_or_404(Order, order_number=order_number, user=request.user)
        if order.status not in [Order.Status.DRAFT, Order.Status.PENDING_PAYMENT, Order.Status.PAID]:
            return Response(
                {"detail": f"Cannot cancel order in status '{order.status}'."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        order.cancel()
        order.save()
        return Response(OrderDetailSerializer(order).data)


@extend_schema(tags=["Orders - Vendor Dashboard"])
class VendorOrderListView(generics.ListAPIView):
    """Vendor dashboard: List vendor's assigned sub-orders."""

    permission_classes = [permissions.IsAuthenticated, IsActiveVendor]
    serializer_class = VendorSubOrderSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return VendorSubOrder.objects.none()
        vendor = self.request.user.vendor_profile
        return VendorSubOrder.objects.filter(vendor=vendor).prefetch_related("items")


@extend_schema(tags=["Orders - Vendor Dashboard"])
class VendorOrderStatusUpdateView(generics.UpdateAPIView):
    """Vendor dashboard: Update sub-order fulfillment status or add tracking info."""

    permission_classes = [permissions.IsAuthenticated, IsActiveVendor]
    serializer_class = VendorSubOrderSerializer

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return VendorSubOrder.objects.none()
        return VendorSubOrder.objects.filter(vendor=self.request.user.vendor_profile)


@extend_schema(tags=["Orders - Returns"])
class ReturnRequestCreateListView(generics.ListCreateAPIView):
    """Request a product return (RMA) or view past return requests."""

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ReturnRequestSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        return ReturnRequest.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        order_number = request.data.get("order_number")
        order = generics.get_object_or_404(Order, order_number=order_number, user=request.user)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return_request = serializer.save(user=request.user, order=order)
        return Response(ReturnRequestSerializer(return_request).data, status=status.HTTP_201_CREATED)
