from ninja import Router

from apps.shops.models import ShopMembership
from apps.shops.permissions import aget_shop_context
from apps.users.auth import JWTAuth

from .models import Product, Warehouse
from .schemas import CategoryIn, CouponIn, ProductIn, ProductOut, StockAdjustIn
from . import services

catalog_router = Router(tags=["Catalog"])


@catalog_router.get("/{shop_slug}/products", response=list[ProductOut])
async def list_products(request, shop_slug: str):
    from apps.shops.models import Shop
    shop = await Shop.objects.aget(slug=shop_slug, is_active=True)
    products = []
    async for product in Product.objects.filter(shop=shop, status=Product.Status.PUBLISHED).prefetch_related("variants"):
        products.append(services.product_dict(product))
    return products


@catalog_router.post("/{shop_slug}/categories", auth=JWTAuth())
async def create_category(request, shop_slug: str, payload: CategoryIn):
    shop, _ = await aget_shop_context(request, shop_slug, {ShopMembership.Role.OWNER, ShopMembership.Role.MANAGER, ShopMembership.Role.STAFF})
    category = await services.create_category(shop, payload.model_dump())
    return {"id": category.id, "name": category.name, "slug": category.slug}


@catalog_router.post("/{shop_slug}/products", auth=JWTAuth(), response=ProductOut)
async def create_product(request, shop_slug: str, payload: ProductIn):
    shop, _ = await aget_shop_context(request, shop_slug, {ShopMembership.Role.OWNER, ShopMembership.Role.MANAGER, ShopMembership.Role.STAFF})
    return await services.create_product(shop, request.auth, payload.model_dump())


@catalog_router.post("/{shop_slug}/inventory/adjust", auth=JWTAuth())
async def adjust_inventory(request, shop_slug: str, payload: StockAdjustIn):
    shop, _ = await aget_shop_context(request, shop_slug, {ShopMembership.Role.OWNER, ShopMembership.Role.MANAGER, ShopMembership.Role.STAFF})
    return await services.adjust_stock(shop, request.auth, payload.model_dump())


@catalog_router.post("/{shop_slug}/coupons", auth=JWTAuth())
async def create_coupon(request, shop_slug: str, payload: CouponIn):
    shop, _ = await aget_shop_context(request, shop_slug, {ShopMembership.Role.OWNER, ShopMembership.Role.MANAGER})
    return await services.create_coupon(shop, payload.model_dump())
