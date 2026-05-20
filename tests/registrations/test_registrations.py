"""
Test cases for registrations — TC-06, TC-07, TC-09, TC-11, TC-12.
TC-08 (Stripe payment) requires Stripe mock and is in a separate file.
"""
import pytest
from unittest.mock import patch
from registrations.models import Registration, CheckIn
from events.models import TicketTier


@pytest.mark.django_db
class TestTC06_FreeRegistration:
    """TC-06: Register for a free event; inventory decrements; email sent."""

    @patch("core.adapters.email_sender.EmailSender.send_ticket")
    def test_free_registration(self, mock_email, auth_client_attendee, free_tier):
        resp = auth_client_attendee.post("/api/registrations/", {
            "event_id": free_tier.event_id,
            "ticket_tier_id": free_tier.pk,
        })
        assert resp.status_code == 201
        assert resp.data["status"] == "CONFIRMED"
        assert resp.data["qr_code"] != ""
        assert "client_secret" not in resp.data

        # Inventory decremented
        free_tier.refresh_from_db()
        assert free_tier.quantity_sold == 1

        # Email sent
        mock_email.assert_called_once()


@pytest.mark.django_db
class TestTC07_CapacityExhausted:
    """TC-07: Reject registration when capacity is zero."""

    def test_sold_out_rejected(self, auth_client_attendee, sold_out_tier):
        resp = auth_client_attendee.post("/api/registrations/", {
            "event_id": sold_out_tier.event_id,
            "ticket_tier_id": sold_out_tier.pk,
        })
        assert resp.status_code == 409
        assert resp.data["error"] == "capacity_exhausted"


@pytest.mark.django_db
class TestTC09_FailedPaymentPending:
    """TC-09: Failed payment leaves registration in PENDING."""

    @patch("core.adapters.payment_gateway.PaymentGateway.create_intent")
    def test_pending_after_intent_created(self, mock_intent, auth_client_attendee, paid_tier):
        mock_intent.return_value = "pi_test_client_secret"
        resp = auth_client_attendee.post("/api/registrations/", {
            "event_id": paid_tier.event_id,
            "ticket_tier_id": paid_tier.pk,
        })
        assert resp.status_code == 201
        assert resp.data["status"] == "PENDING"
        assert resp.data["client_secret"] == "pi_test_client_secret"

        # Inventory NOT decremented yet (decremented only on confirm)
        paid_tier.refresh_from_db()
        assert paid_tier.quantity_sold == 0


@pytest.mark.django_db
class TestTC11_ValidCheckIn:
    """TC-11: Valid QR scan marks attendee CHECKED_IN."""

    def test_checkin_success(self, auth_client_attendee, confirmed_registration):
        resp = auth_client_attendee.post("/api/checkins/", {
            "qr_token": confirmed_registration.qr_code,
        })
        assert resp.status_code == 200
        assert CheckIn.objects.filter(
            registration=confirmed_registration
        ).exists()


@pytest.mark.django_db
class TestTC12_DuplicateCheckIn:
    """TC-12: Duplicate check-in returns HTTP 409."""

    def test_duplicate_rejected(self, auth_client_attendee, checked_in_registration):
        resp = auth_client_attendee.post("/api/checkins/", {
            "qr_token": checked_in_registration.qr_code,
        })
        assert resp.status_code == 409
        assert resp.data["error"] == "already_checked_in"

        # No new CheckIn row created
        assert CheckIn.objects.filter(
            registration=checked_in_registration
        ).count() == 1
