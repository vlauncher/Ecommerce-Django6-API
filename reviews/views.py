from rest_framework import generics, permissions, status
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
from catalog.models import Product
from reviews.models import Review, ReviewHelpfulVote
from reviews.serializers import ReviewSerializer
from common.pagination import StandardResultsSetPagination


@extend_schema(tags=["Reviews"])
class ProductReviewListView(generics.ListCreateAPIView):
    """List reviews for a product or submit a new review."""

    serializer_class = ReviewSerializer
    pagination_class = StandardResultsSetPagination

    def get_permissions(self):
        if self.request.method == "POST":
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    def get_queryset(self):
        product_slug = self.kwargs["product_slug"]
        return Review.objects.filter(
            product__slug=product_slug, is_approved=True
        ).select_related("user")

    def create(self, request, *args, **kwargs):
        product_slug = self.kwargs["product_slug"]
        product = generics.get_object_or_404(Product, slug=product_slug)
        serializer = self.get_serializer(
            data=request.data, context={"request": request, "product": product}
        )
        serializer.is_valid(raise_exception=True)
        review = serializer.save()
        return Response(
            ReviewSerializer(review).data,
            status=status.HTTP_201_CREATED,
        )


@extend_schema(tags=["Reviews"])
class ReviewDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Manage own review."""

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ReviewSerializer

    def get_queryset(self):
        return Review.objects.filter(user=self.request.user)


from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers

@extend_schema(
    tags=["Reviews"],
    request=inline_serializer(
        name="ReviewVoteRequest",
        fields={"is_helpful": serializers.BooleanField(default=True)},
    ),
    responses={
        200: inline_serializer(
            name="ReviewVoteResponse",
            fields={
                "helpful_count": serializers.IntegerField(),
                "unhelpful_count": serializers.IntegerField(),
            },
        )
    },
)
class ReviewHelpfulVoteView(generics.GenericAPIView):
    """Vote helpful/unhelpful on a review."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        review = generics.get_object_or_404(Review, pk=pk)
        is_helpful = request.data.get("is_helpful", True)

        vote, created = ReviewHelpfulVote.objects.update_or_create(
            review=review,
            user=request.user,
            defaults={"is_helpful": is_helpful},
        )

        # Recalculate helpful counts
        review.helpful_count = review.votes.filter(is_helpful=True).count()
        review.unhelpful_count = review.votes.filter(is_helpful=False).count()
        review.save(update_fields=["helpful_count", "unhelpful_count"])

        return Response({
            "helpful_count": review.helpful_count,
            "unhelpful_count": review.unhelpful_count,
        })

