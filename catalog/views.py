from rest_framework import generics, permissions, status, filters
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from catalog.models import (
    Category,
    ProductType,
    AttributeGroup,
    Attribute,
    Product,
    ProductVariant,
    ProductImage,
)
from catalog.serializers import (
    CategoryTreeSerializer,
    CategoryDetailSerializer,
    ProductTypeSerializer,
    AttributeGroupSerializer,
    AttributeSerializer,
    ProductListSerializer,
    ProductDetailSerializer,
    ProductCreateUpdateSerializer,
    ProductVariantSerializer,
    ProductVariantCreateUpdateSerializer,
    ProductImageSerializer,
)
from catalog.filters import ProductFilter
from vendors.permissions import IsActiveVendor, IsVendorOwner
from common.pagination import StandardResultsSetPagination


# ─── CATEGORY VIEWS ────────────────────────────────────────

@extend_schema(tags=["Catalog - Categories"])
class CategoryListView(generics.ListAPIView):
    """List root categories with their full subcategory tree."""

    permission_classes = [permissions.AllowAny]
    serializer_class = CategoryTreeSerializer

    def get_queryset(self):
        return Category.get_root_nodes().filter(is_active=True)


@extend_schema(tags=["Catalog - Categories"])
class CategoryDetailView(generics.RetrieveAPIView):
    """Get category details by slug."""

    permission_classes = [permissions.AllowAny]
    serializer_class = CategoryDetailSerializer
    queryset = Category.objects.filter(is_active=True)
    lookup_field = "slug"


@extend_schema(tags=["Catalog - Admin Categories"])
class AdminCategoryCreateView(generics.CreateAPIView):
    """Create a new root or child category (Admin only)."""

    permission_classes = [permissions.IsAdminUser]
    serializer_class = CategoryDetailSerializer

    def create(self, request, *args, **kwargs):
        parent_id = request.data.get("parent_id")
        name = request.data.get("name")
        slug = request.data.get("slug")
        description = request.data.get("description", "")

        if parent_id:
            parent = Category.objects.get(id=parent_id)
            node = parent.add_child(
                name=name,
                slug=slug,
                description=description,
            )
        else:
            node = Category.add_root(
                name=name,
                slug=slug,
                description=description,
            )
        return Response(
            CategoryDetailSerializer(node).data,
            status=status.HTTP_201_CREATED,
        )


# ─── PRODUCT TYPE & ATTRIBUTE VIEWS ────────────────────────

@extend_schema(tags=["Catalog - Metadata"])
class ProductTypeListView(generics.ListAPIView):
    """List all product types (e.g. T-Shirt, eBook, Smartphone)."""

    permission_classes = [permissions.AllowAny]
    serializer_class = ProductTypeSerializer
    queryset = ProductType.objects.all()


@extend_schema(tags=["Catalog - Metadata"])
class AttributeGroupListView(generics.ListAPIView):
    """List all attribute groups and their nested attributes/options."""

    permission_classes = [permissions.AllowAny]
    serializer_class = AttributeGroupSerializer
    queryset = AttributeGroup.objects.prefetch_related("attributes__options").all()


# ─── PUBLIC PRODUCT VIEWS ──────────────────────────────────

@extend_schema(tags=["Catalog - Products"])
class ProductListView(generics.ListAPIView):
    """Public searchable & filterable product catalog."""

    permission_classes = [permissions.AllowAny]
    serializer_class = ProductListSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ProductFilter
    search_fields = ["name", "description", "short_description", "vendor__store_name"]
    ordering_fields = ["min_price", "created_at", "average_rating", "total_sold"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return (
            Product.objects
            .filter(status=Product.Status.ACTIVE)
            .select_related("vendor", "category")
            .prefetch_related("images")
        )


@extend_schema(tags=["Catalog - Products"])
class ProductDetailView(generics.RetrieveAPIView):
    """Public detailed product view with all variants, images, and attributes."""

    permission_classes = [permissions.AllowAny]
    serializer_class = ProductDetailSerializer
    lookup_field = "slug"

    def get_queryset(self):
        return (
            Product.objects
            .filter(status=Product.Status.ACTIVE)
            .select_related("vendor", "category", "product_type")
            .prefetch_related(
                "variants__attribute_values__attribute",
                "variants__attribute_values__attribute_option",
                "variants__images",
                "images",
                "attribute_values__attribute",
            )
        )


# ─── VENDOR PRODUCT VIEWS ──────────────────────────────────

@extend_schema(tags=["Catalog - Vendor Dashboard"])
class VendorProductListView(generics.ListCreateAPIView):
    """Vendor dashboard: List vendor's products or create a new product."""

    permission_classes = [permissions.IsAuthenticated, IsActiveVendor]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = ProductFilter
    search_fields = ["name", "description", "slug"]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ProductCreateUpdateSerializer
        return ProductListSerializer

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Product.objects.none()
        vendor = self.request.user.vendor_profile
        return (
            Product.objects
            .filter(vendor=vendor)
            .select_related("vendor", "category")
            .prefetch_related("images")
        )


@extend_schema(tags=["Catalog - Vendor Dashboard"])
class VendorProductDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Vendor dashboard: Manage single product."""

    permission_classes = [permissions.IsAuthenticated, IsActiveVendor, IsVendorOwner]
    lookup_field = "pk"

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return ProductCreateUpdateSerializer
        return ProductDetailSerializer

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Product.objects.none()
        return Product.objects.filter(vendor=self.request.user.vendor_profile)



# ─── VENDOR VARIANT & MEDIA VIEWS ──────────────────────────

@extend_schema(tags=["Catalog - Vendor Dashboard"])
class VendorVariantCreateView(generics.CreateAPIView):
    """Vendor dashboard: Add a variant SKU to an existing product."""

    permission_classes = [permissions.IsAuthenticated, IsActiveVendor]
    serializer_class = ProductVariantCreateUpdateSerializer

    def perform_create(self, serializer):
        product_id = self.kwargs["product_id"]
        product = Product.objects.get(
            id=product_id, vendor=self.request.user.vendor_profile
        )
        serializer.save(product=product)


@extend_schema(tags=["Catalog - Vendor Dashboard"])
class VendorVariantDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Vendor dashboard: Update or delete a variant SKU."""

    permission_classes = [permissions.IsAuthenticated, IsActiveVendor]
    serializer_class = ProductVariantCreateUpdateSerializer

    def get_queryset(self):
        return ProductVariant.objects.filter(
            product__vendor=self.request.user.vendor_profile
        )


@extend_schema(tags=["Catalog - Vendor Dashboard"])
class VendorImageUploadView(generics.CreateAPIView):
    """Vendor dashboard: Upload product image."""

    permission_classes = [permissions.IsAuthenticated, IsActiveVendor]
    serializer_class = ProductImageSerializer

    def perform_create(self, serializer):
        product_id = self.kwargs["product_id"]
        product = Product.objects.get(
            id=product_id, vendor=self.request.user.vendor_profile
        )
        serializer.save(product=product)
