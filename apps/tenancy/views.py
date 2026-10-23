from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET

from apps.audit.models import AuditEvent
from apps.planning.models import Task

from .context import accessible_weddings
from .models import Membership
from .permissions import PLANNING_ROLES, TASK_ROLES


@require_GET
def health(request):
    return JsonResponse({"status": "ok"})


@login_required
@require_GET
def wedding_list(request):
    weddings = accessible_weddings()
    labels = dict(Membership.Role.choices)
    for wedding in weddings:
        wedding["role_label"] = labels[wedding["role"]]
    return render(request, "tenancy/weddings.html", {"weddings": weddings})


@login_required
@require_GET
def wedding_dashboard(request, wedding_id):
    can_plan = request.membership.role in PLANNING_ROLES
    can_tasks = request.membership.role in TASK_ROLES
    tasks = Task.objects.filter(wedding_id=wedding_id) if can_tasks else Task.objects.none()
    return render(
        request,
        "tenancy/dashboard.html",
        {
            "wedding": request.wedding,
            "membership": request.membership,
            "can_plan": can_plan,
            "can_tasks": can_tasks,
            "tasks": tasks.order_by("is_done", "due_date", "created_at")[:5],
            "open_tasks": tasks.filter(is_done=False).count(),
            "done_tasks": tasks.filter(is_done=True).count(),
            "recent_changes": AuditEvent.objects.filter(wedding_id=wedding_id).order_by(
                "-created_at"
            )[:5]
            if request.membership.role == Membership.Role.OWNER
            else [],
        },
    )
