from django.contrib import admin

from .models import Shop, ShopInvitation, ShopMembership


@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active", "created_by", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(ShopMembership)
class ShopMembershipAdmin(admin.ModelAdmin):
    list_display = ("shop", "user", "role", "is_active", "created_at")
    list_filter = ("role", "is_active")
    search_fields = ("shop__name", "user__email")


@admin.register(ShopInvitation)
class ShopInvitationAdmin(admin.ModelAdmin):
    list_display = ("shop", "email", "role", "expires_at", "accepted_at", "revoked_at")
    list_filter = ("role", "accepted_at", "revoked_at")
    search_fields = ("shop__name", "email")
    readonly_fields = ("token_hash",)
