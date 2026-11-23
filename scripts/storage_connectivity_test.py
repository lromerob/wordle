"""Supervised diagnostic only. No ARM writes, Terraform, AKS or persistent tokens."""
import argparse
import datetime as dt
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import re
import secrets
import socket
import ssl
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

REPOSITORY = "lromerob/wordle"
BRANCH = "refs/heads/codex/pg01-07-consolidation"
OWNER = "lromerob"
WAIT_SECONDS = 600
JOURNAL = "wordle-storage-connectivity.json"


def public_ipv4(value):
    if not isinstance(value, str) or "/" in value:
        raise ValueError("An individual public IPv4 is required")
    ip = ipaddress.ip_address(value)
    if ip.version != 4 or not ip.is_global or ip.is_multicast:
        raise ValueError("An individual public IPv4 is required")
    return str(ip)


def confirmation_matches(comment, phrase, started, issue_url):
    if not isinstance(comment, dict):
        return False
    created = comment.get("created_at", "")
    return (comment.get("user", {}).get("login") == OWNER
            and comment.get("user", {}).get("type") == "User"
            and comment.get("author_association") == "OWNER"
            and comment.get("issue_url") == issue_url
            and comment.get("body") == phrase
            and re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z", created) is not None
            and created >= started
            and comment.get("updated_at") == created)


def wait_for_confirmation(base, phrase, started, wait_seconds=WAIT_SECONDS):
    deadline = time.monotonic() + wait_seconds
    url = base + "/comments?" + urllib.parse.urlencode({"since": started, "per_page": 100})
    while time.monotonic() < deadline:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break
        comments = json.loads(public_get(url, timeout=min(15, remaining)))
        if not isinstance(comments, list) or len(comments) >= 100:
            raise ValueError("Unexpected or saturated confirmation channel")
        if time.monotonic() >= deadline:
            break
        for comment in comments:
            if confirmation_matches(comment, phrase, started, base):
                return comment
        time.sleep(min(60, max(0, deadline - time.monotonic())))
    raise TimeoutError("Operator confirmation timed out")


def summary(text):
    print(text, flush=True)
    with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as f:
        f.write(text + "\n\n")


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise ValueError("Diagnostic HTTP redirects are forbidden")


def public_get(url, timeout=15):
    # Public GitHub coordination and IP services only: no token or Azure credential.
    request = urllib.request.Request(url, headers={"User-Agent": "wordle-storage-diagnostic"})
    with urllib.request.build_opener(NoRedirect()).open(request, timeout=timeout) as response:
        return response.read(1024 * 1024)


def outward_ip():
    a = public_ipv4(public_get("https://api.ipify.org").decode().strip())
    b = public_ipv4(public_get("https://checkip.amazonaws.com").decode().strip())
    if a != b:
        raise ValueError("Outbound IPv4 observations disagree")
    return a


def az_json(*args):
    p = subprocess.run(["az", *args, "--only-show-errors", "-o", "json"],
                       capture_output=True, timeout=45)
    if p.returncode:
        raise RuntimeError("Azure authentication command failed; raw output suppressed")
    return json.loads(p.stdout)


def token():
    # Short-lived data-plane token stays in process memory; never output or persist it.
    return az_json("account", "get-access-token", "--resource", "https://storage.azure.com/")["accessToken"]


def blob(method, name, credential, data=None, create=False):
    account = os.environ["TEST_ACCOUNT"]
    container = os.environ["TEST_CONTAINER"]
    if account != "stwordletfgstate7c92d4" or container != "wordle-connectivity-test":
        raise ValueError("Only the dedicated diagnostic container is permitted")
    if not re.fullmatch(r"diagnostic-[0-9]+-[0-9]+-[a-f0-9]{32}\.json", name):
        raise ValueError("Invalid owned diagnostic blob name")
    url = f"https://{account}.blob.core.windows.net/{container}/{name}"
    headers = {"Authorization": "Bearer " + credential, "x-ms-version": "2023-11-03",
               "x-ms-date": dt.datetime.now(dt.timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")}
    if method == "PUT":
        headers.update({"x-ms-blob-type": "BlockBlob", "Content-Type": "application/json"})
    if create:
        headers["If-None-Match"] = "*"
    request = urllib.request.Request(url, method=method, data=data, headers=headers)
    with urllib.request.build_opener(NoRedirect()).open(request, timeout=20) as response:
        return response.read(4096)


def journal_path():
    return Path(os.environ["RUNNER_TEMP"]) / JOURNAL


def cleanup():
    path = journal_path()
    if not path.exists():
        return True
    state = json.loads(path.read_text(encoding="utf-8"))
    summary("FINISH: operator must remove only this run's manually added IP and verify the ARM baseline. "
            "Network restoration is NOT verified by this workflow. Run " + state["run"] +
            ", attempt " + state["attempt"] + ", IPv4 " + state["ip"] + ", owned synthetic blob " + state["blob"])
    if not state.get("blob_may_exist"):
        return True
    try:
        blob("DELETE", state["blob"], token())
    except urllib.error.HTTPError as error:
        if error.code != 404:
            summary("Synthetic blob cleanup NOT VERIFIED: HTTP " + str(error.code))
            return False
    except Exception:
        summary("Synthetic blob cleanup NOT VERIFIED; operator recovery required")
        return False
    state["blob_may_exist"] = False
    path.write_text(json.dumps(state), encoding="utf-8")
    summary("Owned synthetic blob absent; firewall closure remains an operator action")
    return True


def validate_context():
    env = os.environ
    account = az_json("account", "show")
    if (account["id"] != env["TEST_SUBSCRIPTION_ID"] or account["tenantId"] != env["TEST_TENANT_ID"]
            or account.get("user", {}).get("type") != "servicePrincipal"):
        raise ValueError("Unexpected Azure identity context")
    if account.get("user", {}).get("name", "").lower() != env["TEST_CLIENT_ID"].lower():
        raise ValueError("Unexpected Azure client identity")


def prepare():
    env = os.environ
    if (env.get("GITHUB_REPOSITORY") != REPOSITORY or env.get("GITHUB_REF") != BRANCH
            or env.get("GITHUB_ACTOR") != OWNER or env.get("GITHUB_EVENT_NAME") != "workflow_dispatch"
            or env.get("GITHUB_SHA") != env.get("APPROVED_SHA")
            or not re.fullmatch(r"[a-f0-9]{40}", env.get("APPROVED_SHA", ""))):
        raise ValueError("Unauthorized workflow source")
    for name in ("GITHUB_RUN_ID", "GITHUB_RUN_ATTEMPT", "CONFIRMATION_ISSUE"):
        if not re.fullmatch(r"[1-9][0-9]*", env.get(name, "")):
            raise ValueError("Invalid execution/issue identifier")
    if (env.get("TEST_ACCOUNT") != "stwordletfgstate7c92d4"
            or env.get("TEST_CONTAINER") != "wordle-connectivity-test"):
        raise ValueError("Unexpected diagnostic account or container")
    if env.get("TEST_RESOURCE_GROUP") != "rg-wordle-state":
        raise ValueError("Unexpected Storage group")
    validate_context()
    issue = env["CONFIRMATION_ISSUE"]
    base = "https://api.github.com/repos/" + REPOSITORY + "/issues/" + issue
    info = json.loads(public_get(base))
    if (info.get("state") != "open" or "pull_request" in info
            or info.get("url") != base or info.get("number") != int(issue)):
        raise ValueError("Use an open issue, not a pull request")
    ip = outward_ip()
    started = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    nonce = secrets.token_hex(16)
    run, attempt = env["GITHUB_RUN_ID"], env["GITHUB_RUN_ATTEMPT"]
    phrase = f"WORDLE-STORAGE-READY {run} {attempt} {env['GITHUB_SHA']} {ip} {nonce}"
    state = {"run": run, "attempt": attempt, "sha": env["GITHUB_SHA"], "ip": ip,
             "blob": f"diagnostic-{run}-{attempt}-{nonce}.json", "blob_may_exist": False,
             "phrase": phrase, "started": started, "issue": issue,
             "client": env["TEST_CLIENT_ID"], "tenant": env["TEST_TENANT_ID"],
             "subscription": env["TEST_SUBSCRIPTION_ID"]}
    journal_path().write_text(json.dumps(state), encoding="utf-8")
    summary("PREPARE: run " + run + ", attempt " + attempt + ", commit " + env["GITHUB_SHA"] +
            ", IPv4 " + ip + ". Operator: reserve exclusive firewall maintenance; record baseline, "
            "add this individual IPv4 only if absent, verify Deny and unchanged administrative rules.")
    summary("WAIT: lromerob must post this exact line in issue #" + issue +
            " AFTER the manual checks, within 10 minutes:\n```text\n" + phrase + "\n```")


def verify():
    env = os.environ
    state = json.loads(journal_path().read_text(encoding="utf-8"))
    if (state["sha"] != env["GITHUB_SHA"] or state["run"] != env["GITHUB_RUN_ID"]
            or state["attempt"] != env["GITHUB_RUN_ATTEMPT"]
            or state["issue"] != env["CONFIRMATION_ISSUE"]
            or state["client"] != env["TEST_CLIENT_ID"]
            or state["tenant"] != env["TEST_TENANT_ID"]
            or state["subscription"] != env["TEST_SUBSCRIPTION_ID"]):
        raise ValueError("Prepared execution changed")
    run, attempt, ip = state["run"], state["attempt"], state["ip"]
    phrase, started = state["phrase"], state["started"]
    base = "https://api.github.com/repos/" + REPOSITORY + "/issues/" + state["issue"]
    comment = wait_for_confirmation(base, phrase, started)
    state["confirmation"] = {k: comment[k] for k in ("id", "created_at", "updated_at", "issue_url")}
    state["confirmation"]["body_sha256"] = hashlib.sha256(phrase.encode()).hexdigest()
    journal_path().write_text(json.dumps(state), encoding="utf-8")
    summary("WAIT: owner confirmation accepted, comment ID " + str(comment["id"]) +
            ", body SHA-256 " + state["confirmation"]["body_sha256"])
    validate_context()  # Azure account/session must still match PREPARE before any Blob token.
    if outward_ip() != ip:
        raise ValueError("Outbound IPv4 changed; operator must close original exception")
    host = env["TEST_ACCOUNT"] + ".blob.core.windows.net"
    socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
    with socket.create_connection((host, 443), timeout=15) as tcp:
        with ssl.create_default_context().wrap_socket(tcp, server_hostname=host):
            pass
    summary("VERIFY: DNS and HTTPS/TLS successful; Blob RBAC still requires its own check")
    payload = json.dumps({"synthetic": True, "run": run, "attempt": attempt,
                          "commit": env["GITHUB_SHA"]}, sort_keys=True).encode()
    credential = token()
    # Set before PUT because a transport failure can occur after the server wrote it.
    state["blob_may_exist"] = True
    journal_path().write_text(json.dumps(state), encoding="utf-8")
    for n in range(6):
        try:
            blob("PUT", state["blob"], credential, payload, create=True)
            break
        except urllib.error.HTTPError as error:
            if error.code != 403 or n == 5:
                raise
            time.sleep(10)
    received = blob("GET", state["blob"], credential)
    if received != payload:
        raise ValueError("Synthetic data differs")
    summary("VERIFY: OIDC Blob write/read integrity PASS (SHA-256 " + hashlib.sha256(payload).hexdigest() + ")")
    if not cleanup():
        raise RuntimeError("Synthetic cleanup incomplete")
    summary("FINISH: BLOB CHECK PASS / FIREWALL RESTORATION PENDING OPERATOR VERIFICATION. "
            "This is not Terraform or CD validation.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--cleanup", action="store_true")
    mode.add_argument("--prepare", action="store_true")
    mode.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    try:
        if args.cleanup:
            raise SystemExit(0 if cleanup() else 1)
        try:
            if args.prepare:
                prepare()
            elif args.verify:
                verify()
            else:
                prepare()
                verify()
        finally:
            if not args.prepare and journal_path().exists():
                if not cleanup():
                    raise RuntimeError("Cleanup requires operator recovery")
    except Exception as error:
        if isinstance(error, urllib.error.HTTPError):
            code = error.headers.get("x-ms-error-code", "")
            allowed = {"AuthorizationFailure", "AuthorizationPermissionMismatch", "AuthenticationFailed",
                       "ContainerNotFound", "BlobNotFound", "ConditionNotMet", "KeyBasedAuthenticationNotPermitted"}
            print("HTTP status: " + str(error.code) + "; Azure error category: " + (code if code in allowed else "unclassified"))
        # No raw response bodies, subprocess output or credential-bearing request objects.
        print("Diagnostic failed safely: " + type(error).__name__ + "; see stage summary and operator runbook", flush=True)
        raise SystemExit(1)
