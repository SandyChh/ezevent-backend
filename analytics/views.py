"""
Analytics views — FR-15 (dashboard) and FR-16 (CSV export).
Organizer-only endpoints with ownership checks.
"""
import csv
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status as http_status

from core.permissions import IsOrganizer
from core.repositories.registration_repo import RegistrationRepo
from events.models import Event


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsOrganizer])
def event_analytics(request, event_id):
    """
    GET /api/events/{id}/analytics/ — FR-15.
    Returns tickets_sold, revenue, check_in_rate, average_rating, registrations_by_tier.
    """
    event = get_object_or_404(Event, pk=event_id)
    if event.organizer_id != request.user.organizer.pk:
        return Response(
            {"error": "permission_denied", "detail": "You do not own this event."},
            status=http_status.HTTP_403_FORBIDDEN,
        )
    data = RegistrationRepo.event_analytics(event_id)
    return Response(data)


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsOrganizer])
def attendee_csv_export(request, event_id):
    """
    GET /api/events/{id}/attendees.csv — FR-16.
    Returns a CSV file with one row per confirmed registration.
    """
    event = get_object_or_404(Event, pk=event_id)
    if event.organizer_id != request.user.organizer.pk:
        return Response(
            {"error": "permission_denied", "detail": "You do not own this event."},
            status=http_status.HTTP_403_FORBIDDEN,
        )

    registrations = RegistrationRepo.confirmed_attendees_for_export(event_id)

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="attendees_event_{event_id}.csv"'

    writer = csv.writer(response)
    writer.writerow([
        "Registration ID", "Attendee Name", "Email",
        "Tier", "Amount Paid", "Registered At",
        "Checked In", "Check-In Time",
    ])

    for reg in registrations:
        checked_in = hasattr(reg, "check_in")
        checkin_time = reg.check_in.checked_in_at.isoformat() if checked_in else ""
        amount = reg.payment.amount if hasattr(reg, "payment") else "0.00"
        writer.writerow([
            reg.pk,
            reg.attendee.user.full_name,
            reg.attendee.user.email,
            reg.ticket_tier.tier_name,
            str(amount),
            reg.registered_at.isoformat(),
            "Yes" if checked_in else "No",
            checkin_time,
        ])

    return response
