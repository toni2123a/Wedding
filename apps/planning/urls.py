from django.urls import path

from .views import task_create, task_list, task_status

urlpatterns = [
    path("", task_list, name="task-list"),
    path("neu/", task_create, name="task-create"),
    path("<uuid:task_id>/status/", task_status, name="task-status"),
]
