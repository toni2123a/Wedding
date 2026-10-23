from unittest.mock import patch

import pytest
from django.core.exceptions import PermissionDenied
from django.db import transaction

from apps.audit.models import AuditEvent
from apps.planning.models import Task
from apps.planning.services import create_task
from apps.tenancy.context import tenant_context
from apps.tenancy.demo import demo_id
from apps.tenancy.models import Membership


def wedding_url(key="a"):
    return f"/hochzeiten/{demo_id(f'wedding-{key}')}/"


def task_url(key, wedding="a"):
    return wedding_url(wedding) + f"aufgaben/{demo_id(f'task-{key}')}/status/"


def test_switcher_does_not_expose_another_wedding(client_for):
    client = client_for("mara@demo.invalid")
    body = client.get("/planung/").content.decode()
    assert "Mara &amp; Jonas" in body
    assert "Lea &amp; Emil" not in body


def test_foreign_wedding_url_returns_generic_not_found(client_for):
    response = client_for("mara@demo.invalid").get(wedding_url("b"))
    assert response.status_code == 404
    assert "Lea" not in response.content.decode()


@pytest.mark.parametrize("email", ["gast@demo.invalid", "anbieter@demo.invalid"])
def test_readonly_guest_roles_cannot_open_or_write_planning(email, client_for):
    client = client_for(email)
    assert client.get(wedding_url()).status_code == 200
    assert client.get(wedding_url() + "aufgaben/").status_code == 403
    assert client.post(wedding_url() + "aufgaben/neu/", {"title": "Verboten"}).status_code == 403


def test_witness_sees_only_assigned_tasks_and_cannot_create(client_for):
    client = client_for("toni@demo.invalid")
    response = client.get(wedding_url() + "aufgaben/")
    assert response.status_code == 200
    body = response.content.decode()
    assert "Ringe für die Trauung" in body
    assert "Einladungen abstimmen" not in body
    assert client.get(wedding_url() + "aufgaben/neu/").status_code == 403


def test_witness_can_complete_assigned_task_but_not_other_tasks(client_for):
    client = client_for("toni@demo.invalid")
    assert client.post(task_url("a-rings"), {"version": 1, "is_done": "true"}).status_code == 302
    assert (
        client.post(task_url("a-invitations"), {"version": 1, "is_done": "true"}).status_code == 404
    )


def test_owner_can_create_task_and_audit_it_atomically(client_for):
    client = client_for("mara@demo.invalid")
    response = client.post(
        wedding_url() + "aufgaben/neu/",
        {
            "title": "Blumen abstimmen",
            "description": "Nur künstliche Testdaten.",
            "assigned_to": str(demo_id("member-toni-a")),
            "due_date": "2027-02-20",
        },
    )
    assert response.status_code == 302
    with tenant_context(user_id=demo_id("mara@demo.invalid"), wedding_id=demo_id("wedding-a")):
        task = Task.objects.get(title="Blumen abstimmen")
        assert task.created_by_id == demo_id("mara@demo.invalid")
        assert AuditEvent.objects.filter(object_id=task.pk, action="task.created").count() == 1


def test_foreign_assignee_is_rejected_before_saving(client_for):
    client = client_for("mara@demo.invalid")
    response = client.post(
        wedding_url() + "aufgaben/neu/",
        {
            "title": "Fremde Zuordnung",
            "assigned_to": str(demo_id("member-lea-b")),
        },
    )
    assert response.status_code == 200
    assert "gültige Auswahl" in response.content.decode()
    with tenant_context(user_id=demo_id("mara@demo.invalid"), wedding_id=demo_id("wedding-a")):
        assert not Task.objects.filter(title="Fremde Zuordnung").exists()


def test_status_change_for_a_foreign_task_is_rejected(client_for):
    client = client_for("mara@demo.invalid")
    assert client.post(task_url("b-contract"), {"version": 1, "is_done": "true"}).status_code == 404


def test_repeated_stale_status_change_creates_no_second_audit(client_for):
    client = client_for("mara@demo.invalid")
    data = {"version": 1, "is_done": "true"}
    assert client.post(task_url("a-invitations"), data).status_code == 302
    assert client.post(task_url("a-invitations"), data).status_code == 409
    with tenant_context(user_id=demo_id("mara@demo.invalid"), wedding_id=demo_id("wedding-a")):
        assert (
            AuditEvent.objects.filter(
                object_id=demo_id("task-a-invitations"), action="task.completed"
            ).count()
            == 1
        )


def test_status_change_does_not_accept_get(client_for):
    assert client_for("mara@demo.invalid").get(task_url("a-invitations")).status_code == 405


def test_user_text_is_escaped_in_html(client_for):
    client = client_for("mara@demo.invalid")
    client.post(
        wedding_url() + "aufgaben/neu/",
        {
            "title": "<script>alert(1)</script>",
            "description": "<img src=x onerror=alert(1)>",
        },
    )
    body = client.get(wedding_url() + "aufgaben/").content.decode()
    assert "<script>" not in body
    assert "&lt;script&gt;" in body
    assert "<img src=x" not in body


def test_failed_audit_rolls_back_the_business_change():
    with tenant_context(user_id=demo_id("mara@demo.invalid"), wedding_id=demo_id("wedding-a")):
        member = Membership.objects.get(pk=demo_id("member-mara-a"))
        with patch("apps.planning.services.AuditEvent.objects.create", side_effect=RuntimeError):
            with pytest.raises(RuntimeError), transaction.atomic():
                create_task(membership=member, title="Darf nicht bleiben")
        assert not Task.objects.filter(title="Darf nicht bleiben").exists()


def test_service_rejects_a_membership_from_another_actor():
    with tenant_context(user_id=demo_id("sam@demo.invalid"), wedding_id=demo_id("wedding-a")):
        other_member = Membership.objects.get(pk=demo_id("member-mara-a"))
        with pytest.raises(PermissionDenied):
            create_task(membership=other_member, title="Falsche Identität")


def test_revoking_membership_blocks_an_existing_session(client_for, admin_change):
    client = client_for("toni@demo.invalid")
    assert client.get(wedding_url()).status_code == 200
    member_id = demo_id("member-toni-a")
    with admin_change(
        "UPDATE tenancy_memberships SET is_active = false WHERE id = %s",
        [member_id],
        "UPDATE tenancy_memberships SET is_active = true WHERE id = %s",
        [member_id],
    ):
        assert client.get(wedding_url()).status_code == 404


def test_platform_superuser_does_not_get_an_implicit_customer_view(client_for):
    client = client_for("ohne-zugang@demo.invalid")
    assert "Mara &amp; Jonas" not in client.get("/planung/").content.decode()
    assert client.get(wedding_url()).status_code == 404
