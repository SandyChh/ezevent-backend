"""
Accounts views — thin views that delegate to serializers/JWT.
Login endpoint is rate-limited to 5/min/IP (OWASP A07, Section 5.7).
"""
from django.contrib.auth import authenticate
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import RegisterSerializer, UserSerializer


class LoginRateThrottle(AnonRateThrottle):
    """5 attempts per minute per IP (A07 mitigation)."""
    rate = "5/min"


@api_view(["POST"])
@permission_classes([AllowAny])
def register_view(request):
    """POST /api/auth/register/ — FR-01: register an account."""
    serializer = RegisterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.save()
    refresh = RefreshToken.for_user(user)
    return Response(
        {
            "user_id": user.pk,
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([LoginRateThrottle])
def login_view(request):
    """POST /api/auth/login/ — authenticate and return JWT pair."""
    email = request.data.get("email", "").lower()
    password = request.data.get("password", "")
    user = authenticate(request, username=email, password=password)
    if user is None:
        return Response(
            {"error": "invalid_credentials", "detail": "Invalid email or password."},
            status=status.HTTP_401_UNAUTHORIZED,
        )
    if not user.is_active:
        return Response(
            {"error": "account_suspended", "detail": "This account has been suspended."},
            status=status.HTTP_403_FORBIDDEN,
        )
    refresh = RefreshToken.for_user(user)
    response = Response({"access": str(refresh.access_token), "refresh": str(refresh)})
    # Also set refresh token as HttpOnly cookie
    response.set_cookie(
        key="refresh_token",
        value=str(refresh),
        httponly=True,
        secure=request.is_secure(),
        samesite="Lax",
        max_age=7 * 24 * 60 * 60,  # 7 days (NFR-S3)
    )
    return response


@api_view(["POST"])
@permission_classes([AllowAny])
def refresh_view(request):
    """POST /api/auth/refresh/ — rotate refresh token."""
    token_str = request.COOKIES.get("refresh_token") or request.data.get("refresh")
    if not token_str:
        return Response(
            {"error": "no_refresh_token", "detail": "Refresh token not provided."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    try:
        old_refresh = RefreshToken(token_str)
        old_refresh.blacklist()
        user_id = old_refresh["user_id"]
        from django.contrib.auth import get_user_model
        user = get_user_model().objects.get(pk=user_id)
        new_refresh = RefreshToken.for_user(user)
        response = Response({"access": str(new_refresh.access_token)})
        response.set_cookie(
            key="refresh_token",
            value=str(new_refresh),
            httponly=True,
            secure=request.is_secure(),
            samesite="Lax",
            max_age=7 * 24 * 60 * 60,
        )
        return response
    except Exception:
        return Response(
            {"error": "invalid_refresh_token", "detail": "Refresh token is invalid or expired."},
            status=status.HTTP_401_UNAUTHORIZED,
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """POST /api/auth/logout/ — blacklist refresh token, clear cookie."""
    token_str = request.COOKIES.get("refresh_token") or request.data.get("refresh")
    if token_str:
        try:
            RefreshToken(token_str).blacklist()
        except Exception:
            pass
    response = Response({"detail": "Logged out."}, status=status.HTTP_200_OK)
    response.delete_cookie("refresh_token")
    return response


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me_view(request):
    """GET /api/auth/me/ — return current user profile."""
    return Response(UserSerializer(request.user).data)
