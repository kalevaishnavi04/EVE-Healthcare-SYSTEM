from django.urls import path

from .views import CreatePaymentView, PaymentWebhookView

urlpatterns = [
    path("", CreatePaymentView.as_view(), name="create-payment"),
    path("webhook/", PaymentWebhookView.as_view(), name="payment-webhook"),
]
