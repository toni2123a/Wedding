#!/usr/bin/env bash
set -euo pipefail

APP_PASSWORD="$(tr -d '\r\n' < /run/secrets/db_app_password)"
MIGRATOR_PASSWORD="$(tr -d '\r\n' < /run/secrets/db_migrator_password)"
export APP_PASSWORD MIGRATOR_PASSWORD

psql --username "$POSTGRES_USER" --dbname postgres --set ON_ERROR_STOP=1 <<'SQL'
\getenv app_password APP_PASSWORD
\getenv migrator_password MIGRATOR_PASSWORD
CREATE ROLE wedding_app LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS PASSWORD :'app_password';
CREATE ROLE wedding_migrator LOGIN NOSUPERUSER CREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS PASSWORD :'migrator_password';
CREATE DATABASE wedding OWNER wedding_migrator;
\connect wedding
REVOKE ALL ON SCHEMA public FROM PUBLIC;
GRANT USAGE, CREATE ON SCHEMA public TO wedding_migrator;
GRANT USAGE ON SCHEMA public TO wedding_app;
SQL

unset APP_PASSWORD MIGRATOR_PASSWORD
