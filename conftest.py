"""
Shared pytest fixtures for the EventEase test suite.
Uses factory_boy for consistent test data generation.
"""
import uuid
from decimal import Decimal
from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import User, Organizer, Attendee
from events.models import Event, Session, TicketTier
from registrations.models import Registration, Payment, CheckIn


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def admin_user(db):
    user = User.objects.create_superuser(
        email="admin@test.com", full_name="Admin", password="TestPass123!",
    )
    return user


@pytest.fixture
def organizer_user(db):
    user = User.objects.create_user(
        email="organizer@test.com", full_name="Org User",
        password="TestPass123!", role="ORGANIZER",
    )
    org = Organizer.objects.create(
        user=user, organisation_name="Test Org", contact_phone="+610000",
    )
    return user


@pytest.fixture
def attendee_user(db):
    user = User.objects.create_user(
        email="attendee@test.com", full_name="Att User",
        password="TestPass123!", role="ATTENDEE",
    )
    att = Attendee.objects.create(user=user)
    return user


@pytest.fixture
def second_attendee_user(db):
    user = User.objects.create_user(
        email="attendee2@test.com", full_name="Att User 2",
        password="TestPass123!", role="ATTENDEE",
    )
    Attendee.objects.create(user=user)
    return user


@pytest.fixture
def published_event(organizer_user):
    now = timezone.now()
    return Event.objects.create(
        organizer=organizer_user.organizer,
        title="Test Event",
        description="A test event",
        start_time=now + timedelta(days=7),
        end_time=now + timedelta(days=7, hours=4),
        venue="Test Venue",
        capacity=100,
        status=Event.STATUS_PUBLISHED,
    )


@pytest.fixture
def free_tier(published_event):
    return TicketTier.objects.create(
        event=published_event, tier_name="Free", price=Decimal("0.00"),
        quantity_total=100, quantity_sold=0,
    )


@pytest.fixture
def paid_tier(published_event):
    return TicketTier.objects.create(
        event=published_event, tier_name="General", price=Decimal("20.00"),
        quantity_total=100, quantity_sold=0,
    )


@pytest.fixture
def sold_out_tier(published_event):
    return TicketTier.objects.create(
        event=published_event, tier_name="VIP", price=Decimal("50.00"),
        quantity_total=10, quantity_sold=10,
    )


@pytest.fixture
def confirmed_registration(attendee_user, free_tier):
    qr = uuid.uuid4().hex
    reg = Registration.objects.create(
        attendee=attendee_user.attendee,
        ticket_tier=free_tier,
        status="CONFIRMED",
        qr_code=qr,
    )
    Payment.objects.create(
        registration=reg, amount=Decimal("0.00"),
        gateway_ref="free", status="SUCCEEDED", paid_at=timezone.now(),
    )
    return reg


@pytest.fixture
def checked_in_registration(confirmed_registration):
    CheckIn.objects.create(registration=confirmed_registration, method="QR_SCAN")
    confirmed_registration.refresh_from_db()
    return confirmed_registration


@pytest.fixture
def auth_client_organizer(api_client, organizer_user):
    api_client.force_authenticate(user=organizer_user)
    return api_client


@pytest.fixture
def auth_client_attendee(api_client, attendee_user):
    api_client.force_authenticate(user=attendee_user)
    return api_client


@pytest.fixture
def auth_client_admin(api_client, admin_user):
    api_client.force_authenticate(user=admin_user)
    return api_client
