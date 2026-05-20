"""
TC-08: Pay for a ticket via Stripe test card.
Stripe is mocked — the intent flow is simulated server-side.
"""
import pytest
from unittest.mock import patch, MagicMock
from decimal import Decimal

from registrations.models import Registration, Payment
from events.models import TicketTier


@pytest.mark.django_db
class TestTC08_StripePayment:
    """TC-08: Full payment flow with mocked Stripe."""

    @patch("core.adapters.email_sender.EmailSender.send_ticket")
    @patch("core.adapters.payment_gateway.PaymentGateway.retrieve_intent_for_registration")
    @patch("core.adapters.payment_gateway.PaymentGateway.create_intent")
    def test_paid_registration_flow(
        self, mock_create, mock_retrieve, mock_email,
        auth_client_attendee, paid_tier,
    ):
        # Step 1: create registration (PENDING + client_secret)
        mock_create.return_value = "pi_test_secret_123"
        resp = auth_client_attendee.post("/api/registrations/", {
            "event_id": paid_tier.event_id,
            "ticket_tier_id": paid_tier.pk,
        })
        assert resp.status_code == 201
        assert resp.data["status"] == "PENDING"
        reg_id = resp.data["id"]

        # Step 2: simulate Stripe payment success, then confirm
        mock_retrieve.return_value = {
            "id": "pi_test_abc123",
            "status": "succeeded",
        }
        resp = auth_client_attendee.post(f"/api/registrations/{reg_id}/confirm/")
        assert resp.status_code == 200
        assert resp.data["status"] == "CONFIRMED"

        # Verify Payment row created
        payment = Payment.objects.get(registration_id=reg_id)
        assert payment.status == "SUCCEEDED"
        assert payment.gateway_ref == "pi_test_abc123"
        assert payment.amount == Decimal("20.00")

        # Verify inventory decremented
        paid_tier.refresh_from_db()
        assert paid_tier.quantity_sold == 1

        # Verify email sent
        mock_email.assert_called_once()
