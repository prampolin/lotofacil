"""Opt-in production configuration; deployment still requires operational review."""

import os

from django.core.exceptions import ImproperlyConfigured

from .settings import *  # noqa: F403
from .settings import ALLOWED_HOSTS, DATABASES, SECRET_KEY

if (
    len(SECRET_KEY) < 50
    or len(set(SECRET_KEY)) < 5
    or SECRET_KEY.startswith("django-insecure-")
):
    raise ImproperlyConfigured("Production requires a strong DJANGO_SECRET_KEY.")
if (
    not os.environ.get("DJANGO_ALLOWED_HOSTS")
    or not ALLOWED_HOSTS
    or any("*" in host for host in ALLOWED_HOSTS)
):
    raise ImproperlyConfigured("Production requires explicit DJANGO_ALLOWED_HOSTS.")
if not DATABASES["default"]["PASSWORD"]:
    raise ImproperlyConfigured("Production requires POSTGRES_PASSWORD.")

DEBUG = False
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
# Do not trust forwarded headers without an explicitly configured trusted proxy.

MAILERS = {
    "default": {
        "BACKEND": "django.core.mail.backends.smtp.EmailBackend",
        "OPTIONS": {
            "host": os.environ.get("SMTP_HOST", "localhost"),
            "port": int(os.environ.get("SMTP_PORT", "587")),
            "username": os.environ.get("SMTP_USER", ""),
            "password": os.environ.get("SMTP_PASSWORD", ""),
            "use_tls": True,
            "timeout": 10,
        },
    },
}
