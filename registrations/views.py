"""
Registrations views — thin views delegating to service layer.
"""
from datetime import timedelta

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from core.services.register_for_event import (
    RegisterForEventService,
    ConfirmRegistrationService,
)
from core.services.check_in_attendee import CheckInAttendeeService
from core.repositories.registration_repo import RegistrationRepo
from .models import Registration
from .serializers import (
    RegistrationSerializer,
    CreateRegistrationSerializer,
    CheckInRequestSerializer,
    CheckInSerializer,
    FeedbackCreateSerializer,
)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def registration_create(request):
    """
    POST /api/registrations/ — FR-08, FR-09, FR-10.
    Delegates to RegisterForEventService.
    """
    serializer = CreateRegistrationSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    if not hasattr(request.user, "attendee"):
        return Response(
            {"error": "not_attendee", "detail": "Only attendees can register for events."},
            status=status.HTTP_403_FORBIDDEN,
        )

    registration, client_secret = RegisterForEventService.execute(
        attendee=request.user.attendee,
        ticket_tier_id=serializer.validated_data["ticket_tier_id"],
    )

    data = RegistrationSerializer(registration).data
    if client_secret:
        data["client_secret"] = client_secret
    return Response(data, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def registration_confirm(request, pk):
    """
    POST /api/registrations/{id}/confirm/ — steps 7-12 of sequence diagram.
    Verifies PaymentIntent server-side, then confirms.
    """
    registration = get_object_or_404(Registration, pk=pk)

    # Ownership check
    if registration.attendee.user_id != request.user.pk:
        return Response(
            {"error": "permission_denied", "detail": "Not your registration."},
            status=status.HTTP_403_FORBIDDEN,
        )

    confirmed = ConfirmRegistrationService.execute(registration.pk)
    return Response(RegistrationSerializer(confirmed).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def registration_cancel(request, pk):
    """POST /api/registrations/{id}/cancel/ — attendee cancels own registration."""
    registration = get_object_or_404(
        Registration.objects.select_related("attendee__user", "ticket_tier"),
        pk=pk,
    )
    if registration.attendee.user_id != request.user.pk:
        return Response(
            {"error": "permission_denied", "detail": "Not your registration."},
            status=status.HTTP_403_FORBIDDEN,
        )
    if registration.status not in ("PENDING", "CONFIRMED"):
        return Response(
            {"error": "invalid_state", "detail": "Cannot cancel this registration."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    registration.cancel()
    return Response(RegistrationSerializer(registration).data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_registrations(request):
    """GET /api/me/registrations/ — list current attendee's registrations."""
    if not hasattr(request.user, "attendee"):
        return Response([], status=status.HTTP_200_OK)
    regs = RegistrationRepo.get_attendee_registrations(request.user.attendee)
    return Response(RegistrationSerializer(regs, many=True).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def checkin_create(request):
    """
    POST /api/checkins/ — FR-12, FR-13.
    Staff endpoint. Returns 409 on duplicate (TC-12).
    """
    serializer = CheckInRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    checkin = CheckInAttendeeService.execute(
        qr_token=serializer.validated_data["qr_token"],
    )
    return Response(CheckInSerializer(checkin).data, status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def feedback_create(request):
    """
    POST /api/feedback/ — FR-14: rating + comment within 14 days.
    Validates that check-in exists and event ended within 14 days.
    """
    serializer = FeedbackCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    registration = get_object_or_404(
        Registration.objects.select_related("ticket_tier__event", "attendee__user"),
        pk=serializer.validated_data["registration_id"],
    )

    # Must be the attendee's own registration
    if registration.attendee.user_id != request.user.pk:
        return Response(
            {"error": "permission_denied", "detail": "Not your registration."},
            status=status.HTTP_403_FORBIDDEN,
        )

    # Must have checked in
    if not hasattr(registration, "check_in"):
        return Response(
            {"error": "not_attended", "detail": "You must check in before leaving feedback."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Must be within 14 days of event end
    event = registration.ticket_tier.event
    if timezone.now() > event.end_time + timedelta(days=14):
        return Response(
            {"error": "feedback_window_closed", "detail": "Feedback window (14 days) has closed."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Already submitted?
    if hasattr(registration, "feedback"):
        return Response(
            {"error": "already_submitted", "detail": "Feedback already submitted."},
            status=status.HTTP_409_CONFLICT,
        )

    feedback = RegistrationRepo.create_feedback(
        registration=registration,
        rating=serializer.validated_data["rating"],
        comment=serializer.validated_data.get("comment", ""),
    )

    return Response(
        {"id": feedback.pk, "rating": feedback.rating, "comment": feedback.comment},
        status=status.HTTP_201_CREATED,
    )
