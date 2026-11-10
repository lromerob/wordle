"""Opt-in FIN-10/15 integrated observability and Blue-Green demonstration; disposable kind only."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import secrets
import socket
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
import uuid

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "k8s/demo-kind"))
sys.path.insert(0, str(ROOT / "scripts"))
from run_demo import command, TRAEFIK
from configure_demo_secrets import configure
sys.path.insert(0, str(ROOT / "k8s/blue-green"))
from promotion import PromotionController
from validation import IMAGES, prepare, wait_stack, validate

NS = "wordle-demo"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-disposable-kind", required=True, action="store_true")
    parser.add_argument("--evidence-dir", type=Path)
    parser.add_argument("--inspect-seconds", type=int, default=0)
    args = parser.parse_args()
    if not 0 <= args.inspect_seconds <= 300:
        parser.error("inspect-seconds must be between zero and 300")
    if args.inspect_seconds and len(os.environ.get("WORDLE_GRAFANA_DEMO_PASSWORD", "")) < 32:
        parser.error("Inspection requires an external synthetic WORDLE_GRAFANA_DEMO_PASSWORD")
    evidence = args.evidence_dir or Path(tempfile.mkdtemp(prefix="wordle-fin1015-evidence-"))
    if evidence.resolve() == ROOT or ROOT in evidence.resolve().parents:
        parser.error("Evidence must be outside the repository")
    evidence.mkdir(parents=True, exist_ok=True)
    if any(evidence.iterdir()):
        parser.error("Evidence directory must be empty")
    started = time.monotonic()
    events, samples = [], []
    phase = ["bootstrap"]
    stop = threading.Event()
    monitor = None
    forwards = []
    outcome = "FAIL"
    summary = {}
    telemetry_port = None

    def record(event, **fields):
        item = {"elapsed": round(time.monotonic() - started, 3),
                "utc": datetime.now(timezone.utc).isoformat(), "event": event, **fields}
        events.append(item)
        (evidence / "events.json").write_text(json.dumps(events, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(item), flush=True)
        if telemetry_port is not None:
            payload={"resourceLogs":[{"resource":{"attributes":[{"key":"service.name","value":{"stringValue":"wordle-deploy"}}]},
                "scopeLogs":[{"scope":{"name":"wordle-deployment-demo"},"logRecords":[{"timeUnixNano":str(time.time_ns()),
                "severityNumber":9,"body":{"stringValue":json.dumps(item,separators=(",",":"))}}]}]}]}
            try:
                opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
                request=urllib.request.Request(f"http://127.0.0.1:{telemetry_port}/v1/logs",data=json.dumps(payload).encode(),headers={"Content-Type":"application/json"})
                with opener.open(request,timeout=1) as response:response.read()
            except Exception:
                pass

    def set_phase(value):
        phase[0] = value
        record("phase", phase=value)

    def fetch(port, path, *, payload=None, method="GET"):
        data = json.dumps(payload).encode() if payload is not None else None
        request = urllib.request.Request(f"http://127.0.0.1:{port}" + path,
            data=data, method=method, headers={"Host": "wordle.test", "Content-Type": "application/json"})
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        try:
            response = opener.open(request, timeout=3)
        except urllib.error.HTTPError as error:
            response = error
        with response:
            raw = response.read()
            body = json.loads(raw) if response.headers.get_content_type() == "application/json" else raw
            return response.status, response.headers.get("X-Wordle-Release"), body

    cluster = "wordle-fin1015-" + uuid.uuid4().hex[:8]
    previous_clusters = set(command(["kind", "get", "clusters"]).stdout.decode().split())
    if cluster in previous_clusters:
        raise RuntimeError("Cluster name collision")
    created = False
    env_keys = ("WORDLE_DEMO_ADMIN_PASSWORD", "WORDLE_DEMO_APP_PASSWORD")
    saved_env = {key: os.environ.get(key) for key in env_keys}
    try:
        with tempfile.TemporaryDirectory(prefix="wordle-fin1015-private-") as folder:
            private = Path(folder)
            config = private / "kind.kubeconfig"
            context = "kind-" + cluster
            prefix = ["kubectl", "--kubeconfig", config, "--context", context]
            def kube(*a, **kw):
                # The observability render deliberately contains two namespaces.
                namespace = [] if a[0] == "apply" else ["-n", NS]
                result = command([*prefix, *namespace, *a], check=False, **kw)
                if result.returncode:
                    # Only the secret-free declarative render may emit validation details.
                    detail = result.stderr.decode(errors="replace")[:2000] if a[0] == "apply" else "raw output suppressed"
                    raise RuntimeError("Kubernetes operation failed: " + str(a[0]) + "; " + detail)
                return result
            def query(sql):
                return kube("exec", "-i", "postgres-0", "--", "sh", "-c",
                    'exec psql --no-psqlrc -U "$POSTGRES_USER" -d "$POSTGRES_DB" -v ON_ERROR_STOP=1 -tA',
                    data=sql.encode(), timeout=30).stdout.decode().strip()
            def database_hash():
                rows = {table: json.loads(query("SELECT coalesce(json_agg(r ORDER BY id),'[]'::json) FROM (SELECT * FROM public." + table + ") r;"))
                        for table in ("palabras", "partidas", "intentos", "estadisticas")}
                rows["word_sequence"] = query("SELECT last_value,is_called FROM public.palabras_id_seq;")
                return hashlib.sha256(json.dumps(rows, sort_keys=True).encode()).hexdigest()
            def port_forward(service, namespace=NS, remote_port=8080):
                with socket.socket() as sock:
                    sock.bind(("127.0.0.1", 0)); port = sock.getsockname()[1]
                process = subprocess.Popen(["kubectl", "--kubeconfig", str(config), "--context", context,
                    "-n", namespace, "port-forward", "--address", "127.0.0.1", "service/" + service,
                    f"{port}:{remote_port}"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                forwards.append(process)
                for _ in range(80):
                    if process.poll() is not None:
                        raise RuntimeError("Owned port-forward stopped")
                    try:
                        with socket.create_connection(("127.0.0.1", port), timeout=.2):
                            return port
                    except OSError:
                        time.sleep(.1)
                raise RuntimeError("Port-forward timeout")
            def patch_frontend(slot, path, value):
                kube("patch", "deployment", "frontend-" + slot, "--type=json", "-p",
                     json.dumps([{"op": "replace", "path": path, "value": value}]))
            try:
                created = True
                record("cluster_create", name=cluster, version="1.35.0")
                command(["kind", "create", "cluster", "--name", cluster,
                         "--image", "kindest/node:v1.35.0", "--kubeconfig", config, "--wait", "180s"], timeout=480)
                record("cluster_ready")
                for component in ("backend", "frontend"):
                    command(["docker", "build", "--target", "runtime", "-t",
                             f"wordle-fin0507-{component}:local", ROOT / component], timeout=480)
                for image in ("postgres:16.15", TRAEFIK):
                    if command(["docker", "image", "inspect", image], check=False).returncode:
                        command(["docker", "pull", image], timeout=300)
                for image in IMAGES:
                    if command(["docker", "image", "inspect", image], check=False).returncode:
                        command(["docker", "pull", image], timeout=300)
                archive = private / "images.tar"
                command(["docker", "image", "save", "--platform", "linux/amd64", "-o", archive,
                    "wordle-fin0507-backend:local", "wordle-fin0507-frontend:local",
                    "postgres:16.15", "traefik:v3.7.17", *IMAGES], timeout=360)
                record("image_archive_ready")
                command(["kind", "load", "image-archive", "--name", cluster, archive], timeout=360)
                archive.unlink()
                record("images_imported")
                namespace = {"apiVersion": "v1", "kind": "Namespace", "metadata": {"name": NS,
                    "labels": {"wordle.environment": "private-postgres-demo",
                    "pod-security.kubernetes.io/enforce": "restricted",
                    "pod-security.kubernetes.io/enforce-version": "v1.34"}}}
                kube("create", "-f", "-", data=json.dumps(namespace).encode())
                for key in env_keys:
                    os.environ[key] = secrets.token_urlsafe(36)
                configure(config, context)
                grafana_password = prepare(command, prefix)
                kube("apply", "--dry-run=server", "-k", str(ROOT / "k8s/observability"))
                kube("apply", "-k", str(ROOT / "k8s/observability"))
                wait_stack(command, prefix)
                telemetry_port = port_forward("collector", namespace="wordle-observability", remote_port=4318)
                kube("rollout", "status", "statefulset/postgres", "--timeout=240s", timeout=260)
                for name in ("backend-blue", "frontend-blue", "ingress"):
                    kube("rollout", "status", "deployment/" + name, "--timeout=180s", timeout=200)
                pvc = json.loads(kube("get", "pvc", "-o", "json").stdout)["items"]
                assert len(pvc) == 1 and pvc[0]["status"]["phase"] == "Bound"
                pvc_uid = pvc[0]["metadata"]["uid"]
                assert len(json.loads(kube("get", "statefulsets", "-o", "json").stdout)["items"]) == 1
                query((ROOT / "supabase/tests/schema_contracts.sql").read_text(encoding="utf-8"))
                public_port = port_forward("ingress")
                public = lambda path: fetch(public_port, path)
                for _ in range(40):
                    try:
                        assert public("/api/health")[:2] == (200, "blue"); break
                    except Exception:
                        time.sleep(.5)
                else:
                    raise RuntimeError("Initial Blue not reachable through Ingress")
                status, release, game = fetch(public_port, "/api/game/nueva?usuario_id=fin0809-synthetic", method="POST")
                assert (status, release) == (200, "blue")
                game_id = str(uuid.UUID(game["partida_id"]))
                game_path = "/api/game/" + game_id
                assert "palabra_secreta" not in public(game_path)[2]["partida"]
                record("stable_blue_verified", postgres="16.15", pvc_bound=True)

                def sample():
                    while not stop.is_set():
                        for name, path in (("frontend", "/"), ("health", "/api/health"), ("game", game_path)):
                            item = {"elapsed": round(time.monotonic() - started, 3), "phase": phase[0], "path": name}
                            try:
                                code, slot, _ = public(path)
                                item.update(status=code, release=slot)
                            except Exception as error:
                                item.update(status=0, release=None, error=type(error).__name__)
                            samples.append(item)
                        stop.wait(.25)
                monitor = threading.Thread(target=sample, daemon=True)
                monitor.start()
                candidate_ports = {}
                def candidate(slot, path):
                    if slot not in candidate_ports:
                        candidate_ports[slot] = port_forward("frontend-" + slot)
                    return fetch(candidate_ports[slot], path)
                controller = PromotionController(kube, public,
                    {s: lambda path, s=s: candidate(s, path) for s in ("blue", "green")},
                    record, game_path, set_phase)
                set_phase("prepare-green")
                kube("scale", "deployment/backend-green", "deployment/frontend-green", "--replicas=1")
                # Gate waits while the sampler proves that Blue continues serving.
                result_a = controller.promote("green")
                assert result_a["outcome"] == "promoted" and controller.active() == "green"
                assert any(s["phase"] == "prepare-green" and s["status"] == 200 and s["release"] == "blue" for s in samples)
                solution = query("SELECT palabra_secreta FROM public.partidas WHERE id='" + game_id + "';")
                payload = {"partida_id": game_id, "usuario_id": "fin0809-synthetic", "palabra": solution}
                status, release, answer = fetch(public_port, "/api/game/intento", method="POST", payload=payload)
                assert (status, release) == (200, "green") and answer["estado"] == "ganada"
                record("scenario_A_pass", active="green", persisted_victory=True)
                before_faults = database_hash()

                set_phase("reject-blue")
                patch_frontend("blue", "/spec/template/spec/containers/0/readinessProbe/httpGet/path", "/api/fin0809-unhealthy")
                result_reject = controller.promote("blue", gate_timeout=25)
                assert result_reject["outcome"] == "rejected" and controller.active() == "green"
                record("scenario_B_pre_promotion_pass", active="green", rollback=False)
                set_phase("restore-blue-candidate")
                patch_frontend("blue", "/spec/template/spec/containers/0/readinessProbe/httpGet/path", "/api/health")
                kube("rollout", "status", "deployment/frontend-blue", "--timeout=180s", timeout=200)

                def inject_fault():
                    set_phase("fault-blue")
                    cms = json.loads(kube("get", "configmaps", "-o", "json").stdout)["items"]
                    fault_cm = next(c["metadata"]["name"] for c in cms if c["metadata"]["name"].startswith("wordle-nginx-blue-fault-"))
                    patch_frontend("blue", "/spec/template/spec/volumes/1/configMap/name", fault_cm)
                    kube("rollout", "status", "deployment/frontend-blue", "--timeout=180s", timeout=200)
                    for _ in range(80):
                        try:
                            status, release, _ = public(game_path)
                            if (status, release) == (503, "blue"):
                                record("controlled_functional_fault_observed", status=503, release="blue", health_still_ready=True)
                                time.sleep(1)
                                return
                        except Exception:
                            pass
                        time.sleep(.25)
                    raise RuntimeError("Controlled functional failure not observed")
                set_phase("promotion-blue")
                result_rollback = controller.promote("blue", after_switch=inject_fault)
                assert result_rollback["outcome"] == "rolled-back" and result_rollback["reason"]
                # Transport errors also require rollback. The injected 503 must have
                # been observed independently; do not confuse an unrelated failure
                # before promotion with this controlled post-promotion scenario.
                assert any(e["event"] == "controlled_functional_fault_observed" and e["status"] == 503 for e in events)
                assert controller.active() == "green"
                set_phase("steady-green")
                controller.await_public("green")
                assert public(game_path)[2]["partida"]["estado"] == "ganada"
                assert database_hash() == before_faults
                final_pvc = json.loads(kube("get", "pvc", "-o", "json").stdout)["items"]
                assert len(final_pvc) == 1 and final_pvc[0]["metadata"]["uid"] == pvc_uid
                deployments = json.loads(kube("get", "deployments", "-o", "json").stdout)["items"]
                assert len(deployments) == 5 and all(d["spec"]["replicas"] == 1 and d["status"].get("availableReplicas") == 1 for d in deployments)
                services = json.loads(kube("get", "services", "-o", "json").stdout)["items"]
                assert all(s["spec"]["type"] == "ClusterIP" and not s["spec"].get("externalIPs") for s in services)
                assert any(s["status"] == 503 and s["release"] == "blue" for s in samples)
                time.sleep(1)
                summary.update(cluster=cluster, scenario_A=result_a, scenario_B_rejection=result_reject,
                               scenario_B_rollback=result_rollback, database_hash=before_faults,
                               shared_postgres=True, pvc_preserved=True, final_active="green",
                               ready_deployments=5, services={s["metadata"]["name"]:s["spec"]["selector"] for s in services})
                record("scenario_B_post_promotion_pass", active="green", database_unchanged=True)
                set_phase("observability-alerts")
                summary["observability"] = validate(command, prefix, query, database_hash,
                    game_id, grafana_password, evidence, record)
                if args.inspect_seconds:
                    grafana_port = port_forward("grafana", namespace="wordle-observability", remote_port=3000)
                    record("grafana_inspection", url=f"http://127.0.0.1:{grafana_port}/d/wordle-demo", user="demo", seconds=args.inspect_seconds)
                    until=time.monotonic()+args.inspect_seconds
                    while time.monotonic()<until:
                        time.sleep(min(30,until-time.monotonic()))
                outcome = "PASS"
            finally:
                stop.set()
                if monitor:
                    monitor.join(timeout=15)
                for process in forwards:
                    if process.poll() is None:
                        process.terminate()
                        try:
                            process.wait(timeout=8)
                        except subprocess.TimeoutExpired:
                            process.kill(); process.wait(timeout=5)
                if created:
                    command(["kind", "delete", "cluster", "--name", cluster], timeout=180)
                remaining = set(command(["kind", "get", "clusters"]).stdout.decode().split())
                assert cluster not in remaining and previous_clusters <= remaining
                record("cleanup_pass", owned_cluster_removed=True, prior_clusters_preserved=True)
    except Exception as error:
        outcome = "FAIL"
        record("run_failed", reason=str(error))
        raise
    finally:
        for key, value in saved_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        counts = {}
        for sample in samples:
            key = sample["phase"]
            count = counts.setdefault(key, {"requests": 0, "failed": 0, "by_status": {}, "by_release": {}})
            count["requests"] += 1
            count["failed"] += sample["status"] != 200
            for field, target in (("status", "by_status"), ("release", "by_release")):
                value = str(sample[field]); count[target][value] = count[target].get(value, 0) + 1
        failure_windows = []
        start = None
        for sample in samples:
            if sample["status"] != 200 and start is None:
                start = sample["elapsed"]
            elif sample["status"] == 200 and start is not None:
                failure_windows.append(round(sample["elapsed"] - start, 3)); start = None
        path_windows = {}
        for path in ("frontend", "health", "game"):
            windows, first_failure = [], None
            for sample in (s for s in samples if s["path"] == path):
                if sample["status"] != 200 and first_failure is None:
                    first_failure = sample["elapsed"]
                elif sample["status"] == 200 and first_failure is not None:
                    windows.append({"first_failure": first_failure, "recovered": sample["elapsed"],
                                    "observed_seconds": round(sample["elapsed"] - first_failure, 3)})
                    first_failure = None
            path_windows[path] = {"windows": windows, "unrecovered_since": first_failure}
        summary.update(result=outcome, traffic_by_phase=counts,
                       failure_windows_by_path=path_windows,
                       observed_failure_windows_seconds=failure_windows,
                       sample_interval_seconds=.25, requests=len(samples),
                       failed_requests=sum(s["status"] != 200 for s in samples))
        (evidence / "traffic.json").write_text(json.dumps(samples, indent=2) + "\n", encoding="utf-8")
        (evidence / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
        print("Sanitized evidence:", evidence, flush=True)
    print("FIN-10/15 " + outcome + ": promotion, rejection and real automatic rollback", flush=True)


if __name__ == "__main__":
    main()
