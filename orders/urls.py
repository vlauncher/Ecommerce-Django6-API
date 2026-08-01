from django.urls import path
from orders.views import (
    CheckoutView,
    OrderListView,
    OrderDetailView,
    OrderCancelView,
    VendorOrderListView,
    VendorOrderStatusUpdateView,
    ReturnRequestCreateListView,
)

urlpatterns = [
    path("checkout/", CheckoutView.as_view(), name="order-checkout"),
    path("", OrderListView.as_view(), name="order-list"),
    path("returns/", ReturnRequestCreateListView.as_view(), name="return-request-list"),
    path("vendor/sub-orders/", VendorOrderListView.as_view(), name="vendor-order-list"),
    path("vendor/sub-orders/<uuid:pk>/", VendorOrderStatusUpdateView.as_view(), name="vendor-order-update"),
    path("<str:order_number>/", OrderDetailView.as_view(), name="order-detail"),
    path("<str:order_number>/cancel/", OrderCancelView.as_view(), name="order-cancel"),
]
