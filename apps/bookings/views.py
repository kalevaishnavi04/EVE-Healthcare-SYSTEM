from django.utils import timezone
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Booking
from .permissions import IsOwner
from .serializers import BookingCreateSerializer, BookingSerializer


class BookingViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """
    POST   /api/bookings/            create a booking (PENDING) for the current user
    GET    /api/bookings/            list the current user's bookings
    GET    /api/bookings/{id}/       retrieve one of the current user's bookings
    POST   /api/bookings/{id}/cancel/ cancel a PENDING/CONFIRMED booking

    Update/delete are intentionally not exposed: a booking's lifecycle is
    driven only by cancel/payment/webhook, never by a raw PATCH/PUT, so the
    status machine can't be corrupted by an arbitrary field update.
    """

    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def get_queryset(self):
        # Scoping the queryset to the requesting user means a request for
        # someone else's booking id naturally 404s instead of leaking
        # whether that booking exists (belt-and-braces with IsOwner).
        return Booking.objects.filter(user=self.request.user).select_related("diagnostic_test", "centre")

    def get_serializer_class(self):
        if self.action == "create":
            return BookingCreateSerializer
        return BookingSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        booking = serializer.save()
        return Response(BookingSerializer(booking).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        booking = self.get_object()

        if booking.status not in (Booking.Status.PENDING, Booking.Status.CONFIRMED):
            return Response(
                {"detail": f"A booking with status {booking.status} cannot be cancelled."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if booking.appointment_datetime <= timezone.now():
            return Response({"detail": "Cannot cancel a past appointment."}, status=status.HTTP_400_BAD_REQUEST)

        booking.status = Booking.Status.CANCELLED
        booking.save(update_fields=["status", "updated_at"])
        return Response(BookingSerializer(booking).data)
