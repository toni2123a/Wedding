from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import Http404
from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from apps.tenancy.permissions import PLANNING_ROLES, TASK_ROLES, require_role

from .forms import TaskForm, TaskStatusForm
from .models import Task
from .services import StaleTaskError, create_task, set_task_status


@login_required
@require_GET
def task_list(request, wedding_id):
    require_role(request.membership, TASK_ROLES)
    page = Paginator(
        Task.objects.filter(wedding_id=wedding_id).select_related("assigned_to__user"), 25
    ).get_page(request.GET.get("seite"))
    return render(
        request,
        "planning/tasks.html",
        {
            "wedding": request.wedding,
            "membership": request.membership,
            "can_plan": request.membership.role in PLANNING_ROLES,
            "tasks": page,
            "page": page,
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
def task_create(request, wedding_id):
    require_role(request.membership, PLANNING_ROLES)
    form = TaskForm(request.POST if request.method == "POST" else None, wedding_id=wedding_id)
    if request.method == "POST" and form.is_valid():
        create_task(membership=request.membership, **form.cleaned_data)
        messages.success(request, "Die Aufgabe wurde hinzugefügt.")
        return redirect("task-list", wedding_id=wedding_id)
    return render(request, "planning/task_form.html", {"form": form, "wedding": request.wedding})


@login_required
@require_POST
def task_status(request, wedding_id, task_id):
    require_role(request.membership, TASK_ROLES)
    form = TaskStatusForm(request.POST)
    if not form.is_valid():
        return render(request, "planning/conflict.html", {"wedding": request.wedding}, status=400)
    try:
        set_task_status(
            membership=request.membership,
            task_id=task_id,
            expected_version=form.cleaned_data["version"],
            is_done=form.cleaned_data["is_done"],
        )
    except Task.DoesNotExist as error:
        raise Http404("Diese Aufgabe ist nicht verfügbar.") from error
    except StaleTaskError:
        return render(request, "planning/conflict.html", {"wedding": request.wedding}, status=409)
    return redirect("task-list", wedding_id=wedding_id)
