from django.db import transaction
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import logging

from apps.commerce.models import Order

from .models import LedgerEntry, Payment, PaymentEvent

logger = logging.getLogger(__name__)


def process_event(event_type, data):
    event_id = str(data.get("id") or data.get("reference") or f"{event_type}:{data.get('transaction_reference')}")
    with transaction.atomic():
        event, created = PaymentEvent.objects.get_or_create(event_id=event_id, defaults={"event_type": event_type, "payload": data})
        if not created or event.processed_at:
            return
        reference = data.get("reference") or data.get("transaction_reference")
        payment = Payment.objects.select_for_update().filter(reference=reference).first()
        if payment and event_type in {"charge.success", "transaction.success"}:
            amount = data.get("amount")
            currency = str(data.get("currency", "")).upper()
            if amount is None or int(amount) != payment.amount_minor or currency != payment.currency.upper():
                logger.error("Ignoring payment event with mismatched amount/currency: %s", event_id)
                event.processed_at = timezone.now()
                event.save(update_fields=("processed_at",))
                return
            payment.status = Payment.Status.SUCCESS
            payment.provider_id = str(data.get("id", ""))
            payment.paid_at = timezone.now()
            payment.raw_data = data
            payment.save(update_fields=("status", "provider_id", "paid_at", "raw_data", "updated_at"))
            payment.order.status = Order.Status.PAID
            payment.order.save(update_fields=("status", "updated_at"))
            from apps.interactions.models import Notification
            if payment.order.user_id:
                Notification.objects.create(user_id=payment.order.user_id, kind="payment.success", title="Payment received", body=f"Payment received for order {payment.order.number}.", payload={"order_id": payment.order_id, "reference": payment.reference})
            for seller_order in payment.order.seller_orders.all():
                LedgerEntry.objects.get_or_create(shop=seller_order.shop, seller_order=seller_order, entry_type=LedgerEntry.EntryType.SELLER_PAYABLE, reference=f"payable_{seller_order.id}", defaults={"amount_minor": seller_order.seller_net_minor, "currency": payment.currency, "available_at": timezone.now() + timedelta(days=settings.SELLER_PAYOUT_HOLD_DAYS)})
                LedgerEntry.objects.get_or_create(shop=seller_order.shop, seller_order=seller_order, entry_type=LedgerEntry.EntryType.COMMISSION, reference=f"commission_{seller_order.id}", defaults={"amount_minor": seller_order.commission_minor, "currency": payment.currency})
        event.processed_at = timezone.now()
        event.save(update_fields=("processed_at",))
