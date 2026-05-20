"""
Admin views — user listing and suspend (FR-17, TC-18).
Admin-only endpoints.
"""
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.permissions import IsAdmin
from accounts.serializers import UserSerializer

User = get_user_model()


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsAdmin])
def user_list(request):
    """GET /api/admin/users/ — list all users (admin only)."""
    search = request.query_params.get("search", "")
    qs = User.objects.all().order_by("-created_at")
    if search:
        qs = qs.filter(email__icontains=search)
    return Response(UserSerializer(qs, many=True).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated, IsAdmin])
def user_suspend(request, pk):
    """
    POST /api/admin/users/{id}/suspend/ — FR-17.
    Sets is_active = False. TC-18: suspended user cannot log in.
    """
    user = get_object_or_404(User, pk=pk)
    if user.pk == request.user.pk:
        return Response(
            {"error": "self_suspend", "detail": "You cannot suspend your own account."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    user.is_active = False
    user.save(update_fields=["is_active"])
    return Response(UserSerializer(user).data)
