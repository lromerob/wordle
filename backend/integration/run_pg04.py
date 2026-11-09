"""Opt-in runner: owns one disposable PG16 container/network; never accepts a DSN."""
import argparse
import asyncio
from contextlib import ExitStack
import json
import logging
import os
from pathlib import Path
import secrets
import socket
import subprocess
import sys
import time
import unittest
from unittest.mock import patch
import uuid

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
import psycopg
from psycopg import sql
from psycopg.rows import dict_row


def docker(*args, env=None, timeout=60, check=True):
    result = subprocess.run(["docker", *args], capture_output=True, text=True, env=env, timeout=timeout)
    if check and result.returncode:
        # Never print Docker environment/config or SQL containing test passwords.
        raise RuntimeError("Docker operation failed: " + " ".join(args[:2]))
    return result


async def prepare(config):
    deadline = time.monotonic() + 40
    while True:
        try:
            conn = await psycopg.AsyncConnection.connect(**config["admin"])
            break
        except psycopg.OperationalError:
            if time.monotonic() >= deadline:
                raise RuntimeError("Temporary PostgreSQL did not become ready") from None
            await asyncio.sleep(0.25)
    async with conn:
        assert (await (await conn.execute("SELECT count(*) AS n FROM information_schema.tables WHERE table_schema='public'")).fetchone())["n"] == 0
        await conn.execute((ROOT / "supabase/migrations/20261108000100_initial_wordle.sql").read_text(encoding="utf-8"))
        await conn.execute((ROOT / "supabase/tests/schema_contracts.sql").read_text(encoding="utf-8"))
        await conn.execute(sql.SQL("CREATE ROLE wordle_pg04_app LOGIN PASSWORD {}").format(sql.Literal(config["app_password"])))
        await conn.execute("GRANT USAGE ON SCHEMA public TO wordle_pg04_app")
        await conn.execute("GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO wordle_pg04_app")
        await conn.execute("GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO wordle_pg04_app")
        version = (await (await conn.execute("SELECT version() AS v")).fetchone())["v"]
        isolation = (await (await conn.execute("SHOW transaction_isolation")).fetchone())["transaction_isolation"]
        assert isolation == "read committed"
        assert (await (await conn.execute("SELECT current_database() AS db")).fetchone())["db"] == config["database"]
        print("PostgreSQL:", version, flush=True)
        print("Schema catalog contracts: PASS; isolation:", isolation, flush=True)


async def verify_empty_database(config):
    async with await psycopg.AsyncConnection.connect(**config["admin"]) as connection:
        for table in ("intentos", "partidas", "estadisticas", "palabras"):
            row = await (await connection.execute(sql.SQL("SELECT count(*) AS n FROM public.{}").format(sql.Identifier(table)))).fetchone()
            assert row["n"] == 0
        row = await (await connection.execute("SELECT deadlocks FROM pg_stat_database WHERE datname=current_database()")).fetchone()
        assert row["deadlocks"] == 0
    print("After tests: all four tables empty; recorded database deadlocks: zero", flush=True)


async def outage(config, container):
    import httpx
    from app.main import app
    with patch.dict(os.environ, config["environment"]):
        async with app.router.lifespan_context(app):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test", trust_env=False) as client:
                response = await client.get("/stats/outage-check")
                assert response.status_code == 200
                await asyncio.to_thread(docker, "stop", "--time", "3", container)
                response = await asyncio.wait_for(client.post("/game/nueva", params={"usuario_id": "outage-check"}), timeout=8)
                assert response.status_code == 500
                assert response.json() == {"detail": "Base de datos no disponible"}
                assert (await client.get("/health")).json() == {"status": "ok"}
            pool = app.state.db_pool
        assert pool.closed
    print("Real server outage: sanitized 500 + process health 200 + pool closed: PASS", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-disposable-postgres", action="store_true", required=True)
    parser.parse_args()
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    run_id = uuid.uuid4().hex[:12]
    name = "wordle-pg04-" + run_id
    database = "pg04_" + run_id
    network = container = None
    admin_password, app_password = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
    image = "postgres:16"
    logging.getLogger("psycopg.pool").setLevel(logging.ERROR)
    try:
        if docker("image", "inspect", image, check=False).returncode:
            docker("pull", image, timeout=240)
        image_id = json.loads(docker("image", "inspect", image, "--format", "{{json .Id}}").stdout)
        network = docker("network", "create", "--label", "wordle.pg04.run=" + run_id, name).stdout.strip()
        env = os.environ.copy()
        env["POSTGRES_PASSWORD"] = admin_password
        container = docker(
            "create", "--name", name, "--label", "wordle.pg04.run=" + run_id,
            "--network", network, "--publish", "127.0.0.1::5432", "--memory", "512m", "--cpus", "1",
            "--tmpfs", "/var/lib/postgresql/data:rw,noexec,nosuid,size=256m",
            "--tmpfs", "/var/run/postgresql:rw,noexec,nosuid,size=16m",
            "--env", "POSTGRES_PASSWORD", "--env", "POSTGRES_USER=pg04_owner", "--env", "POSTGRES_DB=" + database,
            image, env=env,
        ).stdout.strip()
        docker("start", container)
        # Inspect only non-secret fields, never .Config.Env.
        settings = json.loads(docker("inspect", container, "--format", '{{json .NetworkSettings.Ports}}').stdout)
        bindings = settings["5432/tcp"]
        assert len(bindings) == 1 and bindings[0]["HostIp"] == "127.0.0.1"
        port = int(bindings[0]["HostPort"])
        mounts = json.loads(docker("inspect", container, "--format", '{{json .Mounts}}').stdout)
        assert all(m["Type"] == "tmpfs" for m in mounts), "Persistent mounts forbidden"
        tmpfs = json.loads(docker("inspect", container, "--format", "{{json .HostConfig.Tmpfs}}").stdout)
        assert set(tmpfs) == {"/var/lib/postgresql/data", "/var/run/postgresql"}
        networks = json.loads(docker("inspect", container, "--format", '{{json .NetworkSettings.Networks}}').stdout)
        assert list(networks) == [name]
        members = json.loads(docker("network", "inspect", network, "--format", "{{json .Containers}}").stdout)
        assert set(members) == {container}
        print("Temporary container:", name, "image:", image_id, "binding: 127.0.0.1:" + str(port), flush=True)
        common = dict(host="127.0.0.1", port=port, dbname=database, passfile=os.devnull, sslmode="disable", connect_timeout=2, autocommit=True, row_factory=dict_row)
        config = {"database": database, "admin": dict(common, user="pg04_owner", password=admin_password), "app_password": app_password,
                  "environment": {"PGHOST": "127.0.0.1", "PGPORT": str(port), "PGDATABASE": database, "PGUSER": "wordle_pg04_app", "PGPASSWORD": app_password, "PGSSLMODE": "disable"}}
        original_connect = psycopg.AsyncConnection.connect
        async def only_temporary(conninfo="", **kwargs):
            assert not conninfo, "DSNs forbidden"
            assert kwargs.get("host") == "127.0.0.1" and int(kwargs.get("port", 0)) == port
            assert kwargs.get("dbname") == database and kwargs.get("user") in ("pg04_owner", "wordle_pg04_app")
            return await original_connect(conninfo, **kwargs)
        original_socket = socket.socket.connect
        def loopback_only(sock, address):
            if isinstance(address, tuple) and address[0] in ("127.0.0.1", "::1"):
                return original_socket(sock, address)
            raise AssertionError("External socket forbidden")
        with ExitStack() as guards:
            guards.enter_context(patch("psycopg.AsyncConnection.connect", side_effect=only_temporary))
            guards.enter_context(patch("socket.socket.connect", new=loopback_only))
            guards.enter_context(patch("socket.socket.connect_ex", side_effect=AssertionError("External connect_ex forbidden")))
            guards.enter_context(patch("socket.getaddrinfo", side_effect=AssertionError("DNS forbidden")))
            guards.enter_context(patch("dotenv.load_dotenv", side_effect=AssertionError("dotenv forbidden")))
            asyncio.run(prepare(config))
            import test_postgres_integration as cases
            cases.CONFIG = config
            result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(cases))
            if not result.wasSuccessful() or result.skipped:
                raise RuntimeError("Integration tests failed; see individual test output")
            asyncio.run(verify_empty_database(config))
            asyncio.run(outage(config, container))
            log_result = docker("logs", container)
            logs = log_result.stdout + log_result.stderr
            assert logs.count("division by zero") == 3
            assert "deadlock detected" not in logs
            print("Server logs: three expected SQL division-by-zero errors, no deadlock detected", flush=True)
        print("PG-04 integration suite:", result.testsRun, "passed, zero skipped", flush=True)
    finally:
        # IDs returned by this execution only: never enumerate/delete unrelated resources.
        try:
            if container:
                docker("rm", "--force", container)
                assert docker("inspect", container, check=False).returncode != 0
                print("Cleanup: dedicated container removed and absence verified", flush=True)
        finally:
            if network:
                docker("network", "rm", network)
                assert docker("network", "inspect", network, check=False).returncode != 0
                print("Cleanup: dedicated network removed and absence verified", flush=True)


if __name__ == "__main__":
    main()
