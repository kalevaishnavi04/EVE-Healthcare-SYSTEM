from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.centres.models import DiagnosticCentre, DiagnosticTest

from .models import Booking

User = get_user_model()


class BookingTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="alice", password="StrongPass123!")
        self.other_user = User.objects.create_user(username="bob", password="StrongPass123!")
        self.centre = DiagnosticCentre.objects.create(name="City Diagnostics", location="Pune")
        self.test = DiagnosticTest.objects.create(centre=self.centre, name="CBC", price=500)
        self.client.force_authenticate(user=self.user)

    def test_create_booking_success(self):
        payload = {
            "diagnostic_test": self.test.id,
            "appointment_datetime": (timezone.now() + timedelta(days=2)).isoformat(),
        }
        response = self.client.post("/api/bookings/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["status"], Booking.Status.PENDING)
        self.assertEqual(str(response.data["amount"]), "500.00")

    def test_cannot_book_in_the_past(self):
        payload = {
            "diagnostic_test": self.test.id,
            "appointment_datetime": (timezone.now() - timedelta(days=1)).isoformat(),
        }
        response = self.client.post("/api/bookings/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_book_inactive_test(self):
        self.test.is_active = False
        self.test.save()
        payload = {
            "diagnostic_test": self.test.id,
            "appointment_datetime": (timezone.now() + timedelta(days=2)).isoformat(),
        }
        response = self.client.post("/api/bookings/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unauthenticated_user_cannot_book(self):
        self.client.force_authenticate(user=None)
        payload = {
            "diagnostic_test": self.test.id,
            "appointment_datetime": (timezone.now() + timedelta(days=2)).isoformat(),
        }
        response = self.client.post("/api/bookings/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_cannot_see_other_users_booking(self):
        booking = Booking.objects.create(
            user=self.other_user,
            diagnostic_test=self.test,
            centre=self.centre,
            appointment_datetime=timezone.now() + timedelta(days=2),
            amount=500,
        )
        response = self.client.get(f"/api/bookings/{booking.id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_invalid_booking_id_returns_404(self):
        response = self.client.get("/api/bookings/00000000-0000-0000-0000-000000000000/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_cancel_booking(self):
        booking = Booking.objects.create(
            user=self.user,
            diagnostic_test=self.test,
            centre=self.centre,
            appointment_datetime=timezone.now() + timedelta(days=2),
            amount=500,
        )
        response = self.client.post(f"/api/bookings/{booking.id}/cancel/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.Status.CANCELLED)

    def test_cannot_cancel_already_cancelled_booking(self):
        booking = Booking.objects.create(
            user=self.user,
            diagnostic_test=self.test,
            centre=self.centre,
            appointment_datetime=timezone.now() + timedelta(days=2),
            amount=500,
            status=Booking.Status.CANCELLED,
        )
        response = self.client.post(f"/api/bookings/{booking.id}/cancel/")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
