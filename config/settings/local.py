import os

from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F403

if os.environ.get("APP_ENV") != "local":
    raise ImproperlyConfigured("Diese Umgebung ist ausschließlich für APP_ENV=local freigegeben.")

ALLOWED_HOSTS = ["localhost", "127.0.0.1", "[::1]"]
SESSION_COOKIE_SECURE = False
SESSION_COOKIE_NAME = "wedding_local_session"
CSRF_COOKIE_SECURE = False
CSRF_COOKIE_NAME = "wedding_local_csrf"
ALLOW_DEMO_DATA = True
