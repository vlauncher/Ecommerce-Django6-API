from django.contrib import admin
from payments.models import PaymentTransaction


@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = ("gateway", "gateway_transaction_id", "order", "amount", "currency", "status", "created_at")
    list_filter = ("gateway", "status", "created_at")
    search_fields = ("gateway_transaction_id", "order__order_number", "idempotency_key")
