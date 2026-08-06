from django.contrib import admin

from .models import LedgerEntry, Payment, PaymentEvent, PayoutRecipient, Refund, Withdrawal

for model in (LedgerEntry, Payment, PaymentEvent, PayoutRecipient, Refund, Withdrawal):
    admin.site.register(model)
