"""
Test cases for events — TC-04.
"""
import pytest
from datetime import timedelta
from django.utils import timezone


@pytest.mark.django_db
class TestTC04_EventValidation:
    """TC-04: Reject event with end-time before start-time."""

    def test_end_before_start_rejected(self, auth_client_organizer):
        now = timezone.now()
        resp = auth_client_organizer.post("/api/events/", {
            "title": "Bad Event",
            "description": "Should fail",
            "start_time": (now + timedelta(days=7)).isoformat(),
            "end_time": (now + timedelta(days=6)).isoformat(),
            "venue": "Nowhere",
            "capacity": 50,
        })
        assert resp.status_code == 400

    def test_valid_event_created(self, auth_client_organizer):
        now = timezone.now()
        resp = auth_client_organizer.post("/api/events/", {
            "title": "Good Event",
            "description": "Should succeed",
            "start_time": (now + timedelta(days=7)).isoformat(),
            "end_time": (now + timedelta(days=7, hours=3)).isoformat(),
            "venue": "Test Venue",
            "capacity": 100,
        })
        assert resp.status_code == 201
        assert resp.data["title"] == "Good Event"
        assert resp.data["status"] == "DRAFT"
