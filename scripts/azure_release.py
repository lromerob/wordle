"""Offline recovery package: fixed images and source hashes; no secrets or reports."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tarfile

from azure_supervised import ROOT, external

from operational_contract import REQUIRED, verify_references
NEW = REQUIRED
SCOPES = ("k8s", "infra/terraform", "infra/scripts", "scripts", "docker/postgres", "supabase/migrations", "supabase/tests", "backend/integration")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def sources():
    git = ["git", "-c", "safe.directory=" + ROOT.as_posix(), "-C", str(ROOT)]
    tracked = subprocess.check_output([*git, "ls-files", "--", *SCOPES], text=True).splitlines()
    paths = sorted(set(tracked) | set(NEW))
    for path in paths:
        file = ROOT / path
        if file.is_symlink() or not file.is_file():
            raise ValueError("Release source is absent or is a symlink")
        if any(s in Path(path).parts for s in (".terraform", "__pycache__", "node_modules", ".git")) or file.name.endswith((".tfstate", ".tfplan", ".kubeconfig", ".dump")):
            raise ValueError("Generated/private file is not permitted in the source package")
    verify_references(ROOT, paths)
    return git, paths


def create(folder):
    folder = external(folder)
    if folder.exists() and any(folder.iterdir()):
        raise ValueError("Use an empty private directory outside the repository")
    git, paths = sources()
    folder.mkdir(parents=True, exist_ok=True)
    hashes = {p: digest((ROOT / p).read_bytes()) for p in paths}
    with tarfile.open(folder / "source.tar", "w") as archive:
        for path in paths:
            archive.add(ROOT / path, arcname=path, recursive=False)
    manifest = {"format": 1, "base_commit": subprocess.check_output([*git, "rev-parse", "HEAD"], text=True).strip(),
        "contract": "operational-recovery-kit; NOT application-source or academic bundle",
        "scope": "Includes locally prepared files; requires separately verified full Git checkout for application sources",
        "application_source": "Full Git repository at the release commit; images.lock records the application image source commit",
        "files": hashes, "archive_sha256": digest((folder / "source.tar").read_bytes()),
        "images": json.loads((ROOT / "k8s/aks-full/images.lock.json").read_text())["images"],
        "external_requirements": ["Approved Azure variables/backend", "Entra membership and access", "External synthetic secrets",
                                  "Independent PostgreSQL backup plus SQL/HTTP acceptance", "State storage retained separately"]}
    (folder / "release.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    verify(folder)


def verify(folder):
    folder = external(folder)
    manifest = json.loads((folder / "release.json").read_text(encoding="utf-8"))
    if digest((folder / "source.tar").read_bytes()) != manifest["archive_sha256"]:
        raise ValueError("Release archive checksum mismatch")
    with tarfile.open(folder / "source.tar", "r") as archive:
        members = archive.getmembers()
        if len(members) != len(manifest["files"]) or {m.name for m in members} != set(manifest["files"]):
            raise ValueError("Unexpected release members")
        for m in members:
            if not m.isfile() or Path(m.name).is_absolute() or ".." in Path(m.name).parts:
                raise ValueError("Unsafe archive member")
            if digest(archive.extractfile(m).read()) != manifest["files"][m.name]:
                raise ValueError("Release source checksum mismatch")
    print("PASS: recovery source package and all file hashes verified; no Azure or database operations")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("create", "verify"))
    parser.add_argument("--directory", required=True, type=Path)
    args = parser.parse_args()
    try:
        (create if args.action == "create" else verify)(args.directory)
    except Exception:
        parser.exit(1, "Release package refused or failed validation.\n")


if __name__ == "__main__":
    main()
