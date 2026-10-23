import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

if sys.argv[1:2] == ["gunicorn"]:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
    import django
    from django.core.management import call_command

    django.setup()
    call_command("check_isolation")

os.execvp(sys.argv[1], sys.argv[1:])  # noqa: S606
