from django.contrib import admin

from .models import (Attribute, BundleComponent, Category, Collection, Coupon, CouponRedemption, InventoryLedgerEntry, PriceRule, Product, ProductVariant, Promotion, StockItem, Warehouse)

for model in (Attribute, BundleComponent, Category, Collection, Coupon, CouponRedemption, InventoryLedgerEntry, PriceRule, Product, ProductVariant, Promotion, StockItem, Warehouse):
    admin.site.register(model)
