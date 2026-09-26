import uuid

from django.db import models


class Payment(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        SUCCESS = "SUCCESS", "Success"
        FAILED = "FAILED", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking = models.ForeignKey("bookings.Booking", related_name="payments", on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    # Unique so the same provider transaction can never be recorded twice,
    # which is one of the two idempotency guards (the other is WebhookEvent).
    transaction_id = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Payment {self.transaction_id} - {self.status}"


class WebhookEvent(models.Model):
    """
    Every inbound webhook call is logged here first, keyed by the
    provider's event_id. If the same event_id arrives again (a retry /
    at-least-once delivery), we detect it here and skip re-processing -
    this is what makes POST /api/payments/webhook/ idempotent.
    """

    event_id = models.CharField(max_length=128, unique=True)
    payload = models.JSONField()
    processed = models.BooleanField(default=False)
    received_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"WebhookEvent {self.event_id} processed={self.processed}"
