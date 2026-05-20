"""
Stripe webhook handler.
Handles payment_intent.succeeded and payment_intent.payment_failed.
This is the production-grade confirmation path that survives the user
closing the browser between steps 6 and 7 of the sequence diagram.
"""
import logging
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.db import transaction
from django.utils import timezone

from core.adapters.payment_gateway import PaymentGateway
from core.repositories.event_repo import EventRepo
from core.repositories.registration_repo import RegistrationRepo
from core.adapters.email_sender import EmailSender
from registrations.models import Registration

logger = logging.getLogger("eventease")


@csrf_exempt
@require_POST
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE", "")

    try:
        event = PaymentGateway.construct_webhook_event(payload, sig_header)
    except Exception as e:
        logger.warning("Stripe webhook signature verification failed: %s", str(e))
        return HttpResponse(status=400)

    event_type = event["type"]
    data_object = event["data"]["object"]

    if event_type == "payment_intent.succeeded":
        _handle_payment_succeeded(data_object)
    elif event_type == "payment_intent.payment_failed":
        _handle_payment_failed(data_object)

    return HttpResponse(status=200)


def _handle_payment_succeeded(payment_intent):
    """
    Webhook path for successful payment.
    Steps 8-12 of the sequence diagram, triggered by Stripe rather than the client.
    Idempotent — if the registration is already CONFIRMED, skip.
    """
    registration_id = payment_intent.get("metadata", {}).get("registration_id")
    if not registration_id:
        logger.warning("payment_intent.succeeded without registration_id in metadata")
        return

    try:
        with transaction.atomic():
            registration = Registration.objects.select_related(
                "attendee__user", "ticket_tier__event", "ticket_tier"
            ).select_for_update().get(pk=int(registration_id))

            # Idempotency: already confirmed (client path beat the webhook)
            if registration.status == Registration.STATUS_CONFIRMED:
                return

            if registration.status != Registration.STATUS_PENDING:
                logger.warning(
                    "Webhook: registration %s in unexpected status %s",
                    registration_id, registration.status,
                )
                return

            tier = EventRepo.get_tier(registration.ticket_tier_id)

            # Confirm registration
            registration.status = Registration.STATUS_CONFIRMED
            registration.save(update_fields=["status"])

            # Decrement inventory atomically
            EventRepo.decrement_inventory(tier)

            # Create Payment record
            RegistrationRepo.create_payment(
                registration=registration,
                amount=tier.price,
                gateway_ref=payment_intent["id"],
                status="SUCCEEDED",
                paid_at=timezone.now(),
            )

        # Send ticket email outside the atomic block
        EmailSender.send_ticket(
            to_email=registration.attendee.user.email,
            registration=registration,
        )

        logger.info(
            "Webhook: registration confirmed via payment_intent.succeeded",
            extra={
                "event_type": "registration_confirmed_webhook",
                "user_id": registration.attendee.user.pk,
                "registration_id": registration.pk,
                "payment_ref": payment_intent["id"],
            },
        )

    except Registration.DoesNotExist:
        logger.error("Webhook: registration %s not found", registration_id)
    except Exception:
        logger.exception("Webhook: error processing payment_intent.succeeded for reg %s", registration_id)


def _handle_payment_failed(payment_intent):
    """Log the failure. Registration stays in PENDING — the client shows an error."""
    registration_id = payment_intent.get("metadata", {}).get("registration_id")
    logger.info(
        "Webhook: payment_intent.payment_failed",
        extra={
            "event_type": "payment_failed",
            "registration_id": registration_id,
            "payment_ref": payment_intent.get("id", ""),
        },
    )
