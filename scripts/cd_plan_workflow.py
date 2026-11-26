"""Supervised PLAN only. Cloud operations are reachable only through explicit workflow stages."""
import argparse
import base64
from decimal import Decimal
import re
from contextlib import contextmanager
import subprocess
import urllib.error
from datetime import datetime, timezone, timedelta
import json
import os
from pathlib import Path
import secrets
import sys
import time
import urllib.request
import uuid

import azure_supervised as ops
from cd_plan_contract import ContractError, build_manifest, canonical, decode, digest, identifier, keys, matching, require
from cd_github_adapter import GitHubReadAdapter
from release_gate import ci_evidence
from storage_connectivity_test import NoRedirect, outward_ip, confirmation_matches, summary

ACCOUNT = "stwordletfgstate7c92d4"
GROUP = "rg-wordle-state"
CONTAINER = "wordle-cd-private"
BACKEND = {"resource_group_name": GROUP, "storage_account_name": ACCOUNT,
           "container_name": "tfstate", "key": "wordle/aks-demo.tfstate", "use_azuread_auth": True}
BRANCH = "refs/heads/codex/pg01-07-consolidation"
WORKFLOW = ".github/workflows/azure-plan.yml"


def now(): return datetime.now(timezone.utc)
def stamp(value): return value.strftime("%Y-%m-%dT%H:%M:%SZ")


def config(env=None):
    e = os.environ if env is None else env
    require(e.get("GITHUB_REPOSITORY") == "lromerob/wordle" and e.get("GITHUB_REF") == BRANCH
            and e.get("GITHUB_ACTOR") == "lromerob" and e.get("GITHUB_EVENT_NAME") == "workflow_dispatch",
            "Unauthorized PLAN execution context")
    require(e.get("GITHUB_WORKFLOW_REF") == "lromerob/wordle/" + WORKFLOW + "@" + BRANCH,
            "Unexpected PLAN workflow")
    matching(r"[a-f0-9]{40}", e.get("APPROVED_SHA"))
    require(e.get("GITHUB_SHA") == e["APPROVED_SHA"] and e.get("GITHUB_RUN_ATTEMPT") == "1",
            "Reviewed SHA differs or rerun unsupported")
    for name in ("GITHUB_RUN_ID", "CONFIRMATION_ISSUE", "CI_RUN"):
        matching(r"[1-9][0-9]*", e.get(name))
    require(e.get("PLAN_OPERATION") in {"create", "update", "diagnose-state"}, "Unsupported supervised operation")
    for name in ("ARM_CLIENT_ID", "ARM_SUBSCRIPTION_ID", "ARM_TENANT_ID", "DIAGNOSTIC_CLIENT_ID"):
        identifier(e.get(name))
    require(e["ARM_CLIENT_ID"] != e["DIAGNOSTIC_CLIENT_ID"], "Diagnostic identity cannot run infrastructure PLAN")
    require(not any(k.startswith("TF_CLI_ARGS") and v for k, v in e.items()), "Injected Terraform CLI arguments forbidden")
    values = decode(e.get("PLAN_VARIABLES_JSON", ""))
    ops.validate_inputs(values, BACKEND)
    require(values["subscription_id"] == e["ARM_SUBSCRIPTION_ID"] and values["tenant_id"] == e["ARM_TENANT_ID"]
            and values.get("location", ops.terraform_defaults()["location"]) == "swedencentral", "PLAN target mismatch")
    ops.validate_oidc(values, e)
    return values


def check():
    config()
    ci_evidence(os.environ["CI_RUN"], os.environ["APPROVED_SHA"])
    api = GitHubReadAdapter()
    env = api.environment("wordle-azure-demo")
    require(env.get("can_admins_bypass") is False, "Environment bypass must be disabled")
    reviews = [r for r in env.get("protection_rules", []) if r.get("type") == "required_reviewers"]
    require(len(reviews) == 1 and any(r.get("reviewer", {}).get("id") == 69647965
            for r in reviews[0].get("reviewers", [])), "Owner review protection unavailable")
    policies = api.branch_policies("wordle-azure-demo")
    require(policies["total_count"] == 1 and policies["branch_policies"][0]["name"] == BRANCH.removeprefix("refs/heads/")
            and policies["branch_policies"][0]["type"] == "branch", "Unexpected environment branch policy")


def workdir():
    return ops.external(Path(os.environ["RUNNER_TEMP"]) / ("wordle-plan-" + os.environ["GITHUB_RUN_ID"] + "-1"))


def account():
    return ops.az("storage", "account", "show", "--resource-group", GROUP, "--name", ACCOUNT,
                  "--subscription", os.environ["ARM_SUBSCRIPTION_ID"])


def boundary(value):
    rules = value["networkRuleSet"]
    return {"rules": {**rules, "ipRules": sorted(rules.get("ipRules", []), key=canonical),
                      "virtualNetworkRules": sorted(rules.get("virtualNetworkRules", []), key=canonical)},
            **{k: value[k] for k in ("publicNetworkAccess", "allowSharedKeyAccess", "allowBlobPublicAccess",
                                    "enableHttpsTrafficOnly", "minimumTlsVersion")}}


def opened(baseline, ip):
    result = decode(canonical(baseline))
    result["rules"]["ipRules"].append({"ipAddressOrRange": ip, "action": "Allow"})
    result["rules"]["ipRules"].sort(key=canonical)
    return result


def prepare(validate=None):
    values = (validate or config)()
    ops.authenticate(values)
    session = ops.az("account", "show")
    require(session.get("user", {}).get("type") == "servicePrincipal"
            and session["user"].get("name", "").lower() == os.environ["ARM_CLIENT_ID"], "Unexpected federated identity")
    work = workdir(); work.mkdir(mode=0o700, parents=False, exist_ok=False)
    # Input values stay outside checkout, never in the step summary.
    (work / "input.json").write_bytes(canonical(values))
    (work / "backend.json").write_bytes(canonical(BACKEND))
    ops.prepare(work / "terraform", work / "input.json", work / "backend.json")
    baseline = boundary(account())
    require(baseline["rules"]["defaultAction"] == "Deny" and baseline["allowSharedKeyAccess"] is False
            and baseline["allowBlobPublicAccess"] is False and baseline["publicNetworkAccess"] == "Enabled"
            and baseline["enableHttpsTrafficOnly"] is True and baseline["minimumTlsVersion"] == "TLS1_2",
            "Unexpected Storage baseline")
    ip = outward_ip()
    require(not any(x["ipAddressOrRange"] in {ip, ip + "/32"} for x in baseline["rules"]["ipRules"]),
            "Runner IPv4 already present; refuse ambiguous exception")
    nonce = secrets.token_hex(16)
    phrase = f"WORDLE-PLAN-STORAGE-READY {os.environ['GITHUB_RUN_ID']} 1 {os.environ['GITHUB_SHA']} {ip} {nonce}"
    journal = {"baseline": baseline, "ip": ip, "nonce": nonce, "phrase": phrase, "started": stamp(now()),
               "run": os.environ["GITHUB_RUN_ID"], "sha": os.environ["GITHUB_SHA"], "inputs_sha256": digest(canonical(values))}
    (work / "firewall.json").write_bytes(canonical(journal))
    summary(f"PLAN PREPARE run {journal['run']} attempt 1, IPv4 {ip}, nonce {nonce}; baseline SHA256 {digest(canonical(baseline))}")
    summary("Operator: snapshot baseline, manually add only this IP, verify Deny and unchanged rules; then post in issue #" +
            os.environ["CONFIRMATION_ISSUE"] + ":\n```text\n" + phrase + "\n```")
    summary("PowerShell OPEN: az storage account network-rule add --resource-group " + GROUP + " --account-name " + ACCOUNT +
            " --subscription $ExpectedSubscription --ip-address " + ip + " --only-show-errors --output none")
    closing_instructions(journal)


def closing_instructions(journal):
    summary("Operator CLOSE: az storage account network-rule remove --resource-group " + GROUP + " --account-name " + ACCOUNT +
            " --subscription $ExpectedSubscription --ip-address " + journal["ip"] + " --only-show-errors --output none; "
            "verify the original baseline exactly. Timeout/cancellation is NOT evidence of closure.")


def journal_for_run():
    j = decode((workdir() / "firewall.json").read_bytes())
    require(j["run"] == os.environ["GITHUB_RUN_ID"] and j["sha"] == os.environ["GITHUB_SHA"], "Journal context changed")
    return j


def wait_open(validate=None):
    values = (validate or config)(); j = journal_for_run()
    require(j["inputs_sha256"] == digest(canonical(values)), "PLAN inputs changed")
    api = GitHubReadAdapter()
    deadline = time.monotonic() + 600
    issue_url = "https://api.github.com/repos/lromerob/wordle/issues/" + os.environ["CONFIRMATION_ISSUE"]
    while time.monotonic() < deadline:
        matches = [c for c in api.comments(os.environ["CONFIRMATION_ISSUE"])
                   if confirmation_matches(c, j["phrase"], j["started"], issue_url)
                   and c.get("user", {}).get("id") == 69647965]
        require(time.monotonic() < deadline, "Firewall confirmation window expired")
        require(len(matches) <= 1, "Duplicate firewall confirmation")
        if matches:
            require(outward_ip() == j["ip"] and boundary(account()) == opened(j["baseline"], j["ip"]),
                    "Firewall exception or baseline not verified")
            j["opening_verified"] = True
            (workdir() / "firewall.json").write_bytes(canonical(j))
            return
        time.sleep(15)
    raise ValueError("Firewall approval window expired; close exception manually")


class PlanBlobStore:
    """Minimal publish/readback only, not the distributed consumption adapter."""
    def __init__(self, credential, opener=None):
        self.credential = credential
        self.opener = opener or urllib.request.build_opener(NoRedirect())

    def put(self, plan_id, name, raw):
        identifier(plan_id)
        require(name in {"approved.tfplan", "manifest.json", "review.txt", "challenge.json", "complete.json"}, "Unexpected plan object")
        url = f"https://{ACCOUNT}.blob.core.windows.net/{CONTAINER}/plans/{plan_id}/{name}"
        headers = {"Authorization": "Bearer " + self.credential, "x-ms-version": "2023-11-03",
                   "x-ms-date": now().strftime("%a, %d %b %Y %H:%M:%S GMT"), "x-ms-blob-type": "BlockBlob",
                   "If-None-Match": "*", "Content-Type": "application/octet-stream"}
        with diagnostic("BLOB_WRITE", "blob"), self.opener.open(urllib.request.Request(url, data=raw, headers=headers, method="PUT"), timeout=60) as response:
            require(response.status == 201 and bool(response.headers.get("ETag")), "Private object creation not verified")
            etag = response.headers["ETag"]
            version = response.headers.get("x-ms-version-id")
        read_headers = {k: v for k, v in headers.items() if k not in {"If-None-Match", "x-ms-blob-type"}}
        read_headers["If-Match"] = etag
        with diagnostic("BLOB_VERIFY", "blob"), self.opener.open(urllib.request.Request(url, headers=read_headers, method="GET"), timeout=60) as response:
            require(response.status == 200 and response.read(len(raw) + 1) == raw, "Private readback integrity failed")
        return {"sha256": digest(raw), "size": len(raw), "etag": etag, "version_id": version}


def publish(store, manifest, plan, challenge, review):
    # Local validation before the first write; complete marker is committed last.
    from cd_plan_contract import Snapshot
    raw = canonical(manifest)
    Snapshot(raw, plan, digest(raw), 1, "STORED", b"{}").manifest()
    keys(challenge, {"schema_version", "purpose", "plan_id", "manifest_sha256", "plan_sha256", "producer", "nonce", "issued_at", "expires_at"})
    matching(r"[a-f0-9]{32}", challenge["nonce"])
    require(challenge["schema_version"] == 1 and challenge["purpose"] == "PLAN_REVIEW_ONLY_NOT_APPLY_AUTHORIZATION"
            and challenge["plan_id"] == manifest["plan_id"] and challenge["manifest_sha256"] == digest(raw)
            and challenge["plan_sha256"] == digest(plan) and challenge["producer"] == manifest["producer"]
            and challenge["issued_at"] == manifest["created_at"] and challenge["expires_at"] == manifest["expires_at"],
            "Review challenge not bound to this plan")
    objects = {"approved.tfplan": plan, "manifest.json": raw, "challenge.json": canonical(challenge), "review.txt": review}
    receipts = {name: store.put(manifest["plan_id"], name, data) for name, data in objects.items()}
    complete = {"schema_version": 1, "plan_id": manifest["plan_id"], "state": "PENDING_APPROVAL", "objects": receipts}
    marker = store.put(manifest["plan_id"], "complete.json", canonical(complete))
    return {"plan_id": manifest["plan_id"], "manifest_sha256": digest(raw), "plan_sha256": digest(plan),
            "complete_sha256": marker["sha256"], "state": "PENDING_APPROVAL"}


class StateIntegrityError(ContractError):
    def __init__(self, code):
        super().__init__(code)
        self.code = code


def state_fingerprint(raw):
    # Tagged canonical tree avoids float rounding and preserves JSON types/array order.
    def unique(pairs):
        result = {}
        for key, value in pairs:
            key.encode("utf-8", errors="strict")
            if key in result: raise ValueError()
            result[key] = value
        return result
    def invalid_constant(_): raise ValueError()
    def tree(value):
        if isinstance(value, dict): return ["object", [[k, tree(v)] for k, v in sorted(value.items())]]
        if isinstance(value, list): return ["array", [tree(v) for v in value]]
        if isinstance(value, Decimal):
            sign, digits, exponent = value.as_tuple()
            digits = list(digits)
            while len(digits) > 1 and digits[-1] == 0:
                digits.pop(); exponent += 1
            if not any(digits): sign, digits, exponent = 0, [0], 0
            return ["decimal", sign, digits, exponent]
        if value is None: return ["null"]
        if type(value) is bool: return ["boolean", value]
        if type(value) is int: return ["integer", str(value)]
        if isinstance(value, str):
            value.encode("utf-8", errors="strict")  # Reject unpaired Unicode surrogates.
            return ["string", value]
        raise ValueError()
    try:
        value = json.loads(raw.decode("utf-8", errors="strict"), object_pairs_hook=unique,
                           parse_float=Decimal, parse_constant=invalid_constant)
        require(isinstance(value, dict) and type(value.get("version")) is int and value["version"] == 4,
                "Invalid state")
        identifier(value["lineage"])
        require(type(value["serial"]) is int and value["serial"] >= 0
                and isinstance(value.get("resources"), list) and isinstance(value.get("outputs", {}), dict)
                and all(isinstance(r, dict) and isinstance(r.get("instances", []), list) for r in value["resources"]),
                "Invalid state")
        semantic = digest(canonical(tree(value)))
    except (ValueError, KeyError, TypeError, OverflowError, RecursionError):
        raise StateIntegrityError("STATE_STRUCTURE_INVALID") from None
    return {"lineage": value["lineage"], "serial": value["serial"],
            "sha256": digest(raw), "semantic_sha256": semantic}


def compare_state(before, after):
    for key, code in (("lineage", "STATE_LINEAGE_CHANGED"), ("serial", "STATE_SERIAL_CHANGED"),
                      ("semantic_sha256", "STATE_CONTENT_CHANGED")):
        if before[key] != after[key]: raise StateIntegrityError(code)
    if before["sha256"] != after["sha256"]:
        print("[STATE-INTEGRITY] REPRESENTATION_ONLY semantic equality verified", flush=True)


def diagnostic_failure(step, component, error):
    # All output fields are fixed strings or numeric metadata, never exception text.
    category, code, exit_code = "UNKNOWN_ERROR", "UNCLASSIFIED", None
    if isinstance(error, StateIntegrityError):
        category, code = "INTEGRITY_ERROR", error.code
    elif isinstance(error, ops.CommandFailure):
        component, category, code, exit_code = error.component, error.category, error.code, error.exit_code
    elif isinstance(error, urllib.error.HTTPError):
        category = "AUTHENTICATION_ERROR" if error.code == 401 else "AUTHORIZATION_ERROR" if error.code == 403 else "PERSISTENCE_ERROR"
        code = "HTTP_" + str(error.code) if type(error.code) is int and 100 <= error.code <= 599 else "HTTP_ERROR"
    elif isinstance(error, (TimeoutError, subprocess.TimeoutExpired)):
        category, code = "TIMEOUT", "TIMEOUT"
    elif isinstance(error, urllib.error.URLError):
        category, code = "CONNECTIVITY_ERROR", "CONNECTION_FAILED"
    elif isinstance(error, (ValueError, KeyError, TypeError)):
        category, code = ("INTEGRITY_ERROR", "VALIDATION_REJECTED") if step in {"STATE_BEFORE", "STATE_AFTER", "LOCK_VERIFY", "PLAN_REVIEW", "MANIFEST", "HASHES", "BLOB_VERIFY"} else ("CONFIGURATION_ERROR", "VALIDATION_REJECTED")
    elif isinstance(error, OSError):
        category, code = "IO_ERROR", "IO_FAILED"
    print(f"[PLAN][{step}] FAIL component={component} exit_code={exit_code if type(exit_code) is int else 'NA'} category={category} code={code}", flush=True)


@contextmanager
def diagnostic(step, component):
    print(f"[PLAN][{step}] START component={component}", flush=True)
    try:
        yield
    except Exception as error:
        diagnostic_failure(step, component, error)
        raise
    else:
        print(f"[PLAN][{step}] PASS component={component}", flush=True)


def execute_plan():
    require(os.environ.get("PLAN_OPERATION") in {"create", "update"}, "Diagnostic operation cannot execute PLAN")
    def tf(*args): return ops.run(["terraform", *args], cwd=work)
    with diagnostic("CONFIGURATION", "python"):
        values = config(); j = journal_for_run(); work = workdir() / "terraform"
    with diagnostic("FIREWALL_VERIFY", "azure-cli"):
        require(j.get("opening_verified") is True and boundary(account()) == opened(j["baseline"], j["ip"])
                and outward_ip() == j["ip"], "Verified firewall opening required")
    with diagnostic("INPUT_VERIFY", "python"):
        require(digest(canonical(values)) == j["inputs_sha256"], "PLAN inputs changed")
    with diagnostic("TF_VERSION", "terraform"):
        require(decode(tf("version", "-json"))["terraform_version"] == "1.9.8", "Unexpected Terraform version")
    with diagnostic("PRIVATE_CONTAINER", "azure-cli"):
        container = ops.az("storage", "container", "show", "--account-name", ACCOUNT, "--name", CONTAINER, "--auth-mode", "login")
        require("publicAccess" in container.get("properties", {}) and container["properties"]["publicAccess"] is None,
                "Existing private plan container required")
    with diagnostic("LOCK_READ", "python"):
        lock = (work / ".terraform.lock.hcl").read_bytes()
    with diagnostic("BACKEND_INIT", "terraform"):
        tf("init", "-input=false", "-reconfigure", "-lockfile=readonly", "-backend-config=backend.hcl")
    with diagnostic("LOCK_VERIFY", "python"):
        require((work / ".terraform.lock.hcl").read_bytes() == lock, "Provider lock changed")
    with diagnostic("WORKSPACE", "terraform"):
        require(tf("workspace", "show").strip() == b"default", "Unexpected backend workspace")
    with diagnostic("STATE_BEFORE", "terraform"):
        before = state_fingerprint(tf("state", "pull"))
    with diagnostic("OUTPUT_GUARD", "python"):
        require(not (work / "approved.tfplan").exists(), "Refusing plan overwrite")
    with diagnostic("VALIDATE", "terraform"):
        tf("validate", "-no-color")
    with diagnostic("GENERATE", "terraform"):
        tf("plan", "-input=false", "-lock-timeout=60s", "-var-file=variables.tfvars.json", "-out=approved.tfplan")
    with diagnostic("STATE_AFTER", "terraform"):
        compare_state(before, state_fingerprint(tf("state", "pull")))
    with diagnostic("PLAN_REVIEW", "terraform"):
        rendered = decode(tf("show", "-json", "approved.tfplan"))
        ops.check_plan(rendered, "deploy", values)
        if os.environ["PLAN_OPERATION"] == "create":
            require(all(set(change["change"]["actions"]) <= {"create", "no-op"}
                        for change in rendered.get("resource_changes", []) if change.get("mode") != "data"),
                    "Create intent contains updates; review a new update PLAN")
    with diagnostic("PLAN_READ", "python"):
        plan = (work / "approved.tfplan").read_bytes()
    with diagnostic("REVIEW_TEXT", "terraform"):
        review = tf("show", "-no-color", "approved.tfplan")
    with diagnostic("HASHES", "python"):
        context = {"operation": os.environ["PLAN_OPERATION"], "repository": "lromerob/wordle",
            "commit_sha": os.environ["GITHUB_SHA"], "environment": "wordle-azure-demo", "terraform": {
                "version": "1.9.8", "provider": {"source": "hashicorp/azurerm", "version": "4.50.0"},
                "lock_sha256": digest(lock), "configuration_sha256": ops.fingerprint(work),
                "variables_sha256": digest((work / "variables.tfvars.json").read_bytes()),
                "backend": {"type": "azurerm", "resource_group": GROUP, "account": ACCOUNT, "container": "tfstate",
                            "key": BACKEND["key"], "workspace": "default"}, "state": {k: before[k] for k in ("lineage", "serial", "sha256")}},
            "targets": {"subscription_id": values["subscription_id"], "tenant_id": values["tenant_id"],
                        "resource_group": values["resource_group_name"], "node_resource_group": values["node_resource_group_name"],
                        "cluster": values["cluster_name"]}}
    with diagnostic("MANIFEST", "python"):
        created = now()
        manifest = build_manifest(plan, context, {"workflow": WORKFLOW, "run_id": os.environ["GITHUB_RUN_ID"], "attempt": "1"},
                                  stamp(created), stamp(created + timedelta(hours=2)))
        challenge = {"schema_version": 1, "purpose": "PLAN_REVIEW_ONLY_NOT_APPLY_AUTHORIZATION", "plan_id": manifest["plan_id"],
                     "manifest_sha256": digest(canonical(manifest)), "plan_sha256": digest(plan), "producer": manifest["producer"],
                     "nonce": secrets.token_hex(16), "issued_at": stamp(created), "expires_at": manifest["expires_at"]}
    with diagnostic("STORAGE_TOKEN", "azure-cli"):
        token = ops.az("account", "get-access-token", "--resource", "https://storage.azure.com/")["accessToken"]
    with diagnostic("PRIVATE_PERSIST", "blob"):
        receipt = publish(PlanBlobStore(token), manifest, plan, challenge, review)
    summary("PLAN stored privately; no APPLY authorized. Receipt: " + canonical(receipt).decode())
    closing_instructions(j)


def state_error_details(result):
    """Project stderr onto fixed signatures, never echo an arbitrary redacted fragment."""
    text = result.stderr.decode("utf-8", errors="replace")
    known = {
        "NO_STATE": r"No state file was found",
        "STATE_LOAD": r"(?:Failed|Error) (?:to load|loading|to read) state",
        "TOKEN_ACQUISITION": r"(?:failed|unable) to (?:get|acquire|obtain).*token",
        "OIDC_ENVIRONMENT": r"(?:OIDC|ID_TOKEN).*?(?:missing|not set|not found|unavailable)",
        "CLI_CONTEXT": r"Please run .?az login|Azure CLI Authorization Profile was not found",
        "STATE_FORMAT": r"unsupported checkable object kind|unsupported state file format|Invalid resource instance data",
        "PROVIDER_CONFIGURATION": r"Required plugins are not installed|Invalid provider configuration|No value for required variable",
        "BLOB_NOT_FOUND": r"BlobNotFound",
        "REQUEST_AUTHORIZATION": r"AuthorizationFailed|AuthorizationFailure|AuthorizationPermissionMismatch",
    }
    signatures = [k for k, pattern in known.items() if re.search(pattern, text, re.I)]
    # Only fixed keywords and bounded protocol codes survive unknown diagnostics.
    hints = [k for k in ("state", "backend", "oidc", "token", "credential", "lease", "json", "parse", "provider", "certificate", "timeout", "cli")
             if re.search(r"\b" + k + r"\b", text, re.I)]
    http = sorted(set(re.findall(r"(?:HTTP[/ ](?:1[.]1 |2 )?|status(?:[ _-]?code)?[ :=]+)([1-5][0-9]{2})\b", text, re.I)))
    aadsts = sorted(set(re.findall(r"\bAADSTS(700213|70021|700016|700024|7000215|500011)\b", text)))
    return {"exit_code": result.returncode, "signatures": signatures, "hints": hints,
            "http_status": http, "aadsts": ["AADSTS" + x for x in aadsts],
            "stderr_present": bool(result.stderr), "details_withheld": not bool(signatures or http or aadsts)}


def diagnostic_state_info(raw):
    value = decode(raw)
    state_fingerprint(raw)
    require(value.get("version") == 4 and isinstance(value.get("resources"), list), "Invalid Terraform state structure")
    require(all(isinstance(r, dict) and isinstance(r.get("instances", []), list) for r in value["resources"]), "Invalid resource structure")
    return {"valid": True, "managed_instances": sum(len(r.get("instances", [])) for r in value["resources"] if r.get("mode") == "managed")}


def state_blob_metadata():
    value = ops.az("storage", "blob", "show", "--account-name", ACCOUNT, "--container-name", BACKEND["container_name"],
                   "--name", BACKEND["key"], "--auth-mode", "login")
    p = value["properties"]
    # Only typed, bounded metadata, never user metadata or arbitrary CLI payloads.
    require(type(p["contentLength"]) is int and p["contentLength"] >= 0, "Invalid blob length")
    require(re.fullmatch(r'"?0x[0-9a-fA-F]+"?', p["etag"]) is not None, "Invalid ETag")
    modified = datetime.fromisoformat(p["lastModified"].replace("Z", "+00:00")).isoformat()
    lease = p["lease"]
    require(lease.get("state") in {"available", "leased", "expired", "breaking", "broken"}
            and lease.get("status") in {"locked", "unlocked"}, "Invalid lease metadata")
    return {"exists": True, "size": p["contentLength"], "etag": p["etag"], "last_modified": modified,
            "lease_state": lease["state"], "lease_status": lease["status"]}


def diagnose_state():
    require(os.environ.get("PLAN_OPERATION") == "diagnose-state", "Explicit diagnostic intent required")
    values = config(); j = journal_for_run(); work = workdir() / "terraform"
    require(j.get("opening_verified") is True and boundary(account()) == opened(j["baseline"], j["ip"])
            and outward_ip() == j["ip"] and digest(canonical(values)) == j["inputs_sha256"], "Verified unchanged diagnostic context required")
    failures = []
    def attempt(step, action):
        try:
            with diagnostic(step, "state-diagnostic"):
                return action()
        except Exception:
            failures.append(step)
            return None
    def direct(args):
        # Same executable/cwd/environment/timeout as ops.run; no shell, retry or raw logging.
        result = subprocess.run(["terraform", *args], cwd=work, capture_output=True, timeout=2700)
        if result.returncode:
            print("[STATE-DIAG] " + canonical(state_error_details(result)).decode(), flush=True)
            raise ops.command_failure(["terraform"], result.returncode, result.stderr)
        return result.stdout
    def identity():
        ops.authenticate(values)
        session = ops.az("account", "show")
        require(session.get("user", {}).get("type") == "servicePrincipal"
                and session["user"].get("name", "").lower() == os.environ["ARM_CLIENT_ID"], "CLI identity mismatch")
        managed = ops.az("identity", "show", "--name", "wordle-terraform-plan", "--resource-group", GROUP,
                         "--subscription", values["subscription_id"])
        require(managed["clientId"] == os.environ["ARM_CLIENT_ID"] and managed["tenantId"] == values["tenant_id"], "PLAN identity mismatch")
        token = ops.az("account", "get-access-token", "--resource", "https://storage.azure.com/")["accessToken"]
        claims = decode(base64.urlsafe_b64decode(token.split(".")[1] + "==="))
        require(claims.get("appid", claims.get("azp")) == managed["clientId"] and claims.get("oid") == managed["principalId"]
                and claims.get("tid") == managed["tenantId"], "Storage token identity mismatch")
        # Claim comparison is context evidence, not standalone JWT verification or proof of Terraform's effective token.
        print("[STATE-DIAG] CLI/token/managed identity match; Terraform OIDC wiring present; Terraform token identity not independently observed", flush=True)
        return token
    token = attempt("DIAG_01_IDENTITY", identity)
    require(token is not None, "Cannot diagnose under an unverified identity")
    before = attempt("DIAG_02_METADATA", state_blob_metadata)
    if before is not None: print("[STATE-DIAG] " + canonical(before).decode(), flush=True)
    def read_blob():
        url = f"https://{ACCOUNT}.blob.core.windows.net/{BACKEND['container_name']}/{BACKEND['key']}"
        headers = {"Authorization": "Bearer " + token, "x-ms-version": "2023-11-03"}
        if before is not None: headers["If-Match"] = before["etag"]
        with urllib.request.build_opener(NoRedirect()).open(urllib.request.Request(url, headers=headers, method="GET"), timeout=60) as response:
            require(response.status == 200, "Unexpected Blob response")
            return diagnostic_state_info(response.read())
    blob_info = attempt("DIAG_03_BLOB_READ", read_blob)
    if blob_info is not None: print("[STATE-DIAG] blob " + canonical(blob_info).decode(), flush=True)
    def initialize():
        require(decode(direct(["version", "-json"]))["terraform_version"] == "1.9.8", "Unexpected Terraform version")
        lock = (work / ".terraform.lock.hcl").read_bytes()
        direct(["init", "-input=false", "-reconfigure", "-lockfile=readonly", "-backend-config=backend.hcl"])
        require((work / ".terraform.lock.hcl").read_bytes() == lock, "Provider lock changed")
        require(direct(["workspace", "show"]).strip() == b"default", "Unexpected workspace")
        cache = decode((work / ".terraform/terraform.tfstate").read_bytes())["backend"]
        require(cache["type"] == "azurerm" and all(cache["config"].get(k) == v for k, v in BACKEND.items()), "Effective backend mismatch")
        return True
    initialized = attempt("DIAG_04_INIT", initialize) if before is not None and before["lease_status"] == "unlocked" else None
    if not initialized: print("[STATE-DIAG] DIAG_05_DIRECT_PULL SKIP initialized existing backend required", flush=True)
    environment_before = dict(os.environ)
    def pull_direct():
        raw = direct(["state", "pull"])
        print("[STATE-DIAG] direct " + canonical(diagnostic_state_info(raw)).decode(), flush=True)
        return raw
    raw = attempt("DIAG_05_DIRECT_PULL", pull_direct) if initialized else None
    if raw is not None:
        def compare():
            info = diagnostic_state_info(raw)
            require(dict(os.environ) == environment_before, "Diagnostic environment changed")
            wrapped = ops.run(["terraform", "state", "pull"], cwd=work)
            require(diagnostic_state_info(wrapped) == info, "Direct/wrapper state mismatch")
            compare_state(state_fingerprint(raw), state_fingerprint(wrapped))
            return True
        attempt("DIAG_06_WRAPPER", compare)
    else:
        print("[STATE-DIAG] DIAG_06_WRAPPER SKIP direct pull not successful", flush=True)
    after = attempt("DIAG_METADATA_AFTER", state_blob_metadata)
    require(before is not None and after == before, "Remote metadata preservation not verified")
    print("[STATE-DIAG] metadata unchanged; no state writes or leases requested", flush=True)
    require(not failures, "State diagnostic failed; follow FINISH; no planning or publication")


def finish():
    path = workdir() / "firewall.json"
    if not path.exists():
        summary("No prepared firewall request. Verify manually if any exception was opened outside this execution.")
        return
    j = journal_for_run(); closing_instructions(j)
    deadline = time.monotonic() + 600
    while time.monotonic() < deadline:
        if boundary(account()) == j["baseline"]:
            summary("Firewall baseline restoration verified by ARM read; no firewall modification performed.")
            return
        time.sleep(15)
    raise ValueError("Firewall baseline NOT restored/verified; operator intervention required")


def main():
    parser = argparse.ArgumentParser(); parser.add_argument("stage", choices=("check", "prepare", "wait-open", "plan", "finish", "diagnose-state"))
    args = parser.parse_args()
    try:
        with diagnostic({"check": "CHECK", "prepare": "PREPARE", "wait-open": "WAIT_OPEN", "plan": "EXECUTION", "finish": "FINISH", "diagnose-state": "STATE_DIAG"}[args.stage], "python"):
            {"check": check, "prepare": prepare, "wait-open": wait_open, "plan": execute_plan, "finish": finish, "diagnose-state": diagnose_state}[args.stage]()
    except Exception:
        print("PLAN stage failed; raw output suppressed. No automatic retry or firewall write; follow manual closure runbook.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__": sys.exit(main())
