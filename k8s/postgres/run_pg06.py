"""Explicit local PG-06 lifecycle; no deletion of clusters, namespaces or PVCs."""
import argparse
import base64
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parents[2]
NS = "wordle-pg06"
sys.path.insert(0, str(ROOT / "backend/integration"))
from run_pg05_compose import http, WORDS


def command(args, *, data=None, timeout=240, check=True):
    result = subprocess.run([str(a) for a in args], input=data, capture_output=True, timeout=timeout)
    if check and result.returncode:
        # Never emit expanded manifests, Secret objects, environment or raw logs.
        raise RuntimeError("Operation failed: " + str(args[0]) + " " + str(args[1]))
    return result


def kubectl(state, *args, **kwargs):
    return command(["kubectl", "--kubeconfig", state["kubeconfig"], "--context", "kind-" + state["cluster"], "--namespace", NS, *args], **kwargs)


def save(state):
    Path(state["state_file"]).write_text(json.dumps(state, indent=2), encoding="utf-8")


def query(state, sql):
    return kubectl(state, "exec", "-i", "postgres-0", "--", "sh", "-c",
        'exec psql --no-psqlrc --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" --set=ON_ERROR_STOP=1 --tuples-only --no-align',
        data=sql.encode(), timeout=30).stdout.decode().strip()


def snapshot(state):
    return {t: json.loads(query(state, "SELECT coalesce(json_agg(r ORDER BY id),'[]'::json) FROM (SELECT * FROM public." + t + ") r;"))
            for t in ("palabras", "partidas", "intentos", "estadisticas")}


def resources(state):
    pods = json.loads(kubectl(state, "get", "pods", "-o", "json").stdout)["items"]
    assert len(pods) == 3
    for pod in pods:
        assert pod["status"]["phase"] == "Running"
        assert all(c["ready"] and c["restartCount"] == 0 for c in pod["status"]["containerStatuses"])
    services = json.loads(kubectl(state, "get", "services", "-o", "json").stdout)["items"]
    assert len(services) == 3
    assert all(s["spec"]["type"] == "ClusterIP" and not s["spec"].get("externalIPs") for s in services)
    print("Three Running/Ready pods, zero restarts; three ClusterIP Services, no external exposure.", flush=True)


def start():
    clusters = command(["kind", "get", "clusters"]).stdout.decode().split()
    cluster = "wordle-pg06-" + uuid.uuid4().hex[:8]
    if cluster in clusters:
        raise RuntimeError("Cluster name collision; stopped")
    private = Path(os.environ["LOCALAPPDATA"]) / "WordlePG06" / cluster
    private.mkdir(parents=True, exist_ok=False)
    state = {"cluster": cluster, "namespace": NS, "kubeconfig": str(private / "kind.kubeconfig"), "state_file": str(private / "state.json")}
    save(state)
    import tempfile
    Path(tempfile.gettempdir(), "wordle-pg06-state-location.txt").write_text(state["state_file"], encoding="utf-8")
    print("New dedicated cluster:", cluster, "state:", state["state_file"], flush=True)
    command(["kind", "create", "cluster", "--name", cluster, "--image", "kindest/node:v1.35.0", "--kubeconfig", state["kubeconfig"], "--wait", "180s"], timeout=480)
    for context, tag in (("backend", "wordle-backend:v1-pg06"), ("frontend", "wordle-frontend:v1-pg06")):
        command(["docker", "build", "--target", "runtime", "-t", tag, str(ROOT / context)], timeout=480)
        print("Built:", tag, flush=True)
    # A moving postgres:16 tag must not silently change the validated version.
    if command(["docker", "image", "inspect", "postgres:16.15"], check=False).returncode:
        command(["docker", "pull", "postgres:16.15"], timeout=300)
    version = command(["docker", "run", "--rm", "--network", "none", "--entrypoint", "postgres", "postgres:16.15", "--version"]).stdout.decode().strip()
    assert "16.15" in version
    state["postgres_version"] = version
    save(state)
    load_images(state)
    deploy(state)


def load_images(state):
    import tempfile
    with tempfile.TemporaryDirectory(prefix="wordle-pg06-images-") as folder:
        archive = Path(folder) / "linux-amd64.tar"
        command(["docker", "image", "save", "--platform", "linux/amd64", "--output", archive, "wordle-backend:v1-pg06", "wordle-frontend:v1-pg06", "postgres:16.15"], timeout=300)
        command(["kind", "load", "image-archive", "--name", state["cluster"], archive], timeout=360)
    print("Loaded local linux/amd64 image archive; temporary archive removed.", flush=True)


def deploy(state):
    if kubectl(state, "get", "namespace", NS, check=False).returncode == 0:
        raise RuntimeError("Namespace already exists; do not repeat initial deployment or delete PVC")
    text = kubectl(state, "create", "--dry-run=client", "-k", str(ROOT / "k8s/postgres"), "-o", "json").stdout.decode().strip()
    objects = []
    decoder = json.JSONDecoder()
    while text:
        obj, end = decoder.raw_decode(text)
        objects.extend(obj["items"] if obj.get("kind") == "List" else [obj])
        text = text[end:].strip()
    namespace = next(o for o in objects if o["kind"] == "Namespace")
    kubectl(state, "create", "-f", "-", data=json.dumps(namespace).encode())
    # Fresh random values travel on stdin to Kubernetes, never arguments/files/logs.
    secret = {"apiVersion": "v1", "kind": "Secret", "metadata": {"name": "wordle-db", "namespace": NS}, "type": "Opaque",
              "data": {key: base64.b64encode(secrets.token_urlsafe(32).encode()).decode() for key in ("admin-password", "app-password")}}
    kubectl(state, "create", "-f", "-", data=json.dumps(secret).encode())
    del secret
    sources = {"00-check-config.sh": ROOT / "docker/postgres/00-check-config.sh",
               "10-wordle-schema.sql": ROOT / "supabase/migrations/20261108000100_initial_wordle.sql",
               "20-demo-words.sql": ROOT / "docker/postgres/20-demo-words.sql",
               "30-app-role.sh": ROOT / "docker/postgres/30-app-role.sh"}
    init = {"apiVersion": "v1", "kind": "ConfigMap", "metadata": {"name": "wordle-postgres-init", "namespace": NS}, "immutable": True,
            "data": {k: v.read_text(encoding="utf-8").replace("\r\n", "\n") for k,v in sources.items()}}
    kubectl(state, "create", "-f", "-", data=json.dumps(init).encode())
    kubectl(state, "apply", "--dry-run=server", "-k", str(ROOT / "k8s/postgres"))
    first = [o for o in objects if o["kind"] not in ("Namespace", "Deployment")]
    kubectl(state, "apply", "-f", "-", data=json.dumps({"apiVersion":"v1","kind":"List","items":first}).encode())
    # A failed first init must STOP; do not apply application or wipe the PVC.
    kubectl(state, "rollout", "status", "statefulset/postgres", "--timeout=180s", timeout=200)
    query(state, (ROOT / "supabase/tests/schema_contracts.sql").read_text(encoding="utf-8"))
    assert query(state, "SELECT count(*) FROM public.palabras;") == "5"
    kubectl(state, "apply", "-k", str(ROOT / "k8s/postgres"))
    for name in ("backend", "frontend"):
        kubectl(state, "rollout", "status", "deployment/" + name, "--timeout=150s", timeout=170)
    resources(state)
    print("Clean initialization, schema contracts, five demo words and application deployment PASS.", flush=True)
    print("State:", state["state_file"], flush=True)


def smoke(state):
    base = state["base_url"]
    assert http(base, "/")[0] == 200
    assert http(base, "/api/health") == (200, {"status":"ok"})
    ids = []
    for win in (True, False):
        user = "pg06-api-" + uuid.uuid4().hex[:8]
        code, game = http(base, "/api/game/nueva?usuario_id=" + user, method="POST")
        assert code == 200
        identifier = str(uuid.UUID(game["partida_id"]))
        ids.append(identifier)
        active = http(base, "/api/game/" + identifier)[1]
        assert "palabra_secreta" not in active["partida"]
        solution = query(state, "SELECT palabra_secreta FROM public.partidas WHERE id='" + identifier + "';")
        word = solution if win else next(w for w in WORDS if w != solution)
        for invalid in ("AB", "ZZZZZ"):
            assert http(base, "/api/game/intento", {"partida_id":identifier,"usuario_id":user,"palabra":invalid}, "POST")[0] == 400
        for n in range(1, 2 if win else 7):
            code, result = http(base, "/api/game/intento", {"partida_id":identifier,"usuario_id":user,"palabra":word}, "POST")
            assert code == 200 and result["intentos_usados"] == n
        assert result["estado"] == ("ganada" if win else "perdida")
        assert http(base, "/api/game/intento", {"partida_id":identifier,"usuario_id":user,"palabra":word}, "POST")[0] == 400
        code, stats = http(base, "/api/stats/" + user)
        assert code == 200 and stats["partidas_jugadas"] == 1 and stats["partidas_ganadas"] == int(win)
    assert http(base, "/api/stats/ranking/global")[0] == 200
    values = snapshot(state)
    for row in values["partidas"]:
        code, stored = http(base, "/api/game/" + row["id"])
        assert code == 200 and stored["partida"]["estado"] == row["estado"]
        assert stored["partida"]["intentos_usados"] == row["intentos_usados"]
    state["api_game_ids"] = ids
    save(state)
    print("HTTP frontend/proxy, active secret hidden, invalid guesses, win, six-attempt loss, stats/ranking and SQL persistence PASS. Game IDs:", ids, flush=True)


def verify(state):
    values = snapshot(state)
    if "persistence" in state:
        assert {t:len(rows) for t,rows in values.items()} == state["persistence"]["counts"]
        assert set(state["api_game_ids"]) <= {r["id"] for r in values["partidas"]}
    for row in values["partidas"]:
        code, data = http(state["base_url"], "/api/game/" + row["id"])
        assert code == 200
        for key in ("id", "estado", "intentos_usados"):
            assert data["partida"][key] == row[key]
    for row in values["estadisticas"]:
        code, data = http(state["base_url"], "/api/stats/" + row["usuario_id"])
        assert code == 200
        for key in ("id", "partidas_jugadas", "partidas_ganadas", "racha_actual", "racha_maxima", "intentos_promedio"):
            assert data[key] == row[key]
    assert http(state["base_url"], "/")[0] == 200
    assert http(state["base_url"], "/api/health") == (200, {"status":"ok"})
    resources(state)
    print("Retained IDs/counts and API game/statistics fields match SQL after application rollouts.", flush=True)


def persist(state):
    before = snapshot(state)
    assert before["partidas"] and before["estadisticas"]
    pvc = json.loads(kubectl(state, "get", "pvc", "data-postgres-0", "-o", "json").stdout)
    old = json.loads(kubectl(state, "get", "pod", "postgres-0", "-o", "json").stdout)["metadata"]["uid"]
    # The only deletion in this script is this owned application's replaceable pod.
    kubectl(state, "delete", "pod", "postgres-0", "--wait=true", "--timeout=60s", timeout=80)
    deadline = time.monotonic() + 150
    while time.monotonic() < deadline:
        result = kubectl(state, "get", "pod", "postgres-0", "-o", "json", check=False)
        if result.returncode == 0:
            pod = json.loads(result.stdout)
            if pod["metadata"]["uid"] != old and pod.get("status",{}).get("containerStatuses") and all(c.get("ready",False) for c in pod["status"]["containerStatuses"]):
                break
        time.sleep(1)
    else:
        raise RuntimeError("Recreated PostgreSQL pod not ready; preserve PVC and diagnose")
    after_pvc = json.loads(kubectl(state, "get", "pvc", "data-postgres-0", "-o", "json").stdout)
    assert pvc["metadata"]["uid"] == after_pvc["metadata"]["uid"] and pvc["spec"]["volumeName"] == after_pvc["spec"]["volumeName"]
    assert snapshot(state) == before
    logs = kubectl(state, "logs", "postgres-0").stdout.decode()
    assert "Skipping initialization" in logs and "running /docker-entrypoint-initdb.d/10-wordle-schema.sql" not in logs
    for name in ("backend", "frontend"):
        kubectl(state, "rollout", "restart", "deployment/" + name)
        kubectl(state, "rollout", "status", "deployment/" + name, "--timeout=150s", timeout=170)
    assert snapshot(state) == before
    resources(state)
    state["persistence"] = {"counts":{t:len(rows) for t,rows in before.items()},"old_pod_uid":old,"new_pod_uid":pod["metadata"]["uid"],"pvc_uid":pvc["metadata"]["uid"],"pv":pvc["spec"]["volumeName"],"storage_class":pvc["spec"]["storageClassName"]}
    save(state)
    # Port-forward terminates on frontend pod replacement; reconnect before API checks.
    print("PG pod replacement and application rollouts: identical full SQL snapshots; same PVC/PV; initialization skipped.", state["persistence"], flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("start","load_images","deploy","smoke","persist","verify","inspect"))
    parser.add_argument("--state", type=Path)
    parser.add_argument("--base-url")
    args = parser.parse_args()
    if args.action == "start":
        if args.state or args.base_url:
            parser.error("start requires a new dedicated cluster")
        start()
    else:
        if not args.state:
            parser.error("--state is required")
        state = json.loads(args.state.read_text(encoding="utf-8"))
        assert state["cluster"].startswith("wordle-pg06-") and state["namespace"] == NS
        # Verify exact ownership before any further action, including pod replacement.
        labels = json.loads(command(["docker","inspect",state["cluster"]+"-control-plane","--format","{{json .Config.Labels}}"]).stdout)
        assert labels["io.x-k8s.kind.cluster"] == state["cluster"]
        if args.base_url:
            assert args.base_url.startswith("http://127.0.0.1:")
            state["base_url"] = args.base_url
            save(state)
        if args.action == "inspect":
            resources(state)
        else:
            globals()[args.action](state)
