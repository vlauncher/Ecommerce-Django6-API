from ninja.errors import HttpError

from .selectors import aget_membership, aget_shop_by_slug


async def aget_shop_context(request, shop_slug: str, roles: set[str] | None = None):
    shop = await aget_shop_by_slug(shop_slug)
    if not shop or not shop.is_active:
        raise HttpError(404, "Shop not found.")

    membership = await aget_membership(shop, request.auth)
    if not membership or not membership.is_active:
        raise HttpError(403, "You are not a member of this shop.")
    if roles and membership.role not in roles:
        raise HttpError(403, "You do not have permission for this shop action.")
    return shop, membership
