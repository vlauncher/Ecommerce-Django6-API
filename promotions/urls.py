from django.urls import path
from promotions.views import (
    ApplyCouponView,
    PublicFlashSaleListView,
    VendorCouponListCreateView,
)

urlpatterns = [
    path("apply-coupon/", ApplyCouponView.as_view(), name="apply-coupon"),
    path("flash-sales/", PublicFlashSaleListView.as_view(), name="flash-sale-list"),
    path("vendor/coupons/", VendorCouponListCreateView.as_view(), name="vendor-coupon-list"),
]
