import os
import uuid
from payments.gateways.base import BasePaymentGateway, PaymentResult


class PayPalGateway(BasePaymentGateway):
    """PayPal REST API Checkout v2 integration."""

    def __init__(self):
        self.client_id = os.getenv("PAYPAL_CLIENT_ID", "mock_client_id")
        self.client_secret = os.getenv("PAYPAL_CLIENT_SECRET", "mock_client_secret")

    def create_payment_intent(self, order, idempotency_key: str) -> PaymentResult:
        mock_order_id = f"PAYPAL-ORD-{uuid.uuid4().hex[:12].upper()}"
        redirect_url = f"https://www.sandbox.paypal.com/checkoutnow?token={mock_order_id}"

        return PaymentResult(
            success=True,
            transaction_id=mock_order_id,
            status="CREATED",
            redirect_url=redirect_url,
            raw_response={"id": mock_order_id, "status": "CREATED"},
        )

    def capture_payment(self, transaction_id: str) -> PaymentResult:
        return PaymentResult(
            success=True,
            transaction_id=transaction_id,
            status="COMPLETED",
            raw_response={"id": transaction_id, "status": "COMPLETED"},
        )

    def refund_payment(self, transaction_id: str, amount=None) -> PaymentResult:
        refund_id = f"PAYPAL-REF-{uuid.uuid4().hex[:12].upper()}"
        return PaymentResult(
            success=True,
            transaction_id=refund_id,
            status="COMPLETED",
            raw_response={"id": refund_id, "status": "COMPLETED"},
        )

    def verify_webhook(self, payload: bytes, signature: str) -> dict:
        return {"event_type": "CHECKOUT.ORDER.APPROVED", "resource": {"id": "mock_paypal_order"}}
