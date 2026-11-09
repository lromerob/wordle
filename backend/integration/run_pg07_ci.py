"""PG-07: run unchanged PG-04 tests against an explicitly labelled tmpfs CI service."""
import argparse
import asyncio
from contextlib import ExitStack
import json
import logging
import os
import secrets
import socket
import sys
import unittest
from unittest.mock import patch

from run_pg04 import ROOT, docker, prepare, verify_empty_database, outage
import psycopg
from psycopg.rows import dict_row


async def seed(config):
    async with await psycopg.AsyncConnection.connect(**config["admin"]) as connection:
        await connection.execute((ROOT / "docker/postgres/20-demo-words.sql").read_text(encoding="utf-8"))
        row = await (await connection.execute("SELECT count(*) AS n FROM public.palabras")).fetchone()
        assert row["n"] == 5
    print("Existing demo seed: five words; each PG-04 test then installs its own five-word fixture", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--service-container", required=True)
    args = parser.parse_args()
    container = args.service_container
    # Inspect metadata only. Never inspect .Config.Env or accept a host/DSN.
    assert container and not container.startswith("-")
    identifier = docker("inspect", container, "--format", "{{.Id}}").stdout.strip()
    assert len(identifier) == 64
    container = identifier
    labels = json.loads(docker("inspect", container, "--format", "{{json .Config.Labels}}").stdout)
    assert labels.get("wordle.pg07") == "ci", "Only the labelled PG-07 service is allowed"
    image = docker("inspect", container, "--format", "{{.Config.Image}}").stdout.strip()
    assert image == "postgres:16.15"
    mounts = json.loads(docker("inspect", container, "--format", "{{json .Mounts}}").stdout)
    assert all(m["Type"] == "tmpfs" for m in mounts), "Persistent/bind mounts forbidden"
    tmpfs = json.loads(docker("inspect", container, "--format", "{{json .HostConfig.Tmpfs}}").stdout)
    assert "/var/lib/postgresql/data" in tmpfs
    bindings = json.loads(docker("inspect", container, "--format", "{{json .NetworkSettings.Ports}}").stdout)["5432/tcp"]
    assert len(bindings) == 1 and bindings[0]["HostIp"] == "127.0.0.1"
    port = int(bindings[0]["HostPort"])
    password = os.environ["PG07_CI_ADMIN_PASSWORD"]
    assert password
    app_password = secrets.token_urlsafe(32)
    common = dict(host="127.0.0.1", port=port, dbname="pg07_ci", passfile=os.devnull,
                  sslmode="disable", connect_timeout=2, autocommit=True, row_factory=dict_row)
    config = {"database":"pg07_ci", "admin":dict(common, user="pg04_owner", password=password),
              "app_password":app_password, "environment":{"PGHOST":"127.0.0.1", "PGPORT":str(port),
              "PGDATABASE":"pg07_ci", "PGUSER":"wordle_pg04_app", "PGPASSWORD":app_password, "PGSSLMODE":"disable"}}
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    logging.getLogger("psycopg.pool").setLevel(logging.ERROR)
    original_connect = psycopg.AsyncConnection.connect
    async def only_service(conninfo="", **kwargs):
        assert not conninfo and kwargs.get("host") == "127.0.0.1"
        assert int(kwargs.get("port", 0)) == port and kwargs.get("dbname") == "pg07_ci"
        assert kwargs.get("user") in ("pg04_owner", "wordle_pg04_app")
        return await original_connect(conninfo, **kwargs)
    original_socket = socket.socket.connect
    def loopback_only(sock, address):
        if isinstance(address, tuple) and address[0] in ("127.0.0.1", "::1"):
            return original_socket(sock, address)
        raise AssertionError("External socket forbidden")
    with ExitStack() as guards:
        guards.enter_context(patch("psycopg.AsyncConnection.connect", side_effect=only_service))
        guards.enter_context(patch("socket.socket.connect", new=loopback_only))
        guards.enter_context(patch("socket.socket.connect_ex", side_effect=AssertionError("External connect_ex forbidden")))
        guards.enter_context(patch("socket.getaddrinfo", side_effect=AssertionError("DNS forbidden")))
        guards.enter_context(patch("dotenv.load_dotenv", side_effect=AssertionError("dotenv forbidden")))
        # prepare refuses any public table before DDL. Never truncate an existing schema.
        asyncio.run(prepare(config))
        asyncio.run(seed(config))
        import test_postgres_integration as cases
        cases.CONFIG = config
        result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(cases))
        if result.testsRun != 11 or result.skipped or not result.wasSuccessful():
            raise RuntimeError("Expected eleven passing integration tests, zero skips")
        asyncio.run(verify_empty_database(config))
        # Last operation: stop only this job's verified service, never another DB.
        asyncio.run(outage(config, container))
        logs_result = docker("logs", container)
        logs = logs_result.stdout + logs_result.stderr
        assert logs.count("division by zero") == 3 and "deadlock detected" not in logs
        print("PG-07: eleven real tests + isolated server outage PASS; no raw DB logs emitted", flush=True)
    # GitHub Actions owns service cleanup; the local validation wrapper owns its IDs.


if __name__ == "__main__":
    main()
