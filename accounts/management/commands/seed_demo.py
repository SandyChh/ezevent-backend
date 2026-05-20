"""
Management command: python manage.py seed_demo
Creates the demo data set described in the build spec Section 17:
- 1 admin, 2 organizers, 3 attendees
- 4 published events with mixed free/paid tiers
- Sample registrations and check-ins so analytics aren't empty
"""
import uuid
from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import User, Organizer, Attendee
from events.models import Event, Session, TicketTier
from registrations.models import Registration, Payment, CheckIn


class Command(BaseCommand):
    help = "Seed the database with demo data for marking."

    def handle(self, *args, **options):
        if User.objects.filter(email="admin@eventease.test").exists():
            self.stdout.write(self.style.WARNING("Demo data already exists. Skipping."))
            return

        now = timezone.now()

        # ---------- Users ----------
        admin = User.objects.create_superuser(
            email="admin@eventease.test",
            full_name="Admin User",
            password="Demo1234!",
        )
        self.stdout.write(f"  Created admin: {admin.email}")

        org1_user = User.objects.create_user(
            email="org1@eventease.test",
            full_name="Alice Organizer",
            password="Demo1234!",
            role="ORGANIZER",
        )
        org1 = Organizer.objects.create(
            user=org1_user,
            organisation_name="TechConf Australia",
            contact_phone="+61400000001",
        )

        org2_user = User.objects.create_user(
            email="org2@eventease.test",
            full_name="Bob Organizer",
            password="Demo1234!",
            role="ORGANIZER",
        )
        org2 = Organizer.objects.create(
            user=org2_user,
            organisation_name="Community Events Co",
            contact_phone="+61400000002",
        )
        self.stdout.write(f"  Created organizers: {org1_user.email}, {org2_user.email}")

        attendees = []
        for i, (name, email) in enumerate([
            ("Charlie Attendee", "att1@eventease.test"),
            ("Diana Attendee", "att2@eventease.test"),
            ("Eve Attendee", "att3@eventease.test"),
        ], start=1):
            u = User.objects.create_user(
                email=email, full_name=name, password="Demo1234!", role="ATTENDEE",
            )
            att = Attendee.objects.create(user=u)
            attendees.append(att)
        self.stdout.write(f"  Created {len(attendees)} attendees")

        # ---------- Events ----------
        events_data = [
            {
                "organizer": org1,
                "title": "AI & Machine Learning Summit 2026",
                "description": "A full-day summit exploring the latest in artificial intelligence, from large language models to computer vision, with hands-on workshops and networking.",
                "start_time": now + timedelta(days=14),
                "end_time": now + timedelta(days=14, hours=8),
                "venue": "Sydney Convention Centre, Darling Harbour",
                "capacity": 200,
                "tiers": [
                    ("Early Bird", Decimal("25.00"), 50),
                    ("General Admission", Decimal("45.00"), 100),
                    ("VIP (includes lunch)", Decimal("85.00"), 50),
                ],
                "sessions": [
                    ("Keynote: The State of AI in 2026", "Dr Sarah Chen", 0, 60),
                    ("Workshop: Building with LLMs", "James Park", 75, 90),
                    ("Panel: Ethics in AI", "Multiple speakers", 180, 60),
                ],
            },
            {
                "organizer": org1,
                "title": "Intro to Web Development Workshop",
                "description": "A free beginner-friendly workshop covering HTML, CSS, and JavaScript fundamentals. Laptops provided.",
                "start_time": now + timedelta(days=7),
                "end_time": now + timedelta(days=7, hours=3),
                "venue": "CDU Waterfront Campus, Room 3.12",
                "capacity": 30,
                "tiers": [
                    ("Free", Decimal("0.00"), 30),
                ],
                "sessions": [
                    ("HTML & CSS Basics", "Alice Organizer", 0, 60),
                    ("JavaScript Fundamentals", "Alice Organizer", 75, 90),
                ],
            },
            {
                "organizer": org2,
                "title": "Darwin Food & Wine Festival",
                "description": "Sample dishes from 20 local restaurants paired with wines from across Australia. Live music all evening.",
                "start_time": now + timedelta(days=30),
                "end_time": now + timedelta(days=30, hours=5),
                "venue": "Mindil Beach, Darwin",
                "capacity": 500,
                "tiers": [
                    ("Standard Entry", Decimal("35.00"), 400),
                    ("Premium (unlimited tastings)", Decimal("75.00"), 100),
                ],
                "sessions": [
                    ("Welcome & Opening Toast", "Mayor of Darwin", 0, 15),
                    ("Live Music: The Sunsetters", "", 30, 120),
                    ("Dessert Pairing Masterclass", "Chef Nguyen", 180, 45),
                ],
            },
            {
                "organizer": org2,
                "title": "Community Coding Meetup",
                "description": "Monthly meetup for developers of all levels. This month: building REST APIs with Django.",
                "start_time": now + timedelta(days=3),
                "end_time": now + timedelta(days=3, hours=2),
                "venue": "Innovation Hub, 42 Mitchell St, Darwin",
                "capacity": 40,
                "tiers": [
                    ("Free", Decimal("0.00"), 40),
                ],
                "sessions": [
                    ("Talk: REST API Design", "Bob Organizer", 0, 45),
                    ("Live Coding Demo", "Bob Organizer", 60, 45),
                ],
            },
        ]

        created_events = []
        for ed in events_data:
            event = Event.objects.create(
                organizer=ed["organizer"],
                title=ed["title"],
                description=ed["description"],
                start_time=ed["start_time"],
                end_time=ed["end_time"],
                venue=ed["venue"],
                capacity=ed["capacity"],
                status=Event.STATUS_PUBLISHED,
            )
            tiers = []
            for tier_name, price, qty in ed["tiers"]:
                tier = TicketTier.objects.create(
                    event=event, tier_name=tier_name, price=price, quantity_total=qty,
                )
                tiers.append(tier)
            for title, speaker, offset_min, duration in ed["sessions"]:
                Session.objects.create(
                    event=event,
                    title=title,
                    speaker=speaker,
                    start_time=ed["start_time"] + timedelta(minutes=offset_min),
                    duration_minutes=duration,
                )
            created_events.append((event, tiers))
        self.stdout.write(f"  Created {len(created_events)} events with tiers and sessions")

        # ---------- Sample registrations & check-ins ----------
        # Register all 3 attendees for the free workshop (event index 1)
        workshop_event, workshop_tiers = created_events[1]
        free_tier = workshop_tiers[0]
        for att in attendees:
            qr = uuid.uuid4().hex
            reg = Registration.objects.create(
                attendee=att, ticket_tier=free_tier,
                status="CONFIRMED", qr_code=qr,
            )
            Payment.objects.create(
                registration=reg, amount=Decimal("0.00"),
                gateway_ref="free", status="SUCCEEDED", paid_at=now,
            )
            free_tier.quantity_sold += 1
        free_tier.save()

        # Check in the first two attendees
        workshop_regs = Registration.objects.filter(ticket_tier=free_tier).order_by("pk")[:2]
        for reg in workshop_regs:
            CheckIn.objects.create(registration=reg, method="QR_SCAN")

        # Register attendee 1 for the AI summit (paid, event index 0)
        summit_event, summit_tiers = created_events[0]
        early_tier = summit_tiers[0]
        qr = uuid.uuid4().hex
        reg = Registration.objects.create(
            attendee=attendees[0], ticket_tier=early_tier,
            status="CONFIRMED", qr_code=qr,
        )
        Payment.objects.create(
            registration=reg, amount=early_tier.price,
            gateway_ref="pi_demo_summit_001", status="SUCCEEDED", paid_at=now,
        )
        early_tier.quantity_sold += 1
        early_tier.save()

        self.stdout.write(self.style.SUCCESS(
            "\nDemo data seeded successfully!\n"
            "Login credentials (all passwords: Demo1234!):\n"
            "  Admin:      admin@eventease.test\n"
            "  Organizer:  org1@eventease.test / org2@eventease.test\n"
            "  Attendee:   att1@eventease.test / att2@eventease.test / att3@eventease.test"
        ))
