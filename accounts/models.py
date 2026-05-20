"""
Accounts models — User, Organizer, Attendee.
Matches the ER diagram in Appendix B.4 exactly.
Class-table inheritance: Organizer and Attendee have separate tables
with PK = FK to USER (report Section 4.1.3 implementation notes).
"""
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    def create_user(self, email, full_name, password=None, role="ATTENDEE", **extra):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, full_name=full_name, role=role, **extra)
        user.set_password(password)  # PBKDF2-SHA256 (NFR-S2, TC-24)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, full_name, password=None, **extra):
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        return self.create_user(email, full_name, password, role="ADMIN", **extra)


class User(AbstractBaseUser, PermissionsMixin):
    ROLE_ORGANIZER = "ORGANIZER"
    ROLE_ATTENDEE = "ATTENDEE"
    ROLE_ADMIN = "ADMIN"
    ROLE_CHOICES = [
        (ROLE_ORGANIZER, "Organizer"),
        (ROLE_ATTENDEE, "Attendee"),
        (ROLE_ADMIN, "Admin"),
    ]

    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=150)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name"]

    class Meta:
        db_table = "user"

    def __str__(self):
        return f"{self.full_name} ({self.email})"


class Organizer(models.Model):
    """
    Extends User via class-table inheritance (FK + PK = user_id).
    ER columns: user_id (PK/FK), organisation_name, contact_phone.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True, related_name="organizer")
    organisation_name = models.CharField(max_length=200)
    contact_phone = models.CharField(max_length=30, blank=True, default="")

    class Meta:
        db_table = "organizer"

    def __str__(self):
        return self.organisation_name


class Attendee(models.Model):
    """
    Extends User via class-table inheritance (FK + PK = user_id).
    ER columns: user_id (PK/FK), preferences.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True, related_name="attendee")
    preferences = models.TextField(blank=True, default="")

    class Meta:
        db_table = "attendee"

    def __str__(self):
        return self.user.full_name
