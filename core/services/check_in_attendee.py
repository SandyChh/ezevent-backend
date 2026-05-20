"""
CheckInAttendee service (Service-Layer Pattern — report Section 4.2.2).
Handles QR scan at venue. Enforces FR-12 (check-in) and FR-13 (no duplicate).
TC-11: valid scan → CHECKED_IN.
TC-12: duplicate scan → HTTP 409.
"""
import logging
from django.db import IntegrityError

from core.exceptions import (
    AlreadyCheckedInError,
    InvalidQRError,
    RegistrationNotConfirmedError,
)
from core.repositories.registration_repo import RegistrationRepo
from registrations.models import Registration

logger = logging.getLogger("eventease")


class CheckInAttendeeService:
    @staticmethod
    def execute(qr_token, method="QR_SCAN"):
        """
        Look up registration by qr_token, create CheckIn row.
        Returns the CheckIn object on success.
        Raises AlreadyCheckedInError (409) if duplicate.
        Raises InvalidQRError (404) if token not found.
        Raises RegistrationNotConfirmedError (410) if not confirmed.
        """
        try:
            registration = Registration.objects.select_related(
                "attendee__user", "ticket_tier__event"
            ).get(qr_code=qr_token)
        except Registration.DoesNotExist:
            raise InvalidQRError()

        if registration.status != Registration.STATUS_CONFIRMED:
            raise RegistrationNotConfirmedError()

        # The UNIQUE constraint on CheckIn.registration enforces FR-13
        if RegistrationRepo.is_checked_in(registration.pk):
            raise AlreadyCheckedInError()

        try:
            checkin = RegistrationRepo.create_checkin(registration, method=method)
        except IntegrityError:
            # Race condition safety net — unique constraint caught at DB level
            raise AlreadyCheckedInError()

        logger.info(
            "Attendee checked in",
            extra={
                "event_type": "check_in",
                "user_id": registration.attendee.user.pk,
                "registration_id": registration.pk,
            },
        )
        return checkin
