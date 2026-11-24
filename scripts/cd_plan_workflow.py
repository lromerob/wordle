"""Supervised PLAN only. Cloud operations are reachable only through explicit workflow stages."""
import argparse
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
from cd_plan_contract import build_manifest, canonical, decode, digest, identifier, keys, matching, require
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
    require(e.get("PLAN_OPERATION") in {"create", "update"}, "Only create/update PLAN is permitted")
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


def prepare():
    values = config()
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


def wait_open():
    values = config(); j = journal_for_run()
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
        with self.opener.open(urllib.request.Request(url, data=raw, headers=headers, method="PUT"), timeout=60) as response:
            require(response.status == 201 and bool(response.headers.get("ETag")), "Private object creation not verified")
            etag = response.headers["ETag"]
            version = response.headers.get("x-ms-version-id")
        read_headers = {k: v for k, v in headers.items() if k not in {"If-None-Match", "x-ms-blob-type"}}
        read_headers["If-Match"] = etag
        with self.opener.open(urllib.request.Request(url, headers=read_headers, method="GET"), timeout=60) as response:
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


def state_fingerprint(raw):
    value = decode(raw); identifier(value["lineage"])
    require(type(value["serial"]) is int and value["serial"] >= 0, "Existing remote state required")
    return {"lineage": value["lineage"], "serial": value["serial"], "sha256": digest(raw)}


def execute_plan():
    values = config(); j = journal_for_run(); work = workdir() / "terraform"
    require(j.get("opening_verified") is True and boundary(account()) == opened(j["baseline"], j["ip"])
            and outward_ip() == j["ip"], "Verified firewall opening required")
    require(digest(canonical(values)) == j["inputs_sha256"], "PLAN inputs changed")
    def tf(*args): return ops.run(["terraform", *args], cwd=work)
    require(decode(tf("version", "-json"))["terraform_version"] == "1.9.8", "Unexpected Terraform version")
    container = ops.az("storage", "container", "show", "--account-name", ACCOUNT, "--name", CONTAINER, "--auth-mode", "login")
    require("publicAccess" in container.get("properties", {}) and container["properties"]["publicAccess"] is None,
            "Existing private plan container required")
    lock = (work / ".terraform.lock.hcl").read_bytes()
    tf("init", "-input=false", "-reconfigure", "-lockfile=readonly", "-backend-config=backend.hcl")
    require((work / ".terraform.lock.hcl").read_bytes() == lock, "Provider lock changed")
    require(tf("workspace", "show").strip() == b"default", "Unexpected backend workspace")
    before = state_fingerprint(tf("state", "pull"))
    require(not (work / "approved.tfplan").exists(), "Refusing plan overwrite")
    tf("validate", "-no-color")
    tf("plan", "-input=false", "-lock-timeout=60s", "-var-file=variables.tfvars.json", "-out=approved.tfplan")
    require(before == state_fingerprint(tf("state", "pull")), "Remote state changed during PLAN")
    rendered = decode(tf("show", "-json", "approved.tfplan"))
    ops.check_plan(rendered, "deploy", values)
    if os.environ["PLAN_OPERATION"] == "create":
        require(all(set(change["change"]["actions"]) <= {"create", "no-op"}
                    for change in rendered.get("resource_changes", []) if change.get("mode") != "data"),
                "Create intent contains updates; review a new update PLAN")
    plan = (work / "approved.tfplan").read_bytes()
    review = tf("show", "-no-color", "approved.tfplan")
    context = {"operation": os.environ["PLAN_OPERATION"], "repository": "lromerob/wordle",
        "commit_sha": os.environ["GITHUB_SHA"], "environment": "wordle-azure-demo", "terraform": {
            "version": "1.9.8", "provider": {"source": "hashicorp/azurerm", "version": "4.50.0"},
            "lock_sha256": digest(lock), "configuration_sha256": ops.fingerprint(work),
            "variables_sha256": digest((work / "variables.tfvars.json").read_bytes()),
            "backend": {"type": "azurerm", "resource_group": GROUP, "account": ACCOUNT, "container": "tfstate",
                        "key": BACKEND["key"], "workspace": "default"}, "state": before},
        "targets": {"subscription_id": values["subscription_id"], "tenant_id": values["tenant_id"],
                    "resource_group": values["resource_group_name"], "node_resource_group": values["node_resource_group_name"],
                    "cluster": values["cluster_name"]}}
    created = now()
    manifest = build_manifest(plan, context, {"workflow": WORKFLOW, "run_id": os.environ["GITHUB_RUN_ID"], "attempt": "1"},
                              stamp(created), stamp(created + timedelta(hours=2)))
    challenge = {"schema_version": 1, "purpose": "PLAN_REVIEW_ONLY_NOT_APPLY_AUTHORIZATION", "plan_id": manifest["plan_id"],
                 "manifest_sha256": digest(canonical(manifest)), "plan_sha256": digest(plan), "producer": manifest["producer"],
                 "nonce": secrets.token_hex(16), "issued_at": stamp(created), "expires_at": manifest["expires_at"]}
    token = ops.az("account", "get-access-token", "--resource", "https://storage.azure.com/")["accessToken"]
    receipt = publish(PlanBlobStore(token), manifest, plan, challenge, review)
    summary("PLAN stored privately; no APPLY authorized. Receipt: " + canonical(receipt).decode())
    closing_instructions(j)


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
    parser = argparse.ArgumentParser(); parser.add_argument("stage", choices=("check", "prepare", "wait-open", "plan", "finish"))
    args = parser.parse_args()
    try:
        {"check": check, "prepare": prepare, "wait-open": wait_open, "plan": execute_plan, "finish": finish}[args.stage]()
    except Exception:
        print("PLAN stage failed; raw output suppressed. No automatic retry or firewall write; follow manual closure runbook.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__": sys.exit(main())
