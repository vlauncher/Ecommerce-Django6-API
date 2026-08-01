from django.urls import path
from inventory.views import (
    WarehouseListCreateView,
    VendorStockRecordListView,
    VendorStockAdjustmentView,
    VendorStockMovementListView,
)

urlpatterns = [
    path("admin/warehouses/", WarehouseListCreateView.as_view(), name="admin-warehouse-list"),
    path("vendor/stock/", VendorStockRecordListView.as_view(), name="vendor-stock-list"),
    path("vendor/adjust/", VendorStockAdjustmentView.as_view(), name="vendor-stock-adjust"),
    path("vendor/movements/", VendorStockMovementListView.as_view(), name="vendor-stock-movements"),
]
