"""
Registration repository — all database access for Registration, Payment, CheckIn, Feedback.
"""
from django.db.models import Avg, Count, Sum, Q
from registrations.models import Registration, Payment, CheckIn, Feedback


class RegistrationRepo:
    @staticmethod
    def create_registration(attendee, ticket_tier, status="PENDING", qr_code=""):
        return Registration.objects.create(
            attendee=attendee,
            ticket_tier=ticket_tier,
            status=status,
            qr_code=qr_code,
        )

    @staticmethod
    def get_by_id(registration_id):
        return Registration.objects.select_related(
            "attendee__user", "ticket_tier__event"
        ).get(pk=registration_id)

    @staticmethod
    def get_by_qr(qr_token):
        return Registration.objects.select_related(
            "attendee__user", "ticket_tier__event"
        ).get(qr_code=qr_token, status=Registration.STATUS_CONFIRMED)

    @staticmethod
    def get_attendee_registrations(attendee):
        return Registration.objects.filter(attendee=attendee).select_related(
            "ticket_tier__event", "payment"
        ).order_by("-registered_at")

    @staticmethod
    def create_payment(registration, amount, gateway_ref, status, paid_at=None):
        return Payment.objects.create(
            registration=registration,
            amount=amount,
            gateway_ref=gateway_ref,
            status=status,
            paid_at=paid_at,
        )

    @staticmethod
    def create_checkin(registration, method="QR_SCAN"):
        return CheckIn.objects.create(registration=registration, method=method)

    @staticmethod
    def is_checked_in(registration_id):
        return CheckIn.objects.filter(registration_id=registration_id).exists()

    @staticmethod
    def create_feedback(registration, rating, comment=""):
        return Feedback.objects.create(
            registration=registration, rating=rating, comment=comment
        )

    @staticmethod
    def event_analytics(event_id):
        """Aggregate analytics for a single event (FR-15)."""
        from events.models import TicketTier

        tiers = TicketTier.objects.filter(event_id=event_id)
        tier_ids = tiers.values_list("id", flat=True)

        confirmed = Registration.objects.filter(
            ticket_tier_id__in=tier_ids, status=Registration.STATUS_CONFIRMED
        )
        total_sold = confirmed.count()
        revenue = Payment.objects.filter(
            registration__in=confirmed, status="SUCCEEDED"
        ).aggregate(total=Sum("amount"))["total"] or 0

        checkins = CheckIn.objects.filter(registration__in=confirmed).count()
        check_in_rate = (checkins / total_sold * 100) if total_sold > 0 else 0

        avg_rating = Feedback.objects.filter(
            registration__in=confirmed
        ).aggregate(avg=Avg("rating"))["avg"] or 0

        tier_breakdown = []
        for tier in tiers:
            tier_breakdown.append({
                "tier_id": tier.id,
                "tier_name": tier.tier_name,
                "price": str(tier.price),
                "quantity_total": tier.quantity_total,
                "quantity_sold": tier.quantity_sold,
            })

        return {
            "tickets_sold": total_sold,
            "revenue": str(revenue),
            "check_in_rate": round(check_in_rate, 1),
            "average_rating": round(float(avg_rating), 1),
            "registrations_by_tier": tier_breakdown,
        }

    @staticmethod
    def confirmed_attendees_for_export(event_id):
        """Return confirmed registrations for CSV export (FR-16)."""
        from events.models import TicketTier

        tier_ids = TicketTier.objects.filter(event_id=event_id).values_list("id", flat=True)
        return (
            Registration.objects.filter(
                ticket_tier_id__in=tier_ids, status=Registration.STATUS_CONFIRMED
            )
            .select_related("attendee__user", "ticket_tier", "payment", "check_in")
            .order_by("registered_at")
        )
