from django.contrib import admin
from .models import Registration, Payment, CheckIn, Feedback


@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = ("id", "attendee", "ticket_tier", "status", "qr_code", "registered_at")
    list_filter = ("status",)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("id", "registration", "amount", "gateway_ref", "status", "paid_at")


@admin.register(CheckIn)
class CheckInAdmin(admin.ModelAdmin):
    list_display = ("id", "registration", "checked_in_at", "method")


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ("id", "registration", "rating", "submitted_at")