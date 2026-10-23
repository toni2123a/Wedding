from django.db import migrations

SECURITY_SQL = """
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
GRANT USAGE ON SCHEMA public TO wedding_app;
CREATE SCHEMA wedding_private AUTHORIZATION wedding_migrator;
REVOKE ALL ON SCHEMA wedding_private FROM PUBLIC;
GRANT USAGE ON SCHEMA wedding_private TO wedding_app;

ALTER TABLE tenancy_weddings ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenancy_weddings FORCE ROW LEVEL SECURITY;
ALTER TABLE tenancy_memberships ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenancy_memberships FORCE ROW LEVEL SECURITY;
ALTER TABLE planning_tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE planning_tasks FORCE ROW LEVEL SECURITY;
ALTER TABLE audit_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_events FORCE ROW LEVEL SECURITY;

CREATE POLICY wedding_migration ON tenancy_weddings TO wedding_migrator USING (true) WITH CHECK (true);
CREATE POLICY membership_migration ON tenancy_memberships TO wedding_migrator USING (true) WITH CHECK (true);
CREATE POLICY task_migration ON planning_tasks TO wedding_migrator USING (true) WITH CHECK (true);
CREATE POLICY audit_migration ON audit_events TO wedding_migrator USING (true) WITH CHECK (true);

CREATE FUNCTION wedding_private.user_id() RETURNS uuid
LANGUAGE sql STABLE SET search_path = pg_catalog AS $$
    SELECT nullif(current_setting('wedding.user_id', true), '')::uuid
$$;
CREATE FUNCTION wedding_private.wedding_id() RETURNS uuid
LANGUAGE sql STABLE SET search_path = pg_catalog AS $$
    SELECT nullif(current_setting('wedding.wedding_id', true), '')::uuid
$$;
CREATE FUNCTION wedding_private.member_role(target_wedding uuid) RETURNS text
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = pg_catalog AS $$
    SELECT m.role::text FROM public.tenancy_memberships m
    JOIN public.identity_users u ON u.id = m.user_id
    WHERE m.wedding_id = target_wedding AND m.user_id = wedding_private.user_id()
      AND m.is_active AND u.is_active
$$;
CREATE FUNCTION wedding_private.member_id(target_wedding uuid) RETURNS uuid
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = pg_catalog AS $$
    SELECT m.id FROM public.tenancy_memberships m
    JOIN public.identity_users u ON u.id = m.user_id
    WHERE m.wedding_id = target_wedding AND m.user_id = wedding_private.user_id()
      AND m.is_active AND u.is_active
$$;
CREATE FUNCTION wedding_private.visible_weddings()
RETURNS TABLE (id uuid, title text, date date, role text)
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = pg_catalog AS $$
    SELECT w.id, w.title::text, w.date, m.role::text
    FROM public.tenancy_weddings w
    JOIN public.tenancy_memberships m ON m.wedding_id = w.id
    JOIN public.identity_users u ON u.id = m.user_id
    WHERE m.user_id = wedding_private.user_id() AND m.is_active AND u.is_active
    ORDER BY w.date, w.id
$$;

REVOKE ALL ON ALL FUNCTIONS IN SCHEMA wedding_private FROM PUBLIC;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA wedding_private TO wedding_app;

CREATE POLICY wedding_read ON tenancy_weddings FOR SELECT TO wedding_app
USING (id = wedding_private.wedding_id() AND wedding_private.member_role(id) IS NOT NULL);

CREATE POLICY membership_read ON tenancy_memberships FOR SELECT TO wedding_app
USING (
    wedding_id = wedding_private.wedding_id()
    AND wedding_private.member_role(wedding_id) IS NOT NULL
    AND (user_id = wedding_private.user_id()
         OR wedding_private.member_role(wedding_id) IN ('owner', 'planner'))
);

CREATE POLICY task_read ON planning_tasks FOR SELECT TO wedding_app
USING (
    wedding_id = wedding_private.wedding_id()
    AND (wedding_private.member_role(wedding_id) IN ('owner', 'planner')
         OR (wedding_private.member_role(wedding_id) = 'witness'
             AND assigned_to_id = wedding_private.member_id(wedding_id)))
);
CREATE POLICY task_insert ON planning_tasks FOR INSERT TO wedding_app
WITH CHECK (
    wedding_id = wedding_private.wedding_id()
    AND wedding_private.member_role(wedding_id) IN ('owner', 'planner')
    AND created_by_id = wedding_private.user_id()
);
CREATE POLICY task_update ON planning_tasks FOR UPDATE TO wedding_app
USING (
    wedding_id = wedding_private.wedding_id()
    AND (wedding_private.member_role(wedding_id) IN ('owner', 'planner')
         OR (wedding_private.member_role(wedding_id) = 'witness'
             AND assigned_to_id = wedding_private.member_id(wedding_id)))
)
WITH CHECK (
    wedding_id = wedding_private.wedding_id()
    AND (wedding_private.member_role(wedding_id) IN ('owner', 'planner')
         OR (wedding_private.member_role(wedding_id) = 'witness'
             AND assigned_to_id = wedding_private.member_id(wedding_id)))
);
CREATE POLICY task_delete ON planning_tasks FOR DELETE TO wedding_app
USING (
    wedding_id = wedding_private.wedding_id()
    AND wedding_private.member_role(wedding_id) IN ('owner', 'planner')
);

CREATE POLICY audit_read ON audit_events FOR SELECT TO wedding_app
USING (
    wedding_id = wedding_private.wedding_id()
    AND wedding_private.member_role(wedding_id) = 'owner'
);
CREATE POLICY audit_append ON audit_events FOR INSERT TO wedding_app
WITH CHECK (
    wedding_id = wedding_private.wedding_id()
    AND actor_id = wedding_private.user_id()
    AND wedding_private.member_role(wedding_id) IN ('owner', 'planner', 'witness')
);

ALTER TABLE planning_tasks ADD CONSTRAINT task_assignee_same_wedding
FOREIGN KEY (wedding_id, assigned_to_id)
REFERENCES tenancy_memberships(wedding_id, id) NOT DEFERRABLE;

CREATE FUNCTION wedding_private.task_identity_immutable() RETURNS trigger
LANGUAGE plpgsql SET search_path = pg_catalog AS $$
BEGIN
    IF NEW.wedding_id IS DISTINCT FROM OLD.wedding_id
       OR NEW.created_by_id IS DISTINCT FROM OLD.created_by_id THEN
        RAISE EXCEPTION 'Die Aufgabenzuordnung ist unveraenderlich.' USING ERRCODE = '23514';
    END IF;
    RETURN NEW;
END
$$;
REVOKE ALL ON FUNCTION wedding_private.task_identity_immutable() FROM PUBLIC;
CREATE TRIGGER task_identity_immutable BEFORE UPDATE ON planning_tasks
FOR EACH ROW EXECUTE FUNCTION wedding_private.task_identity_immutable();

GRANT SELECT ON tenancy_weddings, tenancy_memberships TO wedding_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON planning_tasks TO wedding_app;
GRANT SELECT, INSERT ON audit_events TO wedding_app;
GRANT SELECT ON identity_users TO wedding_app;
GRANT UPDATE (last_login) ON identity_users TO wedding_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON django_session, identity_login_buckets TO wedding_app;
"""


class Migration(migrations.Migration):
    dependencies = [
        ("tenancy", "0001_initial"),
        ("identity", "0001_initial"),
        ("planning", "0001_initial"),
        ("audit", "0002_initial"),
        ("sessions", "0001_initial"),
    ]
    # Sicherheitsgrenzen werden nicht durch eine automatische Rückmigration entfernt.
    operations = [migrations.RunSQL(SECURITY_SQL)]
