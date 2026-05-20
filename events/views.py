"""
Events views — thin views delegating to repos/serializers.
All write operations require authentication and ownership (A01 mitigation).
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from core.permissions import IsOrganizer, IsOrganizerOwner
from core.repositories.event_repo import EventRepo
from .models import Event, Session, TicketTier
from .serializers import (
    EventListSerializer,
    EventDetailSerializer,
    EventCreateSerializer,
    SessionSerializer,
    TicketTierSerializer,
)


# ---------- Events ----------

@api_view(["GET", "POST"])
def event_list_create(request):
    """
    GET  /api/events/ — public list of published events (FR-06, FR-07).
    POST /api/events/ — create event (organizer only, FR-02).
    """
    if request.method == "GET":
        search = request.query_params.get("search")
        ordering = request.query_params.get("ordering", "start_time")
        if ordering not in ("start_time", "-start_time", "title"):
            ordering = "start_time"
        events = EventRepo.get_published_events(search=search, ordering=ordering)
        # Prefetch tiers for min_price
        events = events.prefetch_related("ticket_tiers")
        serializer = EventListSerializer(events, many=True)
        return Response(serializer.data)

    # POST — create
    if not request.user.is_authenticated or request.user.role != "ORGANIZER":
        return Response(
            {"error": "permission_denied", "detail": "Only organizers can create events."},
            status=status.HTTP_403_FORBIDDEN,
        )
    serializer = EventCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    event = serializer.save(organizer=request.user.organizer)
    return Response(EventDetailSerializer(event).data, status=status.HTTP_201_CREATED)


@api_view(["GET", "PATCH"])
def event_detail(request, pk):
    """
    GET  /api/events/{id}/ — event detail with sessions and tiers.
    PATCH /api/events/{id}/ — update event (owner organizer only).
    """
    event = get_object_or_404(
        Event.objects.select_related("organizer__user").prefetch_related("sessions", "ticket_tiers"),
        pk=pk,
    )
    if request.method == "GET":
        return Response(EventDetailSerializer(event).data)

    # PATCH — update (ownership check)
    if not request.user.is_authenticated or not hasattr(request.user, "organizer"):
        return Response(
            {"error": "permission_denied", "detail": "Only the owning organizer can edit."},
            status=status.HTTP_403_FORBIDDEN,
        )
    if event.organizer_id != request.user.organizer.pk:
        return Response(
            {"error": "permission_denied", "detail": "You do not own this event."},
            status=status.HTTP_403_FORBIDDEN,
        )
    serializer = EventCreateSerializer(event, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(EventDetailSerializer(event).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated, IsOrganizer])
def event_publish(request, pk):
    """POST /api/events/{id}/publish/ — FR-03: DRAFT → PUBLISHED."""
    event = get_object_or_404(Event, pk=pk)
    if event.organizer_id != request.user.organizer.pk:
        return Response(
            {"error": "permission_denied", "detail": "You do not own this event."},
            status=status.HTTP_403_FORBIDDEN,
        )
    if event.status != Event.STATUS_DRAFT:
        return Response(
            {"error": "invalid_state", "detail": "Only draft events can be published."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    event.publish()
    return Response(EventDetailSerializer(event).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated, IsOrganizer])
def event_cancel(request, pk):
    """POST /api/events/{id}/cancel/ — cancel event."""
    event = get_object_or_404(Event, pk=pk)
    if event.organizer_id != request.user.organizer.pk:
        return Response(
            {"error": "permission_denied", "detail": "You do not own this event."},
            status=status.HTTP_403_FORBIDDEN,
        )
    event.cancel()
    return Response(EventDetailSerializer(event).data)


# ---------- Sessions ----------

@api_view(["POST"])
@permission_classes([IsAuthenticated, IsOrganizer])
def session_create(request, event_id):
    """POST /api/events/{eventId}/sessions/ — FR-05: add session."""
    event = get_object_or_404(Event, pk=event_id)
    if event.organizer_id != request.user.organizer.pk:
        return Response(
            {"error": "permission_denied", "detail": "You do not own this event."},
            status=status.HTTP_403_FORBIDDEN,
        )
    serializer = SessionSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    session = serializer.save(event=event)
    return Response(SessionSerializer(session).data, status=status.HTTP_201_CREATED)


@api_view(["PATCH", "DELETE"])
@permission_classes([IsAuthenticated, IsOrganizer])
def session_detail(request, pk):
    """PATCH/DELETE /api/sessions/{id}/ — update or remove session."""
    session = get_object_or_404(Session.objects.select_related("event"), pk=pk)
    if session.event.organizer_id != request.user.organizer.pk:
        return Response(
            {"error": "permission_denied", "detail": "You do not own this event."},
            status=status.HTTP_403_FORBIDDEN,
        )
    if request.method == "DELETE":
        session.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    serializer = SessionSerializer(session, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(SessionSerializer(session).data)


# ---------- Ticket Tiers ----------

@api_view(["POST"])
@permission_classes([IsAuthenticated, IsOrganizer])
def tier_create(request, event_id):
    """POST /api/events/{eventId}/tiers/ — FR-04: create ticket tier."""
    event = get_object_or_404(Event, pk=event_id)
    if event.organizer_id != request.user.organizer.pk:
        return Response(
            {"error": "permission_denied", "detail": "You do not own this event."},
            status=status.HTTP_403_FORBIDDEN,
        )
    serializer = TicketTierSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    tier = serializer.save(event=event)
    return Response(TicketTierSerializer(tier).data, status=status.HTTP_201_CREATED)


@api_view(["PATCH", "DELETE"])
@permission_classes([IsAuthenticated, IsOrganizer])
def tier_detail(request, pk):
    """PATCH/DELETE /api/tiers/{id}/ — update or remove tier."""
    tier = get_object_or_404(TicketTier.objects.select_related("event"), pk=pk)
    if tier.event.organizer_id != request.user.organizer.pk:
        return Response(
            {"error": "permission_denied", "detail": "You do not own this event."},
            status=status.HTTP_403_FORBIDDEN,
        )
    if request.method == "DELETE":
        if tier.quantity_sold > 0:
            return Response(
                {"error": "tier_has_sales", "detail": "Cannot delete a tier with existing sales."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        tier.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    serializer = TicketTierSerializer(tier, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(TicketTierSerializer(tier).data)
