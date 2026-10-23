from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction

from apps.audit.models import AuditEvent
from apps.tenancy.context import current_scope
from apps.tenancy.models import Membership
from apps.tenancy.permissions import PLANNING_ROLES, TASK_ROLES, require_role

from .models import Task


class StaleTaskError(Exception):
    pass


def _current_membership(membership):
    if membership is None or current_scope() != (membership.user_id, membership.wedding_id):
        raise PermissionDenied("Die Freigabe passt nicht zum aktuellen Zugang.")
    current = Membership.objects.filter(
        pk=membership.pk,
        user_id=membership.user_id,
        wedding_id=membership.wedding_id,
        is_active=True,
    ).first()
    if current is None:
        raise PermissionDenied("Die Freigabe ist nicht mehr gültig.")
    return current


@transaction.atomic
def create_task(*, membership, title, description="", due_date=None, assigned_to=None):
    membership = _current_membership(membership)
    require_role(membership, PLANNING_ROLES)
    if assigned_to is not None and (
        assigned_to.wedding_id != membership.wedding_id
        or not assigned_to.is_active
        or assigned_to.role not in TASK_ROLES
    ):
        raise ValidationError("Die zuständige Person gehört nicht zu dieser Planung.")
    task = Task(
        wedding_id=membership.wedding_id,
        title=title,
        description=description,
        due_date=due_date,
        assigned_to=assigned_to,
        created_by_id=membership.user_id,
    )
    task.full_clean()
    task.save(force_insert=True)
    AuditEvent.objects.create(
        wedding_id=membership.wedding_id,
        actor_id=membership.user_id,
        action=AuditEvent.Action.TASK_CREATED,
        object_id=task.pk,
    )
    return task


@transaction.atomic
def set_task_status(*, membership, task_id, expected_version, is_done):
    membership = _current_membership(membership)
    require_role(membership, TASK_ROLES)
    task = Task.objects.select_for_update().get(pk=task_id, wedding_id=membership.wedding_id)
    if membership.role == Membership.Role.WITNESS and task.assigned_to_id != membership.pk:
        raise PermissionDenied("Diese Aufgabe ist nicht zugewiesen.")
    if task.version != expected_version:
        raise StaleTaskError
    if task.is_done == is_done:
        return task
    task.is_done = is_done
    task.version += 1
    task.save(update_fields=["is_done", "version", "updated_at"])
    AuditEvent.objects.create(
        wedding_id=membership.wedding_id,
        actor_id=membership.user_id,
        action=AuditEvent.Action.TASK_COMPLETED if is_done else AuditEvent.Action.TASK_REOPENED,
        object_id=task.pk,
    )
    return task
