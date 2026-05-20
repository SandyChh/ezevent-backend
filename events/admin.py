from django.contrib import admin
from .models import Event, Session, TicketTier


class SessionInline(admin.TabularInline):
    model = Session
    extra = 0


class TicketTierInline(admin.TabularInline):
    model = TicketTier
    extra = 0


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("title", "organizer", "status", "start_time", "venue", "capacity")
    list_filter = ("status",)
    search_fields = ("title", "venue")
    inlines = [SessionInline, TicketTierInline]


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ("title", "event", "speaker", "start_time", "duration_minutes")


@admin.register(TicketTier)
class TicketTierAdmin(admin.ModelAdmin):
    list_display = ("tier_name", "event", "price", "quantity_total", "quantity_sold")