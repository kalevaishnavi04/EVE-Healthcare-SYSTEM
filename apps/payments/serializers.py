from rest_framework import serializers

from .models import Payment


class PaymentCreateSerializer(serializers.Serializer):
    booking_id = serializers.UUIDField()


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ["id", "booking", "amount", "status", "transaction_id", "created_at"]
        read_only_fields = fields


class WebhookSerializer(serializers.Serializer):
    """
    Shape of the payload a simulated payment provider sends us.
    event_id must be unique per delivery attempt-set (the provider is
    expected to reuse the same event_id when retrying the same event).
    """

    event_id = serializers.CharField(max_length=128)
    booking_id = serializers.UUIDField()
    status = serializers.ChoiceField(choices=["SUCCESS", "FAILED"])
    transaction_id = serializers.CharField(max_length=64, required=False, allow_blank=False)
