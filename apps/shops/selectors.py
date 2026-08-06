from .models import Shop, ShopMembership


async def aget_shop_by_slug(slug: str) -> Shop | None:
    try:
        return await Shop.objects.aget(slug=slug)
    except Shop.DoesNotExist:
        return None


async def aget_membership(shop: Shop, user) -> ShopMembership | None:
    try:
        return await ShopMembership.objects.select_related("user").aget(shop=shop, user=user)
    except ShopMembership.DoesNotExist:
        return None
