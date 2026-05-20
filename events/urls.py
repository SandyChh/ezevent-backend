from django.urls import path
from . import views

urlpatterns = [
    path("", views.event_list_create, name="event-list-create"),
    path("<int:pk>/", views.event_detail, name="event-detail"),
    path("<int:pk>/publish/", views.event_publish, name="event-publish"),
    path("<int:pk>/cancel/", views.event_cancel, name="event-cancel"),
    path("<int:event_id>/sessions/", views.session_create, name="session-create"),
    path("sessions/<int:pk>/", views.session_detail, name="session-detail"),
    path("<int:event_id>/tiers/", views.tier_create, name="tier-create"),
    path("tiers/<int:pk>/", views.tier_detail, name="tier-detail"),
]
