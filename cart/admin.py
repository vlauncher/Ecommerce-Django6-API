from django.contrib import admin
from cart.models import Cart, CartItem, SavedForLater


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "session_key", "total_quantity", "subtotal", "updated_at")
    inlines = [CartItemInline]


@admin.register(SavedForLater)
class SavedForLaterAdmin(admin.ModelAdmin):
    list_display = ("user", "variant", "created_at")
