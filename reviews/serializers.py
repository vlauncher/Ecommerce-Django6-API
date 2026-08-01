from rest_framework import serializers
from reviews.models import Review, ReviewHelpfulVote


class ReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.full_name", read_only=True)

    class Meta:
        model = Review
        fields = (
            "id",
            "product",
            "rating",
            "title",
            "comment",
            "is_verified_buyer",
            "helpful_count",
            "unhelpful_count",
            "user_name",
            "created_at",
        )
        read_only_fields = ("is_verified_buyer", "helpful_count", "unhelpful_count", "product")

    def create(self, validated_data):
        user = self.context["request"].user
        product = self.context["product"]

        if Review.objects.filter(product=product, user=user).exists():
            raise serializers.ValidationError("You have already reviewed this product.")

        review = Review.objects.create(
            product=product,
            user=user,
            **validated_data
        )

        # Recalculate product average rating & review count
        self._update_product_rating(product)
        return review

    def _update_product_rating(self, product):
        reviews = product.reviews.filter(is_approved=True)
        count = reviews.count()
        if count > 0:
            avg = sum(r.rating for r in reviews) / count
            product.average_rating = round(avg, 2)
            product.review_count = count
        else:
            product.average_rating = 0.00
            product.review_count = 0
        product.save(update_fields=["average_rating", "review_count"])
