from rest_framework import generics, permissions, status
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
from promotions.models import Coupon, FlashSale, TieredPrice
from promotions.serializers import (
    CouponSerializer,
    ApplyCouponSerializer,
    FlashSaleSerializer,
    TieredPriceSerializer,
)
from promotions.engine import calculate_coupon_discount, InvalidCouponError
from cart.views import get_or_create_cart
from vendors.permissions import IsActiveVendor
from common.pagination import StandardResultsSetPagination


@extend_schema(tags=["Promotions"])
class ApplyCouponView(generics.GenericAPIView):
    """Validate and calculate discount for a coupon code against current cart."""

    permission_classes = [permissions.AllowAny]
    serializer_class = ApplyCouponSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        code = serializer.validated_data["code"].upper().strip()
        coupon = generics.get_object_or_404(Coupon, code=code)

        cart = get_or_create_cart(request)
        if not cart.items.exists():
            return Response({"detail": "Shopping cart is empty."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            discount_amount = calculate_coupon_discount(
                coupon=coupon, cart_subtotal=cart.subtotal, user=request.user
            )
        except InvalidCouponError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            "code": coupon.code,
            "discount_type": coupon.discount_type,
            "discount_value": str(coupon.value),
            "discount_amount": str(discount_amount),
            "subtotal": str(cart.subtotal),
            "new_subtotal": str(cart.subtotal - discount_amount),
        }, status=status.HTTP_200_OK)


@extend_schema(tags=["Promotions"])
class PublicFlashSaleListView(generics.ListAPIView):
    """List currently active flash sales."""

    permission_classes = [permissions.AllowAny]
    serializer_class = FlashSaleSerializer

    def get_queryset(self):
        return FlashSale.objects.filter(is_active=True).prefetch_related("products")


@extend_schema(tags=["Promotions - Vendor Dashboard"])
class VendorCouponListCreateView(generics.ListCreateAPIView):
    """Vendor dashboard: Manage promotional discount coupons."""

    permission_classes = [permissions.IsAuthenticated, IsActiveVendor]
    serializer_class = CouponSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        return Coupon.objects.all()
