from ninja import Router

from apps.users.auth import JWTAuth

from .schemas import CartItemIn, CartOut, CheckoutIn, CheckoutOut, CouponApplyIn
from . import services

commerce_router = Router(tags=["Commerce"])


@commerce_router.get("/cart", auth=JWTAuth(), response=CartOut)
async def get_cart(request):
    return await services.get_or_create_cart(request.auth)


@commerce_router.post("/cart/items", auth=JWTAuth(), response=CartOut)
async def add_cart_item(request, payload: CartItemIn):
    return await services.add_to_cart(request.auth, payload.model_dump())


@commerce_router.post("/cart/coupon", auth=JWTAuth(), response=CartOut)
async def apply_coupon(request, payload: CouponApplyIn):
    return await services.apply_coupon(request.auth, payload.code)


@commerce_router.post("/checkout", auth=JWTAuth(), response=CheckoutOut)
async def checkout(request, payload: CheckoutIn):
    return await services.checkout(request.auth, payload.model_dump())


@commerce_router.get("/orders", auth=JWTAuth())
async def list_orders(request):
    from .models import Order
    return [{"id": order.id, "number": order.number, "status": order.status, "total_minor": order.total_minor, "currency": order.currency, "created_at": order.created_at} async for order in Order.objects.filter(user=request.auth).order_by("-created_at")]


@commerce_router.get("/orders/{order_id}", auth=JWTAuth())
async def get_order(request, order_id: int):
    from ninja.errors import HttpError
    from .models import Order
    try:
        order = await Order.objects.prefetch_related("seller_orders__items").aget(pk=order_id, user=request.auth)
    except Order.DoesNotExist:
        raise HttpError(404, "Order not found.")
    return {"id": order.id, "number": order.number, "status": order.status, "total_minor": order.total_minor, "currency": order.currency, "seller_orders": [{"id": seller_order.id, "shop_id": seller_order.shop_id, "status": seller_order.status, "subtotal_minor": seller_order.subtotal_minor, "items": [{"sku": item.sku, "product_name": item.product_name, "quantity": item.quantity, "total_minor": item.total_minor} for item in seller_order.items.all()]} for seller_order in order.seller_orders.all()]}
