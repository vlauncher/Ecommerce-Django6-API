import json
import uuid

from django.http import JsonResponse
from ninja import Router
from ninja.errors import HttpError
from django.utils import timezone

from apps.users.auth import JWTAuth
from apps.commerce.models import Order

from apps.shops.models import ShopMembership
from apps.shops.permissions import aget_shop_context

from .models import LedgerEntry, Payment, Refund, Withdrawal
from .paystack import create_recipient, initialize, refund as paystack_refund, transfer, verify as paystack_verify, verify_signature
from .schemas import PaymentInitializeIn, PaymentInitializeOut, PayoutRecipientIn, RefundIn, WithdrawalIn

payment_router = Router(tags=["Payments"])


@payment_router.post("/initialize", auth=JWTAuth(), response=PaymentInitializeOut)
async def initialize_payment(request, payload: PaymentInitializeIn):
    from asgiref.sync import sync_to_async

    def create():
        try:
            order = Order.objects.get(pk=payload.order_id, user=request.auth)
        except Order.DoesNotExist:
            raise HttpError(404, "Order not found.")
        if order.status != Order.Status.PENDING_PAYMENT:
            raise HttpError(400, "Only unpaid orders can be initialized for payment.")
        existing = Payment.objects.filter(order=order).first()
        if existing:
            return existing.raw_data
        reference = f"pay_{uuid.uuid4().hex}"
        result = initialize(request.auth.email, order.total_minor, reference, {"order_id": order.id, "order_number": order.number})
        Payment.objects.create(order=order, reference=reference, amount_minor=order.total_minor, raw_data=result)
        return result

    return await sync_to_async(create, thread_sensitive=True)()


@payment_router.post("/guest/initialize", auth=None, response=PaymentInitializeOut)
async def initialize_guest_payment(request, payload: PaymentInitializeIn):
    from asgiref.sync import sync_to_async
    guest_token = request.headers.get("X-Guest-Token", "")
    if not guest_token:
        raise HttpError(400, "X-Guest-Token is required.")

    def create():
        try:
            order = Order.objects.get(pk=payload.order_id, guest_token=guest_token, user__isnull=True)
        except Order.DoesNotExist:
            raise HttpError(404, "Order not found.")
        if order.status != Order.Status.PENDING_PAYMENT or not order.guest_email:
            raise HttpError(400, "This order cannot be initialized for payment.")
        existing = Payment.objects.filter(order=order).first()
        if existing:
            return existing.raw_data
        reference = f"pay_{uuid.uuid4().hex}"
        result = initialize(order.guest_email, order.total_minor, reference, {"order_id": order.id, "order_number": order.number})
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
        if payment.status != Payment.Status.SUCCESS:
            raise HttpError(400, "Only successful payments can be refunded.")
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
    from django.db import transaction
    from django.db.models import Sum
    from django.utils import timezone

    def create():
        with transaction.atomic():
            locked_shop = type(shop).objects.select_for_update().get(pk=shop.pk)
            available = LedgerEntry.objects.filter(shop=locked_shop, entry_type=LedgerEntry.EntryType.SELLER_PAYABLE, available_at__lte=timezone.now()).aggregate(total=Sum("amount_minor"))["total"] or 0
            withdrawn = Withdrawal.objects.filter(shop=locked_shop, status__in=[Withdrawal.Status.REQUESTED, Withdrawal.Status.APPROVED, Withdrawal.Status.PROCESSING, Withdrawal.Status.SUCCESS]).aggregate(total=Sum("amount_minor"))["total"] or 0
            if payload.amount_minor > available - withdrawn:
                raise HttpError(400, "Withdrawal exceeds the available seller balance.")
            withdrawal = Withdrawal.objects.create(shop=locked_shop, requested_by=request.auth, amount_minor=payload.amount_minor, reference=f"wd_{uuid.uuid4().hex}", reason=payload.reason)
            return {"id": withdrawal.id, "reference": withdrawal.reference, "status": withdrawal.status, "amount_minor": withdrawal.amount_minor}

    return await sync_to_async(create, thread_sensitive=True)()


@payment_router.post("/shops/{shop_slug}/payout-recipient", auth=JWTAuth())
async def configure_payout_recipient(request, shop_slug: str, payload: PayoutRecipientIn):
    from asgiref.sync import sync_to_async
    from django.db import transaction
    from .models import PayoutRecipient
    shop, _ = await aget_shop_context(request, shop_slug, {ShopMembership.Role.OWNER, ShopMembership.Role.MANAGER})

    def save_recipient():
        result = create_recipient(payload.account_name or shop.name, payload.account_number, payload.bank_code)
        with transaction.atomic():
            recipient, _ = PayoutRecipient.objects.update_or_create(shop=shop, defaults={"bank_code": payload.bank_code, "account_number": payload.account_number, "account_name": payload.account_name, "recipient_code": result.get("recipient_code", ""), "is_verified": bool(result.get("recipient_code"))})
        return {"id": recipient.id, "recipient_code": recipient.recipient_code, "is_verified": recipient.is_verified}

    return await sync_to_async(save_recipient, thread_sensitive=True)()


@payment_router.post("/shops/{shop_slug}/withdrawals/{withdrawal_id}/process", auth=JWTAuth())
async def process_withdrawal(request, shop_slug: str, withdrawal_id: int):
    from asgiref.sync import sync_to_async
    from django.db import transaction
    from .models import LedgerEntry, PayoutRecipient, Withdrawal
    shop, _ = await aget_shop_context(request, shop_slug, {ShopMembership.Role.OWNER, ShopMembership.Role.MANAGER})

    def process():
        with transaction.atomic():
            withdrawal = Withdrawal.objects.select_for_update().get(pk=withdrawal_id, shop=shop, status=Withdrawal.Status.APPROVED)
            recipient = PayoutRecipient.objects.filter(shop=shop, is_verified=True).first()
            if not recipient or not recipient.recipient_code:
                raise HttpError(400, "A verified payout recipient is required.")
            result = transfer(recipient.recipient_code, withdrawal.amount_minor, withdrawal.reason or f"Withdrawal {withdrawal.reference}")
            withdrawal.status = result.get("status", Withdrawal.Status.PROCESSING)
            withdrawal.transfer_code = str(result.get("transfer_code", ""))
            withdrawal.save(update_fields=("status", "transfer_code", "updated_at"))
            LedgerEntry.objects.get_or_create(shop=shop, entry_type=LedgerEntry.EntryType.WITHDRAWAL, reference=withdrawal.reference, defaults={"amount_minor": withdrawal.amount_minor, "currency": withdrawal.currency, "available_at": timezone.now()})
            return {"id": withdrawal.id, "reference": withdrawal.reference, "status": withdrawal.status, "transfer_code": withdrawal.transfer_code}

    try:
        return await sync_to_async(process, thread_sensitive=True)()
    except Withdrawal.DoesNotExist:
        raise HttpError(404, "Approved withdrawal not found.")


@payment_router.post("/webhook", auth=None)
def paystack_webhook(request):
    if not verify_signature(request.body, request.headers.get("x-paystack-signature", "")):
        return JsonResponse({"detail": "Invalid signature"}, status=401)
    payload = json.loads(request.body or b"{}")
    from .services import process_event

    process_event(payload.get("event", ""), payload.get("data", {}))
    return JsonResponse({"status": True})
