from django.urls import path
from cart.views import (
    CartDetailView,
    CartItemAddView,
    CartItemUpdateDeleteView,
    CartClearView,
    CartMergeView,
    SavedForLaterListView,
    SavedForLaterDeleteView,
)

urlpatterns = [
    path("", CartDetailView.as_view(), name="cart-detail"),
    path("items/", CartItemAddView.as_view(), name="cart-item-add"),
    path("items/<uuid:pk>/", CartItemUpdateDeleteView.as_view(), name="cart-item-update-delete"),
    path("clear/", CartClearView.as_view(), name="cart-clear"),
    path("merge/", CartMergeView.as_view(), name="cart-merge"),
    path("saved-items/", SavedForLaterListView.as_view(), name="saved-items-list"),
    path("saved-items/<uuid:pk>/", SavedForLaterDeleteView.as_view(), name="saved-items-delete"),
]
