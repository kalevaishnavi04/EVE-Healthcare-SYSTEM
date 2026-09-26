from django.contrib import admin

from .models import Payment, WebhookEvent


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ["id", "booking", "amount", "status", "transaction_id", "created_at"]
    list_filter = ["status"]
    search_fields = ["transaction_id", "booking__id"]


@admin.register(WebhookEvent)
class WebhookEventAdmin(admin.ModelAdmin):
    list_display = ["event_id", "processed", "received_at", "processed_at"]
    list_filter = ["processed"]
    search_fields = ["event_id"]
