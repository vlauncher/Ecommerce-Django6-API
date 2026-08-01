from django.urls import path
from vendors.views import (
    VendorRegisterView,
    VendorListView,
    VendorDetailView,
    VendorDashboardView,
)

urlpatterns = [
    path("register/", VendorRegisterView.as_view(), name="vendor-register"),
    path("", VendorListView.as_view(), name="vendor-list"),
    path("me/", VendorDashboardView.as_view(), name="vendor-dashboard"),
    path("<slug:slug>/", VendorDetailView.as_view(), name="vendor-detail"),
]
