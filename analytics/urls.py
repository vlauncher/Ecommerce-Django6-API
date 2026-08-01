from django.urls import path
from analytics.views import (
    VendorSalesAnalyticsView,
    VendorTopProductsView,
    AdminPlatformAnalyticsView,
)

urlpatterns = [
    path("vendor/sales/", VendorSalesAnalyticsView.as_view(), name="vendor-analytics-sales"),
    path("vendor/top-products/", VendorTopProductsView.as_view(), name="vendor-analytics-top-products"),
    path("admin/platform/", AdminPlatformAnalyticsView.as_view(), name="admin-analytics-platform"),
]
