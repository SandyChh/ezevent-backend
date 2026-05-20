"""
RegisterForEvent service (Service-Layer Pattern — report Section 4.2.2).
Implements the 12-step sequence diagram from Appendix B.2.
"""
import uuid
import logging
from django.db import transaction
from django.utils import timezone

from core.exceptions import CapacityExhaustedError, PaymentFailedError
from core.repositories.event_repo import EventRepo
from core.repositories.registration_repo import RegistrationRepo
from core.adapters.payment_gateway import PaymentGateway
from core.adapters.email_sender import EmailSender

logger = logging.getLogger("eventease")


class RegisterForEventService:
    """
    Use-case service: register an attendee for an event.

    Two paths:
      - Free tier (price == 0): confirm immediately, send email.
      - Paid tier (price > 0): create PENDING registration, return Stripe client_secret.
        Client confirms payment, then calls ConfirmRegistrationService.
    """

    @staticmethod
    def execute(attendee, ticket_tier_id):
        """
        Step 2-4 of the sequence diagram.
        Returns (registration, client_secret_or_none).
        """
        with transaction.atomic():
            tier = EventRepo.get_tier(ticket_tier_id)  # SELECT … FOR UPDATE

            # Check capacity (TC-07)
            if EventRepo.remaining_capacity(tier) <= 0:
                raise CapacityExhaustedError()

            qr_token = uuid.uuid4().hex

            if tier.price == 0:
                # Free tier — confirm immediately
                registration = RegistrationRepo.create_registration(
                    attendee=attendee,
                    ticket_tier=tier,
                    status="CONFIRMED",
                    qr_code=qr_token,
                )
                EventRepo.decrement_inventory(tier)
                RegistrationRepo.create_payment(
                    registration=registration,
                    amount=0,
                    gateway_ref="free",
                    status="SUCCEEDED",
                    paid_at=timezone.now(),
                )
                # Send ticket email (step 9-11)
                EmailSender.send_ticket(
                    to_email=attendee.user.email,
                    registration=registration,
                )
                logger.info(
                    "Free registration confirmed",
                    extra={
                        "event_type": "registration_confirmed",
                        "user_id": attendee.user.pk,
                        "registration_id": registration.pk,
                    },
                )
                return registration, None
            else:
                # Paid tier — create PENDING, return Stripe client_secret
                registration = RegistrationRepo.create_registration(
                    attendee=attendee,
                    ticket_tier=tier,
                    status="PENDING",
                    qr_code=qr_token,
                )
                client_secret = PaymentGateway.create_intent(
                    amount=tier.price,
                    currency="aud",
                    idempotency_key=f"reg-{registration.pk}",
                    metadata={"registration_id": str(registration.pk)},
                )
                logger.info(
                    "Paid registration pending payment",
                    extra={
                        "event_type": "registration_pending",
                        "user_id": attendee.user.pk,
                        "registration_id": registration.pk,
                    },
                )
                return registration, client_secret


class ConfirmRegistrationService:
    """
    Steps 7-12 of the sequence diagram.
    Called after the frontend confirms Stripe payment succeeded.
    Verifies the PaymentIntent server-side (do NOT trust the client).
    """

    @staticmethod
    def execute(registration_id):
        with transaction.atomic():
            registration = RegistrationRepo.get_by_id(registration_id)

            if registration.status != "PENDING":
                raise PaymentFailedError("Registration is not in PENDING status.")

            tier = EventRepo.get_tier(registration.ticket_tier_id)

            # Check capacity again inside the atomic block
            if EventRepo.remaining_capacity(tier) <= 0:
                raise CapacityExhaustedError()

            # Step 8: verify PaymentIntent server-side via Stripe
            intent = PaymentGateway.retrieve_intent_for_registration(registration.pk)
            if not intent or intent.get("status") != "succeeded":
                raise PaymentFailedError()

            # Confirm registration
            registration.status = "CONFIRMED"
            registration.save(update_fields=["status"])

            # Decrement inventory atomically
            EventRepo.decrement_inventory(tier)

            # Create Payment record
            RegistrationRepo.create_payment(
                registration=registration,
                amount=tier.price,
                gateway_ref=intent.get("id", ""),
                status="SUCCEEDED",
                paid_at=timezone.now(),
            )

            # Send ticket email (step 9-11)
            EmailSender.send_ticket(
                to_email=registration.attendee.user.email,
                registration=registration,
            )

            logger.info(
                "Paid registration confirmed",
                extra={
                    "event_type": "registration_confirmed",
                    "user_id": registration.attendee.user.pk,
                    "registration_id": registration.pk,
                    "payment_ref": intent.get("id", ""),
                },
            )
            return registration
