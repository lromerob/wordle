"""Supervised saved-plan APPLY. No operation is performed by importing this module."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import time
import urllib.error
import urllib.request

import azure_supervised as ops
import cd_plan_workflow as flow
from cd_plan_contract import (CONTEXT_KEYS, TRANSITIONS, ContractError, PlanContract, Snapshot,
    canonical, decode, digest, identifier, matching, require, timestamp, WORKFLOW)
from cd_github_adapter import GitHubReadAdapter
from cd_github_trust import AuthorizationPolicy, Challenge, GitHubTrustVerifier, confirmation
from release_gate import ci_evidence
from storage_connectivity_test import NoRedirect, summary


def now(): return datetime.now(timezone.utc)


class BlobStore:
    """ArtifactStore over conditional Blob writes; no SQLite or expiring consumption right."""
    def __init__(self, token, plan_id, manifest_sha, backend_key, request=None):
        identifier(plan_id); matching(r"[a-f0-9]{64}", manifest_sha); matching(r"[a-f0-9]{64}", backend_key)
        self.token, self.plan_id, self.manifest_sha = token, plan_id, manifest_sha
        self.backend_key = backend_key
        self.request = request or self.http
        self.loaded = None

    def http(self, method, name, data=None, headers=None):
        require(name.startswith(("plans/", "coordination/")), "Unexpected private path")
        url = f"https://{flow.ACCOUNT}.blob.core.windows.net/{flow.CONTAINER}/{name}"
        h = {"Authorization": "Bearer " + self.token, "x-ms-version": "2023-11-03",
             "x-ms-date": now().strftime("%a, %d %b %Y %H:%M:%S GMT")}
        h.update(headers or {})
        if method == "PUT": h.update({"x-ms-blob-type": "BlockBlob", "Content-Type": "application/json"})
        try:
            with urllib.request.build_opener(NoRedirect()).open(urllib.request.Request(url, data=data, headers=h, method=method), timeout=60) as response:
                raw = response.read(65 * 1024 * 1024)
                require(len(raw) < 65 * 1024 * 1024, "Private object too large")
                return raw, response.headers.get("ETag")
        except urllib.error.HTTPError as error:
            if error.code == 404: raise FileNotFoundError() from None
            raise ContractError("Private storage request rejected or uncertain") from None
        except (OSError, urllib.error.URLError):
            raise ContractError("Private storage unavailable; no automatic retry") from None

    def path(self): return "coordination/plans/" + self.plan_id + ".json"

    def bundle(self):
        if self.loaded is not None: return self.loaded
        prefix = "plans/" + self.plan_id + "/"
        complete_raw, _ = self.request("GET", prefix + "complete.json")
        complete = decode(complete_raw)
        require(complete["plan_id"] == self.plan_id and complete["state"] == "PENDING_APPROVAL", "Invalid completion marker")
        objects = {}
        for name in ("manifest.json", "approved.tfplan", "challenge.json"):
            record = complete["objects"][name]
            raw, etag = self.request("GET", prefix + name, headers={"If-Match": record["etag"]})
            require(etag == record["etag"] and digest(raw) == record["sha256"] and len(raw) == record["size"], "Private object integrity mismatch")
            objects[name] = raw
        snap = Snapshot(objects["manifest.json"], objects["approved.tfplan"], self.manifest_sha, 1, "PENDING_APPROVAL", b"{}")
        manifest = snap.manifest(); challenge = decode(objects["challenge.json"])
        require(manifest["plan_id"] == self.plan_id and challenge["plan_id"] == self.plan_id
                and challenge["manifest_sha256"] == self.manifest_sha and challenge["plan_sha256"] == manifest["plan"]["sha256"]
                and challenge["purpose"] == "PLAN_REVIEW_ONLY_NOT_APPLY_AUTHORIZATION", "Producer challenge mismatch")
        self.loaded = snap
        return snap

    def coordinate(self, challenge):
        # Create-once challenge binds this plan to one APPLY run; never overwrite/reopen it.
        record = {"revision": 1, "state": "PENDING_APPROVAL", "metadata": {},
                  "manifest_sha256": self.manifest_sha, "challenge": challenge}
        try:
            self.request("GET", self.path())
        except FileNotFoundError:
            self.request("PUT", self.path(), canonical(record), {"If-None-Match": "*"})
        raw, _ = self.request("GET", self.path()); got = decode(raw)
        require(got == record, "Plan already coordinated, consumed or uncertain")

    def get(self, plan_id):
        require(plan_id == self.plan_id, "Unexpected plan")
        snap = self.bundle(); raw, _ = self.request("GET", self.path()); record = decode(raw)
        require(record["manifest_sha256"] == self.manifest_sha and type(record["revision"]) is int, "Coordination mismatch")
        return Snapshot(snap.manifest_raw, snap.plan, snap.manifest_sha256, record["revision"], record["state"], canonical(record["metadata"]))

    def transition(self, plan_id, version, state, metadata):
        require(plan_id == self.plan_id, "Unexpected plan")
        raw, etag = self.request("GET", self.path()); record = decode(raw)
        require(record["manifest_sha256"] == self.manifest_sha and record["revision"] == version
                and state in TRANSITIONS.get(record["state"], set()), "Invalid or concurrent transition")
        if state == "CONSUMING": self.claim_backend(metadata["consumer"])
        updated = dict(record, revision=version+1, state=state, metadata=metadata)
        self.request("PUT", self.path(), canonical(updated), {"If-Match": etag})
        verified, _ = self.request("GET", self.path()); require(verified == canonical(updated), "Coordination write uncertain")
        return self.get(plan_id)

    def claim_backend(self, consumer):
        name = "coordination/backends/" + self.backend_key + ".json"
        record = {"state": "CONSUMING", "plan_id": self.plan_id, "consumer": consumer}
        try:
            raw, etag = self.request("GET", name)
        except FileNotFoundError:
            self.request("PUT", name, canonical(record), {"If-None-Match": "*"})
        else:
            require(decode(raw).get("state") == "CONSUMED", "Backend has active or uncertain consumer")
            self.request("PUT", name, canonical(record), {"If-Match": etag})
        raw, _ = self.request("GET", name); require(raw == canonical(record), "Backend claim uncertain")

    def record_started(self, consumer, deadline):
        raw, etag = self.request("GET", self.path()); record = decode(raw)
        require(record["state"] == "CONSUMING" and record["metadata"]["consumer"] == consumer
                and not record["metadata"].get("apply_started"), "APPLY start already recorded or ownership lost")
        record["metadata"].update(apply_started=True, deadline=deadline)
        record["revision"] += 1
        data=canonical(record); self.request("PUT",self.path(),data,{"If-Match":etag})
        raw,_=self.request("GET",self.path());require(raw==data,"APPLY start write uncertain")

    def record_inventory(self, consumer, resources):
        require(isinstance(resources,list) and all(isinstance(x,str) for x in resources),"Invalid private inventory")
        data=canonical({"consumer":consumer,"resources":resources})
        self.request("PUT","coordination/inventories/"+self.plan_id+".json",data,{"If-None-Match":"*"})
        verified,_=self.request("GET","coordination/inventories/"+self.plan_id+".json")
        require(verified==data,"Inventory receipt uncertain")
        raw,etag=self.request("GET",self.path());record=decode(raw)
        require(record["state"]=="CONSUMING" and record["metadata"]["consumer"]==consumer,"Inventory ownership mismatch")
        record["metadata"].update(inventory_sha256=digest(data),resource_count=len(resources));record["revision"]+=1
        self.request("PUT",self.path(),canonical(record),{"If-Match":etag})
        raw,_=self.request("GET",self.path());require(raw==canonical(record),"Inventory metadata uncertain")

    def close_backend(self, consumer):
        name = "coordination/backends/" + self.backend_key + ".json"
        raw, etag = self.request("GET", name); record = decode(raw)
        require(record == {"state":"CONSUMING", "plan_id":self.plan_id, "consumer":consumer}, "Backend ownership mismatch")
        record["state"] = "CONSUMED"
        self.request("PUT", name, canonical(record), {"If-Match": etag})
        raw, _ = self.request("GET", name); require(raw == canonical(record), "Backend completion uncertain")


def config():
    e = os.environ
    require(e.get("GITHUB_ACTIONS") == "true" and e.get("WORDLE_APPLY_ENABLED") == "true" and e.get("GITHUB_REPOSITORY") == "lromerob/wordle"
            and e.get("GITHUB_REF") == flow.BRANCH and e.get("GITHUB_ACTOR") == "lromerob"
            and e.get("GITHUB_EVENT_NAME") == "workflow_dispatch" and e.get("GITHUB_RUN_ATTEMPT") == "1"
            and e.get("GITHUB_WORKFLOW_REF") == "lromerob/wordle/" + WORKFLOW + "@" + flow.BRANCH,
            "Unauthorized APPLY context")
    matching(r"[a-f0-9]{40}", e.get("APPROVED_SHA")); require(e.get("GITHUB_SHA") == e["APPROVED_SHA"], "SHA mismatch")
    identifier(e.get("PLAN_ID")); matching(r"[a-f0-9]{64}", e.get("MANIFEST_SHA256"))
    for key in ("CI_RUN", "CONFIRMATION_ISSUE", "GITHUB_RUN_ID", "APPLY_WORKFLOW_ID", "APPLY_ENVIRONMENT_ID"):
        matching(r"[1-9][0-9]*", e.get(key))
    require(e.get("APPLY_COSTS_APPROVED") == "true", "Explicit cost acknowledgement required")
    require(e.get("PLAN_OPERATION") in {"create", "update"}, "Unsupported APPLY intent")
    require(not any(k.startswith("TF_CLI_ARGS") and v for k,v in e.items()), "Injected Terraform flags forbidden")
    values = decode(e.get("PLAN_VARIABLES_JSON", "")); ops.validate_inputs(values, flow.BACKEND); ops.validate_oidc(values,e)
    require(values["subscription_id"] == e.get("ARM_SUBSCRIPTION_ID") and values["tenant_id"] == e.get("ARM_TENANT_ID"), "Target mismatch")
    require(e.get("INFRA_CLIENT_ID") and e.get("ARM_CLIENT_ID") == e["INFRA_CLIENT_ID"], "Pinned infrastructure identity required")
    require(e.get("ARM_CLIENT_ID") not in {e.get("PLAN_CLIENT_ID"),e.get("DIAGNOSTIC_CLIENT_ID")}
            and e.get("PLAN_CLIENT_ID") and e.get("DIAGNOSTIC_CLIENT_ID"), "Separate infrastructure identity required")
    return values


def check():
    config(); ci_evidence(os.environ["CI_RUN"],os.environ["APPROVED_SHA"])
    api = GitHubReadAdapter(); env = api.environment("wordle-azure-demo")
    require(str(env["id"]) == os.environ["APPLY_ENVIRONMENT_ID"] and env["can_admins_bypass"] is False
            and any(r.get("type")=="required_reviewers" and any(x.get("reviewer",{}).get("id")==69647965 for x in r.get("reviewers",[])) for r in env["protection_rules"]), "Protected environment required")


def runtime(store, work, values):
    def tf(*args): return ops.run(["terraform",*args],cwd=work)
    snap = store.bundle(); m = snap.manifest()
    require(decode(tf("version","-json"))["terraform_version"] == "1.9.8", "Terraform version mismatch")
    lock = (work/".terraform.lock.hcl").read_bytes()
    tf("init","-input=false","-reconfigure","-lockfile=readonly","-backend-config=backend.hcl")
    require((work/".terraform.lock.hcl").read_bytes()==lock and tf("workspace","show").strip()==b"default", "Lock/workspace mismatch")
    current = flow.state_fingerprint(tf("state","pull"))
    expected = {"operation":os.environ["PLAN_OPERATION"],"repository":"lromerob/wordle","commit_sha":os.environ["GITHUB_SHA"],"environment":"wordle-azure-demo",
       "terraform":{"version":"1.9.8","provider":{"source":"hashicorp/azurerm","version":"4.50.0"},"lock_sha256":digest(lock),"configuration_sha256":ops.fingerprint(work),"variables_sha256":digest((work/"variables.tfvars.json").read_bytes()),"backend":{"type":"azurerm","resource_group":flow.GROUP,"account":flow.ACCOUNT,"container":"tfstate","key":flow.BACKEND["key"],"workspace":"default"},"state":{k:current[k] for k in ("lineage","serial","sha256")}},
       "targets":{"subscription_id":values["subscription_id"],"tenant_id":values["tenant_id"],"resource_group":values["resource_group_name"],"node_resource_group":values["node_resource_group_name"],"cluster":values["cluster_name"]}}
    require({k:m[k] for k in CONTEXT_KEYS}==expected, "Current runtime differs from approved context")
    return expected


def consume(contract, store, expected, reference, work, execute=None, clock=now):
    plan_id=store.plan_id; run=os.environ["GITHUB_RUN_ID"]
    contract.approve(plan_id,expected,reference,run,"1",clock())
    claimed=contract.begin(plan_id,expected,run,"1",clock()); consumer=decode(claimed.metadata_raw)["consumer"]
    try:
        # Re-query independent approval after CAS, immediately before executable bytes are used.
        contract._verify_trust(claimed,reference,run,"1",clock())
        plan=work/"approved.tfplan"; require(not plan.exists(),"Plan path already exists")
        with plan.open("xb") as stream: stream.write(claimed.plan)
        os.chmod(plan,0o600)
        require(digest(plan.read_bytes())==claimed.manifest()["plan"]["sha256"],"Plan file changed")
        remaining=int((timestamp(claimed.manifest()["expires_at"])-clock()).total_seconds());require(remaining>0,"Plan expired")
        require(ops.fingerprint(work)==expected["terraform"]["configuration_sha256"],"Workspace changed during approval")
        store.record_started(consumer,claimed.manifest()["expires_at"])
        command=["terraform","apply","-input=false","-lock-timeout=60s","approved.tfplan"]
        summary("APPLY_STARTED; exclusive consumption recorded; no automatic replay")
        if execute: execute(command,work,remaining)
        else:
            result=subprocess.run(command,cwd=work,capture_output=True,timeout=min(2700,remaining))
            require(result.returncode==0,"Saved plan APPLY failed; output withheld")
        targets = expected["targets"]
        store.record_inventory(consumer, ops.inventory({
            "subscription_id": targets["subscription_id"],
            "resource_group_name": targets["resource_group"],
            "node_resource_group_name": targets["node_resource_group"],
        }))
        final=contract.finish(plan_id,consumer,True,clock());require(final.state=="CONSUMED","Consumption not completed")
        store.close_backend(consumer)
        summary("APPLY completed; plan CONSUMED; scoped inventory persisted privately")
    except BaseException:
        try: contract.mark_unknown(plan_id,consumer,"interrupted_unknown_outcome",clock())
        except Exception: pass  # Persistent CONSUMING/backend claim remains fail-closed.
        summary("APPLY outcome uncertain; backend blocked; human reconciliation required; no replay")
        raise


def apply():
    values=config(); j=flow.journal_for_run()
    require(j.get("opening_verified") is True and flow.boundary(flow.account())==flow.opened(j["baseline"],j["ip"])
            and flow.outward_ip()==j["ip"] and j["inputs_sha256"]==digest(canonical(values)),"Firewall/input context changed")
    ops.authenticate(values)
    token=ops.az("account","get-access-token","--resource","https://storage.azure.com/")["accessToken"]
    store=BlobStore(token,os.environ["PLAN_ID"],os.environ["MANIFEST_SHA256"],digest(canonical(flow.BACKEND)))
    work=flow.workdir()/"terraform"; expected=runtime(store,work,values)
    api=GitHubReadAdapter(); jobs=api.jobs(os.environ["GITHUB_RUN_ID"],"1");require(len(jobs["jobs"])==1,"Unexpected jobs")
    c=Challenge(os.environ["GITHUB_RUN_ID"],"1",secrets.token_hex(16),flow.stamp(now()),jobs["jobs"][0]["id"])
    store.coordinate(c.__dict__)
    policy=AuthorizationPolicy(1367282140,69647965,"lromerob",int(os.environ["APPLY_ENVIRONMENT_ID"]),"wordle-azure-demo",int(os.environ["APPLY_WORKFLOW_ID"]),flow.BRANCH.removeprefix("refs/heads/"),int(os.environ["CONFIRMATION_ISSUE"]),job_name="supervised",producer_workflow_id=428694070)
    snapshot=store.get(store.plan_id);trust=GitHubTrustVerifier(api,snapshot,expected,policy,c,now)
    summary("Review the private plan; then post exactly in the coordination issue:\n"+confirmation(snapshot,policy,c))
    deadline=time.monotonic()+600
    while time.monotonic()<deadline and now()<timestamp(snapshot.manifest()["expires_at"]):
        # Only absence may wait. Invalid/duplicate/edited evidence is rejected by verifier.
        comments=api.comments(policy.issue)
        if any(x.get("body")==confirmation(snapshot,policy,c) for x in comments):
            approval=trust.approval(None)
            consume(PlanContract(store,trust),store,expected,approval["reference"],work)
            return
        time.sleep(15)
    raise ContractError("Bound plan approval timed out; no APPLY started")


def main():
    parser=argparse.ArgumentParser();parser.add_argument("stage",choices=("check","prepare","wait-open","apply","finish"));args=parser.parse_args()
    try:
        {"check":check,"prepare":lambda:flow.prepare(config),"wait-open":lambda:flow.wait_open(config),"apply":apply,"finish":flow.finish}[args.stage]()
    except BaseException:
        print("APPLY stage refused/failed; private output withheld; close firewall and reconcile any consumption",file=sys.stderr)
        return 1
    return 0

if __name__=="__main__":sys.exit(main())
