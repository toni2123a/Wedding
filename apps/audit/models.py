import uuid

from django.conf import settings
from django.db import models

from apps.tenancy.models import Wedding


class AuditEvent(models.Model):
    class Action(models.TextChoices):
        TASK_CREATED = "task.created", "Aufgabe hinzugefügt"
        TASK_COMPLETED = "task.completed", "Aufgabe erledigt"
        TASK_REOPENED = "task.reopened", "Aufgabe wieder geöffnet"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    wedding = models.ForeignKey(Wedding, on_delete=models.CASCADE)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    action = models.CharField(max_length=40, choices=Action.choices)
    object_id = models.UUIDField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "audit_events"
        indexes = [models.Index(fields=["wedding", "created_at"], name="audit_wedding_time_idx")]
