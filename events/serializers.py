"""Events serializers."""
from rest_framework import serializers
from .models import Event, Session, TicketTier


class SessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Session
        fields = ["id", "event", "title", "speaker", "start_time", "duration_minutes"]
        read_only_fields = ["id"]
        extra_kwargs = {"event": {"required": False}}


class TicketTierSerializer(serializers.ModelSerializer):
    quantity_remaining = serializers.IntegerField(read_only=True)

    class Meta:
        model = TicketTier
        fields = [
            "id", "event", "tier_name", "price",
            "quantity_total", "quantity_sold", "quantity_remaining",
        ]
        read_only_fields = ["id", "quantity_sold", "quantity_remaining"]
        extra_kwargs = {"event": {"required": False}}


class EventListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for the public event list (FR-06)."""
    organizer_name = serializers.CharField(source="organizer.organisation_name", read_only=True)
    min_price = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = [
            "id", "title", "description", "start_time", "end_time",
            "venue", "capacity", "status", "organizer_name", "min_price",
        ]

    def get_min_price(self, obj):
        tiers = obj.ticket_tiers.all()
        if tiers:
            return str(min(t.price for t in tiers))
        return None


class EventDetailSerializer(serializers.ModelSerializer):
    """Full detail with sessions and tiers for event detail page."""
    organizer_name = serializers.CharField(source="organizer.organisation_name", read_only=True)
    sessions = SessionSerializer(many=True, read_only=True)
    ticket_tiers = TicketTierSerializer(many=True, read_only=True)

    class Meta:
        model = Event
        fields = [
            "id", "title", "description", "start_time", "end_time",
            "venue", "capacity", "status", "organizer_name",
            "sessions", "ticket_tiers",
        ]


class EventCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating events (FR-02)."""

    class Meta:
        model = Event
        fields = [
            "id", "title", "description", "start_time", "end_time",
            "venue", "capacity", "status",
        ]
        read_only_fields = ["id"]

    def validate(self, data):
        start = data.get("start_time")
        end = data.get("end_time")
        if start and end and end <= start:
            raise serializers.ValidationError(
                {"end_time": "End time must be after start time."}
            )
        return data
