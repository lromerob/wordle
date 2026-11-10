"""Opt-in independent FIN-02B dump/restore with actual loopback Uvicorn HTTP."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import secrets
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
import uuid

from run_fin02a import ROOT, TABLES, apply_seed, digest, docker, snapshot, sql


def meta(container, field):
    return json.loads(docker("inspect", container, "--format", "{{json ." + field + "}}").stdout)


def wait_pg(container, database):
    for _ in range(100):
        if docker("exec", container, "pg_isready", "-h", "127.0.0.1", "-U", "fin02_owner", "-d", database, check=False).returncode == 0:
            return
        time.sleep(0.2)
    raise RuntimeError("PostgreSQL readiness timeout")


def create(name, run, database, password, network="none", *, publish=False):
    assert docker("inspect", name, check=False).returncode != 0, "Name already exists"
    env = os.environ.copy()
    env["POSTGRES_PASSWORD"] = password
    args = ["create", "--name", name, "--label", "wordle.fin02.disposable=" + run,
            "--network", network, "--memory", "512m", "--cpus", "1",
            "--tmpfs", "/var/lib/postgresql/data:rw,noexec,nosuid,size=256m",
            "--tmpfs", "/var/run/postgresql:rw,noexec,nosuid,size=16m",
            "--env", "POSTGRES_PASSWORD", "--env", "POSTGRES_USER=fin02_owner", "--env", "POSTGRES_DB=" + database]
    if publish: args += ["--publish", "127.0.0.1::5432"]
    return docker(*args, "postgres:16.15", env=env).stdout.decode().strip()


def http(opener, base, path, method="GET", payload=None, expected=200):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(base + path, data=data, method=method, headers={"Content-Type": "application/json"})
    try: response = opener.open(req, timeout=8)
    except urllib.error.HTTPError as error: response = error
    with response:
        assert response.status == expected, "Unexpected HTTP status: " + path
        return json.load(response)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-disposable-postgres", action="store_true", required=True)
    parser.parse_args()
    run = uuid.uuid4().hex[:12]
    database, prefix = "fin02b_" + run, "wordle-fin02b-" + run
    source = target = network = server = None
    result = {"result": "FIN-02B FAIL", "run": run}
    stage = "preflight"
    source_password, target_password, app_password = [secrets.token_urlsafe(32) for _ in range(3)]
    assert len({source_password, target_password, app_password}) == 3
    docker("info", "--format", "{{.ServerVersion}}")
    docker("image", "inspect", "postgres:16.15")  # Local image required; no implicit download.
    temp = tempfile.TemporaryDirectory(prefix="wordle-fin02b-")
    try:
        stage = "source bootstrap and seeds"
        source = create(prefix + "-source", run, database, source_password)
        docker("start", source)
        wait_pg(source, database)
        assert sql(source, database, "SELECT count(*) FROM information_schema.tables WHERE table_schema='public';").stdout.strip() == b"0"
        sql(source, database, (ROOT / "supabase/migrations/20261108000100_initial_wordle.sql").read_text(encoding="utf-8"))
        sql(source, database, (ROOT / "supabase/tests/schema_contracts.sql").read_text(encoding="utf-8"))
        apply_seed(source, database, authorized=True)
        initial = snapshot(source, database)
        apply_seed(source, database, authorized=True)
        assert snapshot(source, database) == initial
        assert {t: len(initial[t]) for t in TABLES} == {"palabras": 5, "partidas": 3, "intentos": 8, "estadisticas": 1}
        stage = "pg_dump"
        dump_options = ["--format=custom", "--no-owner", "--no-acl"]
        dump = docker("exec", source, "pg_dump", "-U", "fin02_owner", "-d", database, *dump_options).stdout
        assert dump.startswith(b"PGDMP")
        backup = Path(temp.name) / "synthetic.dump"
        backup.write_bytes(dump)
        backup_sha = hashlib.sha256(backup.read_bytes()).hexdigest()
        assert backup.stat().st_size == len(dump) > 0
        stage = "independent destination creation"
        assert docker("network", "inspect", prefix, check=False).returncode != 0
        network = docker("network", "create", "--label", "wordle.fin02.disposable=" + run, prefix).stdout.decode().strip()
        target = create(prefix + "-target", run, database, target_password, network, publish=True)
        assert target != source
        docker("start", target)
        wait_pg(target, database)
        for container in [source, target]:
            assert not meta(container, "Mounts")
            assert set(meta(container, "HostConfig.Tmpfs")) == {"/var/lib/postgresql/data", "/var/run/postgresql"}
        assert meta(source, "HostConfig.NetworkMode") == "none" and not meta(source, "HostConfig.PortBindings")
        bindings = meta(target, "NetworkSettings.Ports")["5432/tcp"]
        assert len(bindings) == 1 and bindings[0]["HostIp"] == "127.0.0.1"
        assert set(meta(target, "NetworkSettings.Networks")) == {prefix}
        db_port = bindings[0]["HostPort"]
        assert sql(target, database, "SELECT count(*) FROM information_schema.tables WHERE table_schema='public';").stdout.strip() == b"0"
        stage = "pg_restore"
        docker("exec", "-i", target, "pg_restore", "-U", "fin02_owner", "-d", database,
               "--exit-on-error", "--no-owner", "--no-acl", data=backup.read_bytes())
        assert hashlib.sha256(backup.read_bytes()).hexdigest() == backup_sha
        stage = "SQL comparison"
        sql(target, database, (ROOT / "supabase/tests/schema_contracts.sql").read_text(encoding="utf-8"))
        restored = snapshot(target, database)
        assert restored == initial
        orphan_query = "SELECT count(*) FROM public.intentos i LEFT JOIN public.partidas p ON p.id=i.partida_id WHERE p.id IS NULL OR i.usuario_id<>p.usuario_id;"
        assert sql(target, database, orphan_query).stdout.strip() == b"0"
        assert restored["sequence"]["last_value"] >= max(p["id"] for p in restored["palabras"])
        # Compare structures/constraints/indexes without OIDs or role/password metadata.
        schema_query = """SELECT json_build_object(
'columns',(SELECT json_agg(row_to_json(c) ORDER BY table_name,ordinal_position) FROM
 (SELECT table_name,column_name,ordinal_position,data_type,is_nullable,column_default,character_maximum_length,numeric_precision,numeric_scale FROM information_schema.columns WHERE table_schema='public') c),
'constraints',(SELECT json_agg(row_to_json(c) ORDER BY tab,definition) FROM
 (SELECT conrelid::regclass::text tab,pg_get_constraintdef(oid) definition FROM pg_constraint WHERE connamespace='public'::regnamespace) c),
'indexes',(SELECT json_agg(indexdef ORDER BY indexname) FROM pg_indexes WHERE schemaname='public'));"""
        schema_source = json.loads(sql(source, database, schema_query).stdout)
        assert schema_source == json.loads(sql(target, database, schema_query).stdout)
        stage = "application role bootstrap"
        # Reuse existing documented role/grants script; no Supabase policies or owner credentials in backend.
        env = os.environ.copy()
        env.update(WORDLE_APP_USER="wordle_app", WORDLE_APP_PASSWORD=app_password)
        docker("exec", "-i", "--env", "WORDLE_APP_USER", "--env", "WORDLE_APP_PASSWORD", target, "sh", "-s",
               data=(ROOT / "docker/postgres/30-app-role.sh").read_bytes().replace(b"\r\n", b"\n"), env=env)
        assert sql(target, database, "SELECT rolsuper FROM pg_roles WHERE rolname='wordle_app';").stdout.strip() == b"f"
        stage = "FastAPI TCP HTTP"
        with socket.socket() as reservation:
            reservation.bind(("127.0.0.1", 0))
            http_port = reservation.getsockname()[1]
        env = os.environ.copy()
        env.update(PGHOST="127.0.0.1", PGPORT=db_port, PGDATABASE=database, PGUSER="wordle_app",
                   PGPASSWORD=app_password, PGSSLMODE="disable", PYTHONDONTWRITEBYTECODE="1")
        launch = ("import asyncio,sys,uvicorn; sys.path.insert(0,sys.argv[1]); "
                  "config=uvicorn.Config('app.main:app',host='127.0.0.1',port=int(sys.argv[2]),workers=1,access_log=False); "
                  "asyncio.run(uvicorn.Server(config).serve(),loop_factory=asyncio.SelectorEventLoop)")
        server = subprocess.Popen([sys.executable, "-B", "-c", launch, str(ROOT / "backend"), str(http_port)],
                                  cwd=ROOT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        base = "http://127.0.0.1:" + str(http_port)
        for _ in range(80):
            assert server.poll() is None, "Temporary backend exited"
            try:
                assert http(opener, base, "/health") == {"status": "ok"}
                break
            except (OSError, urllib.error.URLError): time.sleep(0.1)
        else: raise RuntimeError("Backend readiness timeout")
        stats = initial["estadisticas"][0]
        stage = "HTTP restored statistics"
        actual_stats = http(opener, base, "/stats/fin02a-demo")
        assert all(actual_stats[k] == v for k,v in stats.items())
        assert actual_stats["porcentaje_victorias"] == 50
        stage = "HTTP restored ranking"
        ranking = http(opener, base, "/stats/ranking/global")["ranking"]
        assert ranking == [{"usuario_id":"fin02a-demo","partidas_ganadas":1,"partidas_jugadas":2,"racha_maxima":1}]
        stage = "HTTP restored games"
        for game in initial["partidas"]:
            state = http(opener, base, "/game/" + game["id"])
            expected = dict(game)
            if game["estado"] == "en_curso": expected.pop("palabra_secreta")
            assert state["partida"] == expected
            assert state["intentos"] == sorted([a for a in initial["intentos"] if a["partida_id"] == game["id"]], key=lambda a:a["numero"])
        assert snapshot(target, database) == initial, "Reads must not mutate DB"
        stage = "post-restore writes"
        active = "f102a000-0000-4000-8000-000000000003"
        body = {"partida_id":active,"usuario_id":"fin02a-demo","palabra":"ZZZZZ"}
        http(opener, base, "/game/intento", "POST", body, expected=400)
        assert snapshot(target, database) == initial
        body["palabra"] = "CASAS"
        won = http(opener, base, "/game/intento", "POST", body)
        assert won["estado"] == "ganada" and won["intentos_usados"] == 2
        after_stats = http(opener, base, "/stats/fin02a-demo")
        assert [after_stats[k] for k in ("partidas_jugadas","partidas_ganadas","intentos_promedio")] == [3,2,1.5]
        new = http(opener, base, "/game/nueva?usuario_id=fin02b-new", "POST")
        assert http(opener, base, "/game/" + new["partida_id"])["partida"]["estado"] == "en_curso"
        assert len(snapshot(target, database)["intentos"]) == 9
        assert snapshot(source, database) == initial, "Source changed after backup"
        result.update(result="FIN-02B PASS", source=prefix+"-source",target=prefix+"-target",database=database,
                      postgres=sql(source,database,"SHOW server_version;").stdout.decode().strip(),
                      backup_format="custom",backup_options=dump_options,backup_bytes=len(dump),backup_sha256=backup_sha,
                      source_data_sha256=digest(initial),restored_data_sha256=digest(restored),
                      schema_match=True,source_unchanged=True,role_non_superuser=True,
                      counts={t:len(initial[t]) for t in TABLES},sequence=initial["sequence"],
                      http_checks=["health","three restored games","restored stats","ranking","invalid guess 400/no write","restored active game victory","stats mean 1.5","new game UUID"],
                      backend_port=http_port,postgres_port=int(db_port))
    except Exception as error:
        result.update(failed_stage=stage,error_category=type(error).__name__)
        # Sanitized diagnostics only; never print SQL/passwords/process env or raw logs.
    finally:
        try:
            if server:
                server.terminate()
                try: server.wait(timeout=10)
                except subprocess.TimeoutExpired: server.kill();server.wait(timeout=5)
            for container in [target,source]:
                if container:
                    assert meta(container,"Config.Labels").get("wordle.fin02.disposable")==run
                    docker("rm","--force",container)
                    assert docker("inspect",container,check=False).returncode != 0
            if network:
                docker("network","rm",network)
                assert docker("network","inspect",network,check=False).returncode != 0
            temp.cleanup()
            result["cleanup"]="PASS: own backend, two containers, network and temporary dump removed"
        except Exception:
            result["result"]="FIN-02B FAIL"
            result["cleanup"]="FAILED: inspect owned resources before any retry"
    print(json.dumps(result))
    return 0 if result["result"]=="FIN-02B PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
