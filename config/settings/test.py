from .local import *  # noqa: F403

ALLOWED_HOSTS = ["testserver", "localhost", "127.0.0.1"]
DATABASES["default"]["CONN_MAX_AGE"] = 0  # noqa: F405
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}
