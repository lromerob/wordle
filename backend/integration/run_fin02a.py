"""Explicit FIN-02A validation; owns a new PG16 tmpfs container, no destination argument."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parents[2]
SEED = ROOT / "backend/integration/fin02a_seed.sql"
TABLES = ("palabras", "partidas", "intentos", "estadisticas")


def docker(*args, data=None, env=None, check=True):
    result = subprocess.run(["docker", *args], input=data, capture_output=True,
                            env=env, timeout=90)
    if check and result.returncode:
        raise RuntimeError("Docker/SQL operation failed (details withheld): " + args[0])
    return result


def apply_seed(container, database, *, authorized=False):
    """For reuse by FIN-02B only on a separately verified disposable container."""
    if not authorized:
        raise PermissionError("Explicit authorization required before inspecting or connecting")
    if not container or container.startswith("-"):
        raise ValueError("Container ID required")
    import re
    if not re.fullmatch(r"fin02[ab]_[0-9a-f]{12}", database):
        raise ValueError("Only disposable FIN-02 databases allowed")
    # Inspect only non-secret metadata, never Config.Env.
    inspect = lambda field: json.loads(docker("inspect", container, "--format", "{{json ." + field + "}}").stdout)
    labels = inspect("Config.Labels") or {}
    run = database.split("_", 1)[1]
    if labels.get("wordle.fin02.disposable") != run:
        raise ValueError("Disposable ownership label mismatch")
    if inspect("HostConfig.NetworkMode") != "none" or inspect("HostConfig.PortBindings"):
        raise ValueError("Seed container must have no network or published ports")
    if inspect("Mounts") or set(inspect("HostConfig.Tmpfs")) != {"/var/lib/postgresql/data", "/var/run/postgresql"}:
        raise ValueError("Only dedicated tmpfs storage allowed")
    return sql(container, database,
               "SET wordle.synthetic_seed='authorized-disposable';\n" + SEED.read_text(encoding="utf-8"))


def sql(container, database, source, *, check=True):
    return docker("exec", "-i", container, "psql", "-X", "-qAt", "-v", "ON_ERROR_STOP=1",
                  "-U", "fin02_owner", "-d", database, data=source.encode("utf-8"), check=check)


def snapshot(container, database):
    rows = {}
    for table in TABLES:
        # Table names are fixed constants, not user input.
        query = "SELECT coalesce(jsonb_agg(to_jsonb(t) ORDER BY id),'[]'::jsonb) FROM public." + table + " t;"
        rows[table] = json.loads(sql(container, database, query).stdout)
    rows["sequence"] = json.loads(sql(container, database,
        "SELECT row_to_json(s) FROM (SELECT last_value,is_called FROM public.palabras_id_seq) s;").stdout)
    return rows


def digest(state):
    return hashlib.sha256(json.dumps(state, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def validate(state):
    # One foreign sentinel per table remains outside the seed set.
    assert {t: len(state[t]) for t in TABLES} == {"palabras": 6, "partidas": 4, "intentos": 9, "estadisticas": 2}
    games = {p["id"]: p for p in state["partidas"]}
    sys.path.insert(0, str(ROOT / "backend"))
    from app.routers.game import evaluar_intento
    for attempt in state["intentos"]:
        game = games[attempt["partida_id"]]
        assert attempt["usuario_id"] == game["usuario_id"]
        assert attempt["resultado"] == evaluar_intento(game["palabra_secreta"], attempt["palabra"])
    demo = [p for p in games.values() if p["usuario_id"] == "fin02a-demo"]
    assert sorted(p["estado"] for p in demo) == ["en_curso", "ganada", "perdida"]
    for game in demo:
        attempts = [a for a in state["intentos"] if a["partida_id"] == game["id"]]
        assert sorted(a["numero"] for a in attempts) == list(range(1, game["intentos_usados"] + 1))
        assert len(attempts) == game["intentos_usados"] <= 6
        won = any(a["palabra"] == game["palabra_secreta"] for a in attempts)
        assert won == (game["estado"] == "ganada")
        if game["estado"] == "perdida": assert len(attempts) == 6
    stats = next(s for s in state["estadisticas"] if s["usuario_id"] == "fin02a-demo")
    assert [stats[k] for k in ("partidas_jugadas", "partidas_ganadas", "racha_actual", "racha_maxima", "intentos_promedio")] == [2, 1, 0, 1, 1]
    assert state["sequence"]["last_value"] >= max(p["id"] for p in state["palabras"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-disposable-postgres", action="store_true", required=True)
    parser.parse_args()  # Refuses execution before any Docker call without opt-in.
    run = uuid.uuid4().hex[:12]
    name, database = "wordle-fin02a-" + run, "fin02a_" + run
    image, container = "postgres:16.15", None
    assert docker("inspect", name, check=False).returncode != 0, "Name already exists"
    docker("info", "--format", "{{.ServerVersion}}")
    docker("image", "inspect", image)  # Do not download implicitly.
    try:
        env = os.environ.copy()
        env["POSTGRES_PASSWORD"] = secrets.token_urlsafe(32)
        container = docker("create", "--name", name, "--label", "wordle.fin02.disposable=" + run,
            "--network", "none", "--memory", "512m", "--cpus", "1",
            "--tmpfs", "/var/lib/postgresql/data:rw,noexec,nosuid,size=256m",
            "--tmpfs", "/var/run/postgresql:rw,noexec,nosuid,size=16m",
            "--env", "POSTGRES_PASSWORD", "--env", "POSTGRES_USER=fin02_owner",
            "--env", "POSTGRES_DB=" + database, image, env=env).stdout.decode().strip()
        docker("start", container)
        for _ in range(100):
            if docker("exec", container, "pg_isready", "-U", "fin02_owner", "-d", database, check=False).returncode == 0:
                # Wait for the final server, not initdb's temporary socket server.
                if docker("exec", container, "pg_isready", "-h", "127.0.0.1", "-U", "fin02_owner", "-d", database, check=False).returncode == 0: break
            time.sleep(0.2)
        else: raise RuntimeError("Temporary PostgreSQL not ready")
        assert sql(container, database, "SELECT count(*) FROM information_schema.tables WHERE table_schema='public';").stdout.strip() == b"0"
        sql(container, database, (ROOT / "supabase/migrations/20261108000100_initial_wordle.sql").read_text(encoding="utf-8"))
        sql(container, database, (ROOT / "supabase/tests/schema_contracts.sql").read_text(encoding="utf-8"))
        # Foreign data are inserted once solely to prove non-interference.
        sql(container, database, """INSERT INTO public.palabras(palabra) VALUES ('LUNAS');
INSERT INTO public.partidas VALUES ('eeeeeeee-0000-4000-8000-000000000001','foreign-demo','LUNAS',1,'en_curso','2025-01-01');
INSERT INTO public.intentos VALUES ('eeeeeeee-0000-4000-8000-000000000002','eeeeeeee-0000-4000-8000-000000000001','foreign-demo',1,'LUNAS','[{"letra":"L","estado":"correcto"},{"letra":"U","estado":"correcto"},{"letra":"N","estado":"correcto"},{"letra":"A","estado":"correcto"},{"letra":"S","estado":"correcto"}]','2025-01-01');
INSERT INTO public.estadisticas VALUES ('eeeeeeee-0000-4000-8000-000000000003','foreign-demo',0,0,0,0,0,'2025-01-01');""")
        foreign = snapshot(container, database)
        before = digest(foreign)
        try: apply_seed(container, database)
        except PermissionError: pass
        else: raise AssertionError("Missing authorization accepted")
        denied = sql(container, database, SEED.read_text(encoding="utf-8"), check=False)
        assert denied.returncode != 0 and digest(snapshot(container, database)) == before
        assert b"requires explicitly authorized" in denied.stderr
        for wrong in ["wordle", "pg05_private", "wordle_pg06"]:
            try: apply_seed(container, wrong, authorized=True)
            except ValueError: pass
            else: raise AssertionError("Non-disposable destination accepted")
        states = []
        for _ in range(3):
            apply_seed(container, database, authorized=True)
            state = snapshot(container, database)
            validate(state)
            for table in TABLES:
                assert all(row in state[table] for row in foreign[table])
            states.append(digest(state))
        assert len(set(states)) == 1
        # Deliberate collision belongs solely to this test; seed must not repair/overwrite it.
        sql(container, database, "UPDATE public.partidas SET estado='collision' WHERE id='f102a000-0000-4000-8000-000000000001';")
        changed = digest(snapshot(container, database))
        try: apply_seed(container, database, authorized=True)
        except RuntimeError: pass
        else: raise AssertionError("Incompatible existing data accepted")
        assert digest(snapshot(container, database)) == changed
        version = sql(container, database, "SHOW server_version;").stdout.decode().strip()
        print(json.dumps({"result":"FIN-02A PASS", "container":name, "database":database,
              "postgres":version, "seed_counts":{"palabras":5,"partidas":3,"intentos":8,"estadisticas":1},
              "loads":3,"snapshots_sha256":states,"foreign_rows_preserved":4,
              "authorization_rejection":True,"collision_rejection":True,"sequence_in_snapshot":True}))
    finally:
        if container:
            labels = json.loads(docker("inspect", container, "--format", "{{json .Config.Labels}}").stdout)
            assert labels.get("wordle.fin02.disposable") == run
            docker("rm", "--force", container)
            assert docker("inspect", container, check=False).returncode != 0
            print("Cleanup PASS: only owned container removed; absence verified; no volumes or networks created")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        print("FIN-02A FAIL: validation or infrastructure error; details withheld to avoid credentials", file=sys.stderr)
        raise SystemExit(1)
