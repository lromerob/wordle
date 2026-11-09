#!/bin/sh
set -eu
# Runs only during the official image's first initialization of an empty PGDATA.
# psql reads the generated password from environment, not command-line arguments.
psql --no-psqlrc --set=ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<'SQL'
\getenv app_user WORDLE_APP_USER
\getenv app_password WORDLE_APP_PASSWORD
CREATE ROLE :"app_user" LOGIN PASSWORD :'app_password';
GRANT USAGE ON SCHEMA public TO :"app_user";
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO :"app_user";
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO :"app_user";
SQL
