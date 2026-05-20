"""
PaymentGateway adapter (Adapter Pattern — report Section 4.2.2).
Wraps the Stripe SDK so business logic never imports stripe directly.
Swappable for a fake in tests.
"""
import stripe
from django.conf import settings


class PaymentGateway:
    @staticmethod
    def _configure():
        stripe.api_key = settings.STRIPE_SECRET_KEY

    @classmethod
    def create_intent(cls, amount, currency="aud", idempotency_key=None, metadata=None):
        """
        Create a Stripe PaymentIntent and return its client_secret.
        Amount is a Decimal — Stripe expects an integer in the smallest unit (cents).
        """
        cls._configure()
        amount_cents = int(amount * 100)
        intent = stripe.PaymentIntent.create(
            amount=amount_cents,
            currency=currency,
            metadata=metadata or {},
            idempotency_key=idempotency_key,
        )
        return intent.client_secret
    
    @classmethod
    def retrieve_intent(cls, payment_intent_id):
        """
        Retrieve a specific PaymentIntent by ID.
        Used in step 8 of the sequence diagram for server-side verification.
        Returns a dict with 'id' and 'status', or None.
        """
        if not payment_intent_id:
            return None
        cls._configure()
        try:
            pi = stripe.PaymentIntent.retrieve(payment_intent_id)
            return {"id": pi.id, "status": pi.status}
        except Exception:
            return None

    @classmethod
    def retrieve_intent_for_registration(cls, registration_id):
        """
        Search for a succeeded PaymentIntent whose metadata.registration_id matches.
        Used in step 8 of the sequence diagram for server-side verification.
        Returns a dict with 'id' and 'status', or None.
        """
        cls._configure()
        # Search recent PaymentIntents by metadata
        intents = stripe.PaymentIntent.search(
            query=f"metadata['registration_id']:'{registration_id}'",
            limit=1,
        )
        if intents.data:
            pi = intents.data[0]
            return {"id": pi.id, "status": pi.status}
        return None

    @classmethod
    def construct_webhook_event(cls, payload, sig_header):
        """Verify and parse a Stripe webhook event."""
        cls._configure()
        return stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )

    @classmethod
    def refund(cls, payment_intent_id, reason="requested_by_customer"):
        """Issue a refund for a PaymentIntent (FR-18)."""
        cls._configure()
        return stripe.Refund.create(
            payment_intent=payment_intent_id,
            reason=reason,
        )
