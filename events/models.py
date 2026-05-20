"""
Events models — Event, Session, TicketTier.
Matches the ER diagram in Appendix B.4 field-for-field.
"""
from django.db import models
from django.core.validators import MinValueValidator
from accounts.models import Organizer


class Event(models.Model):
    STATUS_DRAFT = "DRAFT"
    STATUS_PUBLISHED = "PUBLISHED"
    STATUS_CANCELLED = "CANCELLED"
    STATUS_CHOICES = [
        (STATUS_DRAFT, "Draft"),
        (STATUS_PUBLISHED, "Published"),
        (STATUS_CANCELLED, "Cancelled"),
    ]

    organizer = models.ForeignKey(Organizer, on_delete=models.CASCADE, related_name="events")
    title = models.CharField(max_length=200)
    description = models.TextField()
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    venue = models.CharField(max_length=200)
    capacity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)

    class Meta:
        db_table = "event"
        indexes = [
            models.Index(fields=["status"]),  # NFR-P1: index on status for public listing
        ]

    def __str__(self):
        return self.title

    def publish(self):
        """FR-03: transition DRAFT → PUBLISHED."""
        self.status = self.STATUS_PUBLISHED
        self.save(update_fields=["status"])

    def cancel(self):
        """Transition → CANCELLED."""
        self.status = self.STATUS_CANCELLED
        self.save(update_fields=["status"])

    def clean(self):
        """Validation gate from activity diagram (TC-04)."""
        from django.core.exceptions import ValidationError
        if self.end_time and self.start_time and self.end_time <= self.start_time:
            raise ValidationError({"end_time": "End time must be after start time."})


class Session(models.Model):
    """
    ER columns: id, event_id (FK), title, speaker, start_time, duration_minutes.
    """
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="sessions")
    title = models.CharField(max_length=200)
    speaker = models.CharField(max_length=150, blank=True, default="")
    start_time = models.DateTimeField()
    duration_minutes = models.PositiveIntegerField(validators=[MinValueValidator(1)])

    class Meta:
        db_table = "session"
        ordering = ["start_time"]

    def __str__(self):
        return f"{self.title} ({self.event.title})"


class TicketTier(models.Model):
    """
    ER columns: id, event_id (FK), tier_name, price, quantity_total, quantity_sold.
    """
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="ticket_tiers")
    tier_name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    quantity_total = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    quantity_sold = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "ticket_tier"

    def __str__(self):
        return f"{self.tier_name} — ${self.price}"

    @property
    def quantity_remaining(self):
        return self.quantity_total - self.quantity_sold
