import logging
import random
import uuid

from django.db import transaction
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from apps.bookings.models import Booking

from .models import Payment, WebhookEvent
from .serializers import PaymentCreateSerializer, PaymentSerializer, WebhookSerializer

logger = logging.getLogger(__name__)


class CreatePaymentView(APIView):
    """
    POST /api/payments/
    Body: {"booking_id": "<uuid>"}

    Simulates handing a booking off to a payment gateway: randomly resolves
    to SUCCESS or FAILED and updates the booking status accordingly
    (CONFIRMED / FAILED). Only the booking's owner may pay for it.

    In a real system the gateway's *actual* confirmation would still arrive
    later via /payments/webhook/, which is why that endpoint is the
    idempotent source of truth rather than this one.
    """

    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "payments"

    def post(self, request):
        serializer = PaymentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        booking_id = serializer.validated_data["booking_id"]

        with transaction.atomic():
            try:
                booking = Booking.objects.select_for_update().get(id=booking_id)
            except Booking.DoesNotExist:
                return Response({"detail": "Booking not found."}, status=status.HTTP_404_NOT_FOUND)

            if booking.user_id != request.user.id:
                # Don't reveal that a booking belonging to someone else exists.
                return Response({"detail": "Booking not found."}, status=status.HTTP_404_NOT_FOUND)

            if booking.status == Booking.Status.CONFIRMED:
                return Response(
                    {"detail": "Booking is already paid and confirmed."}, status=status.HTTP_400_BAD_REQUEST
                )
            if booking.status == Booking.Status.CANCELLED:
                return Response(
                    {"detail": "Cannot pay for a cancelled booking."}, status=status.HTTP_400_BAD_REQUEST
                )

            # --- simulated call to an external payment gateway ---
            simulated_status = random.choice([Payment.Status.SUCCESS, Payment.Status.FAILED])

            payment = Payment.objects.create(
                booking=booking,
                amount=booking.amount,
                status=simulated_status,
                transaction_id=f"SIM-{uuid.uuid4().hex[:16]}",
            )

            booking.status = (
                Booking.Status.CONFIRMED if simulated_status == Payment.Status.SUCCESS else Booking.Status.FAILED
            )
            booking.save(update_fields=["status", "updated_at"])

            logger.info(
                "payment.simulated booking_id=%s payment_id=%s result=%s",
                booking.id,
                payment.id,
                simulated_status,
            )

        return Response(PaymentSerializer(payment).data, status=status.HTTP_201_CREATED)


class PaymentWebhookView(APIView):
    """
    POST /api/payments/webhook/
    Body: {"event_id": "...", "booking_id": "<uuid>", "status": "SUCCESS"|"FAILED", "transaction_id": "..."}

    Simulated payment-provider webhook. Providers typically deliver events
    "at least once", so the same event_id can legitimately arrive more than
    once. This endpoint is idempotent:

      1. Every event is first recorded in WebhookEvent, keyed by event_id
         (unique). If that event_id was already marked processed, we return
         200 immediately without touching Payment/Booking again.
      2. Payment rows are keyed by a unique transaction_id, so even a
         duplicate call that slipped past step 1 (e.g. a race between two
         concurrent deliveries) cannot create a second Payment for the same
         transaction - get_or_create on transaction_id makes that safe.
      3. select_for_update() locks the Booking and WebhookEvent rows for the
         duration of the transaction so two concurrent deliveries of the
         same event can't both "win".
      4. A webhook is only allowed to move a booking out of PENDING/FAILED;
         a booking that's already CONFIRMED or CANCELLED is left untouched,
         so a stale/duplicate/late webhook can't undo a cancellation or
         double-apply a status.
    """

    permission_classes = [permissions.AllowAny]  # a real provider would authenticate via a shared secret/signature
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "webhook"

    def post(self, request):
        serializer = WebhookSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        event_id = data["event_id"]

        with transaction.atomic():
            event, created = WebhookEvent.objects.select_for_update().get_or_create(
                event_id=event_id,
                defaults={"payload": request.data},
            )

            if not created and event.processed:
                logger.info("webhook.duplicate event_id=%s ignored", event_id)
                return Response(
                    {"detail": "Event already processed; no action taken.", "duplicate": True},
                    status=status.HTTP_200_OK,
                )

            try:
                booking = Booking.objects.select_for_update().get(id=data["booking_id"])
            except Booking.DoesNotExist:
                event.processed = True
                event.processed_at = timezone.now()
                event.save(update_fields=["processed", "processed_at"])
                return Response({"detail": "Booking not found."}, status=status.HTTP_404_NOT_FOUND)

            if booking.status in (Booking.Status.CONFIRMED, Booking.Status.CANCELLED):
                event.processed = True
                event.processed_at = timezone.now()
                event.save(update_fields=["processed", "processed_at"])
                logger.info(
                    "webhook.ignored event_id=%s booking_id=%s reason=already_%s",
                    event_id,
                    booking.id,
                    booking.status,
                )
                return Response(
                    {
                        "detail": f"Booking already {booking.status}; webhook ignored to avoid corrupting state.",
                        "booking_status": booking.status,
                    },
                    status=status.HTTP_200_OK,
                )

            transaction_id = data.get("transaction_id") or f"WH-{event_id}"
            payment, payment_created = Payment.objects.get_or_create(
                transaction_id=transaction_id,
                defaults={
                    "booking": booking,
                    "amount": booking.amount,
                    "status": data["status"],
                },
            )

            booking.status = Booking.Status.CONFIRMED if data["status"] == "SUCCESS" else Booking.Status.FAILED
            booking.save(update_fields=["status", "updated_at"])

            event.processed = True
            event.processed_at = timezone.now()
            event.save(update_fields=["processed", "processed_at"])

            logger.info(
                "webhook.processed event_id=%s booking_id=%s payment_id=%s payment_created=%s new_status=%s",
                event_id,
                booking.id,
                payment.id,
                payment_created,
                booking.status,
            )

        return Response(
            {"detail": "Webhook processed.", "booking_status": booking.status}, status=status.HTTP_200_OK
        )
