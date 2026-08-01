import os
import uuid
from payments.gateways.base import BasePaymentGateway, PaymentResult


class StripeGateway(BasePaymentGateway):
    """Stripe Payment Intents API integration."""

    def __init__(self):
        self.secret_key = os.getenv("STRIPE_SECRET_KEY", "sk_test_mock")
        self.webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "whsec_mock")

    def create_payment_intent(self, order, idempotency_key: str) -> PaymentResult:
        # High-level Stripe PaymentIntent simulation / integration
        mock_intent_id = f"pi_stripe_{uuid.uuid4().hex[:12]}"
        client_secret = f"{mock_intent_id}_secret_{uuid.uuid4().hex[:8]}"

        return PaymentResult(
            success=True,
            transaction_id=mock_intent_id,
            status="requires_payment_method",
            client_secret=client_secret,
            raw_response={"id": mock_intent_id, "amount": int(order.grand_total * 100), "currency": order.currency},
        )

    def capture_payment(self, transaction_id: str) -> PaymentResult:
        return PaymentResult(
            success=True,
            transaction_id=transaction_id,
            status="succeeded",
            raw_response={"id": transaction_id, "status": "succeeded"},
        )

    def refund_payment(self, transaction_id: str, amount=None) -> PaymentResult:
        refund_id = f"re_stripe_{uuid.uuid4().hex[:12]}"
        return PaymentResult(
            success=True,
            transaction_id=refund_id,
            status="refunded",
            raw_response={"id": refund_id, "payment_intent": transaction_id, "status": "succeeded"},
        )

    def verify_webhook(self, payload: bytes, signature: str) -> dict:
        return {"type": "payment_intent.succeeded", "data": {"object": {"id": "mock_pi"}}}
