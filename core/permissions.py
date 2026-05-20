"""
Custom DRF permission classes.
These enforce ownership checks at the view layer,
complementing the service-layer checks (OWASP A01 mitigation — Section 5.7).
Referenced by TC-21 (cross-tenant rejected 403) and TC-22 (unauth rejected 401).
"""
from rest_framework.permissions import BasePermission


class IsOrganizer(BasePermission):
    """Allow access only to users with role ORGANIZER."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == "ORGANIZER"
        )


class IsAdmin(BasePermission):
    """Allow access only to users with role ADMIN."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == "ADMIN"
        )


class IsOwner(BasePermission):
    """
    Object-level permission: the object must have an ownership path back
    to request.user. Subclasses or views override `get_owner_user(obj)`.
    """

    def has_object_permission(self, request, view, obj):
        owner_user = self._resolve_owner(obj)
        return owner_user == request.user

    @staticmethod
    def _resolve_owner(obj):
        """Walk common FK chains to find the owning User."""
        # Event → organizer → user
        if hasattr(obj, "organizer"):
            org = obj.organizer
            return org.user if hasattr(org, "user") else org
        # Registration → attendee → user
        if hasattr(obj, "attendee"):
            att = obj.attendee
            return att.user if hasattr(att, "user") else att
        return None


class IsOrganizerOwner(BasePermission):
    """Object-level: event must belong to the requesting organizer."""

    def has_object_permission(self, request, view, obj):
        if not hasattr(request.user, "organizer"):
            return False
        if hasattr(obj, "organizer_id"):
            return obj.organizer_id == request.user.organizer.pk
        if hasattr(obj, "event"):
            return obj.event.organizer_id == request.user.organizer.pk
        return False
