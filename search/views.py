from django.db.models import Q
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
from catalog.models import Product, Category
from catalog.serializers import ProductListSerializer
from common.pagination import StandardResultsSetPagination


@extend_schema(tags=["Search"])
class ProductSearchView(generics.ListAPIView):
    """Full-text product search with faceted filtering."""

    permission_classes = [permissions.AllowAny]
    serializer_class = ProductListSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        query = self.request.query_params.get("q", "").strip()
        queryset = Product.objects.filter(status=Product.Status.ACTIVE).select_related("vendor", "category").prefetch_related("images")

        if query:
            queryset = queryset.filter(
                Q(name__icontains=query) |
                Q(description__icontains=query) |
                Q(short_description__icontains=query) |
                Q(vendor__store_name__icontains=query) |
                Q(category__name__icontains=query)
            )

        category_slug = self.request.query_params.get("category")
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)

        vendor_slug = self.request.query_params.get("vendor")
        if vendor_slug:
            queryset = queryset.filter(vendor__slug=vendor_slug)

        min_price = self.request.query_params.get("min_price")
        if min_price:
            queryset = queryset.filter(min_price__gte=min_price)

        max_price = self.request.query_params.get("max_price")
        if max_price:
            queryset = queryset.filter(max_price__lte=max_price)

        min_rating = self.request.query_params.get("min_rating")
        if min_rating:
            queryset = queryset.filter(average_rating__gte=min_rating)

        return queryset.order_by("-created_at")


from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers

@extend_schema(
    tags=["Search"],
    responses={
        200: inline_serializer(
            name="SearchSuggestionResponse",
            fields={
                "products": serializers.ListField(child=serializers.DictField()),
                "categories": serializers.ListField(child=serializers.DictField()),
            },
        )
    },
)
class SearchSuggestionView(generics.GenericAPIView):
    """Instant search autocomplete suggestions for search bar."""

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        query = request.query_params.get("q", "").strip()
        if not query or len(query) < 2:
            return Response({"products": [], "categories": []})

        products = Product.objects.filter(
            status=Product.Status.ACTIVE, name__icontains=query
        ).values("id", "name", "slug")[:5]

        categories = Category.objects.filter(
            is_active=True, name__icontains=query
        ).values("id", "name", "slug")[:5]

        return Response({
            "products": list(products),
            "categories": list(categories),
        }, status=status.HTTP_200_OK)

