"""
Registrations models — Registration, Payment, CheckIn, Feedback.
Matches the ER diagram in Appendix B.4 field-for-field.

Key design decisions from the report (Section 4.1.3):
- Registration.status is a single enumeration, NOT separate booleans.
- CheckIn is a separate table (not a boolean on Registration) so re-entry
  attempts and check-in method can be recorded for analytics.
- CheckIn.registration is OneToOneField — enforces FR-13 (no duplicate check-in).
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from accounts.models import Attendee
from events.models import TicketTier


class Registration(models.Model):
    STATUS_PENDING = "PENDING"
    STATUS_CONFIRMED = "CONFIRMED"
    STATUS_CANCELLED = "CANCELLED"
    STATUS_REFUNDED = "REFUNDED"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_CONFIRMED, "Confirmed"),
        (STATUS_CANCELLED, "Cancelled"),
        (STATUS_REFUNDED, "Refunded"),
    ]

    attendee = models.ForeignKey(Attendee, on_delete=models.PROTECT, related_name="registrations")
    ticket_tier = models.ForeignKey(TicketTier, on_delete=models.PROTECT, related_name="registrations")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    qr_code = models.CharField(max_length=64, blank=True, default="")
    registered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "registration"
        indexes = [
            models.Index(fields=["attendee_id"]),  # NFR-P1: fast lookup for "my registrations"
        ]

    def __str__(self):
        return f"Reg #{self.pk} — {self.attendee.user.full_name} → {self.ticket_tier.event.title}"

    def confirm(self):
        self.status = self.STATUS_CONFIRMED
        self.save(update_fields=["status"])

    def cancel(self):
        self.status = self.STATUS_CANCELLED
        self.save(update_fields=["status"])


class Payment(models.Model):
    STATUS_SUCCEEDED = "SUCCEEDED"
    STATUS_FAILED = "FAILED"
    STATUS_REFUNDED = "REFUNDED"
    STATUS_CHOICES = [
        (STATUS_SUCCEEDED, "Succeeded"),
        (STATUS_FAILED, "Failed"),
        (STATUS_REFUNDED, "Refunded"),
    ]

    registration = models.OneToOneField(Registration, on_delete=models.CASCADE, related_name="payment")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    gateway_ref = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "payment"

    def __str__(self):
        return f"Payment {self.gateway_ref} — ${self.amount}"


class CheckIn(models.Model):
    """
    Separate table from Registration (report Section 4.1.3 note 3).
    OneToOneField on registration enforces FR-13 (no duplicate check-in) — TC-12.
    """
    METHOD_QR_SCAN = "QR_SCAN"
    METHOD_MANUAL = "MANUAL"
    METHOD_CHOICES = [
        (METHOD_QR_SCAN, "QR scan"),
        (METHOD_MANUAL, "Manual"),
    ]

    registration = models.OneToOneField(Registration, on_delete=models.CASCADE, related_name="check_in")
    checked_in_at = models.DateTimeField(auto_now_add=True)
    method = models.CharField(max_length=20, choices=METHOD_CHOICES, default=METHOD_QR_SCAN)

    class Meta:
        db_table = "check_in"

    def __str__(self):
        return f"CheckIn #{self.pk} — reg {self.registration_id}"


class Feedback(models.Model):
    """
    FR-14: rating 1–5 + optional comment, within 14 days of attendance.
    OneToOneField: one feedback per registration.
    """
    registration = models.OneToOneField(Registration, on_delete=models.CASCADE, related_name="feedback")
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField(blank=True, default="")
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "feedback"

    def __str__(self):
        return f"Feedback #{self.pk} — {self.rating}/5"
