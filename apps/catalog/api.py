from ninja import Router, Query
from django.db.models import Q, Min

from apps.shops.models import ShopMembership
from apps.shops.permissions import aget_shop_context
from apps.users.auth import JWTAuth

from .models import Product, Warehouse
from .schemas import CategoryIn, CouponIn, ProductDetailOut, ProductIn, ProductOut, ProductSearchOut, StockAdjustIn
from . import services

catalog_router = Router(tags=["Catalog"])


@catalog_router.get("/{shop_slug}/products", response=list[ProductSearchOut])
async def list_products(request, shop_slug: str, q: str = "", category_id: int | None = None, min_price: int | None = None, max_price: int | None = None, ordering: str = "name", limit: int = Query(50, ge=1, le=100), offset: int = Query(0, ge=0)):
    from apps.shops.models import Shop
    shop = await Shop.objects.aget(slug=shop_slug, is_active=True)
    filters = Q(shop=shop, status=Product.Status.PUBLISHED)
    if q:
        filters &= Q(name__icontains=q) | Q(description__icontains=q) | Q(brand__icontains=q) | Q(variants__sku__icontains=q)
    if category_id is not None:
        filters &= Q(category_id=category_id)
    if min_price is not None:
        filters &= Q(variants__price_minor__gte=min_price)
    if max_price is not None:
        filters &= Q(variants__price_minor__lte=max_price)
    ordering_map = {"name": "name", "-name": "-name", "newest": "-created_at", "price": "min_price", "-price": "-min_price"}
    order = ordering_map.get(ordering, "name")
    qs = Product.objects.filter(filters).annotate(min_price=Min("variants__price_minor")).prefetch_related("variants").distinct().order_by(order)[offset:offset + limit]
    products = []
    async for product in qs:
        item = services.product_dict(product)
        item.update({"shop_slug": shop.slug, "brand": product.brand, "is_digital": product.is_digital, "requires_shipping": product.requires_shipping, "min_price_minor": product.min_price})
        products.append(item)
    return products


@catalog_router.get("/{shop_slug}/products/{product_slug}", response=ProductDetailOut)
async def get_product(request, shop_slug: str, product_slug: str):
    from apps.shops.models import Shop
    from ninja.errors import HttpError
    try:
        product = await Product.objects.prefetch_related("variants").aget(shop__slug=shop_slug, shop__is_active=True, slug=product_slug, status=Product.Status.PUBLISHED)
    except Product.DoesNotExist:
        raise HttpError(404, "Product not found.")
    result = services.product_dict(product)
    result.update({"shop_slug": shop_slug, "brand": product.brand, "is_digital": product.is_digital, "requires_shipping": product.requires_shipping})
    return result


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
