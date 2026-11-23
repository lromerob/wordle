"""Supervised AKS-only bootstrap and PostgreSQL recovery; never touches kind.

Future operations need explicit authorization. Binary dumps and metadata are private,
external files. No password values or raw Kubernetes errors are emitted.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import uuid
from urllib.parse import urlsplit

from azure_supervised import ROOT, az, external
from configure_demo_secrets import configure

TABLES = ("palabras", "partidas", "intentos", "estadisticas")
WORKLOADS = ("backend-blue", "frontend-blue", "backend-green", "frontend-green")


class Cluster:
    def __init__(self, kubeconfig, context, subscription, group, name):
        uuid.UUID(subscription)
        if "kind" in context.lower() or "pg05" in context.lower() or "pg06" in context.lower():
            raise ValueError("Local and persistent test contexts are forbidden")
        info = az("aks", "show", "--subscription", subscription, "--resource-group", group, "--name", name)
        expected_id = "/subscriptions/" + subscription + "/resourceGroups/" + group + "/providers/Microsoft.ContainerService/managedClusters/" + name
        if (info.get("id", "").lower() != expected_id.lower() or info.get("name") != name
                or info.get("resourceGroup") != group):
            raise ValueError("Azure returned a different AKS target")
        if info.get("tags", {}).get("project") != "wordle":
            raise ValueError("Cluster is not marked as the dedicated Wordle deployment")
        self.prefix = ["kubectl", "--kubeconfig", str(kubeconfig), "--context", context]
        endpoint = self.call("config", "view", "--minify", "-o", "jsonpath={.clusters[0].cluster.server}").decode().strip()
        parsed = urlsplit(endpoint)
        if (parsed.scheme != "https" or parsed.hostname != info.get("fqdn", "").lower()
                or parsed.port not in (None, 443) or parsed.username or parsed.password
                or parsed.path not in ("", "/") or parsed.query or parsed.fragment):
            raise ValueError("Kubeconfig endpoint does not match the explicit Azure target")
        self.kubeconfig, self.context = kubeconfig, context

    def call(self, *args, data=None):
        r = subprocess.run([*self.prefix, *args], input=data, capture_output=True, timeout=180)
        if r.returncode:
            raise RuntimeError("Kubernetes operation failed; raw output suppressed")
        return r.stdout

    def kube(self, *args, data=None):
        return self.call("-n", "wordle-demo", *args, data=data)

    def sql(self, sql):
        return self.kube("exec", "-i", "postgres-0", "--", "sh", "-c",
            'exec psql --no-psqlrc -U "$POSTGRES_USER" -d "$POSTGRES_DB" -v ON_ERROR_STOP=1 -tA', data=sql.encode()).decode().strip()

    def quiesced(self):
        ns = json.loads(self.call("get", "namespace", "wordle-demo", "-o", "json"))
        if ns["metadata"].get("labels", {}).get("wordle.environment") != "private-postgres-demo":
            raise ValueError("Wrong demo namespace")
        for name in WORKLOADS:
            d = json.loads(self.kube("get", "deployment", name, "-o", "json"))
            if d["spec"].get("replicas", 1) != 0 or d.get("status", {}).get("replicas", 0) != 0:
                raise ValueError("Quiesce all four application deployments and wait before backup/restore")

    def snapshot(self):
        # Hash complete canonical data and the sequence; never write rows to metadata.
        values = {t: json.loads(self.sql("SELECT coalesce(json_agg(r ORDER BY id),'[]'::json) FROM (SELECT * FROM public." + t + ") r;")) for t in TABLES}
        values["sequence"] = self.sql("SELECT last_value,is_called FROM public.palabras_id_seq;")
        return hashlib.sha256(json.dumps(values, sort_keys=True).encode()).hexdigest()


def bootstrap(cluster, empty):
    keys = ("WORDLE_DEMO_ADMIN_PASSWORD", "WORDLE_DEMO_APP_PASSWORD", "WORDLE_GRAFANA_DEMO_PASSWORD")
    values = [os.environ.get(k, "") for k in keys]
    if any(len(v) < 32 for v in values) or len(set(values)) != 3:
        raise ValueError("Supply three distinct external synthetic passwords of at least 32 characters")
    for namespace in ("wordle-demo", "wordle-observability"):
        if cluster.call("get", "namespace", namespace, "--ignore-not-found", "-o", "name").strip():
            raise ValueError("Bootstrap is restricted to fresh namespaces; never overwrite existing secrets/PVCs")
    namespace = {"apiVersion": "v1", "kind": "Namespace", "metadata": {"name": "wordle-demo", "labels": {
        "wordle.environment": "private-postgres-demo", "pod-security.kubernetes.io/enforce": "restricted",
        "pod-security.kubernetes.io/enforce-version": "v1.34"}}}
    cluster.call("create", "-f", "-", data=json.dumps(namespace).encode())
    configure(cluster.kubeconfig, cluster.context, recover_only=empty)
    if empty:
        # No baseline/word seed in this NEW database. pg_restore will create them.
        sources = {"00-check-config.sh": ROOT / "docker/postgres/00-check-config.sh",
                   "30-app-role.sh": ROOT / "docker/postgres/30-app-role.sh"}
        cm = {"apiVersion": "v1", "kind": "ConfigMap", "immutable": True,
              "metadata": {"name": "wordle-postgres-init", "namespace": "wordle-demo"},
              "data": {k: v.read_text(encoding="utf-8").replace("\r\n", "\n") for k, v in sources.items()}}
        cluster.call("create", "-f", "-", data=json.dumps(cm).encode())
    sys.path.insert(0, str(ROOT / "k8s/observability"))
    from validation import prepare
    def command(args, data=None):
        r = subprocess.run(list(map(str, args)), input=data, capture_output=True, timeout=180)
        if r.returncode:
            raise RuntimeError("Observability bootstrap failed; raw output suppressed")
        return r
    prepare(command, cluster.prefix)  # Uses the explicit external Grafana password.
    print("External secrets and fresh initialization configured; values not displayed")


def recover(cluster, action, folder):
    folder = external(folder)
    cluster.quiesced()
    archive, metadata = folder / "wordle.dump", folder / "recovery.json"
    if action == "backup":
        if folder.exists() and any(folder.iterdir()):
            raise ValueError("Refusing to overwrite a recovery package")
        version = cluster.sql("SHOW server_version_num;")
        if not version.startswith("16"):
            raise ValueError("PostgreSQL 16 required")
        before = cluster.snapshot()
        dump = cluster.kube("exec", "postgres-0", "--", "sh", "-c",
            'exec pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" --format=custom --no-owner --no-acl')
        if not dump.startswith(b"PGDMP") or before != cluster.snapshot():
            raise ValueError("Invalid dump or database changed while quiesced")
        folder.mkdir(parents=True, exist_ok=True)
        archive.write_bytes(dump)
        metadata.write_text(json.dumps({"format": 1, "postgres_major": 16, "sha256": hashlib.sha256(dump).hexdigest(),
            "dataset_sha256": before, "bytes": len(dump), "restore_validated": False}, indent=2), encoding="utf-8")
        print("Binary PostgreSQL dump and checksum saved privately; restore validation still required")
    else:
        meta = json.loads(metadata.read_text(encoding="utf-8"));dump = archive.read_bytes()
        if meta.get("postgres_major") != 16 or not dump.startswith(b"PGDMP") or hashlib.sha256(dump).hexdigest() != meta["sha256"]:
            raise ValueError("Backup checksum/version mismatch")
        if not cluster.sql("SHOW server_version_num;").startswith("16"):
            raise ValueError("PostgreSQL 16 destination required")
        if cluster.sql("SELECT count(*) FROM pg_tables WHERE schemaname='public';") != "0":
            raise ValueError("Restore destination must have zero public tables; no clean/drop performed")
        cluster.kube("exec", "-i", "postgres-0", "--", "sh", "-c",
            'exec pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --exit-on-error --single-transaction --no-owner --no-acl', data=dump)
        # The application role was recreated independently by first initialization.
        cluster.sql("GRANT SELECT,INSERT,UPDATE ON ALL TABLES IN SCHEMA public TO wordle_app; GRANT USAGE,SELECT ON ALL SEQUENCES IN SCHEMA public TO wordle_app;")
        cluster.sql((ROOT / "supabase/tests/schema_contracts.sql").read_text(encoding="utf-8"))
        if cluster.snapshot() != meta["dataset_sha256"]:
            raise ValueError("Restored data/sequence differs from backup")
        (folder / "restored-sql.json").write_text(json.dumps({"sql_verified": True, "http_verified": False,
            "backup_sha256": meta["sha256"]}), encoding="utf-8")
        print("Restored SQL contracts/data/sequence verified; resume applications and validate HTTP separately")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("bootstrap", "backup", "restore"))
    parser.add_argument("--kubeconfig", required=True, type=Path)
    parser.add_argument("--context", required=True)
    parser.add_argument("--subscription", required=True)
    parser.add_argument("--resource-group", required=True)
    parser.add_argument("--cluster", required=True)
    parser.add_argument("--confirm", required=True)
    parser.add_argument("--empty-restore", action="store_true")
    parser.add_argument("--directory", type=Path)
    args = parser.parse_args()
    try:
        if args.confirm != args.action.upper() + " " + args.resource_group + "/" + args.cluster:
            raise ValueError("Explicit action and target confirmation required")
        if args.action != "bootstrap" and not args.directory:
            raise ValueError("A private external recovery directory is required")
        cluster = Cluster(args.kubeconfig, args.context, args.subscription, args.resource_group, args.cluster)
        if args.action == "bootstrap":
            bootstrap(cluster, args.empty_restore)
        else:
            recover(cluster, args.action, args.directory)
    except Exception:
        parser.exit(1, "Operation refused or failed; no secrets or raw cluster errors emitted.\n")


if __name__ == "__main__":
    main()
