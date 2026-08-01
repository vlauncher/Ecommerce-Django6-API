from django.urls import path
from catalog.views import (
    CategoryListView,
    CategoryDetailView,
    AdminCategoryCreateView,
    ProductTypeListView,
    AttributeGroupListView,
    ProductListView,
    ProductDetailView,
    VendorProductListView,
    VendorProductDetailView,
    VendorVariantCreateView,
    VendorVariantDetailView,
    VendorImageUploadView,
)

urlpatterns = [
    # Public Categories
    path("categories/", CategoryListView.as_view(), name="category-list"),
    path("categories/<slug:slug>/", CategoryDetailView.as_view(), name="category-detail"),
    path("admin/categories/", AdminCategoryCreateView.as_view(), name="admin-category-create"),

    # Product Types & Attributes
    path("product-types/", ProductTypeListView.as_view(), name="product-type-list"),
    path("attribute-groups/", AttributeGroupListView.as_view(), name="attribute-group-list"),

    # Public Products
    path("products/", ProductListView.as_view(), name="product-list"),
    path("products/<slug:slug>/", ProductDetailView.as_view(), name="product-detail"),

    # Vendor Dashboard
    path("vendor/products/", VendorProductListView.as_view(), name="vendor-product-list"),
    path("vendor/products/<uuid:pk>/", VendorProductDetailView.as_view(), name="vendor-product-detail"),
    path("vendor/products/<uuid:product_id>/variants/", VendorVariantCreateView.as_view(), name="vendor-variant-create"),
    path("vendor/variants/<uuid:pk>/", VendorVariantDetailView.as_view(), name="vendor-variant-detail"),
    path("vendor/products/<uuid:product_id>/images/", VendorImageUploadView.as_view(), name="vendor-image-upload"),
]
