from django.urls import path
from shipping.views import (
    PublicShippingMethodListView,
    AdminShippingZoneListCreateView,
    VendorFulfillmentCreateView,
)

urlpatterns = [
    path("methods/", PublicShippingMethodListView.as_view(), name="shipping-method-list"),
    path("admin/zones/", AdminShippingZoneListCreateView.as_view(), name="admin-shipping-zone-list"),
    path("vendor/fulfillments/", VendorFulfillmentCreateView.as_view(), name="vendor-fulfillment-create"),
]
