"""Deterministische IDs ausschließlich für künstliche lokale Testdaten."""

from datetime import date
from uuid import NAMESPACE_URL, uuid5

from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.core.management.base import CommandError
from django.db import connection, transaction

from apps.audit.models import AuditEvent
from apps.identity.models import User
from apps.planning.models import Task

from .models import Membership, Wedding


def demo_id(label):
    return uuid5(NAMESPACE_URL, f"https://example.invalid/wedding-local-demo/{label}")


@transaction.atomic
def seed_demo(password):
    if not getattr(settings, "ALLOW_DEMO_DATA", False):
        raise CommandError("Testdaten sind in dieser Umgebung nicht erlaubt.")
    with connection.cursor() as cursor:
        cursor.execute("SELECT current_user")
        if cursor.fetchone()[0] != "wedding_migrator":
            raise CommandError("Testdaten benötigen den getrennten lokalen Migrationszugang.")
    if len(password) < 20:
        raise CommandError("Das lokale Testpasswort ist zu kurz.")
    users = {}
    for name, email, is_staff in [
        ("Mara", "mara@demo.invalid", False),
        ("Lea", "lea@demo.invalid", False),
        ("Sam", "sam@demo.invalid", False),
        ("Toni", "toni@demo.invalid", False),
        ("Gast", "gast@demo.invalid", False),
        ("Anbieter", "anbieter@demo.invalid", False),
        ("Technik", "ohne-zugang@demo.invalid", True),
    ]:
        users[email], _ = User.objects.get_or_create(
            email=email,
            defaults={
                "id": demo_id(email),
                "first_name": name,
                "password": make_password(password),
                "is_active": True,
                "is_staff": is_staff,
                "is_superuser": is_staff,
            },
        )
    weddings = {}
    for key, title, wedding_date in [
        ("a", "Mara & Jonas", date(2027, 6, 12)),
        ("b", "Lea & Emil", date(2027, 8, 21)),
    ]:
        weddings[key], _ = Wedding.objects.get_or_create(
            id=demo_id(f"wedding-{key}"), defaults={"title": title, "date": wedding_date}
        )
    members = {}
    for key, wedding_key, email, role in [
        ("mara-a", "a", "mara@demo.invalid", "owner"),
        ("lea-b", "b", "lea@demo.invalid", "owner"),
        ("sam-a", "a", "sam@demo.invalid", "planner"),
        ("sam-b", "b", "sam@demo.invalid", "witness"),
        ("toni-a", "a", "toni@demo.invalid", "witness"),
        ("gast-a", "a", "gast@demo.invalid", "guest"),
        ("anbieter-a", "a", "anbieter@demo.invalid", "vendor"),
    ]:
        members[key], _ = Membership.objects.get_or_create(
            id=demo_id(f"member-{key}"),
            defaults={
                "wedding": weddings[wedding_key],
                "user": users[email],
                "role": role,
            },
        )
    for key, wedding_key, title, description, member_key, owner_email, due in [
        (
            "a-invitations",
            "a",
            "Einladungen abstimmen",
            "Den Entwurf gemeinsam durchsehen.",
            "mara-a",
            "mara@demo.invalid",
            date(2027, 2, 15),
        ),
        (
            "a-rings",
            "a",
            "Ringe für die Trauung bereitlegen",
            "Den Treffpunkt vorher absprechen.",
            "toni-a",
            "mara@demo.invalid",
            date(2027, 6, 11),
        ),
        (
            "a-timeline",
            "a",
            "Zeitplan für den Abend skizzieren",
            "Zeit für Pausen einplanen.",
            None,
            "mara@demo.invalid",
            None,
        ),
        (
            "b-contract",
            "b",
            "Vertrag der Location prüfen",
            "Private Planungsaufgabe des Paares.",
            "lea-b",
            "lea@demo.invalid",
            date(2027, 3, 1),
        ),
        (
            "b-music",
            "b",
            "Musik für den Einzug abstimmen",
            "Mit den Beteiligten abstimmen.",
            "sam-b",
            "lea@demo.invalid",
            date(2027, 5, 1),
        ),
    ]:
        task, _ = Task.objects.get_or_create(
            id=demo_id(f"task-{key}"),
            defaults={
                "wedding": weddings[wedding_key],
                "title": title,
                "description": description,
                "assigned_to": members[member_key] if member_key else None,
                "created_by": users[owner_email],
                "due_date": due,
            },
        )
        AuditEvent.objects.get_or_create(
            id=demo_id(f"audit-{key}"),
            defaults={
                "wedding": weddings[wedding_key],
                "actor": users[owner_email],
                "action": AuditEvent.Action.TASK_CREATED,
                "object_id": task.pk,
            },
        )
