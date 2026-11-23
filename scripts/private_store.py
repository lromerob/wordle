"""Fail-closed contract for an operator-provisioned, private durable mount."""
import json
import os
from pathlib import Path
import uuid
import hashlib
import re
import time
from pathlib import PureWindowsPath

ROOT = Path(__file__).resolve().parents[1]
STORE_MOUNT = Path("/wordle-private")
HOST_APPROVAL = Path("/run/wordle-host/approval.json")


def require_windows_launch(root, expected_id, marker_bytes, mode):
    """Operator-supervised host receipt, NOT cryptographic attestation or isolation."""
    if os.name != "posix" or root != STORE_MOUNT:
        raise ValueError("Windows compatibility requires the dedicated Linux bind")
    # Separate read-only host mount; a file inside the store or env alone is insufficient.
    entries = [row.split() for row in Path("/proc/self/mountinfo").read_text().splitlines()]
    if not any(len(row) > 6 and row[4] == str(HOST_APPROVAL.parent) and "ro" in row[5].split(",") for row in entries):
        raise ValueError("Separate read-only supervised host receipt mount required")
    if not any(len(row) > 6 and row[4] == str(STORE_MOUNT) for row in entries):
        raise ValueError("Dedicated store bind required")
    if HOST_APPROVAL.is_symlink():
        raise ValueError("Invalid supervised host receipt")
    data = json.loads(HOST_APPROVAL.read_text(encoding="utf-8"))
    keys = {"format", "repository", "issuer", "policy", "store_id", "host_path", "container_path",
            "marker_sha256", "acl_sha256", "session_id", "issued_at", "expires_at", "fixture_only"}
    if not isinstance(data, dict) or set(data) != keys:
        raise ValueError("Invalid supervised receipt structure")
    fixture = mode == "windows-supervised-test"
    if (data["format"] != 1 or data["repository"] != "lromerob/wordle" or
        data["issuer"] != "Invoke-WordleRunner.ps1" or data["policy"] != "owner-system-administrators-v1" or
        data["store_id"] != expected_id or data["container_path"] != str(root) or
        data["fixture_only"] is not fixture or
        data["marker_sha256"] != hashlib.sha256(marker_bytes).hexdigest()):
        raise ValueError("Supervised receipt does not match store")
    if (not isinstance(data["host_path"], str) or not PureWindowsPath(data["host_path"]).is_absolute() or
        data["host_path"].startswith("\\") or not re.fullmatch(r"[a-f0-9]{64}", str(data["acl_sha256"]))):
        raise ValueError("Invalid supervised host configuration")
    uuid.UUID(data["session_id"])
    now = time.time()
    if (type(data["issued_at"]) is not int or type(data["expires_at"]) is not int or
        not data["issued_at"] <= now < data["expires_at"] or
        not 0 < data["expires_at"] - data["issued_at"] <= 21600):
        raise ValueError("Expired or inconsistent supervised receipt")



def require_store(path, expected_id):
    mode = os.environ.get("WORDLE_STORE_MODEL", "posix")
    if mode not in ("posix", "windows-supervised", "windows-supervised-test"):
        raise ValueError("Unknown private store validation model")
    raw = Path(path)
    if not raw.is_absolute() or not expected_id:
        raise ValueError("Approved absolute durable store and identifier required")
    uuid.UUID(expected_id)
    if any(p.is_symlink() for p in (raw, *raw.parents)):
        raise ValueError("Store symlinks are forbidden")
    root = raw.resolve(strict=True)
    if root == ROOT or ROOT in root.parents or root in ROOT.parents:
        raise ValueError("Durable store must be independent of source checkout")
    marker = root / ".wordle-private-store.json"
    if marker.is_symlink():
        raise ValueError("Invalid store marker")
    marker_bytes = marker.read_bytes()
    data = json.loads(marker_bytes.decode("utf-8"))
    expected = {"format": 1, "repository": "lromerob/wordle", "store_id": expected_id,
                "durable_acknowledged": True}
    if mode == "windows-supervised-test":
        expected.update(durable_acknowledged=False, synthetic_fixture=True)
    if data != expected:
        raise ValueError("Unapproved durable store")
    for name in ("plans", "selections", "evidence", "backups"):
        child = root / name
        if not child.is_dir() or child.is_symlink() or child.resolve().parent != root:
            raise ValueError("Missing private store directory")
    if mode != "posix":
        require_windows_launch(root, expected_id, marker_bytes, mode)
    if mode == "posix" and os.name == "posix" and any(p.stat().st_mode & 0o077 for p in (root, marker, *(root / n for n in ("plans", "selections", "evidence", "backups")))):
        raise ValueError("Store must be private to the runner account")
    return root
