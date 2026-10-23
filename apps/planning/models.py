import uuid

from django.conf import settings
from django.db import models

from apps.tenancy.models import Membership, Wedding


class Task(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    wedding = models.ForeignKey(Wedding, on_delete=models.CASCADE)
    title = models.CharField(max_length=160)
    description = models.TextField(max_length=2000, blank=True)
    due_date = models.DateField(null=True, blank=True)
    assigned_to = models.ForeignKey(
        Membership, null=True, blank=True, on_delete=models.PROTECT, db_constraint=False
    )
    is_done = models.BooleanField(default=False)
    version = models.PositiveIntegerField(default=1)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "planning_tasks"
        ordering = ["is_done", "due_date", "created_at"]
        indexes = [models.Index(fields=["wedding", "is_done"], name="task_wedding_status_idx")]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(version__gte=1), name="task_version_positive"
            ),
            models.UniqueConstraint(fields=["wedding", "id"], name="task_tenant_id_unique"),
        ]
