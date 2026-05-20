"""
Event repository — all database access for Event, Session, TicketTier.
Business logic must NEVER import Django QuerySets directly (report Section 4.2.2).
"""
from django.db.models import Q, Sum, F
from events.models import Event, Session, TicketTier


class EventRepo:
    @staticmethod
    def get_published_events(search=None, ordering="start_time"):
        qs = Event.objects.filter(status=Event.STATUS_PUBLISHED).select_related("organizer__user")
        if search:
            qs = qs.filter(Q(title__icontains=search) | Q(description__icontains=search))
        return qs.order_by(ordering)

    @staticmethod
    def get_by_id(event_id):
        return (
            Event.objects.select_related("organizer__user")
            .prefetch_related("sessions", "ticket_tiers")
            .get(pk=event_id)
        )

    @staticmethod
    def create_event(organizer, **kwargs):
        return Event.objects.create(organizer=organizer, **kwargs)

    @staticmethod
    def get_sessions(event_id):
        return Session.objects.filter(event_id=event_id).order_by("start_time")

    @staticmethod
    def create_session(event, **kwargs):
        return Session.objects.create(event=event, **kwargs)

    @staticmethod
    def get_tier(tier_id):
        return TicketTier.objects.select_for_update().get(pk=tier_id)

    @staticmethod
    def create_tier(event, **kwargs):
        return TicketTier.objects.create(event=event, **kwargs)

    @staticmethod
    def remaining_capacity(tier):
        return tier.quantity_total - tier.quantity_sold

    @staticmethod
    def decrement_inventory(tier):
        """Atomically increment quantity_sold by 1."""
        TicketTier.objects.filter(pk=tier.pk).update(quantity_sold=F("quantity_sold") + 1)
        tier.refresh_from_db()
