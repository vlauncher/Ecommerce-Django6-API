from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from common.models import TimeStampedModel


class Review(TimeStampedModel):
    """Verified buyer product reviews."""

    product = models.ForeignKey(
        "catalog.Product", on_delete=models.CASCADE, related_name="reviews"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reviews"
    )
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    title = models.CharField(max_length=255, blank=True)
    comment = models.TextField(blank=True)
    is_verified_buyer = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=True)

    helpful_count = models.PositiveIntegerField(default=0)
    unhelpful_count = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = [("product", "user")]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.full_name} — {self.product.name} ({self.rating}/5)"


class ReviewHelpfulVote(TimeStampedModel):
    """Tracks helpful/unhelpful votes on reviews."""

    review = models.ForeignKey(
        Review, on_delete=models.CASCADE, related_name="votes"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="review_votes"
    )
    is_helpful = models.BooleanField()

    class Meta:
        unique_together = [("review", "user")]
