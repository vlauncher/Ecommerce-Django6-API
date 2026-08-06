from django.contrib import admin

from .models import Address, Cart, CartItem, CustomerProfile, GiftCard, GiftCardTransaction, Order, OrderItem, SellerOrder, Shipment, ShippingRate, ShippingZone, TaxRate, WishlistItem

for model in (Address, Cart, CartItem, CustomerProfile, GiftCard, GiftCardTransaction, Order, OrderItem, SellerOrder, Shipment, ShippingRate, ShippingZone, TaxRate, WishlistItem):
    admin.site.register(model)
