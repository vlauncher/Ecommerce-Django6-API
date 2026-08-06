from ninja import Router

from apps.users.auth import JWTAuth

from .models import ShopMembership
from .permissions import aget_shop_context
from .schemas import (
    InvitationIn,
    InvitationOut,
    MembershipOut,
    MembershipRoleIn,
    MessageOut,
    ShopCreateIn,
    ShopOut,
    ShopUpdateIn,
)
from . import services

shop_router = Router(tags=["Shops"])
invitation_router = Router(tags=["Shop Invitations"])


@shop_router.post("/", auth=JWTAuth(), response={201: ShopOut})
async def create_shop(request, payload: ShopCreateIn):
    return 201, await services.create_shop(request.auth, payload.model_dump())


@shop_router.get("/", auth=JWTAuth())
async def list_shops(request):
    return await services.list_user_shops(request.auth)


@shop_router.get("/{shop_slug}", auth=JWTAuth(), response=ShopOut)
async def get_shop(request, shop_slug: str):
    shop, _ = await aget_shop_context(request, shop_slug)
    return shop


@shop_router.patch("/{shop_slug}", auth=JWTAuth(), response=ShopOut)
async def update_shop(request, shop_slug: str, payload: ShopUpdateIn):
    shop, _ = await aget_shop_context(request, shop_slug, {ShopMembership.Role.OWNER, ShopMembership.Role.MANAGER})
    return await services.update_shop(shop, payload.model_dump(exclude_unset=True))


@shop_router.delete("/{shop_slug}", auth=JWTAuth())
async def deactivate_shop(request, shop_slug: str):
    shop, _ = await aget_shop_context(request, shop_slug, {ShopMembership.Role.OWNER})
    return await services.deactivate_shop(shop)


@shop_router.get("/{shop_slug}/users/profile", auth=JWTAuth())
async def shop_profile(request, shop_slug: str):
    _, membership = await aget_shop_context(request, shop_slug)
    from apps.users.services import aget_user_profile

    profile = await aget_user_profile(request.auth)
    profile["membership"] = {"id": membership.id, "role": membership.role, "is_active": membership.is_active}
    return profile


@shop_router.get("/{shop_slug}/members", auth=JWTAuth(), response=list[MembershipOut])
async def list_members(request, shop_slug: str):
    shop, _ = await aget_shop_context(request, shop_slug, {ShopMembership.Role.OWNER, ShopMembership.Role.MANAGER})
    return await services.list_memberships(shop)


@shop_router.patch("/{shop_slug}/members/{user_id}", auth=JWTAuth(), response=MembershipOut)
async def update_member(request, shop_slug: str, user_id: int, payload: MembershipRoleIn):
    shop, acting_membership = await aget_shop_context(request, shop_slug, {ShopMembership.Role.OWNER, ShopMembership.Role.MANAGER})
    return await services.change_membership(shop, acting_membership, user_id, role=payload.role)


@shop_router.delete("/{shop_slug}/members/{user_id}", auth=JWTAuth(), response=MessageOut)
async def remove_member(request, shop_slug: str, user_id: int):
    shop, acting_membership = await aget_shop_context(request, shop_slug, {ShopMembership.Role.OWNER, ShopMembership.Role.MANAGER})
    await services.change_membership(shop, acting_membership, user_id, remove=True)
    return {"detail": "Membership removed successfully."}


@shop_router.post("/{shop_slug}/invitations", auth=JWTAuth(), response=InvitationOut)
async def invite_member(request, shop_slug: str, payload: InvitationIn):
    shop, _ = await aget_shop_context(request, shop_slug, {ShopMembership.Role.OWNER, ShopMembership.Role.MANAGER})
    return await services.create_invitation(shop, request.auth, payload.email, payload.role)


@invitation_router.post("/{token}/accept", auth=JWTAuth(), response=MessageOut)
async def accept_invitation(request, token: str):
    return await services.accept_invitation(request.auth, token)
