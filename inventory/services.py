from django.db import transaction
from django.db.models import F
from inventory.models import StockRecord, StockMovement


class InsufficientStockError(Exception):
    pass


def reserve_stock_atomic(variant_id, warehouse_id, quantity, reference_id=""):
    """
    Atomically reserve stock using SELECT FOR UPDATE lock inside an atomic transaction.
    Prevents race conditions and over-selling during high-concurrency checkout.
    """
    with transaction.atomic():
        stock_record = (
            StockRecord.objects
            .select_for_update()
            .get(variant_id=variant_id, warehouse_id=warehouse_id)
        )
        available = stock_record.quantity - stock_record.reserved
        if available < quantity:
            raise InsufficientStockError(
                f"Insufficient stock: {available} available, {quantity} requested."
            )

        stock_record.reserved = F("reserved") + quantity
        stock_record.save(update_fields=["reserved"])

        StockMovement.objects.create(
            variant_id=variant_id,
            warehouse_id=warehouse_id,
            movement_type=StockMovement.MovementType.RESERVATION_HOLD,
            quantity_delta=-quantity,
            reference_id=reference_id,
        )


def release_stock_reservation(variant_id, warehouse_id, quantity, reference_id=""):
    """Release unfulfilled stock reservation (e.g. cart timeout or cancelled order)."""
    with transaction.atomic():
        stock_record = (
            StockRecord.objects
            .select_for_update()
            .get(variant_id=variant_id, warehouse_id=warehouse_id)
        )
        stock_record.reserved = F("reserved") - quantity
        stock_record.save(update_fields=["reserved"])

        StockMovement.objects.create(
            variant_id=variant_id,
            warehouse_id=warehouse_id,
            movement_type=StockMovement.MovementType.RESERVATION_RELEASE,
            quantity_delta=quantity,
            reference_id=reference_id,
        )
