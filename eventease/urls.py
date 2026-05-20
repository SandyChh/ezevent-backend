"""EventEase URL Configuration — all API endpoints under /api/"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("accounts.urls")),
    path("api/events/", include("events.urls")),
    path("api/", include("registrations.urls")),
    path("api/", include("analytics.urls")),
    path("api/stripe/", include("core.stripe_urls")),
    path("api/admin/", include("core.admin_urls")),
]
