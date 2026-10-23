from uuid import uuid4

import pytest
from django.core.management import call_command
from django.db import DatabaseError, IntegrityError, connection, transaction

from apps.audit.models import AuditEvent
from apps.identity.models import User
from apps.planning.models import Task
from apps.tenancy.context import accessible_weddings, current_scope, tenant_context
from apps.tenancy.demo import demo_id
from apps.tenancy.models import Membership, Wedding


def actor(email="mara@demo.invalid"):
    return demo_id(email)


def wedding(key="a"):
    return demo_id(f"wedding-{key}")


def test_runtime_is_a_real_unprivileged_database_login():
    with connection.cursor() as cursor:
        cursor.execute("SELECT current_user, session_user")
        assert cursor.fetchone() == ("wedding_app", "wedding_app")
    call_command("check_isolation", verbosity=0)


def test_no_context_exposes_no_tenant_rows():
    assert Wedding.objects.count() == 0
    assert Membership.objects.count() == 0
    assert Task.objects.count() == 0
    assert AuditEvent.objects.count() == 0


def test_bootstrap_only_returns_the_current_users_wedding_metadata():
    assert accessible_weddings() == []
    with tenant_context(user_id=actor()):
        visible = accessible_weddings()
        assert [item["id"] for item in visible] == [wedding()]
        assert set(visible[0]) == {"id", "title", "date", "role"}
        assert Wedding.objects.count() == 0
        assert Task.objects.count() == 0


def test_unscoped_orm_query_is_still_limited_by_rls():
    with tenant_context(user_id=actor(), wedding_id=wedding()):
        assert Task.objects.count() == 3
        assert set(Task.objects.values_list("wedding_id", flat=True)) == {wedding()}
        assert Wedding.objects.get().pk == wedding()


def test_direct_sql_cannot_read_another_weddings_task():
    with tenant_context(user_id=actor(), wedding_id=wedding()):
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT title FROM planning_tasks WHERE id = %s", [demo_id("task-b-contract")]
            )
            assert cursor.fetchall() == []


def test_changing_only_the_tenant_id_does_not_establish_membership():
    with tenant_context(user_id=actor(), wedding_id=wedding("b")):
        assert Wedding.objects.count() == 0
        assert Membership.objects.count() == 0
        assert Task.objects.count() == 0


def test_django_superuser_flag_does_not_bypass_tenant_authorization():
    user = User.objects.get(email="ohne-zugang@demo.invalid")
    assert user.is_superuser
    with tenant_context(user_id=user.pk, wedding_id=wedding()):
        assert accessible_weddings() == []
        assert Task.objects.count() == 0


def test_different_roles_apply_in_different_weddings():
    sam = actor("sam@demo.invalid")
    with tenant_context(user_id=sam, wedding_id=wedding()):
        assert Task.objects.count() == 3
    with tenant_context(user_id=sam, wedding_id=wedding("b")):
        assert list(Task.objects.values_list("id", flat=True)) == [demo_id("task-b-music")]


def test_witness_cannot_read_unassigned_tasks():
    with tenant_context(user_id=actor("toni@demo.invalid"), wedding_id=wedding()):
        assert list(Task.objects.values_list("id", flat=True)) == [demo_id("task-a-rings")]


@pytest.mark.parametrize("email", ["gast@demo.invalid", "anbieter@demo.invalid"])
def test_guest_and_vendor_have_no_internal_task_access(email):
    with tenant_context(user_id=actor(email), wedding_id=wedding()):
        assert Task.objects.count() == 0


def test_database_rejects_cross_tenant_insert():
    with tenant_context(user_id=actor(), wedding_id=wedding()):
        with pytest.raises(DatabaseError), transaction.atomic():
            Task.objects.create(wedding_id=wedding("b"), title="Verboten", created_by_id=actor())


def test_database_rejects_cross_tenant_assignment_even_with_a_valid_task_scope():
    with tenant_context(user_id=actor(), wedding_id=wedding()):
        with pytest.raises(IntegrityError), transaction.atomic():
            Task.objects.create(
                wedding_id=wedding(),
                title="Falsche Zuordnung",
                created_by_id=actor(),
                assigned_to_id=demo_id("member-lea-b"),
            )


def test_tenant_identity_cannot_be_changed_after_creation():
    with tenant_context(user_id=actor(), wedding_id=wedding()):
        with pytest.raises(IntegrityError), transaction.atomic():
            Task.objects.filter(pk=demo_id("task-a-invitations")).update(wedding_id=wedding("b"))


@pytest.mark.parametrize(
    "statement",
    [
        "ALTER TABLE planning_tasks DISABLE ROW LEVEL SECURITY",
        "TRUNCATE planning_tasks CASCADE",
        "SET ROLE wedding_migrator",
        "UPDATE tenancy_memberships SET role = 'owner'",
        "DELETE FROM audit_events",
        "UPDATE audit_events SET action = 'task.created'",
    ],
)
def test_runtime_cannot_remove_security_boundaries(statement):
    with tenant_context(user_id=actor(), wedding_id=wedding()):
        with pytest.raises(DatabaseError), transaction.atomic(), connection.cursor() as cursor:
            cursor.execute(statement)


def test_context_does_not_leak_through_nested_transactions_or_connection_reuse():
    assert current_scope() == (None, None)
    with tenant_context(user_id=actor(), wedding_id=wedding()):
        assert current_scope() == (actor(), wedding())
        with tenant_context(user_id=actor("lea@demo.invalid"), wedding_id=wedding("b")):
            assert Task.objects.count() == 2
        assert current_scope() == (actor(), wedding())
        assert Task.objects.count() == 3
    assert current_scope() == (None, None)
    assert Task.objects.count() == 0


def test_exception_restores_previous_database_context():
    with pytest.raises(RuntimeError), tenant_context(user_id=actor(), wedding_id=wedding()):
        assert Task.objects.count() == 3
        raise RuntimeError("Testabbruch")
    assert current_scope() == (None, None)
    assert Task.objects.count() == 0


def test_unknown_user_has_no_access_to_a_known_wedding():
    with tenant_context(user_id=uuid4(), wedding_id=wedding()):
        assert Task.objects.count() == 0
