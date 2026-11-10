"""Explicit external configuration for the private Wordle demo; never prints secrets."""
import argparse
import base64
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
NAMESPACE = "wordle-demo"


def run(kubeconfig, context, *args, data=None):
    result = subprocess.run(["kubectl", "--kubeconfig", str(kubeconfig), "--context", context,
                             "--namespace", NAMESPACE, *args], input=data,
                            capture_output=True, timeout=60)
    if result.returncode:
        raise RuntimeError("Demo configuration operation failed; no sensitive output emitted")
    return result.stdout


def configure(kubeconfig, context, *, recover_only=False):
    # Credentials must come from an external protected process environment.
    values = {"admin-password": os.environ.get("WORDLE_DEMO_ADMIN_PASSWORD", ""),
              "app-password": os.environ.get("WORDLE_DEMO_APP_PASSWORD", "")}
    if any(len(v) < 32 for v in values.values()) or len(set(values.values())) != 2:
        raise ValueError("Supply two distinct external demo passwords of at least 32 characters")
    ns = json.loads(run(kubeconfig, context, "get", "namespace", NAMESPACE, "-o", "json"))
    if ns["metadata"].get("labels", {}).get("wordle.environment") != "private-postgres-demo":
        raise ValueError("Refusing configuration outside the dedicated private demo namespace")
    secret = {"apiVersion": "v1", "kind": "Secret", "type": "Opaque",
              "metadata": {"name": "wordle-db", "namespace": NAMESPACE},
              "data": {k: base64.b64encode(v.encode()).decode() for k, v in values.items()}}
    # create, not apply: never silently overwrite existing database credentials.
    run(kubeconfig, context, "create", "-f", "-", data=json.dumps(secret).encode())
    if not recover_only:
        sources = {"00-check-config.sh": ROOT / "docker/postgres/00-check-config.sh",
                   "10-wordle-schema.sql": ROOT / "supabase/migrations/20261108000100_initial_wordle.sql",
                   "20-demo-words.sql": ROOT / "docker/postgres/20-demo-words.sql",
                   "30-app-role.sh": ROOT / "docker/postgres/30-app-role.sh"}
        cm = {"apiVersion": "v1", "kind": "ConfigMap", "immutable": True,
              "metadata": {"name": "wordle-postgres-init", "namespace": NAMESPACE},
              "data": {k: v.read_text(encoding="utf-8").replace("\r\n", "\n")
                       for k, v in sources.items()}}
        run(kubeconfig, context, "create", "-f", "-", data=json.dumps(cm).encode())
    print("External Secret configuration created; values not displayed", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kubeconfig", required=True, type=Path)
    parser.add_argument("--context", required=True)
    parser.add_argument("--authorize-private-demo", required=True, action="store_true")
    parser.add_argument("--recover-secret-only", action="store_true")
    args = parser.parse_args()
    try:
        configure(args.kubeconfig, args.context, recover_only=args.recover_secret_only)
    except Exception:
        parser.exit(1, "Configuration failed; credentials and raw Kubernetes errors suppressed.\n")


if __name__ == "__main__":
    main()
