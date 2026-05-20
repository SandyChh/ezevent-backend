from django.urls import path
from . import views

urlpatterns = [
    path("events/<int:event_id>/analytics/", views.event_analytics, name="event-analytics"),
    path("events/<int:event_id>/attendees.csv", views.attendee_csv_export, name="attendee-csv"),
]
