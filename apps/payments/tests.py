from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.bookings.models import Booking
from apps.centres.models import DiagnosticCentre, DiagnosticTest

from .models import Payment, WebhookEvent

User = get_user_model()


class PaymentWebhookIdempotencyTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="patient1", password="StrongPass123!")
        self.centre = DiagnosticCentre.objects.create(name="City Diagnostics", location="Pune")
        self.test = DiagnosticTest.objects.create(centre=self.centre, name="CBC", price=500)
        self.booking = Booking.objects.create(
            user=self.user,
            diagnostic_test=self.test,
            centre=self.centre,
            appointment_datetime=timezone.now() + timedelta(days=1),
            amount=500,
            status=Booking.Status.PENDING,
        )

    def _payload(self, **overrides):
        payload = {
            "event_id": "evt-123",
            "booking_id": str(self.booking.id),
            "status": "SUCCESS",
            "transaction_id": "TXN-1",
        }
        payload.update(overrides)
        return payload

    def test_webhook_confirms_booking(self):
        response = self.client.post("/api/payments/webhook/", self._payload(), format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, Booking.Status.CONFIRMED)
        self.assertEqual(Payment.objects.count(), 1)

    def test_failed_webhook_marks_booking_failed(self):
        response = self.client.post(
            "/api/payments/webhook/", self._payload(status="FAILED", transaction_id="TXN-2"), format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, Booking.Status.FAILED)

    def test_duplicate_webhook_event_is_idempotent(self):
        payload = self._payload()
        for _ in range(3):
            response = self.client.post("/api/payments/webhook/", payload, format="json")
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(WebhookEvent.objects.count(), 1)
        self.assertEqual(Payment.objects.count(), 1)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, Booking.Status.CONFIRMED)

    def test_webhook_does_not_overturn_a_cancelled_booking(self):
        self.booking.status = Booking.Status.CANCELLED
        self.booking.save()

        response = self.client.post("/api/payments/webhook/", self._payload(), format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, Booking.Status.CANCELLED)
        self.assertEqual(Payment.objects.count(), 0)

    def test_webhook_for_unknown_booking_returns_404(self):
        payload = self._payload(event_id="evt-unknown", booking_id="00000000-0000-0000-0000-000000000000")
        response = self.client.post("/api/payments/webhook/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_webhook_invalid_payload_rejected(self):
        response = self.client.post("/api/payments/webhook/", {"event_id": "evt-x"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class CreatePaymentViewTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="patient2", password="StrongPass123!")
        self.centre = DiagnosticCentre.objects.create(name="City Diagnostics", location="Pune")
        self.test = DiagnosticTest.objects.create(centre=self.centre, name="CBC", price=500)
        self.booking = Booking.objects.create(
            user=self.user,
            diagnostic_test=self.test,
            centre=self.centre,
            appointment_datetime=timezone.now() + timedelta(days=1),
            amount=500,
            status=Booking.Status.PENDING,
        )
        self.client.force_authenticate(user=self.user)

    def test_cannot_pay_twice_for_confirmed_booking(self):
        self.booking.status = Booking.Status.CONFIRMED
        self.booking.save()
        response = self.client.post("/api/payments/", {"booking_id": str(self.booking.id)}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_pay_for_cancelled_booking(self):
        self.booking.status = Booking.Status.CANCELLED
        self.booking.save()
        response = self.client.post("/api/payments/", {"booking_id": str(self.booking.id)}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_payment_for_nonexistent_booking_returns_404(self):
        response = self.client.post(
            "/api/payments/", {"booking_id": "00000000-0000-0000-0000-000000000000"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_cannot_pay_for_someone_elses_booking(self):
        other_user = User.objects.create_user(username="patient3", password="StrongPass123!")
        self.client.force_authenticate(user=other_user)
        response = self.client.post("/api/payments/", {"booking_id": str(self.booking.id)}, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_unauthenticated_cannot_pay(self):
        self.client.force_authenticate(user=None)
        response = self.client.post("/api/payments/", {"booking_id": str(self.booking.id)}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
