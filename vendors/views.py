from rest_framework import generics, permissions, status
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view
from vendors.models import Vendor
from vendors.permissions import IsVendorOwner, IsActiveVendor
from vendors.serializers import (
    VendorRegistrationSerializer,
    VendorPublicSerializer,
    VendorDetailSerializer,
)


@extend_schema(tags=["Vendors"])
class VendorRegisterView(generics.CreateAPIView):
    """Register the authenticated user as a vendor."""

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = VendorRegistrationSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        vendor = serializer.save()
        return Response(
            VendorDetailSerializer(vendor).data,
            status=status.HTTP_201_CREATED,
        )


from common.pagination import StandardResultsSetPagination


@extend_schema(tags=["Vendors"])
class VendorListView(generics.ListAPIView):
    """Public directory of active marketplace vendors."""

    permission_classes = [permissions.AllowAny]
    serializer_class = VendorPublicSerializer
    pagination_class = StandardResultsSetPagination
    queryset = Vendor.objects.filter(status=Vendor.Status.ACTIVE)



@extend_schema(tags=["Vendors"])
class VendorDetailView(generics.RetrieveAPIView):
    """Public vendor storefront details."""

    permission_classes = [permissions.AllowAny]
    serializer_class = VendorPublicSerializer
    queryset = Vendor.objects.filter(status=Vendor.Status.ACTIVE)
    lookup_field = "slug"


@extend_schema(tags=["Vendors"])
class VendorDashboardView(generics.RetrieveUpdateAPIView):
    """Vendor's own profile management dashboard."""

    permission_classes = [permissions.IsAuthenticated, IsVendorOwner]
    serializer_class = VendorDetailSerializer

    def get_object(self):
        return self.request.user.vendor_profile
