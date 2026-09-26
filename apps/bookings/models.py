import uuid

from django.conf import settings
from django.db import models


class Booking(models.Model):
    """
    A user's booking of a diagnostic test at a centre for a given
    appointment date/time. `amount` is snapshotted from the test's price
    at booking time so later price changes don't retroactively affect
    existing bookings.
    """

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        CONFIRMED = "CONFIRMED", "Confirmed"
        FAILED = "FAILED", "Failed"
        CANCELLED = "CANCELLED", "Cancelled"

    # UUID primary key: booking IDs are handed to users/URLs and to a
    # simulated external payment provider, so they should not be
    # sequentially guessable integers.
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="bookings", on_delete=models.CASCADE)
    diagnostic_test = models.ForeignKey(
        "centres.DiagnosticTest", related_name="bookings", on_delete=models.PROTECT
    )
    centre = models.ForeignKey("centres.DiagnosticCentre", related_name="bookings", on_delete=models.PROTECT)

    appointment_datetime = models.DateTimeField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "status"])]

    def __str__(self):
        return f"Booking {self.id} - {self.user} - {self.status}"
