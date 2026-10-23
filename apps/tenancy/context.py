from contextlib import contextmanager
from uuid import UUID

from django.db import connection, transaction


def _identifier(value):
    return str(UUID(str(value))) if value is not None else ""


@contextmanager
def tenant_context(*, user_id=None, wedding_id=None):
    """Geprüfte IDs gelten nur innerhalb dieser Transaktion, auch bei verschachtelten Aufrufen."""
    actor = _identifier(user_id)
    wedding = _identifier(wedding_id)
    with transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT current_setting('wedding.user_id', true), "
                "current_setting('wedding.wedding_id', true)"
            )
            previous_actor, previous_wedding = cursor.fetchone()
            cursor.execute(
                "SELECT set_config('wedding.user_id', %s, true), "
                "set_config('wedding.wedding_id', %s, true)",
                [actor, wedding],
            )
        try:
            yield
        finally:
            if not connection.needs_rollback:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT set_config('wedding.user_id', %s, true), "
                        "set_config('wedding.wedding_id', %s, true)",
                        [previous_actor or "", previous_wedding or ""],
                    )


def accessible_weddings():
    """Die Bootstrap-Funktion liefert nur die erlaubte Hochzeitsauswahl des aktuellen Kontos."""
    with connection.cursor() as cursor:
        cursor.execute("SELECT id, title, date, role FROM wedding_private.visible_weddings()")
        return [dict(zip(["id", "title", "date", "role"], row, strict=True)) for row in cursor]


def current_scope():
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT nullif(current_setting('wedding.user_id', true), '')::uuid, "
            "nullif(current_setting('wedding.wedding_id', true), '')::uuid"
        )
        return cursor.fetchone()
