"""
EventEase — production settings.
DEBUG=False, TLS enforced, SendGrid SMTP, security headers.
Matches OWASP A05 mitigation in Section 5.7 of the report.
"""
import os
import dj_database_url
from .base import *  # noqa: F401, F403

DEBUG = False
ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "").split(",")

# ---------- Database — PostgreSQL on Render (NFR-Sc1) ----------
# DATABASE_URL is set automatically by Render when you link a Postgres instance.
# dj-database-url parses it into Django's DATABASES format.
# conn_max_age=600 keeps connections open for 10 min (avoids per-request overhead).
if os.environ.get("DATABASE_URL"):
    DATABASES = {
        "default": dj_database_url.config(
            default=os.environ["DATABASE_URL"],
            conn_max_age=600,
            conn_health_checks=True,
        )
    }

# ---------- HTTPS / security (A02, A05 mitigations) ----------
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000       # Strict-Transport-Security max-age (ZAP finding)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True    # X-Content-Type-Options (ZAP finding)
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"  # Referrer-Policy (ZAP finding)

# ---------- SendGrid SMTP (report Section 11) ----------
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.sendgrid.net"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = "apikey"
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")

# ---------- CORS ----------
CORS_ALLOW_ALL_ORIGINS = False
# CORS_ALLOWED_ORIGINS is already set in base.py from env var
