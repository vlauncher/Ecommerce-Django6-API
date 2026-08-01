from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class PaymentResult:
    success: bool
    transaction_id: str
    status: str
    client_secret: str = ""
    redirect_url: str = ""
    raw_response: dict = None


class BasePaymentGateway(ABC):
    """Abstract interface for all e-commerce payment gateway integrations."""

    @abstractmethod
    def create_payment_intent(self, order, idempotency_key: str) -> PaymentResult:
        """Initialize payment transaction (returns client secret or checkout redirect URL)."""
        pass

    @abstractmethod
    def capture_payment(self, transaction_id: str) -> PaymentResult:
        """Capture authorized payment funds."""
        pass

    @abstractmethod
    def refund_payment(self, transaction_id: str, amount=None) -> PaymentResult:
        """Issue full or partial refund."""
        pass

    @abstractmethod
    def verify_webhook(self, payload: bytes, signature: str) -> dict:
        """Verify webhook signature and parse event payload."""
        pass
