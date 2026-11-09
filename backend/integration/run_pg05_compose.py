"""Staged PG-05 smoke: isolated new Compose project; never removes data volumes."""
import argparse
import json
import os
from pathlib import Path
import secrets
import subprocess
import urllib.error
import urllib.parse
import urllib.request
import uuid

ROOT = Path(__file__).resolve().parents[2]
WORDS = ("CASAS", "GATOS", "NIÑOS", "PERRO", "SACAS")


def command(args, *, input=None, check=True, timeout=180):
    result = subprocess.run(args, input=input, capture_output=True, timeout=timeout)
    if check and result.returncode:
        # No resolved Compose config, environment, SQL passwords or raw DB logs.
        raise RuntimeError("Command failed: " + " ".join(str(a) for a in args[:3]))
    return result


def compose(state, *args, timeout=180, check=True, input=None):
    return command(["docker", "compose", "--env-file", state["env_file"], "--project-name", state["project"], "--file", str(ROOT / "compose.yaml"), *args], timeout=timeout, check=check, input=input)


def port(state):
    binding = compose(state, "port", "frontend", "8080").stdout.decode().strip()
    assert binding.startswith("127.0.0.1:")
    return "http://" + binding


def http(base, path, body=None, method="GET"):
    assert base.startswith("http://127.0.0.1:") and not urllib.parse.urlsplit(base).username
    request = urllib.request.Request(base + path, data=json.dumps(body).encode() if body is not None else None, method=method, headers={"Content-Type": "application/json"})
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open(request, timeout=15) as response:
            raw = response.read()
            return response.status, json.loads(raw) if "application/json" in response.headers.get("Content-Type", "") else raw.decode()
    except urllib.error.HTTPError as error:
        return error.code, json.loads(error.read())


def query(state, sql, database=""):
    return compose(
        state, "exec", "--no-TTY", "postgres", "sh", "-c",
        'exec psql --no-psqlrc --username "$POSTGRES_USER" --dbname "${1:-$POSTGRES_DB}" --set=ON_ERROR_STOP=1 --tuples-only --no-align', "pg05-query", database,
        input=sql.encode(), timeout=30,
    ).stdout.decode().strip()


def snapshot(state, database=""):
    values = {}
    for table in ("palabras", "partidas", "intentos", "estadisticas"):
        values[table] = json.loads(query(state, "SELECT coalesce(json_agg(r ORDER BY id),'[]'::json) FROM (SELECT * FROM public." + table + ") r;", database))
    return values


def verify_resources(state):
    ids = compose(state, "ps", "--quiet").stdout.decode().split()
    assert len(ids) == 3
    for identifier in ids:
        data = json.loads(command(["docker", "inspect", identifier, "--format", '{{json .State.Health.Status}}']).stdout)
        assert data == "healthy"
        labels = json.loads(command(["docker", "inspect", identifier, "--format", '{{json .Config.Labels}}']).stdout)
        assert labels["com.docker.compose.project"] == state["project"]
        service = labels["com.docker.compose.service"]
        bindings = json.loads(command(["docker", "inspect", identifier, "--format", '{{json .HostConfig.PortBindings}}']).stdout)
        assert not bindings if service != "frontend" else all(p["HostIp"] == "127.0.0.1" for ports in bindings.values() for p in ports)
        networks = json.loads(command(["docker", "inspect", identifier, "--format", '{{json .NetworkSettings.Networks}}']).stdout)
        expected = {state["project"] + "_default"} | ({state["project"] + "_ingress"} if service == "frontend" else set())
        assert set(networks) == expected
    internal = json.loads(command(["docker", "network", "inspect", state["project"] + "_default", "--format", '{{json .Internal}}']).stdout)
    assert internal is True
    print("Three healthy services; PostgreSQL/backend unpublished; internal data network verified.", flush=True)


def start():
    project = "wordle-pg05-" + uuid.uuid4().hex[:10]
    volume = project + "_postgres_data"
    if command(["docker", "volume", "inspect", volume], check=False).returncode == 0:
        raise RuntimeError("Volume already exists: authorization required before reuse")
    private = Path(os.environ["LOCALAPPDATA"]) / "WordlePG05" / project
    private.mkdir(parents=True, exist_ok=False)
    env_file = private / "compose.env"
    env_file.write_text("COMPOSE_PROJECT_NAME=" + project + "\nWORDLE_DB_NAME=wordle\nWORDLE_DB_OWNER=wordle_owner\nWORDLE_DB_USER=wordle_app\nWORDLE_HTTP_PORT=0\nWORDLE_DB_ADMIN_PASSWORD=" + secrets.token_urlsafe(32) + "\nWORDLE_DB_PASSWORD=" + secrets.token_urlsafe(32) + "\n", encoding="utf-8")
    state = {"project": project, "volume": volume, "env_file": str(env_file), "state_file": str(private / "state.json")}
    Path(state["state_file"]).write_text(json.dumps(state), encoding="utf-8")
    # Locator contains no secret values. It is outside the repository.
    import tempfile
    Path(tempfile.gettempdir(), "wordle-pg05-state-location.txt").write_text(state["state_file"], encoding="utf-8")
    print("Project:", project, "volume:", volume, "state:", state["state_file"], flush=True)
    try:
        compose(state, "config", "--quiet")
        compose(state, "build", timeout=360)
        compose(state, "up", "--detach", "--wait", "--wait-timeout", "120", timeout=150)
        verify_resources(state)
        print("Frontend:", port(state), flush=True)
    except BaseException:
        compose(state, "down", "--timeout", "15", check=False)
        raise
    return state


def smoke(state):
    base = port(state)
    assert http(base, "/")[0] == 200
    assert http(base, "/api/health") == (200, {"status": "ok"})
    for winning in (True, False):
        user = "pg05-api-" + uuid.uuid4().hex[:8] + "-" + str(winning)
        status, data = http(base, "/api/game/nueva?usuario_id=" + user, method="POST")
        assert status == 200
        identifier = str(uuid.UUID(data["partida_id"]))
        # Test-only SQL observation of fixture data; no change to random production rules.
        solution = query(state, "SELECT palabra_secreta FROM public.partidas WHERE id='" + identifier + "';")
        word = solution if winning else next(w for w in WORDS if w != solution)
        status, invalid = http(base, "/api/game/intento", {"partida_id": identifier, "usuario_id": user, "palabra": "ZZZZZ"}, "POST")
        assert status == 400 and invalid["detail"] == "Palabra no válida"
        for number in range(1, 2 if winning else 7):
            status, result = http(base, "/api/game/intento", {"partida_id": identifier, "usuario_id": user, "palabra": word}, "POST")
            assert status == 200 and result["intentos_usados"] == number
        assert result["estado"] == ("ganada" if winning else "perdida")
        status, stats = http(base, "/api/stats/" + user)
        assert status == 200 and stats["partidas_jugadas"] == 1 and stats["partidas_ganadas"] == int(winning)
        status, stored = http(base, "/api/game/" + identifier)
        assert status == 200 and len(stored["intentos"]) == (1 if winning else 6)
    assert http(base, "/api/stats/ranking/global")[0] == 200
    assert query(state, "SELECT count(*) FROM public.palabras;") == "5"
    print("Real TCP /api smoke: frontend, health, invalid words, win, loss, stats and ranking PASS.", flush=True)


def verify_api_snapshot(state, values):
    base = port(state)
    for row in values["partidas"]:
        status, data = http(base, "/api/game/" + row["id"])
        assert status == 200 and data["partida"]["estado"] == row["estado"]
        assert data["partida"]["intentos_usados"] == row["intentos_usados"]
    for row in values["estadisticas"]:
        status, data = http(base, "/api/stats/" + urllib.parse.quote(row["usuario_id"]))
        assert status == 200
        for field in ("id", "usuario_id", "partidas_jugadas", "partidas_ganadas", "racha_actual", "racha_maxima", "intentos_promedio"):
            assert data[field] == row[field]


def persist(state):
    before = snapshot(state)
    assert before["partidas"] and before["intentos"] and before["estadisticas"]
    compose(state, "restart", timeout=120)
    compose(state, "up", "--detach", "--wait", "--wait-timeout", "120", timeout=150)
    assert snapshot(state) == before
    compose(state, "down", "--timeout", "15")
    assert command(["docker", "volume", "inspect", state["volume"]], check=False).returncode == 0
    compose(state, "up", "--detach", "--wait", "--wait-timeout", "120", timeout=150)
    verify_resources(state)
    assert snapshot(state) == before
    base = port(state)
    verify_api_snapshot(state, before)
    logs = compose(state, "logs", "--no-color", "postgres").stdout.decode()
    assert "Skipping initialization" in logs
    assert "running /docker-entrypoint-initdb.d/10-wordle-schema.sql" not in logs
    counts = {table: len(rows) for table, rows in before.items()}
    state["persistence_counts"] = counts
    Path(state["state_file"]).write_text(json.dumps(state), encoding="utf-8")
    print("Restart + down/up: identical full database snapshots; schema/seed not rerun. Counts:", counts, flush=True)
    print("Frontend after recreation:", base, flush=True)


def backup_restore(state):
    # Native tool demonstration on a NEW database in this owned test cluster only.
    source = snapshot(state)
    dump = compose(state, "exec", "--no-TTY", "postgres", "sh", "-c",
                   'exec pg_dump --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" --format=custom --no-owner --no-acl').stdout
    backup = Path(state["state_file"]).parent / "pg05-demo.dump"
    with backup.open("xb") as output:
        output.write(dump)
    restored = "pg05_restore_" + uuid.uuid4().hex[:10]
    created = False
    try:
        compose(state, "exec", "--no-TTY", "postgres", "sh", "-c",
                'exec createdb --username "$POSTGRES_USER" --maintenance-db "$POSTGRES_DB" "$1"', "pg05-restore", restored)
        created = True
        compose(state, "exec", "--no-TTY", "postgres", "sh", "-c",
                'exec pg_restore --username "$POSTGRES_USER" --dbname "$1" --exit-on-error --no-owner --no-acl', "pg05-restore", restored, input=dump)
        assert snapshot(state, restored) == source
        assert snapshot(state) == source
        state["backup_file"] = str(backup)
        Path(state["state_file"]).write_text(json.dumps(state), encoding="utf-8")
        print("Native pg_dump/pg_restore: identical tables in a new restore DB; source unchanged. Backup:", backup, flush=True)
    finally:
        if created:
            compose(state, "exec", "--no-TTY", "postgres", "sh", "-c",
                    'exec dropdb --username "$POSTGRES_USER" --maintenance-db "$POSTGRES_DB" "$1"', "pg05-restore", restored)


def stop(state):
    compose(state, "down", "--timeout", "15")  # Deliberately never --volumes / -v.
    assert not command(["docker", "ps", "--all", "--filter", "label=com.docker.compose.project=" + state["project"], "--quiet"]).stdout.strip()
    assert not command(["docker", "network", "ls", "--filter", "label=com.docker.compose.project=" + state["project"], "--quiet"]).stdout.strip()
    assert command(["docker", "volume", "inspect", state["volume"]], check=False).returncode == 0
    print("Project containers/networks removed; retained volume:", state["volume"], flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("start", "smoke", "persist", "backup_restore", "stop"))
    parser.add_argument("--state", type=Path)
    args = parser.parse_args()
    if args.action == "start":
        if args.state:
            parser.error("start never reuses an existing state/volume")
        start()
    else:
        if args.state is None:
            parser.error("--state is required; only the state created by this runner")
        state = json.loads(args.state.read_text(encoding="utf-8"))
        assert state["project"].startswith("wordle-pg05-") and state["volume"] == state["project"] + "_postgres_data"
        labels = json.loads(command(["docker", "volume", "inspect", state["volume"], "--format", '{{json .Labels}}']).stdout)
        assert labels["com.docker.compose.project"] == state["project"]
        globals()[args.action](state)
