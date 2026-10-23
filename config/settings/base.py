import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parents[2]


def secret(name):
    file_name = os.environ.get(f"{name}_FILE")
    value = (
        Path(file_name).read_text(encoding="utf-8").strip() if file_name else os.environ.get(name)
    )
    if not value:
        raise ImproperlyConfigured(f"Das erforderliche Geheimnis {name} fehlt.")
    return value


SECRET_KEY = secret("DJANGO_SECRET_KEY")
if len(SECRET_KEY) < 50:
    raise ImproperlyConfigured("DJANGO_SECRET_KEY muss mindestens 50 Zeichen enthalten.")

DEBUG = False
ALLOWED_HOSTS = []
INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "apps.identity.apps.IdentityConfig",
    "apps.tenancy.apps.TenancyConfig",
    "apps.planning.apps.PlanningConfig",
    "apps.audit.apps.AuditConfig",
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "config.middleware.ResponseSecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "apps.tenancy.middleware.TenantContextMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("DATABASE_NAME", "wedding"),
        "USER": os.environ.get("DATABASE_USER", "wedding_app"),
        "PASSWORD": secret("DATABASE_PASSWORD"),
        "HOST": os.environ.get("DATABASE_HOST", "db"),
        "PORT": os.environ.get("DATABASE_PORT", "5432"),
        "CONN_MAX_AGE": 60,
        "OPTIONS": {"connect_timeout": 5},
    }
}
AUTH_USER_MODEL = "identity.User"
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 14},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
]
LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "wedding-list"
LOGOUT_REDIRECT_URL = "landing"
LANGUAGE_CODE = "de"
TIME_ZONE = "Europe/Berlin"
USE_I18N = True
USE_TZ = True
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
SESSION_COOKIE_AGE = 12 * 60 * 60
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_NAME = "__Host-wedding_session"
SESSION_COOKIE_DOMAIN = None
SESSION_SAVE_EVERY_REQUEST = False
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_NAME = "__Host-wedding_csrf"
CSRF_COOKIE_DOMAIN = None
SESSION_IDLE_TIMEOUT = 60 * 60
SESSION_ABSOLUTE_TIMEOUT = 12 * 60 * 60
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"
DATA_UPLOAD_MAX_MEMORY_SIZE = 64 * 1024
DATA_UPLOAD_MAX_NUMBER_FIELDS = 40
FILE_UPLOAD_MAX_MEMORY_SIZE = 0
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}
EMAIL_BACKEND = "django.core.mail.backends.dummy.EmailBackend"
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "WARNING"},
    "loggers": {"django.request": {"handlers": ["console"], "level": "ERROR", "propagate": False}},
}
