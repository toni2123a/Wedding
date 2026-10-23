import copy
import os
import time
from contextlib import contextmanager
from io import StringIO
from uuid import uuid4

import django
import psycopg
import pytest
from psycopg import sql

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.test")
django.setup()

from django.core.management import call_command  # noqa: E402
from django.db import connection, transaction  # noqa: E402
from django.test import Client  # noqa: E402

from apps.tenancy.demo import seed_demo  # noqa: E402
from config.settings.base import secret  # noqa: E402


def _redact(text):
    for name, value in os.environ.items():
        if name.endswith("_FILE") and value.startswith("/run/secrets/"):
            from pathlib import Path

            confidential = Path(value).read_text(encoding="utf-8").strip()
            if confidential:
                text = text.replace(confidential, "[REDACTED]")
    return text


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if report.longrepr is not None:
        report.longrepr = _redact(str(report.longrepr))
    report.sections = [(title, _redact(content)) for title, content in report.sections]


@pytest.fixture(scope="session", autouse=True)
def isolated_database():
    """Migrationen privilegiert, sämtliche Tests anschließend als echte wedding_app-Anmeldung."""
    original = copy.deepcopy(connection.settings_dict)
    database_name = f"wedding_test_{uuid4().hex}"
    admin_options = {
        "host": original["HOST"],
        "port": original["PORT"],
        "user": "wedding_migrator",
        "password": secret("MIGRATOR_PASSWORD"),
        "dbname": "postgres",
        "autocommit": True,
    }
    created = False
    with psycopg.connect(**admin_options) as control:
        try:
            control.execute(
                sql.SQL("CREATE DATABASE {} OWNER wedding_migrator").format(
                    sql.Identifier(database_name)
                )
            )
            created = True
            connection.close()
            connection.settings_dict.update(
                {
                    "NAME": database_name,
                    "USER": "wedding_migrator",
                    "PASSWORD": admin_options["password"],
                }
            )
            call_command("migrate", interactive=False, verbosity=0, stdout=StringIO())
            seed_demo(secret("DEMO_PASSWORD"))
            connection.close()
            connection.settings_dict.update(
                {
                    "USER": original["USER"],
                    "PASSWORD": original["PASSWORD"],
                }
            )
            call_command("check_isolation", stdout=StringIO())
            yield {**admin_options, "dbname": database_name}
        finally:
            connection.close()
            connection.settings_dict.clear()
            connection.settings_dict.update(original)
            if created:
                assert database_name.startswith("wedding_test_")
                control.execute(
                    sql.SQL("DROP DATABASE {} WITH (FORCE)").format(sql.Identifier(database_name))
                )


@pytest.fixture(autouse=True)
def rollback_each_test(isolated_database):
    with transaction.atomic():
        yield
        transaction.set_rollback(True)


@pytest.fixture
def demo_password():
    return secret("DEMO_PASSWORD")


@pytest.fixture
def client_for(demo_password):
    def sign_in(email):
        client = Client()
        response = client.post("/anmelden/", {"username": email, "password": demo_password})
        assert response.status_code == 302
        assert response.url == "/planung/"
        return client

    return sign_in


@pytest.fixture
def admin_change(isolated_database):
    @contextmanager
    def change(statement, parameters, restore_statement, restore_parameters):
        with psycopg.connect(**isolated_database) as admin:
            admin.execute(statement, parameters)
        try:
            yield
        finally:
            with psycopg.connect(**isolated_database) as admin:
                admin.execute(restore_statement, restore_parameters)

    return change


@pytest.fixture
def expire_session():
    def expire(client, *, age=0, idle=0):
        session = client.session
        session["authenticated_at"] = int(time.time()) - age
        session["last_activity_at"] = int(time.time()) - idle
        session.save()

    return expire
