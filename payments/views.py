import uuid
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
from orders.models import Order
from payments.models import PaymentTransaction
from payments.serializers import PaymentInitiateSerializer, PaymentTransactionSerializer
from payments.gateways.stripe_gateway import StripeGateway
from payments.gateways.paypal_gateway import PayPalGateway
from payments.gateways.flutterwave_gateway import FlutterwaveGateway


GATEWAY_MAP = {
    PaymentTransaction.Gateway.STRIPE: StripeGateway,
    PaymentTransaction.Gateway.PAYPAL: PayPalGateway,
    PaymentTransaction.Gateway.FLUTTERWAVE: FlutterwaveGateway,
}


@extend_schema(tags=["Payments"])
class PaymentInitiateView(generics.GenericAPIView):
    """Initiate a payment transaction for an order."""

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PaymentInitiateSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        order_number = serializer.validated_data["order_number"]
        gateway_name = serializer.validated_data["gateway"]

        order = generics.get_object_or_404(Order, order_number=order_number, user=request.user)

        if order.status == Order.Status.PAID:
            return Response({"detail": "Order is already paid."}, status=status.HTTP_400_BAD_REQUEST)

        gateway_class = GATEWAY_MAP.get(gateway_name)
        gateway = gateway_class()
        idempotency_key = f"PAY-{order.id}-{uuid.uuid4().hex[:8]}"

        result = gateway.create_payment_intent(order, idempotency_key=idempotency_key)

        transaction = PaymentTransaction.objects.create(
            order=order,
            gateway=gateway_name,
            gateway_transaction_id=result.transaction_id,
            gateway_response=result.raw_response or {},
            amount=order.grand_total,
            currency=order.currency,
            status=PaymentTransaction.Status.PENDING,
            idempotency_key=idempotency_key,
        )

        return Response({
            "transaction_id": transaction.id,
            "gateway": gateway_name,
            "gateway_transaction_id": result.transaction_id,
            "client_secret": result.client_secret,
            "redirect_url": result.redirect_url,
            "amount": str(order.grand_total),
            "currency": order.currency,
            "status": transaction.status,
        }, status=status.HTTP_200_OK)


@extend_schema(tags=["Payments"])
class PaymentStatusView(generics.ListAPIView):
    """View payment attempts and transactions for an order."""

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PaymentTransactionSerializer

    def get_queryset(self):
        order_number = self.kwargs["order_number"]
        return PaymentTransaction.objects.filter(
            order__order_number=order_number, order__user=self.request.user
        )


from drf_spectacular.utils import inline_serializer
from rest_framework import serializers

WebhookResponseSerializer = inline_serializer(
    name="WebhookResponse",
    fields={"status": serializers.CharField()},
)


@extend_schema(tags=["Payments - Webhooks"], request=None, responses={200: WebhookResponseSerializer})
class StripeWebhookView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        return Response({"status": "received"}, status=status.HTTP_200_OK)


@extend_schema(tags=["Payments - Webhooks"], request=None, responses={200: WebhookResponseSerializer})
class PayPalWebhookView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        return Response({"status": "received"}, status=status.HTTP_200_OK)


@extend_schema(tags=["Payments - Webhooks"], request=None, responses={200: WebhookResponseSerializer})
class FlutterwaveWebhookView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        return Response({"status": "received"}, status=status.HTTP_200_OK)

