"""Opt-in FIN-05/06/07 disposable kind demo; always removes only its own new cluster."""
import argparse
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

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from configure_demo_secrets import configure

NS = "wordle-demo"
TRAEFIK = "traefik:v3.7.17@sha256:f4bb143d1135a579b630ed491e17ec50f6f7c9c6a30585ff3d385471d2a86f5a"


def command(args, *, data=None, timeout=300, check=True):
    r = subprocess.run([str(a) for a in args], input=data, capture_output=True, timeout=timeout)
    if check and r.returncode:
        raise RuntimeError("Operation failed: " + str(args[0]) + " " + str(args[1]) +
                           "; raw output suppressed")
    return r


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-disposable-kind", required=True, action="store_true")
    args = parser.parse_args()
    cluster = "wordle-fin0507-" + uuid.uuid4().hex[:8]
    existing = command(["kind", "get", "clusters"]).stdout.decode().split()
    if cluster in existing:
        raise RuntimeError("Cluster collision; no changes made")
    before = set(existing)
    created = False
    forward = None
    with tempfile.TemporaryDirectory(prefix="wordle-fin0507-") as folder:
        private = Path(folder)
        kubeconfig = private / "kind.kubeconfig"
        context = "kind-" + cluster
        def kube(*a, **kw):
            return command(["kubectl", "--kubeconfig", kubeconfig, "--context", context,
                            "-n", NS, *a], **kw)
        def query(sql):
            return kube("exec", "-i", "postgres-0", "--", "sh", "-c",
                'exec psql --no-psqlrc -U "$POSTGRES_USER" -d "$POSTGRES_DB" -v ON_ERROR_STOP=1 -tA',
                data=sql.encode(), timeout=30).stdout.decode().strip()
        try:
            print("Creating disposable cluster:", cluster, flush=True)
            created = True  # Also clean up a partially created cluster.
            command(["kind", "create", "cluster", "--name", cluster,
                     "--image", "kindest/node:v1.35.0", "--kubeconfig", kubeconfig,
                     "--wait", "180s"], timeout=480)
            print("Cluster Ready; building and loading local runtimes", flush=True)
            for component in ("backend", "frontend"):
                command(["docker", "build", "--target", "runtime", "-t",
                         f"wordle-fin0507-{component}:local", ROOT / component], timeout=480)
            for image in ("postgres:16.15", TRAEFIK):
                if command(["docker", "image", "inspect", image], check=False).returncode:
                    command(["docker", "pull", image], timeout=300)
            archive = private / "images.tar"
            command(["docker", "image", "save", "--platform", "linux/amd64", "-o", archive,
                     "wordle-fin0507-backend:local", "wordle-fin0507-frontend:local",
                     "postgres:16.15", "traefik:v3.7.17"], timeout=300)
            command(["kind", "load", "image-archive", "--name", cluster, archive], timeout=360)
            archive.unlink()
            # kubectl dry-run client may return one JSON object or a List.
            rendered = command(["kubectl", "kustomize", ROOT / "k8s/demo-kind"]).stdout
            # Apply the namespace first; config and Secret are injected outside render.
            namespace = {"apiVersion": "v1", "kind": "Namespace", "metadata": {
                "name": NS, "labels": {"wordle.environment": "private-postgres-demo",
                "pod-security.kubernetes.io/enforce": "restricted",
                "pod-security.kubernetes.io/enforce-version": "v1.34"}}}
            kube("create", "-f", "-", data=json.dumps(namespace).encode())
            old_env = {k: os.environ.get(k) for k in
                       ("WORDLE_DEMO_ADMIN_PASSWORD", "WORDLE_DEMO_APP_PASSWORD")}
            for key in old_env:
                os.environ[key] = secrets.token_urlsafe(36)
            try:
                configure(kubeconfig, context)
                kube("apply", "--dry-run=server", "-f", "-", data=rendered)
                kube("apply", "-f", "-", data=rendered)
                kube("rollout", "status", "statefulset/postgres", "--timeout=240s", timeout=260)
                for name in ("backend", "frontend", "ingress"):
                    kube("rollout", "status", "deployment/" + name, "--timeout=180s", timeout=200)
                assert query("SELECT count(*) FROM public.palabras;") == "5"
                query((ROOT / "supabase/tests/schema_contracts.sql").read_text(encoding="utf-8"))
                print("PASS: schema contracts, seeded dictionary, four workloads Ready", flush=True)
                svc = json.loads(kube("get", "services", "-o", "json").stdout)["items"]
                assert len(svc) == 4
                assert all(s["spec"]["type"] == "ClusterIP" and not s["spec"].get("externalIPs") for s in svc)
                assert json.loads(kube("get", "pvc", "-o", "json").stdout)["items"][0]["status"]["phase"] == "Bound"
                with socket.socket() as sock:
                    sock.bind(("127.0.0.1", 0)); port = sock.getsockname()[1]
                forward = subprocess.Popen(["kubectl", "--kubeconfig", str(kubeconfig),
                    "--context", context, "-n", NS, "port-forward", "--address", "127.0.0.1",
                    "service/ingress", f"{port}:8080"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
                def http(path, *, payload=None, method="GET", host="wordle.test", expected=200):
                    data = json.dumps(payload).encode() if payload is not None else None
                    req = urllib.request.Request(f"http://127.0.0.1:{port}" + path, data=data,
                        method=method, headers={"Host": host, "Content-Type": "application/json"})
                    try:
                        response = opener.open(req, timeout=5)
                    except urllib.error.HTTPError as error:
                        response = error
                    with response:
                        assert response.status == expected, (path, response.status, expected)
                        raw = response.read()
                        return json.loads(raw) if response.headers.get_content_type() == "application/json" else raw
                for _ in range(40):
                    try:
                        assert http("/api/health") == {"status": "ok"}; break
                    except Exception:
                        time.sleep(1)
                else:
                    raise RuntimeError("Ingress readiness failed")
                assert b'<div id="root">' in http("/")
                http("/", host="untrusted.invalid", expected=404)
                user = "fin0507-synthetic"
                game = http("/api/game/nueva?usuario_id=" + user, method="POST")["partida_id"]
                assert "palabra_secreta" not in http("/api/game/" + game)["partida"]
                body = {"partida_id": game, "usuario_id": user, "palabra": "ZZZZZ"}
                http("/api/game/intento", method="POST", payload=body, expected=400)
                solution = query("SELECT palabra_secreta FROM public.partidas WHERE id='" + str(uuid.UUID(game)) + "';")
                body["palabra"] = solution
                assert http("/api/game/intento", method="POST", payload=body)["estado"] == "ganada"
                assert query("SELECT count(*) FROM public.intentos;") == "1"
                print("PASS: Ingress host routing, frontend/API, invalid guess, victory and real SQL persistence", flush=True)
                # Recover the Secret from the SAME external environment, never by dumping Kubernetes data.
                kube("delete", "secret", "wordle-db")
                configure(kubeconfig, context, recover_only=True)
                kube("rollout", "restart", "deployment/backend")
                kube("rollout", "status", "deployment/backend", "--timeout=180s", timeout=200)
                # Rollout Ready does not guarantee every proxy has observed new endpoints.
                # Wait with read-only requests before making a non-idempotent POST.
                for _ in range(30):
                    try:
                        assert http("/api/game/" + game)["partida"]["estado"] == "ganada"
                        break
                    except Exception:
                        time.sleep(1)
                else:
                    raise RuntimeError("Proxy did not recover after backend restart")
                http("/api/game/nueva?usuario_id=fin0507-recovery", method="POST")
                assert query("SELECT count(*) FROM public.partidas;") == "2"
                print("PASS: external Secret recovery and fresh backend connection after restart", flush=True)
                # Recreate only this disposable database pod; PVC and existing game must survive.
                kube("delete", "pod", "postgres-0", "--wait=true")
                kube("rollout", "status", "statefulset/postgres", "--timeout=180s", timeout=200)
                assert query("SELECT count(*) FROM public.partidas;") == "2"
                for _ in range(30):
                    try:
                        assert http("/api/game/" + game)["partida"]["estado"] == "ganada"
                        break
                    except Exception:
                        time.sleep(1)
                else:
                    raise RuntimeError("Application did not recover after PostgreSQL restart")
                print("PASS: PostgreSQL pod recreated; PVC and saved games preserved", flush=True)
            finally:
                for key, value in old_env.items():
                    if value is None:
                        os.environ.pop(key, None)
                    else:
                        os.environ[key] = value
        finally:
            if forward is not None:
                forward.terminate()
                try:
                    forward.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    forward.kill(); forward.wait(timeout=5)
            if created:
                command(["kind", "delete", "cluster", "--name", cluster], timeout=180)
            after = set(command(["kind", "get", "clusters"]).stdout.decode().split())
            assert cluster not in after and before <= after
            print("CLEANUP PASS: owned cluster removed; pre-existing clusters preserved", flush=True)
    print("FIN-05/06/07 local integrated demo PASS", flush=True)


if __name__ == "__main__":
    main()
