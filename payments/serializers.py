from rest_framework import serializers
from payments.models import PaymentTransaction


class PaymentInitiateSerializer(serializers.Serializer):
    order_number = serializers.CharField()
    gateway = serializers.ChoiceField(choices=PaymentTransaction.Gateway.choices)


class PaymentTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentTransaction
        fields = (
            "id",
            "order",
            "gateway",
            "gateway_transaction_id",
            "amount",
            "currency",
            "status",
            "idempotency_key",
            "created_at",
        )
