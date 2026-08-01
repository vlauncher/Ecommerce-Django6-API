from django.urls import path
from reviews.views import (
    ProductReviewListView,
    ReviewDetailView,
    ReviewHelpfulVoteView,
)

urlpatterns = [
    path("product/<slug:product_slug>/", ProductReviewListView.as_view(), name="product-review-list"),
    path("<uuid:pk>/", ReviewDetailView.as_view(), name="review-detail"),
    path("<uuid:pk>/vote/", ReviewHelpfulVoteView.as_view(), name="review-vote"),
]
