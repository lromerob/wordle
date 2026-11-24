"""PLAN integration tests: synthetic inputs, mocked Azure/HTTP/Terraform, no network."""
from copy import deepcopy
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
import io
import os
import socket
import tempfile
import unittest
from unittest.mock import patch
import urllib.error

import yaml
import cd_plan_workflow as flow
from cd_plan_contract import ContractError, PlanContract, build_manifest, canonical, decode, digest
from cd_github_trust import GitHubTrustVerifier, confirmation
import test_cd_github_trust as fixtures
from test_cd_plan_contract import context, PLAN, NOW


class MemoryPublisher:
    def __init__(self): self.objects = {}; self.order = []
    def put(self, plan_id, name, raw):
        if name in self.objects: raise ValueError("Overwrite rejected")
        self.objects[name] = raw; self.order.append(name)
        return {"sha256": digest(raw), "size": len(raw), "etag": '"test-etag"', "version_id": None}


class Response:
    def __init__(self, raw=b"", status=201): self.raw=raw; self.status=status; self.headers={"ETag": '"test-etag"'}
    def __enter__(self): return self
    def __exit__(self,*args): pass
    def read(self, size): return self.raw[:size]


class PlanTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="wordle-plan-workflow-"); self.addCleanup(self.tmp.cleanup)
        self.guard = patch.object(socket.socket, "connect", side_effect=AssertionError("Network forbidden"))
        self.guard.start(); self.addCleanup(self.guard.stop)
        self.work=Path(self.tmp.name)
        self.values={"subscription_id":"22222222-2222-4222-8222-222222222222", "tenant_id":"33333333-3333-4333-8333-333333333333",
            "resource_group_name":"rg-wordle-demo", "node_resource_group_name":"rg-wordle-demo-nodes", "cluster_name":"aks-wordle-demo",
            "admin_group_object_ids":["11111111-1111-4111-8111-111111111111"], "api_authorized_cidrs":["8.8.8.8/32"],
            "api_access_approved":True, "location":"swedencentral"}
        self.env={"GITHUB_REPOSITORY":"lromerob/wordle", "GITHUB_REF":flow.BRANCH, "GITHUB_ACTOR":"lromerob",
            "GITHUB_EVENT_NAME":"workflow_dispatch", "GITHUB_WORKFLOW_REF":"lromerob/wordle/"+flow.WORKFLOW+"@"+flow.BRANCH,
            "APPROVED_SHA":"a"*40, "GITHUB_SHA":"a"*40, "GITHUB_RUN_ID":"100", "GITHUB_RUN_ATTEMPT":"1",
            "CONFIRMATION_ISSUE":"6", "CI_RUN":"99", "PLAN_OPERATION":"create", "ARM_CLIENT_ID":"44444444-4444-4444-8444-444444444444",
            "DIAGNOSTIC_CLIENT_ID":"55555555-5555-4555-8555-555555555555", "ARM_SUBSCRIPTION_ID":self.values["subscription_id"],
            "ARM_TENANT_ID":self.values["tenant_id"], "PLAN_VARIABLES_JSON":canonical(self.values).decode(),
            "GITHUB_ACTIONS":"true", "ARM_USE_OIDC":"true", "ARM_USE_AZUREAD":"true", "ARM_USE_CLI":"false",
            "WORDLE_APPROVED_CLIENT_ID":"44444444-4444-4444-8444-444444444444",
            "ACTIONS_ID_TOKEN_REQUEST_URL":"https://pipelines.actions.githubusercontent.com/token", "ACTIONS_ID_TOKEN_REQUEST_TOKEN":"synthetic"}
        self.patchenv=patch.dict(os.environ,self.env,clear=True); self.patchenv.start(); self.addCleanup(self.patchenv.stop)
        self.baseline={"rules":{"defaultAction":"Deny", "ipRules":[{"ipAddressOrRange":"8.8.4.4","action":"Allow"}],
                                  "virtualNetworkRules":[], "bypass":"None"}, "publicNetworkAccess":"Enabled", "allowSharedKeyAccess":False,
                       "allowBlobPublicAccess":False, "enableHttpsTrafficOnly":True, "minimumTlsVersion":"TLS1_2"}

    def artifacts(self):
        ctx=context();ctx["environment"]="wordle-azure-demo"
        m=build_manifest(PLAN,ctx,{"workflow":flow.WORKFLOW,"run_id":"100","attempt":"1"},
                         "2026-11-23T12:00:00Z","2026-11-23T14:00:00Z")
        challenge={"schema_version":1,"purpose":"PLAN_REVIEW_ONLY_NOT_APPLY_AUTHORIZATION", "plan_id":m["plan_id"],
            "manifest_sha256":digest(canonical(m)),"plan_sha256":digest(PLAN),"producer":m["producer"],"nonce":"f"*32,
            "issued_at":m["created_at"],"expires_at":m["expires_at"]}
        return m,challenge

    def test_valid_configuration(self): self.assertEqual(flow.config(),self.values)
    def test_ci_failure_stops_before_azure(self):
        with patch.object(flow,"ci_evidence",side_effect=ValueError("CI failed")),patch.object(flow.ops,"az") as az:
            with self.assertRaises(ValueError): flow.check()
            az.assert_not_called()
    def test_ci_checked_against_exact_sha(self):
        class API:
            def environment(self,name): return {"can_admins_bypass":False,"protection_rules":[{"type":"required_reviewers","reviewers":[{"reviewer":{"id":69647965}}]}]}
            def branch_policies(self,name): return {"total_count":1,"branch_policies":[{"name":flow.BRANCH.removeprefix("refs/heads/"),"type":"branch"}]}
        with patch.object(flow,"ci_evidence") as ci,patch.object(flow,"GitHubReadAdapter",return_value=API()):
            flow.check();ci.assert_called_once_with("99","a"*40)
    def test_wrong_branch(self):
        os.environ["GITHUB_REF"]="refs/heads/main"
        with self.assertRaises(ContractError): flow.config()
    def test_wrong_sha(self):
        os.environ["GITHUB_SHA"]="b"*40
        with self.assertRaises(ContractError): flow.config()
    def test_missing_private_inputs(self):
        del os.environ["PLAN_VARIABLES_JSON"]
        with self.assertRaises(ContractError): flow.config()
    def test_diagnostic_identity_rejected(self):
        os.environ["ARM_CLIENT_ID"]=os.environ["DIAGNOSTIC_CLIENT_ID"]
        with self.assertRaises(ContractError): flow.config()
    def test_wrong_region(self):
        self.values["location"]="westeurope"; os.environ["PLAN_VARIABLES_JSON"]=canonical(self.values).decode()
        with self.assertRaises(ContractError): flow.config()
    def test_rerun_rejected(self):
        os.environ["GITHUB_RUN_ATTEMPT"]="2"
        with self.assertRaises(ContractError): flow.config()
    def test_unsupported_operation(self):
        os.environ["PLAN_OPERATION"]="destroy"
        with self.assertRaises(ContractError): flow.config()
    def test_injected_lock_false_rejected(self):
        os.environ["TF_CLI_ARGS_plan"]="-lock=false"
        with self.assertRaises(ContractError): flow.config()

    def test_complete_marker_last_and_hashes(self):
        m,c=self.artifacts();store=MemoryPublisher()
        receipt=flow.publish(store,m,PLAN,c,b"synthetic review")
        self.assertEqual(store.order[-1],"complete.json")
        self.assertEqual(receipt["plan_sha256"],digest(PLAN))
        self.assertEqual(decode(store.objects["complete.json"])["state"],"PENDING_APPROVAL")
    def test_plan_integrity_before_upload(self):
        m,c=self.artifacts();store=MemoryPublisher()
        with self.assertRaises(ContractError): flow.publish(store,m,PLAN+b"x",c,b"review")
        self.assertEqual(store.objects,{})
    def test_challenge_wrong_hash_rejected(self):
        m,c=self.artifacts();c["plan_sha256"]="0"*64;store=MemoryPublisher()
        with self.assertRaises(ContractError): flow.publish(store,m,PLAN,c,b"review")
        self.assertEqual(store.objects,{})
    def test_overwrite_rejected(self):
        m,c=self.artifacts();store=MemoryPublisher();flow.publish(store,m,PLAN,c,b"review")
        with self.assertRaises(ValueError): flow.publish(store,m,PLAN,c,b"review")
    def test_partial_upload_has_no_complete_marker(self):
        class Failed(MemoryPublisher):
            def put(self, plan_id,name,raw):
                if name=="challenge.json": raise OSError("synthetic interruption")
                return super().put(plan_id,name,raw)
        m,c=self.artifacts();store=Failed()
        with self.assertRaises(OSError): flow.publish(store,m,PLAN,c,b"review")
        self.assertNotIn("complete.json",store.objects)

    def test_blob_conditional_write_and_readback(self):
        calls=[]
        class Opener:
            def open(self, request, timeout):
                calls.append(request)
                return Response(status=201) if request.method=="PUT" else Response(PLAN,status=200)
        m,_=self.artifacts()
        got=flow.PlanBlobStore("synthetic-token",Opener()).put(m["plan_id"],"approved.tfplan",PLAN)
        self.assertEqual(got["sha256"],digest(PLAN))
        self.assertEqual(calls[0].get_header("If-none-match"),"*")
        self.assertEqual(calls[1].get_header("If-match"),'"test-etag"')
    def test_blob_readback_corruption(self):
        class Opener:
            def open(self,request,timeout):
                return Response(status=201) if request.method=="PUT" else Response(b"wrong",status=200)
        m,_=self.artifacts()
        with self.assertRaises(ContractError): flow.PlanBlobStore("synthetic",Opener()).put(m["plan_id"],"approved.tfplan",PLAN)
    def test_blob_conflict_fails_no_overwrite_retry(self):
        calls=[]
        class Opener:
            def open(self,request,timeout):
                calls.append(request); raise urllib.error.HTTPError(request.full_url,412,"conflict",{},None)
        m,_=self.artifacts()
        with self.assertRaises(urllib.error.HTTPError): flow.PlanBlobStore("synthetic",Opener()).put(m["plan_id"],"approved.tfplan",PLAN)
        self.assertEqual(len(calls),1)

    def test_only_individual_runner_exception_accepted(self):
        result=flow.opened(self.baseline,"1.1.1.1")
        self.assertEqual(len(result["rules"]["ipRules"]),2)
        self.assertEqual(self.baseline["rules"]["defaultAction"],"Deny")
    def test_late_firewall_response_rejected(self):
        class API:
            def comments(self,issue): return []
        j={"inputs_sha256":digest(canonical(self.values)),"phrase":"synthetic","started":"2026-11-23T12:00:00Z"}
        with patch.object(flow,"journal_for_run",return_value=j),patch.object(flow,"GitHubReadAdapter",return_value=API()),             patch.object(flow.time,"monotonic",side_effect=[0,1,601]),patch.object(flow,"account") as account:
            with self.assertRaises(ContractError): flow.wait_open()
            account.assert_not_called()
    def test_opening_confirmed_only_after_exact_arm_check(self):
        j={"inputs_sha256":digest(canonical(self.values)),"phrase":"synthetic","started":"2026-11-23T12:00:00Z",
           "baseline":self.baseline,"ip":"1.1.1.1"}
        class API:
            def comments(self,issue):
                return [{"body":"synthetic","user":{"id":69647965,"login":"lromerob","type":"User"},
                         "author_association":"OWNER","issue_url":"https://api.github.com/repos/lromerob/wordle/issues/6",
                         "created_at":"2026-11-23T12:01:00Z","updated_at":"2026-11-23T12:01:00Z"}]
        with patch.object(flow,"journal_for_run",return_value=j),patch.object(flow,"GitHubReadAdapter",return_value=API()),             patch.object(flow.time,"monotonic",side_effect=[0,1,2]),patch.object(flow,"account",return_value={}),             patch.object(flow,"boundary",return_value=flow.opened(self.baseline,"1.1.1.1")),             patch.object(flow,"outward_ip",return_value="1.1.1.1"),patch.object(flow,"workdir",return_value=self.work):
            flow.wait_open()
        self.assertTrue(decode((self.work/"firewall.json").read_bytes())["opening_verified"])

    def test_finish_requires_exact_baseline(self):
        j={"baseline":self.baseline,"ip":"1.1.1.1"}
        (self.work/"firewall.json").write_bytes(b"{}")
        with patch.object(flow,"workdir",return_value=self.work),patch.object(flow,"journal_for_run",return_value=j),             patch.object(flow,"account",return_value={}),patch.object(flow,"boundary",return_value=flow.opened(self.baseline,"1.1.1.1")),             patch.object(flow,"summary"),patch.object(flow.time,"monotonic",side_effect=[0,1,601]),patch.object(flow.time,"sleep"):
            with self.assertRaises(ValueError): flow.finish()
    def test_state_fingerprint_requires_real_lineage(self):
        with self.assertRaises((ContractError,KeyError)): flow.state_fingerprint(b"{}")

    def planned_execution(self, changed_state=False, public_container=False):
        tfwork=self.work/"terraform"
        (self.work/"values.json").write_bytes(canonical(self.values))
        (self.work/"backend.json").write_bytes(canonical(flow.BACKEND))
        flow.ops.prepare(tfwork,self.work/"values.json",self.work/"backend.json")
        commands=[]; state_calls=[]; store=MemoryPublisher()
        raw_state=canonical({"lineage":"11111111-1111-4111-8111-111111111111","serial":1})
        def command(args, cwd=None):
            commands.append(args)
            self.assertEqual(args[0],"terraform")
            self.assertNotIn("apply",args);self.assertNotIn("destroy",args);self.assertNotIn("-lock=false",args)
            if args[1:]==["version","-json"]: return b'{"terraform_version":"1.9.8"}'
            if args[1:]==["workspace","show"]: return b"default"
            if args[1:]==["state","pull"]:
                state_calls.append(True)
                return raw_state if len(state_calls)==1 or not changed_state else raw_state+b" "
            if args[1]=="plan": (tfwork/"approved.tfplan").write_bytes(PLAN)
            if args[1:]==["show","-json","approved.tfplan"]: return b'{"resource_changes":[]}'
            if args[1:]==["show","-no-color","approved.tfplan"]: return b"synthetic private review"
            return b""
        def az(*args):
            if args[:3]==("storage","container","show"):
                return {"properties":{"publicAccess":"blob" if public_container else None}}
            return {"accessToken":"synthetic-token"}
        j={"opening_verified":True,"baseline":self.baseline,"ip":"1.1.1.1", "inputs_sha256":digest(canonical(self.values))}
        with patch.object(flow,"workdir",return_value=self.work),patch.object(flow,"journal_for_run",return_value=j),             patch.object(flow,"account",return_value={}),patch.object(flow,"boundary",return_value=flow.opened(self.baseline,"1.1.1.1")),             patch.object(flow,"outward_ip",return_value="1.1.1.1"),patch.object(flow.ops,"run",side_effect=command),             patch.object(flow.ops,"az",side_effect=az),patch.object(flow,"PlanBlobStore",return_value=store),patch.object(flow,"summary"):
            flow.execute_plan()
        return commands,store

    def test_mocked_plan_sequence_existing_backend_and_no_apply(self):
        commands,store=self.planned_execution()
        init=next(c for c in commands if c[1]=="init")
        self.assertIn("-lockfile=readonly",init);self.assertIn("-backend-config=backend.hcl",init)
        plan=next(c for c in commands if c[1]=="plan")
        self.assertIn("-out=approved.tfplan",plan);self.assertIn("-lock-timeout=60s",plan)
        self.assertEqual(store.order[-1],"complete.json")
        manifest=decode(store.objects["manifest.json"])
        self.assertEqual(manifest["terraform"]["backend"]["key"],flow.BACKEND["key"])
        self.assertEqual(manifest["producer"]["workflow"],flow.WORKFLOW)

    def test_mocked_state_changed_rejected(self):
        with self.assertRaises(ContractError): self.planned_execution(changed_state=True)

    def test_mocked_public_container_rejected(self):
        with self.assertRaises(ContractError): self.planned_execution(public_container=True)

    def test_workflow_static_limits(self):
        value=yaml.load((Path(__file__).parents[1]/".github/workflows/azure-plan.yml").read_text(),Loader=yaml.BaseLoader)
        self.assertEqual(set(value["on"]),{"workflow_dispatch"})
        job=value["jobs"]["plan"]
        self.assertEqual(job["runs-on"],"ubuntu-24.04")
        self.assertEqual(job["environment"],"wordle-azure-demo")
        self.assertEqual(job["permissions"],{"contents":"read","actions":"read","issues":"read","deployments":"read","id-token":"write"})
        self.assertEqual(value["concurrency"]["group"],"wordle-storage-firewall-supervised")
        commands=[s.get("run","") for s in job["steps"]]
        self.assertFalse(any("terraform apply" in x or "terraform destroy" in x or "network-rule add" in x for x in commands))
        self.assertFalse(any("upload-artifact" in s.get("uses","") for s in job["steps"]))

    def test_new_producer_accepted_by_existing_verifier(self):
        f=fixtures.TrustTests();f.setUp();self.addCleanup(f.doCleanups)
        m=deepcopy(f.manifest);m["plan_id"]="66666666-6666-4666-8666-666666666666";m["producer"]["workflow"]=flow.WORKFLOW
        snapshot=PlanContract(f.store).publish(m,PLAN)
        policy=replace(f.policy,producer_workflow_id=405)
        f.api.runs["100"]["workflow_id"]=405;f.api.runs["100"]["path"]=flow.WORKFLOW
        f.api.issue_comments[0]["body"]=confirmation(snapshot,policy,f.challenge)
        service=PlanContract(f.store,GitHubTrustVerifier(f.api,snapshot,f.expected,policy,f.challenge,lambda:NOW))
        self.assertEqual(service.approve(m["plan_id"],f.expected,f.reference,"200","1",NOW).state,"APPROVED")


if __name__=="__main__": unittest.main(verbosity=2)
