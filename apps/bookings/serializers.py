from django.utils import timezone
from rest_framework import serializers

from apps.centres.models import DiagnosticTest

from .models import Booking


class BookingCreateSerializer(serializers.ModelSerializer):
    """Used only for POST /api/bookings/. centre and amount are derived server-side."""

    diagnostic_test = serializers.PrimaryKeyRelatedField(queryset=DiagnosticTest.objects.filter(is_active=True))

    class Meta:
        model = Booking
        fields = ["id", "diagnostic_test", "appointment_datetime", "status", "amount", "centre", "created_at"]
        read_only_fields = ["id", "status", "amount", "centre", "created_at"]

    def validate_appointment_datetime(self, value):
        if value <= timezone.now():
            raise serializers.ValidationError("Appointment date/time must be in the future.")
        return value

    def create(self, validated_data):
        test = validated_data["diagnostic_test"]
        validated_data["centre"] = test.centre
        validated_data["amount"] = test.price
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)


class BookingSerializer(serializers.ModelSerializer):
    """Read-only representation used for list/retrieve/cancel responses."""

    diagnostic_test_name = serializers.CharField(source="diagnostic_test.name", read_only=True)
    centre_name = serializers.CharField(source="centre.name", read_only=True)

    class Meta:
        model = Booking
        fields = [
            "id",
            "diagnostic_test",
            "diagnostic_test_name",
            "centre",
            "centre_name",
            "appointment_datetime",
            "amount",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields
