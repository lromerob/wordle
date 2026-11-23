"""Read-only CI and image gate. No Azure login, publication or deployment."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import urllib.request
from azure_supervised import ROOT
from private_store import require_store
import ghcr_check

REPOSITORY = "lromerob/wordle"
BRANCH = "codex/pg01-07-consolidation"
JOBS = ("Tests / isolated backend", "Integration / real PostgreSQL 16", "Build / frontend",
        "Build / Docker images (no push)", "Infrastructure / Kustomize rendering",
        "Integration / ephemeral kind smoke test", "Infrastructure / Terraform validation (no Azure)")
LOCK = "k8s/aks-full/images.lock.json"


def digest(data):
    return hashlib.sha256(data).hexdigest()


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise ValueError("API redirects refused")


def api(path):
    if not re.fullmatch(r"/repos/lromerob/wordle/actions/runs/[0-9]+(?:/attempts/[1-9][0-9]*/jobs\?per_page=100&page=[0-9]+)?", path):
        raise ValueError("Unexpected API resource")
    token = os.environ.get("GH_TOKEN")
    if not token:
        raise ValueError("Actions read token unavailable")
    request = urllib.request.Request("https://api.github.com" + path, headers={
        "Authorization": "Bearer " + token, "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"})
    try:
        with urllib.request.build_opener(NoRedirect).open(request, timeout=20) as response:
            raw = response.read(4 * 1024 * 1024 + 1)
        if len(raw) > 4 * 1024 * 1024:
            raise ValueError("Oversized response")
        return json.loads(raw)
    except Exception:
        raise ValueError("CI evidence unavailable or permission denied") from None


def check_run(run, run_id, sha):
    if (not isinstance(run, dict) or run.get("id") != int(run_id)
            or run.get("head_sha") != sha or run.get("head_branch") != BRANCH
            or run.get("repository", {}).get("full_name") != REPOSITORY
            or run.get("head_repository", {}).get("full_name") != REPOSITORY
            or run.get("path") != ".github/workflows/ci.yml"
            or run.get("event") not in ("push", "workflow_dispatch")
            or run.get("status") != "completed" or run.get("conclusion") != "success"
            or type(run.get("run_attempt")) is not int or run["run_attempt"] < 1):
        raise ValueError("CI run is not an unambiguous successful release run")


def ci_evidence(run_id, sha, query=api):
    if not re.fullmatch(r"[1-9][0-9]*", str(run_id)) or not re.fullmatch(r"[a-f0-9]{40}", sha):
        raise ValueError("Exact CI run and release SHA required")
    base = "/repos/" + REPOSITORY + "/actions/runs/" + str(run_id)
    run = query(base)
    check_run(run, run_id, sha)
    jobs = []
    total = None
    for page in range(1, 21):
        result = query(base + "/attempts/" + str(run["run_attempt"]) + "/jobs?per_page=100&page=" + str(page))
        count, batch = result.get("total_count"), result.get("jobs")
        if type(count) is not int or count < 7 or count > 2000 or not isinstance(batch, list) or not batch or len(batch) > 100:
            raise ValueError("Incomplete CI jobs API response")
        if total is not None and total != count:
            raise ValueError("CI jobs changed during selection")
        total = count
        jobs.extend(batch)
        if len(jobs) >= total:
            break
    if len(jobs) != total or len({j["id"] for j in jobs}) != total:
        raise ValueError("Incomplete or duplicated jobs")
    for name in JOBS:
        selected = [j for j in jobs if j.get("name") == name]
        if len(selected) != 1:
            raise ValueError("Missing or ambiguous mandatory CI job")
        j = selected[0]
        if (j.get("run_id") != int(run_id) or j.get("head_sha") != sha
                or j.get("status") != "completed" or j.get("conclusion") != "success"
                or j.get("run_attempt", run["run_attempt"]) != run["run_attempt"]):
            raise ValueError("Mandatory CI job failed, skipped or incomplete")
    final = query(base)
    check_run(final, run_id, sha)
    if final["run_attempt"] != run["run_attempt"]:
        raise ValueError("CI was rerun during selection")
    return {"run_id": int(run_id), "run_attempt": run["run_attempt"], "sha": sha,
            "url": "https://github.com/" + REPOSITORY + "/actions/runs/" + str(run_id), "jobs": list(JOBS)}


def git(*args):
    return subprocess.check_output(["git", "-c", "safe.directory=" + ROOT.as_posix(), "-C", str(ROOT), *args], text=True).strip()


def source_hashes():
    from azure_release import sources
    _, paths = sources()
    return {p: digest((ROOT / p).read_bytes()) for p in paths}


def parse_rendered_images(raw):
    return set(re.findall(r"^[ \t]+(?:- )?image:[ \t]+(\S+)[ \t]*$", raw, re.MULTILINE))


def rendered_images():
    # kubectl kustomize is local; remote Kustomize references are prohibited.
    for path in (ROOT / "k8s").rglob("kustomization.yaml"):
        if re.search(r"https?://|git::|github\.com", path.read_text(encoding="utf-8")):
            raise ValueError("Remote Kustomize dependencies forbidden for release selection")
    raw = subprocess.check_output(["kubectl", "kustomize", str(ROOT / "k8s/aks-full")], text=True, stderr=subprocess.DEVNULL)
    return parse_rendered_images(raw)


def selected_images(sha, inspect=ghcr_check.inspect):
    lock = json.loads((ROOT / LOCK).read_text(encoding="utf-8"))
    source = lock["source_commit"]
    if rendered_images() != set(lock["images"].values()):
        raise ValueError("Effective deployment image digests differ from the selected lock")
    if not re.fullmatch(r"[a-f0-9]{40}", source):
        raise ValueError("Invalid application source SHA")
    # Versioned images.lock cannot contain its own future commit SHA. Reuse is
    # allowed only when both complete Docker build contexts have identical trees.
    for context in ("backend", "frontend"):
        if git("rev-parse", source + ":" + context) != git("rev-parse", sha + ":" + context):
            raise ValueError("Application source differs from the image source")
    images = {}
    for component in ("backend", "frontend"):
        name = "ghcr.io/lromerob/wordle-" + component
        reference = lock["images"][name]
        if not re.fullmatch(re.escape(name) + r"@sha256:[a-f0-9]{64}", reference):
            raise ValueError("Invalid pinned application image")
        result = inspect(reference)
        if result.get("reference") != reference or result.get("revision") != source:
            raise ValueError("Image revision/digest mismatch")
        if (result.get("os") != "linux" or result.get("architecture") != "amd64"
                or reference.split("@", 1)[1] not in result.get("runtime_digests", [])):
            raise ValueError("Incomplete verified image identity")
        images[name] = result
    return source, images


def environment(env):
    if env.get("GITHUB_REPOSITORY") != REPOSITORY or env.get("GITHUB_REF") != "refs/heads/" + BRANCH:
        raise ValueError("Unauthorized repository/branch")
    sha = env.get("GITHUB_SHA", "")
    if not re.fullmatch(r"[a-f0-9]{40}", sha) or git("rev-parse", "HEAD") != sha or git("diff", "HEAD", "--name-only"):
        raise ValueError("Release checkout differs from approved SHA")
    return sha


def select(env=os.environ):
    sha = environment(env)
    store = require_store(env["WORDLE_AZURE_PRIVATE_DIR"], env["WORDLE_AZURE_STORE_ID"])
    event = json.loads(Path(env["GITHUB_EVENT_PATH"]).read_text(encoding="utf-8"))
    evidence = ci_evidence(event["inputs"]["ci_run"], sha)
    application_sha, images = selected_images(sha)
    final = ci_evidence(event["inputs"]["ci_run"], sha)
    if final != evidence:
        raise ValueError("CI evidence changed during image verification")
    content = {"format": 1, "repository": REPOSITORY, "branch": BRANCH, "release_sha": sha,
               "application_sha": application_sha, "ci": evidence, "images": images,
               "store_id": env["WORDLE_AZURE_STORE_ID"], "files": source_hashes()}
    content["release_id"] = digest(json.dumps(content, sort_keys=True).encode())
    raw = (json.dumps(content, sort_keys=True, indent=2) + "\n").encode()
    identifier = env["GITHUB_RUN_ID"] + "-" + env["GITHUB_RUN_ATTEMPT"]
    if not re.fullmatch(r"[1-9][0-9]*-[1-9][0-9]*", identifier):
        raise ValueError("Invalid CD run identity")
    path = store / "selections" / (identifier + ".json")
    with path.open("xb") as file:
        file.write(raw)
    with Path(env["GITHUB_ENV"]).open("a", encoding="utf-8") as file:
        file.write("WORDLE_RELEASE_SELECTION=" + str(path) + "\nWORDLE_RELEASE_SELECTION_SHA256=" + digest(raw) + "\n")
    return content


def verify_selection(env=os.environ):
    sha = environment(env)
    store = require_store(env["WORDLE_AZURE_PRIVATE_DIR"], env["WORDLE_AZURE_STORE_ID"])
    path = Path(env["WORDLE_RELEASE_SELECTION"])
    if path.is_symlink() or path.resolve().parent != store / "selections":
        raise ValueError("Selection is outside the approved store")
    raw = path.read_bytes()
    if digest(raw) != env["WORDLE_RELEASE_SELECTION_SHA256"]:
        raise ValueError("Release selection changed after approval")
    content = json.loads(raw)
    release_id = content.pop("release_id")
    if digest(json.dumps(content, sort_keys=True).encode()) != release_id:
        raise ValueError("Selection identity mismatch")
    if (content["release_sha"] != sha or content["repository"] != REPOSITORY
            or content["branch"] != BRANCH or content["store_id"] != env["WORDLE_AZURE_STORE_ID"]
            or content["files"] != source_hashes()):
        raise ValueError("Release source or target substituted")
    content["release_id"] = release_id
    return content


if __name__ == "__main__":
    try:
        select()
        print("CI jobs and immutable image selection verified; private receipt saved")
    except Exception:
        raise SystemExit("Release gate refused; evidence unavailable, inconsistent or unauthorized")
