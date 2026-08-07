from datetime import date, datetime
from decimal import Decimal

from asgiref.sync import sync_to_async
from django.core.exceptions import ValidationError
from django.db import models, transaction
from ninja import Router
from ninja.errors import HttpError

from apps.catalog.models import Category, Collection, Coupon, CouponRedemption, InventoryLedgerEntry, PriceRule, Product, ProductAttributeValue, ProductVariant, Promotion, StockItem, Warehouse
from apps.commerce.models import Address, GiftCard, GiftCardTransaction, ReturnRequest, SellerOrder, Shipment, ShippingRate, ShippingZone, TaxRate
from apps.interactions.models import AuditLog, Conversation, Dispute, Message, Offer, Review
from apps.payments.models import LedgerEntry, Payment, PaymentEvent, PayoutRecipient, Refund, Withdrawal
from apps.shops.models import ShopMembership
from apps.shops.permissions import aget_shop_context
from apps.users.auth import JWTAuth

management_router = Router(tags=["Management CRUD"])


RESOURCE_MAP = {
    "categories": (Category, "shop", {"owner", "manager", "staff"}),
    "collections": (Collection, "shop", {"owner", "manager", "staff"}),
    "products": (Product, "shop", {"owner", "manager", "staff"}),
    "variants": (ProductVariant, "product__shop", {"owner", "manager", "staff"}),
    "product-attributes": (ProductAttributeValue, "product__shop", {"owner", "manager", "staff"}),
    "bundles": (ProductVariant, "product__shop", {"owner", "manager", "staff"}),
    "warehouses": (Warehouse, "shop", {"owner", "manager", "staff"}),
    "stock": (StockItem, "variant__product__shop", {"owner", "manager", "staff"}),
    "inventory-ledger": (InventoryLedgerEntry, "variant__product__shop", {"owner", "manager", "staff"}),
    "price-rules": (PriceRule, "shop", {"owner", "manager", "staff"}),
    "promotions": (Promotion, "shop", {"owner", "manager", "staff"}),
    "coupons": (Coupon, "promotion__shop", {"owner", "manager"}),
    "coupon-redemptions": (CouponRedemption, "coupon__promotion__shop", {"owner", "manager"}),
    "shipping-zones": (ShippingZone, "shop", {"owner", "manager", "staff"}),
    "shipping-rates": (ShippingRate, "zone__shop", {"owner", "manager", "staff"}),
    "tax-rates": (TaxRate, "shop", {"owner", "manager"}),
    "gift-cards": (GiftCard, "shop", {"owner", "manager"}),
    "gift-card-transactions": (GiftCardTransaction, "gift_card__shop", {"owner", "manager"}),
    "seller-orders": (SellerOrder, "shop", {"owner", "manager", "staff"}),
    "shipments": (Shipment, "seller_order__shop", {"owner", "manager", "staff"}),
    "return-requests": (ReturnRequest, "seller_order__shop", {"owner", "manager", "staff"}),
    "conversations": (Conversation, "shop", {"owner", "manager", "staff"}),
    "messages": (Message, "conversation__shop", {"owner", "manager", "staff"}),
    "offers": (Offer, "shop", {"owner", "manager", "staff"}),
    "reviews": (Review, "product__shop", {"owner", "manager", "staff"}),
    "disputes": (Dispute, "shop", {"owner", "manager", "staff"}),
    "payments": (Payment, "order__seller_orders__shop", {"owner", "manager"}),
    "refunds": (Refund, "payment__order__seller_orders__shop", {"owner", "manager"}),
    "ledger": (LedgerEntry, "shop", {"owner", "manager"}),
    "payment-events": (PaymentEvent, None, {"owner", "manager"}),
    "payout-recipient": (PayoutRecipient, "shop", {"owner", "manager"}),
    "withdrawals": (Withdrawal, "shop", {"owner", "manager"}),
}

READ_ONLY = {"inventory-ledger", "coupon-redemptions", "gift-card-transactions", "ledger", "payment-events", "payments", "refunds"}


def _json_value(value):
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    return value


def _serialize(instance):
    result = {"id": instance.pk}
    for field in instance._meta.concrete_fields:
        if field.name == "id":
            continue
        value = getattr(instance, field.attname)
        result[field.name] = _json_value(value)
    return result


def _model_data(model, payload, shop, create=False):
    concrete = {field.name: field for field in model._meta.concrete_fields if field.name != "id"}
    data = {}
    for key, value in payload.items():
        field = concrete.get(key) or next((item for item in concrete.values() if item.attname == key), None)
        if not field or field.auto_now or field.auto_now_add or field.name in {"created_at", "updated_at"}:
            continue
        if isinstance(field, models.ForeignKey):
            data[field.attname] = value
        elif key in {"id", "pk"}:
            continue
        else:
            data[field.name] = value
    if shop and any(field.name == "shop" for field in concrete.values()):
        data["shop_id"] = shop.id
    return data


def _query(model, lookup, shop):
    qs = model.objects.all()
    if lookup:
        qs = qs.filter(**{lookup: shop})
    return qs


async def _authorized(request, shop_slug, resource, write=False):
    config = RESOURCE_MAP.get(resource)
    if not config:
        raise HttpError(404, "Management resource not found.")
    _, _, roles = config
    shop, membership = await aget_shop_context(request, shop_slug, roles)
    if write and resource in READ_ONLY:
        raise HttpError(405, "This resource is immutable; use its action endpoint.")
    return shop, config


@management_router.get("/shops/{shop_slug}/{resource}", auth=JWTAuth())
async def list_resource(request, shop_slug: str, resource: str):
    shop, (model, lookup, _) = await _authorized(request, shop_slug, resource)

    @sync_to_async(thread_sensitive=True)
    def fetch():
        return [_serialize(item) for item in _query(model, lookup, shop)[:200]]

    return await fetch()


@management_router.post("/shops/{shop_slug}/{resource}", auth=JWTAuth())
async def create_resource(request, shop_slug: str, resource: str, payload: dict):
    shop, (model, lookup, _) = await _authorized(request, shop_slug, resource, write=True)

    @sync_to_async(thread_sensitive=True)
    def create():
        try:
            with transaction.atomic():
                instance = model.objects.create(**_model_data(model, payload, shop, create=True))
                if lookup and not _query(model, lookup, shop).filter(pk=instance.pk).exists():
                    raise HttpError(400, "Related objects must belong to this shop.")
        except (ValidationError, ValueError, TypeError) as exc:
            raise HttpError(400, str(exc))
        AuditLog.objects.create(actor=request.auth, shop=shop, action="create", resource=resource, object_id=str(instance.pk), payload=payload)
        return _serialize(instance)

    return await create()


@management_router.get("/shops/{shop_slug}/{resource}/{object_id}", auth=JWTAuth())
async def get_resource(request, shop_slug: str, resource: str, object_id: int):
    shop, (model, lookup, _) = await _authorized(request, shop_slug, resource)

    @sync_to_async(thread_sensitive=True)
    def fetch():
        try:
            return _serialize(_query(model, lookup, shop).get(pk=object_id))
        except model.DoesNotExist:
            raise HttpError(404, "Resource not found.")

    return await fetch()


@management_router.patch("/shops/{shop_slug}/{resource}/{object_id}", auth=JWTAuth())
async def update_resource(request, shop_slug: str, resource: str, object_id: int, payload: dict):
    shop, (model, lookup, _) = await _authorized(request, shop_slug, resource, write=True)

    @sync_to_async(thread_sensitive=True)
    def update():
        try:
            instance = _query(model, lookup, shop).get(pk=object_id)
        except model.DoesNotExist:
            raise HttpError(404, "Resource not found.")
        try:
            with transaction.atomic():
                for key, value in _model_data(model, payload, None).items():
                    setattr(instance, key, value)
                instance.save()
                if lookup and not _query(model, lookup, shop).filter(pk=instance.pk).exists():
                    raise HttpError(400, "Related objects must belong to this shop.")
        except (ValidationError, ValueError, TypeError) as exc:
            raise HttpError(400, str(exc))
        AuditLog.objects.create(actor=request.auth, shop=shop, action="update", resource=resource, object_id=str(instance.pk), payload=payload)
        return _serialize(instance)

    return await update()


@management_router.delete("/shops/{shop_slug}/{resource}/{object_id}", auth=JWTAuth())
async def delete_resource(request, shop_slug: str, resource: str, object_id: int):
    shop, (model, lookup, _) = await _authorized(request, shop_slug, resource, write=True)

    @sync_to_async(thread_sensitive=True)
    def delete():
        try:
            instance = _query(model, lookup, shop).get(pk=object_id)
        except model.DoesNotExist:
            raise HttpError(404, "Resource not found.")
        instance.delete()
        AuditLog.objects.create(actor=request.auth, shop=shop, action="delete", resource=resource, object_id=str(object_id))
        return {"detail": "Resource deleted successfully."}

    return await delete()


@management_router.post("/shops/{shop_slug}/seller-orders/{seller_order_id}/status", auth=JWTAuth())
async def update_seller_order_status(request, shop_slug: str, seller_order_id: int, payload: dict):
    shop, _ = await aget_shop_context(request, shop_slug, {ShopMembership.Role.OWNER, ShopMembership.Role.MANAGER, ShopMembership.Role.STAFF})
    from apps.commerce.models import SellerOrder
    status = payload.get("status")
    allowed = {choice.value for choice in SellerOrder.Status}
    if status not in allowed:
        raise HttpError(400, "Invalid seller-order status.")
    updated = await sync_to_async(SellerOrder.objects.filter(shop=shop, pk=seller_order_id).update, thread_sensitive=True)(status=status)
    if not updated:
        raise HttpError(404, "Seller order not found.")
    seller_order = await SellerOrder.objects.select_related("order").aget(pk=seller_order_id)
    if seller_order.order.user_id:
        from apps.interactions.models import Notification
        await Notification.objects.acreate(user_id=seller_order.order.user_id, kind="seller_order.status", title="Order status updated", body=f"Your order status is now {status}.", payload={"order_id": seller_order.order_id, "seller_order_id": seller_order_id, "status": status})
    return {"id": seller_order_id, "status": status}


@management_router.post("/shops/{shop_slug}/withdrawals/{withdrawal_id}/approve", auth=JWTAuth())
async def approve_withdrawal(request, shop_slug: str, withdrawal_id: int):
    shop, _ = await aget_shop_context(request, shop_slug, {ShopMembership.Role.OWNER, ShopMembership.Role.MANAGER})
    from apps.payments.models import Withdrawal
    updated = await sync_to_async(Withdrawal.objects.filter(shop=shop, pk=withdrawal_id, status=Withdrawal.Status.REQUESTED).update, thread_sensitive=True)(status=Withdrawal.Status.APPROVED)
    if not updated:
        raise HttpError(404, "Pending withdrawal not found.")
    return {"id": withdrawal_id, "status": Withdrawal.Status.APPROVED}


@management_router.post("/shops/{shop_slug}/disputes/{dispute_id}/resolve", auth=JWTAuth())
async def resolve_dispute(request, shop_slug: str, dispute_id: int, payload: dict):
    shop, _ = await aget_shop_context(request, shop_slug, {ShopMembership.Role.OWNER, ShopMembership.Role.MANAGER})
    from apps.interactions.models import Dispute
    updated = await sync_to_async(Dispute.objects.filter(shop=shop, pk=dispute_id).update, thread_sensitive=True)(status=Dispute.Status.RESOLVED, resolution=payload.get("resolution", ""))
    if not updated:
        raise HttpError(404, "Dispute not found.")
    return {"id": dispute_id, "status": Dispute.Status.RESOLVED}


@management_router.post("/shops/{shop_slug}/offers/{offer_id}/respond", auth=JWTAuth())
async def respond_to_offer(request, shop_slug: str, offer_id: int, payload: dict):
    shop, _ = await aget_shop_context(request, shop_slug, {ShopMembership.Role.OWNER, ShopMembership.Role.MANAGER, ShopMembership.Role.STAFF})
    from apps.interactions.models import Offer
    status = payload.get("status")
    if status not in {Offer.Status.COUNTERED, Offer.Status.ACCEPTED, Offer.Status.REJECTED}:
        raise HttpError(400, "Invalid offer response.")
    updates = {"status": status}
    if payload.get("amount_minor") is not None:
        updates["amount_minor"] = payload["amount_minor"]
    updated = await sync_to_async(Offer.objects.filter(shop=shop, pk=offer_id).update, thread_sensitive=True)(**updates)
    if not updated:
        raise HttpError(404, "Offer not found.")
    return {"id": offer_id, **updates}


@management_router.get("/shops/{shop_slug}/analytics/summary", auth=JWTAuth())
async def analytics_summary(request, shop_slug: str):
    from asgiref.sync import sync_to_async
    from django.db.models import Count, Sum
    from apps.commerce.models import SellerOrder
    from apps.payments.models import LedgerEntry
    shop, _ = await aget_shop_context(request, shop_slug, {ShopMembership.Role.OWNER, ShopMembership.Role.MANAGER, ShopMembership.Role.STAFF})

    def summarize():
        orders = SellerOrder.objects.filter(shop=shop)
        return {"orders_total": orders.count(), "orders_by_status": {row["status"]: row["count"] for row in orders.values("status").annotate(count=Count("id"))}, "sales_minor": orders.aggregate(total=Sum("subtotal_minor"))["total"] or 0, "commission_minor": orders.aggregate(total=Sum("commission_minor"))["total"] or 0, "available_payable_minor": LedgerEntry.objects.filter(shop=shop, entry_type=LedgerEntry.EntryType.SELLER_PAYABLE).aggregate(total=Sum("amount_minor"))["total"] or 0}

    return await sync_to_async(summarize, thread_sensitive=True)()
