"""Authorized read-only AKS screenshot adapter using the existing capture.cjs engine.

No SQL, deletion, selector changes, install, or workload/Ingress creation.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tarfile
from urllib.parse import urlsplit
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from azure_supervised import ROOT
from aks_recovery import Cluster
from aks_run import Session
from private_store import require_store
from release_gate import verify_selection

NAMESPACES = ("wordle-demo", "wordle-observability")
SERVICES = {"ingress": ("wordle-demo", 8080), "grafana": ("wordle-observability", 3000),
            "prometheus": ("wordle-observability", 9090)}
STAGES = ("stable-blue", "promoted-green", "rollback-green", "signals")


def validate_request(mode, authorized, target, expected, namespaces, action="capture"):
    if mode != "aks" or authorized is not True or action != "capture":
        raise ValueError("Explicit AKS screenshot-only authorization required")
    if not expected or set(target) != {"subscription_id", "resource_group_name", "cluster_name", "context"} or target != expected:
        raise ValueError("Capture target differs from the approved installation")
    if tuple(namespaces) != NAMESPACES:
        raise ValueError("Capture namespaces are fixed")
    if not target["context"] or any(x in target["context"].lower() for x in ("kind", "pg05", "pg06")):
        raise ValueError("AKS context required")


def allowed_url(url, owned_ports):
    parsed = urlsplit(url)
    return (parsed.scheme == "http" and parsed.hostname in ("127.0.0.1", "localhost", "wordle.test")
            and not parsed.username and not parsed.password and parsed.port in owned_ports)


def validate_metadata(metadata):
    if (metadata.get("environment") != "azure-aks" or metadata.get("mode") != "aks"
            or not re.fullmatch(r"[a-f0-9]{40}", metadata.get("release_sha", ""))
            or not re.fullmatch(r"[a-f0-9]{64}", metadata.get("release_id", ""))
            or not metadata.get("runtime_images") or not metadata.get("target_verified")):
        raise ValueError("Incomplete AKS capture provenance")
    for row in metadata["runtime_images"]:
        if (not re.search(r"@sha256:[a-f0-9]{64}$", row.get("image", ""))
                or not re.search(r"sha256:[a-f0-9]{64}$", row.get("imageID", ""))):
            raise ValueError("Missing immutable runtime image identity")


def export_evidence(folder, destination, metadata):
    """Existing private mount only; no clobber, partial export never claims success."""
    validate_metadata(metadata)
    if destination.exists() or destination.parent.is_symlink() or not destination.parent.is_dir():
        raise ValueError("Export destination missing or already occupied")
    files = sorted(p for p in folder.rglob("*") if p.is_file())
    if not files or any(p.is_symlink() for p in folder.rglob("*")):
        raise ValueError("No capture or unsafe evidence tree")
    manifest = {"format": 1, "metadata": metadata, "validation": "VISUAL CAPTURE ONLY; functional acceptance separate",
                "files": {p.relative_to(folder).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}}
    with (folder / "manifest.json").open("x", encoding="utf-8") as file:
        json.dump(manifest, file, indent=2)
    with destination.open("xb") as output:
        with tarfile.open(fileobj=output, mode="w") as archive:
            for file in [*files, folder / "manifest.json"]:
                archive.add(file, arcname=file.relative_to(folder).as_posix(), recursive=False)
    with tarfile.open(destination, "r") as archive:
        members = archive.getmembers()
        expected = {**manifest["files"], "manifest.json": hashlib.sha256((folder/"manifest.json").read_bytes()).hexdigest()}
        if len(members) != len(expected) or {m.name for m in members} != set(expected):
            raise ValueError("Incomplete export")
        if any(not m.isfile() or hashlib.sha256(archive.extractfile(m).read()).hexdigest() != expected[m.name] for m in members):
            raise ValueError("Export checksum failure")
    return hashlib.sha256(destination.read_bytes()).hexdigest()


def capture(args, env=os.environ):
    if args.stage not in STAGES or not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,63}", args.export_id):
        raise ValueError("Unique capture identifier/stage required")
    store = require_store(env["WORDLE_AZURE_PRIVATE_DIR"], env["WORDLE_AZURE_STORE_ID"])
    selection = verify_selection(env)
    values = json.loads((store / "variables.json").read_text(encoding="utf-8"))
    expected = {k: values[k] for k in ("subscription_id", "resource_group_name", "cluster_name")}
    expected["context"] = "wordle-azure-supervised"
    target = dict(subscription_id=args.subscription, resource_group_name=args.group, cluster_name=args.cluster, context=args.context)
    validate_request("aks", args.confirm == "CAPTURE " + args.group + "/" + args.cluster, target, expected, NAMESPACES)
    # Runtime dependencies must already exist; no browser/package installation.
    if not shutil.which("node") or not env.get("WORDLE_PLAYWRIGHT_ROOT") or not Path(env["WORDLE_PLAYWRIGHT_ROOT"]).is_dir():
        raise ValueError("Existing Node/Playwright host must be explicitly configured")
    if not (env.get("WORDLE_BROWSER_EXECUTABLE") or env.get("WORDLE_BROWSER_CHANNEL")):
        raise ValueError("Explicit installed browser executable/channel required")
    cluster = Cluster(store/"aks.kubeconfig", args.context, args.subscription, args.group, args.cluster)
    for ns in NAMESPACES:
        obj = json.loads(cluster.call("get", "namespace", ns, "-o", "json"))
        if obj.get("metadata", {}).get("name") != ns:
            raise ValueError("Unexpected capture namespace")
    rows = []
    for ns in NAMESPACES:
        pods = json.loads(cluster.call("-n", ns, "get", "pods", "-o", "json"))["items"]
        for pod in pods:
            for status in pod.get("status", {}).get("containerStatuses", []):
                if status.get("ready"):
                    rows.append({"namespace": ns, "name": status["name"], "image": status["image"], "imageID": status["imageID"]})
    # Both application images must match the reviewed lock and registry runtime digests.
    for image in selection["images"].values():
        observed = [r for r in rows if r["image"] == image["reference"]]
        if not observed or any(not any(r["imageID"].endswith(d) for d in image["runtime_digests"]) for r in observed):
            raise ValueError("Observed application runtime differs from release")
    metadata = {"mode": "aks", "environment": "azure-aks", "release_sha": selection["release_sha"],
                "release_id": selection["release_id"], "runtime_images": rows, "target_verified": True,
                "target_fingerprint": hashlib.sha256(json.dumps(target, sort_keys=True).encode()).hexdigest()}
    validate_metadata(metadata)
    folder = store/"evidence"/args.export_id
    destination = store/"evidence"/(args.export_id+".tar")
    if folder.exists() or destination.exists():
        raise ValueError("Existing evidence must be preserved")
    session = Session(cluster, folder)
    try:
        ports = {name: session.forward(name, port, ns) for name, (ns, port) in SERVICES.items()}
        ctx = {**metadata, "stage": args.stage, "public_port": ports["ingress"], "ports": ports,
               "owned_ports": list(ports.values()), "action": "capture", "namespaces": list(NAMESPACES),
               "password": env.get("WORDLE_GRAFANA_DEMO_PASSWORD", ""), "trace_id": args.trace_id}
        if args.stage == "signals" and (len(ctx["password"]) < 32 or not re.fullmatch(r"[a-f0-9]{32}", args.trace_id)):
            raise ValueError("Signals need authorized ephemeral Grafana login and existing trace ID")
        result = subprocess.run(["node", str(ROOT/"scripts/evidence/capture.cjs"), "--capture"],
            input=json.dumps(ctx).encode(), env=dict(env, WORDLE_CAPTURE_DIR=str(folder)), capture_output=True, timeout=180)
        if result.returncode:
            raise RuntimeError("AKS screenshot failed; no raw browser output emitted")
        # Durable mount receives originals before any separately authorized teardown.
        export_evidence(folder, destination, metadata)
    finally:
        session.close()  # Only processes created by this capture, never existing forwards.


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ("subscription", "group", "cluster", "context", "confirm", "export-id"):
        parser.add_argument("--"+key, required=True)
    parser.add_argument("--stage", choices=STAGES, required=True)
    parser.add_argument("--trace-id", default="")
    try:
        capture(parser.parse_args())
        print("AKS visual capture exported and checksummed; functional acceptance remains separate")
    except Exception:
        parser.exit(1, "Capture refused or failed; no credentials or raw errors emitted.\n")


if __name__ == "__main__":
    main()
