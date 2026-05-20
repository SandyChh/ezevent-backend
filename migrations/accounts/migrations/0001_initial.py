import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.CreateModel(
            name="User",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("password", models.CharField(max_length=128, verbose_name="password")),
                ("last_login", models.DateTimeField(blank=True, null=True, verbose_name="last login")),
                ("is_superuser", models.BooleanField(default=False, verbose_name="superuser status")),
                ("first_name", models.CharField(blank=True, max_length=150, verbose_name="first name")),
                ("last_name", models.CharField(blank=True, max_length=150, verbose_name="last name")),
                ("email", models.EmailField(max_length=254, unique=True)),
                ("full_name", models.CharField(max_length=150)),
                ("role", models.CharField(choices=[("ORGANIZER", "Organizer"), ("ATTENDEE", "Attendee"), ("ADMIN", "Admin")], max_length=20)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("is_active", models.BooleanField(default=True)),
                ("is_staff", models.BooleanField(default=False)),
                ("groups", models.ManyToManyField(blank=True, related_name="user_set", related_query_name="user", to="auth.group", verbose_name="groups")),
                ("user_permissions", models.ManyToManyField(blank=True, related_name="user_set", related_query_name="user", to="auth.permission", verbose_name="user permissions")),
            ],
            options={
                "db_table": "user",
            },
        ),
        migrations.CreateModel(
            name="Attendee",
            fields=[
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, related_name="attendee", serialize=False, to=settings.AUTH_USER_MODEL)),
                ("preferences", models.TextField(blank=True, default="")),
            ],
            options={
                "db_table": "attendee",
            },
        ),
        migrations.CreateModel(
            name="Organizer",
            fields=[
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, related_name="organizer", serialize=False, to=settings.AUTH_USER_MODEL)),
                ("organisation_name", models.CharField(max_length=200)),
                ("contact_phone", models.CharField(blank=True, default="", max_length=30)),
            ],
            options={
                "db_table": "organizer",
            },
        ),
    ]
