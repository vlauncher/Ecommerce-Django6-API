import os
import uuid
from payments.gateways.base import BasePaymentGateway, PaymentResult


class FlutterwaveGateway(BasePaymentGateway):
    """Flutterwave v3 API integration (popular for African & global payments)."""

    def __init__(self):
        self.secret_key = os.getenv("FLUTTERWAVE_SECRET_KEY", "FLWSECK_TEST_mock")

    def create_payment_intent(self, order, idempotency_key: str) -> PaymentResult:
        tx_ref = f"FLW-TX-{uuid.uuid4().hex[:12].upper()}"
        redirect_url = f"https://checkout.flutterwave.com/v3/hosted/pay/{tx_ref}"

        return PaymentResult(
            success=True,
            transaction_id=tx_ref,
            status="pending",
            redirect_url=redirect_url,
            raw_response={"status": "success", "data": {"link": redirect_url, "tx_ref": tx_ref}},
        )

    def capture_payment(self, transaction_id: str) -> PaymentResult:
        return PaymentResult(
            success=True,
            transaction_id=transaction_id,
            status="successful",
            raw_response={"status": "success", "data": {"id": transaction_id, "status": "successful"}},
        )

    def refund_payment(self, transaction_id: str, amount=None) -> PaymentResult:
        refund_id = f"FLW-REF-{uuid.uuid4().hex[:12].upper()}"
        return PaymentResult(
            success=True,
            transaction_id=refund_id,
            status="successful",
            raw_response={"status": "success", "data": {"id": refund_id, "status": "successful"}},
        )

    def verify_webhook(self, payload: bytes, signature: str) -> dict:
        return {"event": "charge.completed", "data": {"tx_ref": "mock_flw_ref", "status": "successful"}}
