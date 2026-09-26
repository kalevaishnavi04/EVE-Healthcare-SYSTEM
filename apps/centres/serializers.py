from rest_framework import serializers

from .models import DiagnosticCentre, DiagnosticTest


class DiagnosticTestSerializer(serializers.ModelSerializer):
    centre_name = serializers.CharField(source="centre.name", read_only=True)

    class Meta:
        model = DiagnosticTest
        fields = ["id", "centre", "centre_name", "name", "description", "price", "is_active", "created_at"]
        read_only_fields = ["id", "created_at"]

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than zero.")
        return value


class DiagnosticTestNestedSerializer(serializers.ModelSerializer):
    """Used when nesting tests inside a centre response (no repeated centre field)."""

    class Meta:
        model = DiagnosticTest
        fields = ["id", "name", "description", "price", "is_active"]


class DiagnosticCentreSerializer(serializers.ModelSerializer):
    tests = DiagnosticTestNestedSerializer(many=True, read_only=True)

    class Meta:
        model = DiagnosticCentre
        fields = ["id", "name", "location", "address", "is_active", "tests", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]
