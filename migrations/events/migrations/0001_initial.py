import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Event",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=200)),
                ("description", models.TextField()),
                ("start_time", models.DateTimeField()),
                ("end_time", models.DateTimeField()),
                ("venue", models.CharField(max_length=200)),
                ("capacity", models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(1)])),
                ("status", models.CharField(choices=[("DRAFT", "Draft"), ("PUBLISHED", "Published"), ("CANCELLED", "Cancelled")], default="DRAFT", max_length=20)),
                ("organizer", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="events", to="accounts.organizer")),
            ],
            options={
                "db_table": "event",
            },
        ),
        migrations.AddIndex(
            model_name="event",
            index=models.Index(fields=["status"], name="event_status_idx"),
        ),
        migrations.CreateModel(
            name="Session",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=200)),
                ("speaker", models.CharField(blank=True, default="", max_length=150)),
                ("start_time", models.DateTimeField()),
                ("duration_minutes", models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(1)])),
                ("event", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="sessions", to="events.event")),
            ],
            options={
                "db_table": "session",
                "ordering": ["start_time"],
            },
        ),
        migrations.CreateModel(
            name="TicketTier",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("tier_name", models.CharField(max_length=100)),
                ("price", models.DecimalField(decimal_places=2, max_digits=10, validators=[django.core.validators.MinValueValidator(0)])),
                ("quantity_total", models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(1)])),
                ("quantity_sold", models.PositiveIntegerField(default=0)),
                ("event", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="ticket_tiers", to="events.event")),
            ],
            options={
                "db_table": "ticket_tier",
            },
        ),
    ]
