import django_filters
from catalog.models import Product


class ProductFilter(django_filters.FilterSet):
    min_price = django_filters.NumberFilter(field_name="min_price", lookup_expr="gte")
    max_price = django_filters.NumberFilter(field_name="max_price", lookup_expr="lte")
    category = django_filters.CharFilter(field_name="category__slug")
    category_id = django_filters.UUIDFilter(field_name="category__id")
    vendor = django_filters.CharFilter(field_name="vendor__slug")
    product_type = django_filters.CharFilter(field_name="product_type__slug")
    is_featured = django_filters.BooleanFilter()
    min_rating = django_filters.NumberFilter(field_name="average_rating", lookup_expr="gte")

    class Meta:
        model = Product
        fields = [
            "category",
            "category_id",
            "vendor",
            "product_type",
            "status",
            "is_featured",
            "min_price",
            "max_price",
            "min_rating",
        ]
