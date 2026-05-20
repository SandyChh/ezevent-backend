"""
EventEase — development settings.
DEBUG=True, console email backend, permissive CORS.
"""
from .base import *  # noqa: F401, F403

DEBUG = True
ALLOWED_HOSTS = ["*"]

# Console email backend — emails appear in the terminal (report Section 11)
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# CORS — allow everything in development
CORS_ALLOW_ALL_ORIGINS = True
