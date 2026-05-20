"""Registrations serializers."""
from rest_framework import serializers
from .models import Registration, Payment, CheckIn, Feedback


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ["id", "amount", "gateway_ref", "status", "paid_at"]
        read_only_fields = fields


class CheckInSerializer(serializers.ModelSerializer):
    class Meta:
        model = CheckIn
        fields = ["id", "registration_id", "checked_in_at", "method"]
        read_only_fields = fields


class RegistrationSerializer(serializers.ModelSerializer):
    event_title = serializers.CharField(source="ticket_tier.event.title", read_only=True)
    event_id = serializers.IntegerField(source="ticket_tier.event.id", read_only=True)
    tier_name = serializers.CharField(source="ticket_tier.tier_name", read_only=True)
    attendee_name = serializers.CharField(source="attendee.user.full_name", read_only=True)
    attendee_email = serializers.CharField(source="attendee.user.email", read_only=True)
    payment = PaymentSerializer(read_only=True)
    is_checked_in = serializers.SerializerMethodField()

    class Meta:
        model = Registration
        fields = [
            "id", "attendee_name", "attendee_email",
            "event_id", "event_title", "tier_name",
            "status", "qr_code", "registered_at",
            "payment", "is_checked_in",
        ]
        read_only_fields = fields

    def get_is_checked_in(self, obj):
        return hasattr(obj, "check_in")


class CreateRegistrationSerializer(serializers.Serializer):
    event_id = serializers.IntegerField()
    ticket_tier_id = serializers.IntegerField()


class CheckInRequestSerializer(serializers.Serializer):
    qr_token = serializers.CharField(max_length=64)


class FeedbackCreateSerializer(serializers.Serializer):
    registration_id = serializers.IntegerField()
    rating = serializers.IntegerField(min_value=1, max_value=5)
    comment = serializers.CharField(required=False, default="", allow_blank=True)
