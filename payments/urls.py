from django.urls import path
from payments.views import (
    PaymentInitiateView,
    PaymentStatusView,
    StripeWebhookView,
    PayPalWebhookView,
    FlutterwaveWebhookView,
)

urlpatterns = [
    path("initiate/", PaymentInitiateView.as_view(), name="payment-initiate"),
    path("webhooks/stripe/", StripeWebhookView.as_view(), name="webhook-stripe"),
    path("webhooks/paypal/", PayPalWebhookView.as_view(), name="webhook-paypal"),
    path("webhooks/flutterwave/", FlutterwaveWebhookView.as_view(), name="webhook-flutterwave"),
    path("<str:order_number>/", PaymentStatusView.as_view(), name="payment-status"),
]
