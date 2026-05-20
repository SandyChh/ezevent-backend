"""
Test cases for accounts — TC-01, TC-04 (auth), TC-21, TC-22, TC-24.
"""
import pytest
from django.contrib.auth.hashers import identify_hasher
from accounts.models import User


@pytest.mark.django_db
class TestTC01_UserRegistration:
    """TC-01: User registration creates a hashed-password account."""

    def test_register_creates_user(self, api_client):
        resp = api_client.post("/api/auth/register/", {
            "email": "user01@test.com",
            "password": "CorrectHorse9!",
            "full_name": "User 01",
            "role": "ATTENDEE",
        })
        assert resp.status_code == 201
        assert "user_id" in resp.data
        assert "access" in resp.data

        user = User.objects.get(email="user01@test.com")
        assert user.full_name == "User 01"
        assert user.role == "ATTENDEE"
        # TC-24: verify PBKDF2-SHA256 hash
        hasher = identify_hasher(user.password)
        assert hasher.algorithm == "pbkdf2_sha256"

    def test_duplicate_email_rejected(self, api_client, attendee_user):
        """TC-02 equivalent: reject duplicate email."""
        resp = api_client.post("/api/auth/register/", {
            "email": "attendee@test.com",
            "password": "AnotherPass1!",
            "full_name": "Dup User",
            "role": "ATTENDEE",
        })
        assert resp.status_code == 400


@pytest.mark.django_db
class TestTC22_UnauthenticatedRejected:
    """TC-22: Unauthenticated write request rejected with HTTP 401."""

    def test_create_event_requires_auth(self, api_client):
        resp = api_client.post("/api/events/", {"title": "Test"})
        assert resp.status_code in (401, 403)

    def test_create_registration_requires_auth(self, api_client):
        resp = api_client.post("/api/registrations/", {"event_id": 1, "ticket_tier_id": 1})
        assert resp.status_code in (401, 403)


@pytest.mark.django_db
class TestTC21_CrossTenantRejected:
    """TC-21: Cross-tenant API access rejected with HTTP 403."""

    def test_other_organizer_cannot_edit_event(
        self, api_client, published_event, db
    ):
        # Create a second organizer
        other = User.objects.create_user(
            email="other_org@test.com", full_name="Other Org",
            password="TestPass123!", role="ORGANIZER",
        )
        from accounts.models import Organizer
        Organizer.objects.create(user=other, organisation_name="Other")
        api_client.force_authenticate(user=other)

        resp = api_client.patch(
            f"/api/events/{published_event.pk}/",
            {"title": "Hacked"},
        )
        assert resp.status_code == 403


@pytest.mark.django_db
class TestTC24_PasswordHashVerification:
    """TC-24: Database stores PBKDF2-SHA256 hash, not plaintext."""

    def test_password_is_hashed(self, attendee_user):
        user = User.objects.get(pk=attendee_user.pk)
        assert user.password.startswith("pbkdf2_sha256$")
        assert "TestPass123!" not in user.password
