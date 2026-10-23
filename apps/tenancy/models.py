import uuid
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


def validate_timezone(value):
    try:
        ZoneInfo(value)
    except ZoneInfoNotFoundError as error:
        raise ValidationError("Diese Zeitzone ist nicht bekannt.") from error


class Wedding(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=160)
    date = models.DateField()
    timezone = models.CharField(
        max_length=64, default="Europe/Berlin", validators=[validate_timezone]
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "tenancy_weddings"
        ordering = ["date", "id"]

    def __str__(self):
        return self.title


class Membership(models.Model):
    class Role(models.TextChoices):
        OWNER = "owner", "Brautpaar"
        PLANNER = "planner", "Mitplaner"
        WITNESS = "witness", "Trauzeuge"
        GUEST = "guest", "Gast"
        VENDOR = "vendor", "Dienstleister"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    wedding = models.ForeignKey(Wedding, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    role = models.CharField(max_length=20, choices=Role.choices)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "tenancy_memberships"
        constraints = [
            models.UniqueConstraint(fields=["wedding", "user"], name="membership_user_unique"),
            models.UniqueConstraint(fields=["wedding", "id"], name="membership_tenant_id_unique"),
            models.CheckConstraint(
                condition=models.Q(role__in=["owner", "planner", "witness", "guest", "vendor"]),
                name="membership_role_valid",
            ),
        ]

    def __str__(self):
        return self.get_role_display()
