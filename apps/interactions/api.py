from datetime import timedelta

from ninja import Router
from ninja.errors import HttpError
from django.utils import timezone

from apps.catalog.models import Product, ProductVariant
from apps.commerce.models import Order, SellerOrder
from apps.shops.permissions import aget_shop_context
from apps.users.auth import JWTAuth

from .models import Conversation, Dispute, Message, Notification, Offer, Review
from .schemas import DisputeIn, MessageIn, OfferIn, ReviewIn

interaction_router = Router(tags=["Interactions"])


@interaction_router.post("/shops/{shop_slug}/conversations/{conversation_id}/messages", auth=JWTAuth())
async def send_message(request, shop_slug: str, conversation_id: int, payload: MessageIn):
    shop, _ = await aget_shop_context(request, shop_slug)
    conversation = await Conversation.objects.aget(pk=conversation_id, shop=shop)
    if request.auth.id not in {conversation.buyer_id, conversation.seller_id}:
        raise HttpError(403, "You are not a conversation participant.")
    message = await Message.objects.acreate(conversation=conversation, sender=request.auth, body=payload.body)
    return {"id": message.id, "body": message.body, "created_at": message.created_at}


@interaction_router.post("/shops/{shop_slug}/offers", auth=JWTAuth())
async def create_offer(request, shop_slug: str, payload: OfferIn):
    shop, _ = await aget_shop_context(request, shop_slug)
    product = await Product.objects.aget(pk=payload.product_id, shop=shop)
    variant = await ProductVariant.objects.aget(pk=payload.variant_id, product=product, is_active=True)
    if payload.amount_minor >= variant.price_minor:
        raise HttpError(400, "Offer must be below the current price.")
    offer = await Offer.objects.acreate(shop=shop, product=product, variant=variant, buyer=request.auth, amount_minor=payload.amount_minor, quantity=payload.quantity, expires_at=timezone.now() + timedelta(hours=24))
    return {"id": offer.id, "status": offer.status, "amount_minor": offer.amount_minor, "expires_at": offer.expires_at}


@interaction_router.post("/reviews", auth=JWTAuth())
async def create_review(request, payload: ReviewIn):
    order = await Order.objects.aget(pk=payload.order_id, user=request.auth)
    product = await Product.objects.aget(pk=payload.product_id)
    if not await order.seller_orders.filter(items__variant__product=product).aexists():
        raise HttpError(400, "You can only review products you purchased.")
    review, _ = await Review.objects.aget_or_create(product=product, order=order, author=request.auth, defaults={"rating": payload.rating, "title": payload.title, "body": payload.body})
    return {"id": review.id, "rating": review.rating, "is_published": review.is_published}


@interaction_router.post("/disputes", auth=JWTAuth())
async def create_dispute(request, payload: DisputeIn):
    order = await Order.objects.aget(pk=payload.order_id, user=request.auth)
    seller_order = await SellerOrder.objects.select_related("shop").aget(pk=payload.seller_order_id, order=order) if payload.seller_order_id else await order.seller_orders.select_related("shop").afirst()
    if not seller_order:
        raise HttpError(400, "The order has no seller fulfillment record.")
    dispute = await Dispute.objects.acreate(order=order, seller_order=seller_order, shop=seller_order.shop, opened_by=request.auth, reason=payload.reason, description=payload.description)
    return {"id": dispute.id, "status": dispute.status}


@interaction_router.get("/shops/{shop_slug}/offers", auth=JWTAuth())
async def list_shop_offers(request, shop_slug: str):
    from apps.shops.permissions import aget_shop_context
    shop, _ = await aget_shop_context(request, shop_slug)
    return [{"id": offer.id, "product_id": offer.product_id, "variant_id": offer.variant_id, "buyer_id": offer.buyer_id, "amount_minor": offer.amount_minor, "quantity": offer.quantity, "status": offer.status, "expires_at": offer.expires_at} async for offer in Offer.objects.filter(shop=shop).order_by("-created_at")]


@interaction_router.post("/offers/{offer_id}/cancel", auth=JWTAuth())
async def cancel_offer(request, offer_id: int):
    from ninja.errors import HttpError
    offer = await Offer.objects.filter(pk=offer_id, buyer=request.auth).afirst()
    if not offer:
        raise HttpError(404, "Offer not found.")
    if offer.status not in {Offer.Status.SUBMITTED, Offer.Status.COUNTERED}:
        raise HttpError(400, "This offer cannot be cancelled.")
    offer.status = Offer.Status.CANCELLED
    await offer.asave(update_fields=("status",))
    return {"id": offer.id, "status": offer.status}


@interaction_router.get("/reviews/{product_id}")
async def list_product_reviews(request, product_id: int):
    reviews = Review.objects.filter(product_id=product_id, is_published=True).select_related("author").order_by("-created_at")
    return [{"id": review.id, "rating": review.rating, "title": review.title, "body": review.body, "seller_reply": review.seller_reply, "author": review.author.full_name, "created_at": review.created_at} async for review in reviews]


@interaction_router.get("/my-disputes", auth=JWTAuth())
async def list_my_disputes(request):
    return [{"id": item.id, "order_id": item.order_id, "seller_order_id": item.seller_order_id, "reason": item.reason, "description": item.description, "status": item.status, "resolution": item.resolution, "created_at": item.created_at} async for item in Dispute.objects.filter(opened_by=request.auth).order_by("-created_at")]


@interaction_router.patch("/notifications/read-all", auth=JWTAuth())
async def mark_all_notifications_read(request):
    from django.utils import timezone
    updated = await Notification.objects.filter(user=request.auth, read_at__isnull=True).aupdate(read_at=timezone.now())
    return {"updated": updated}


@interaction_router.get("/notifications", auth=JWTAuth())
async def list_notifications(request):
    return [{"id": item.id, "kind": item.kind, "title": item.title, "body": item.body, "read_at": item.read_at} async for item in Notification.objects.filter(user=request.auth).order_by("-created_at")[:50]]


@interaction_router.patch("/notifications/{notification_id}/read", auth=JWTAuth())
async def mark_notification_read(request, notification_id: int):
    notification = await Notification.objects.aget(pk=notification_id, user=request.auth)
    notification.read_at = timezone.now()
    await notification.asave(update_fields=("read_at",))
    return {"id": notification.id, "read_at": notification.read_at}
