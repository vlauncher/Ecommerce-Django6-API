import secrets

from ninja import Router

from apps.users.auth import JWTAuth

from .schemas import AddressIn, CartItemIn, CartOut, CheckoutIn, CheckoutOut, CouponApplyIn, ReturnRequestIn, WishlistItemIn
from . import services

commerce_router = Router(tags=["Commerce"])


def _guest_token(request):
    return request.headers.get("X-Guest-Token") or secrets.token_urlsafe(24)


@commerce_router.get("/guest/cart")
async def get_guest_cart(request):
    token = _guest_token(request)
    result = await services.get_guest_cart(token)
    result["guest_token"] = token
    return result


@commerce_router.post("/guest/cart/items")
async def add_guest_cart_item(request, payload: CartItemIn):
    token = _guest_token(request)
    result = await services.add_guest_to_cart(token, payload.model_dump())
    result["guest_token"] = token
    return result


@commerce_router.post("/guest/checkout")
async def guest_checkout(request, payload: CheckoutIn):
    from ninja.errors import HttpError
    token = request.headers.get("X-Guest-Token")
    if not token:
        raise HttpError(400, "X-Guest-Token is required.")
    return await services.checkout(None, payload.model_dump(), request.headers.get("Idempotency-Key", ""), token)


@commerce_router.get("/addresses", auth=JWTAuth())
async def list_addresses(request):
    from .models import Address
    return [{"id": address.id, "label": address.label, "recipient_name": address.recipient_name, "phone": address.phone, "line1": address.line1, "line2": address.line2, "city": address.city, "state": address.state, "country": address.country, "postal_code": address.postal_code} async for address in Address.objects.filter(user=request.auth).order_by("-id")]


@commerce_router.post("/addresses", auth=JWTAuth())
async def create_address(request, payload: AddressIn):
    from .models import Address
    address = await Address.objects.acreate(user=request.auth, **payload.model_dump())
    return {"id": address.id, **payload.model_dump()}


@commerce_router.delete("/addresses/{address_id}", auth=JWTAuth())
async def delete_address(request, address_id: int):
    from ninja.errors import HttpError
    from .models import Address
    deleted, _ = await Address.objects.filter(pk=address_id, user=request.auth).adelete()
    if not deleted:
        raise HttpError(404, "Address not found.")
    return {"detail": "Address deleted successfully."}


@commerce_router.get("/wishlist", auth=JWTAuth())
async def list_wishlist(request):
    from .models import WishlistItem
    return [{"id": item.id, "variant_id": item.variant_id, "product_id": item.variant.product_id, "product_name": item.variant.product.name, "price_minor": item.variant.price_minor, "currency": item.variant.currency} async for item in WishlistItem.objects.filter(user=request.auth).select_related("variant__product").order_by("-created_at")]


@commerce_router.post("/wishlist", auth=JWTAuth())
async def add_wishlist(request, payload: WishlistItemIn):
    from apps.catalog.models import ProductVariant
    from ninja.errors import HttpError
    from .models import WishlistItem
    try:
        variant = await ProductVariant.objects.select_related("product").aget(pk=payload.variant_id, is_active=True, product__status="published")
    except ProductVariant.DoesNotExist:
        raise HttpError(404, "Product variant not found.")
    item, _ = await WishlistItem.objects.aget_or_create(user=request.auth, variant=variant)
    return {"id": item.id, "variant_id": variant.id, "product_id": variant.product_id}


@commerce_router.delete("/wishlist/{variant_id}", auth=JWTAuth())
async def remove_wishlist(request, variant_id: int):
    from ninja.errors import HttpError
    from .models import WishlistItem
    deleted, _ = await WishlistItem.objects.filter(user=request.auth, variant_id=variant_id).adelete()
    if not deleted:
        raise HttpError(404, "Wishlist item not found.")
    return {"detail": "Wishlist item removed successfully."}


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
    return await services.checkout(request.auth, payload.model_dump(), request.headers.get("Idempotency-Key", ""))


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
    return {"id": order.id, "number": order.number, "status": order.status, "subtotal_minor": order.subtotal_minor, "discount_minor": order.discount_minor, "shipping_minor": order.shipping_minor, "tax_minor": order.tax_minor, "total_minor": order.total_minor, "currency": order.currency, "shipping_address": order.shipping_address, "seller_orders": [{"id": seller_order.id, "shop_id": seller_order.shop_id, "status": seller_order.status, "subtotal_minor": seller_order.subtotal_minor, "items": [{"sku": item.sku, "product_name": item.product_name, "quantity": item.quantity, "total_minor": item.total_minor} for item in seller_order.items.all()], "shipments": [{"id": shipment.id, "carrier": shipment.carrier, "tracking_number": shipment.tracking_number, "status": shipment.status, "shipped_at": shipment.shipped_at, "delivered_at": shipment.delivered_at} for shipment in seller_order.shipments.all()]} for seller_order in order.seller_orders.all()]}


@commerce_router.post("/orders/{order_id}/cancel", auth=JWTAuth())
async def cancel_order(request, order_id: int):
    from asgiref.sync import sync_to_async
    from django.db import transaction
    from django.utils import timezone
    from ninja.errors import HttpError
    from .models import Order, StockItem
    def cancel():
        with transaction.atomic():
            try:
                order = Order.objects.select_for_update().prefetch_related("seller_orders__items").get(pk=order_id, user=request.auth)
            except Order.DoesNotExist:
                raise HttpError(404, "Order not found.")
            if order.status not in {Order.Status.PENDING_PAYMENT, Order.Status.PAID, Order.Status.PROCESSING}:
                raise HttpError(400, "This order cannot be cancelled.")
            for seller_order in order.seller_orders.all():
                for item in seller_order.items.all():
                    remaining = item.quantity
                    stocks = list(StockItem.objects.select_for_update().filter(variant_id=item.variant_id).order_by("id"))
                    for stock in stocks:
                        release = min(remaining, stock.reserved)
                        if release:
                            stock.reserved -= release
                            stock.save(update_fields=("reserved", "updated_at"))
                            remaining -= release
                        if not remaining:
                            break
                seller_order.status = seller_order.Status.CANCELLED
                seller_order.save(update_fields=("status",))
            order.status = Order.Status.CANCELLED
            order.updated_at = timezone.now()
            order.save(update_fields=("status", "updated_at"))
            return order.id, order.status
    order_id, status = await sync_to_async(cancel, thread_sensitive=True)()
    return {"id": order_id, "status": status}


@commerce_router.post("/orders/{order_id}/confirm-delivery", auth=JWTAuth())
async def confirm_delivery(request, order_id: int):
    from datetime import timedelta
    from django.utils import timezone
    from django.conf import settings
    from ninja.errors import HttpError
    from .models import Order, SellerOrder
    try:
        order = await Order.objects.prefetch_related("seller_orders").aget(pk=order_id, user=request.auth)
    except Order.DoesNotExist:
        raise HttpError(404, "Order not found.")
    seller_orders = list(order.seller_orders.all())
    if not seller_orders or any(item.status not in {SellerOrder.Status.DELIVERED, SellerOrder.Status.COMPLETED if hasattr(SellerOrder.Status, "COMPLETED") else SellerOrder.Status.DELIVERED} for item in seller_orders):
        raise HttpError(400, "All seller orders must be delivered first.")
    now = timezone.now()
    for seller_order in seller_orders:
        seller_order.delivered_at = seller_order.delivered_at or now
        seller_order.hold_until = now + timedelta(days=settings.DISPUTE_WINDOW_DAYS)
        seller_order.save(update_fields=("delivered_at", "hold_until"))
    order.status = Order.Status.COMPLETED
    await order.asave(update_fields=("status", "updated_at"))
    return {"id": order.id, "status": order.status}


@commerce_router.post("/orders/{order_id}/returns", auth=JWTAuth())
async def create_return_request(request, order_id: int, payload: ReturnRequestIn):
    from ninja.errors import HttpError
    from .models import Order, ReturnRequest, SellerOrder
    try:
        order = await Order.objects.aget(pk=order_id, user=request.auth)
        seller_order = await SellerOrder.objects.aget(pk=payload.seller_order_id, order=order)
    except (Order.DoesNotExist, SellerOrder.DoesNotExist):
        raise HttpError(404, "Order or seller order not found.")
    if seller_order.status not in {SellerOrder.Status.DELIVERED}:
        raise HttpError(400, "Returns are available after delivery.")
    if await ReturnRequest.objects.filter(order=order, seller_order=seller_order, status__in=[ReturnRequest.Status.REQUESTED, ReturnRequest.Status.APPROVED, ReturnRequest.Status.RECEIVED]).aexists():
        raise HttpError(400, "A return request is already active for this seller order.")
    request_record = await ReturnRequest.objects.acreate(order=order, seller_order=seller_order, requested_by=request.auth, reason=payload.reason, description=payload.description)
    return {"id": request_record.id, "status": request_record.status, "reason": request_record.reason, "created_at": request_record.created_at}


@commerce_router.get("/returns", auth=JWTAuth())
async def list_return_requests(request):
    from .models import ReturnRequest
    return [{"id": item.id, "order_id": item.order_id, "seller_order_id": item.seller_order_id, "reason": item.reason, "description": item.description, "status": item.status, "resolution": item.resolution, "refund_amount_minor": item.refund_amount_minor, "created_at": item.created_at} async for item in ReturnRequest.objects.filter(requested_by=request.auth).order_by("-created_at")]
