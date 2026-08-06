import json
import uuid

from django.http import JsonResponse
from ninja import Router
from ninja.errors import HttpError

from apps.users.auth import JWTAuth
from apps.commerce.models import Order

from apps.shops.models import ShopMembership
from apps.shops.permissions import aget_shop_context

from .models import LedgerEntry, Payment, Refund, Withdrawal
from .paystack import initialize, refund as paystack_refund, verify as paystack_verify, verify_signature
from .schemas import PaymentInitializeIn, PaymentInitializeOut, RefundIn, WithdrawalIn

payment_router = Router(tags=["Payments"])


@payment_router.post("/initialize", auth=JWTAuth(), response=PaymentInitializeOut)
async def initialize_payment(request, payload: PaymentInitializeIn):
    from asgiref.sync import sync_to_async

    def create():
        try:
            order = Order.objects.get(pk=payload.order_id, user=request.auth)
        except Order.DoesNotExist:
            raise HttpError(404, "Order not found.")
        reference = f"pay_{uuid.uuid4().hex}"
        result = initialize(request.auth.email, order.total_minor, reference, {"order_id": order.id, "order_number": order.number})
        Payment.objects.create(order=order, reference=reference, amount_minor=order.total_minor, raw_data=result)
        return result

    return await sync_to_async(create, thread_sensitive=True)()


@payment_router.post("/refunds", auth=JWTAuth())
async def create_refund(request, payload: RefundIn):
    from asgiref.sync import sync_to_async

    def create():
        try:
            payment = Payment.objects.select_related("order").get(order_id=payload.order_id, order__user=request.auth)
        except Payment.DoesNotExist:
            raise HttpError(404, "Payment not found.")
        amount = payload.amount_minor or payment.amount_minor
        already_refunded = sum(item.amount_minor for item in payment.refunds.exclude(status=Refund.Status.FAILED))
        if amount + already_refunded > payment.amount_minor:
            raise HttpError(400, "Refund exceeds the paid amount.")
        result = paystack_refund(payment.reference, amount if amount < payment.amount_minor else None)
        refund_record = Refund.objects.create(payment=payment, reference=str(result.get("id") or uuid.uuid4().hex), amount_minor=amount, status=result.get("status", Refund.Status.PENDING), reason=payload.reason, created_by=request.auth, raw_data=result)
        return {"id": refund_record.id, "reference": refund_record.reference, "status": refund_record.status, "amount_minor": refund_record.amount_minor}

    return await sync_to_async(create, thread_sensitive=True)()


@payment_router.post("/verify/{reference}", auth=JWTAuth())
async def verify_payment(request, reference: str):
    from asgiref.sync import sync_to_async
    from .services import process_event

    def verify_payment_with_paystack():
        payment = Payment.objects.select_related("order").get(reference=reference, order__user=request.auth)
        result = paystack_verify(reference)
        process_event("charge.success" if result.get("status") == "success" else "transaction.failed", result)
        return {"reference": reference, "status": result.get("status"), "amount": result.get("amount"), "currency": result.get("currency")}

    try:
        return await sync_to_async(verify_payment_with_paystack, thread_sensitive=True)()
    except Payment.DoesNotExist:
        raise HttpError(404, "Payment not found.")


@payment_router.post("/shops/{shop_slug}/withdrawals", auth=JWTAuth())
async def request_withdrawal(request, shop_slug: str, payload: WithdrawalIn):
    shop, _ = await aget_shop_context(request, shop_slug, {ShopMembership.Role.OWNER, ShopMembership.Role.MANAGER})
    from asgiref.sync import sync_to_async
    from django.db.models import Sum
    from django.utils import timezone

    def create():
        available = LedgerEntry.objects.filter(shop=shop, entry_type=LedgerEntry.EntryType.SELLER_PAYABLE, available_at__lte=timezone.now()).aggregate(total=Sum("amount_minor"))["total"] or 0
        withdrawn = LedgerEntry.objects.filter(shop=shop, entry_type=LedgerEntry.EntryType.WITHDRAWAL).aggregate(total=Sum("amount_minor"))["total"] or 0
        if payload.amount_minor > available - withdrawn:
            raise HttpError(400, "Withdrawal exceeds the available seller balance.")
        withdrawal = Withdrawal.objects.create(shop=shop, requested_by=request.auth, amount_minor=payload.amount_minor, reference=f"wd_{uuid.uuid4().hex}", reason=payload.reason)
        return {"id": withdrawal.id, "reference": withdrawal.reference, "status": withdrawal.status, "amount_minor": withdrawal.amount_minor}

    return await sync_to_async(create, thread_sensitive=True)()


@payment_router.post("/webhook", auth=None)
def paystack_webhook(request):
    if not verify_signature(request.body, request.headers.get("x-paystack-signature", "")):
        return JsonResponse({"detail": "Invalid signature"}, status=401)
    payload = json.loads(request.body or b"{}")
    from .services import process_event

    process_event(payload.get("event", ""), payload.get("data", {}))
    return JsonResponse({"status": True})
