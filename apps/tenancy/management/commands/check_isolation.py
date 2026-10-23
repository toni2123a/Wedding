from django.core.management.base import BaseCommand, CommandError
from django.db import connection

TENANT_TABLES = ["tenancy_weddings", "tenancy_memberships", "planning_tasks", "audit_events"]


class Command(BaseCommand):
    help = "Prüft den eingeschränkten Laufzeitzugang und die erzwungene Mandantentrennung."

    def handle(self, *args, **options):
        errors = []
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT current_user, rolsuper, rolbypassrls, rolcreatedb, rolcreaterole "
                "FROM pg_roles WHERE rolname = current_user"
            )
            role, superuser, bypass, create_db, create_role = cursor.fetchone()
            if role != "wedding_app" or any([superuser, bypass, create_db, create_role]):
                errors.append("Der Datenbankzugang besitzt unerlaubte Laufzeitrechte.")
            cursor.execute("SELECT pg_has_role(current_user, 'wedding_migrator', 'MEMBER')")
            if cursor.fetchone()[0]:
                errors.append("Der Laufzeitzugang darf nicht Mitglied der Migrationsrolle sein.")
            for table in TENANT_TABLES:
                cursor.execute(
                    "SELECT c.relrowsecurity, c.relforcerowsecurity, "
                    "pg_get_userbyid(c.relowner), "
                    "has_table_privilege(current_user, c.oid, 'TRUNCATE') "
                    "FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace "
                    "WHERE n.nspname = 'public' AND c.relname = %s",
                    [table],
                )
                result = cursor.fetchone()
                if result is None or not result[0] or not result[1]:
                    errors.append(f"{table}: Erzwungene Zeilenrechte fehlen.")
                elif result[2] == role or result[3]:
                    errors.append(f"{table}: Besitzer- oder TRUNCATE-Rechte sind nicht zulässig.")
            cursor.execute(
                "SELECT has_table_privilege(current_user, 'audit_events', 'UPDATE'), "
                "has_table_privilege(current_user, 'audit_events', 'DELETE')"
            )
            if any(cursor.fetchone()):
                errors.append("Änderungsprotokolle dürfen nicht verändert oder gelöscht werden.")
        if errors:
            raise CommandError(" ".join(errors))
        self.stdout.write(self.style.SUCCESS("Laufzeitrechte und RLS sind korrekt eingerichtet."))
