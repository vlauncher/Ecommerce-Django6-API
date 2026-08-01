from django.contrib import admin
from reviews.models import Review, ReviewHelpfulVote


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("product", "user", "rating", "title", "is_verified_buyer", "is_approved", "created_at")
    list_filter = ("rating", "is_verified_buyer", "is_approved")
    search_fields = ("product__name", "user__email", "title", "comment")


@admin.register(ReviewHelpfulVote)
class ReviewHelpfulVoteAdmin(admin.ModelAdmin):
    list_display = ("review", "user", "is_helpful", "created_at")
