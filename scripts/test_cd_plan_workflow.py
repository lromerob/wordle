"""PLAN integration tests: synthetic inputs, mocked Azure/HTTP/Terraform, no network."""
from copy import deepcopy
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
import io
import json
import os
import socket
import subprocess
from types import SimpleNamespace
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

    def planned_execution(self, changed_state=False, public_container=False, representation_only=False):
        tfwork=self.work/"terraform"
        (self.work/"values.json").write_bytes(canonical(self.values))
        (self.work/"backend.json").write_bytes(canonical(flow.BACKEND))
        flow.ops.prepare(tfwork,self.work/"values.json",self.work/"backend.json")
        commands=[]; state_calls=[]; store=MemoryPublisher()
        raw_state=canonical({"version":4,"resources":[],"lineage":"11111111-1111-4111-8111-111111111111","serial":1})
        def command(args, cwd=None):
            commands.append(args)
            self.assertEqual(args[0],"terraform")
            self.assertNotIn("apply",args);self.assertNotIn("destroy",args);self.assertNotIn("-lock=false",args)
            if args[1:]==["version","-json"]: return b'{"terraform_version":"1.9.8"}'
            if args[1:]==["workspace","show"]: return b"default"
            if args[1:]==["state","pull"]:
                state_calls.append(True)
                if representation_only and len(state_calls)>1: return json.dumps(decode(raw_state),indent=2).encode()
                return raw_state if len(state_calls)==1 or not changed_state else canonical(dict(decode(raw_state),serial=2))
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

    def test_mocked_representation_change_preserves_manifest_contract(self):
        with patch("sys.stdout",new_callable=io.StringIO) as output:
            commands,store=self.planned_execution(representation_only=True)
        self.assertIn("REPRESENTATION_ONLY",output.getvalue())
        manifest=decode(store.objects["manifest.json"])
        self.assertEqual(set(manifest["terraform"]["state"]),{"lineage","serial","sha256"})
        self.assertEqual(manifest["plan"]["sha256"],digest(PLAN))

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


    def test_command_diagnostic_categories_and_no_raw_output(self):
        sensitive = b"Bearer synthetic-token password=synthetic-secret ?sig=synthetic-sas private_variables=synthetic-input 203.0.113.17"
        cases = [(b"AADSTS700213", "AUTHENTICATION_ERROR"),
                 (b"AuthorizationPermissionMismatch", "AUTHORIZATION_ERROR"),
                 (b"AuthorizationFailure", "AUTHORIZATION_ERROR"),
                 (b"Error acquiring the state lock", "BACKEND_LOCK_ERROR"),
                 (b"Failed to install provider", "PROVIDER_ERROR"),
                 (b"Missing required argument", "CONFIGURATION_ERROR"),
                 (b"Connection refused", "CONNECTIVITY_ERROR"),
                 (b"context deadline exceeded", "TIMEOUT"),
                 (b"unfamiliar failure", "UNKNOWN_ERROR")]
        for marker, category in cases:
            with self.subTest(category=category):
                output = io.StringIO()
                with patch.object(flow.ops.subprocess, "run", return_value=SimpleNamespace(returncode=17, stdout=sensitive, stderr=marker + b" " + sensitive)), patch("sys.stdout", output):
                    with self.assertRaises(flow.ops.CommandFailure) as caught:
                        with flow.diagnostic("BACKEND_INIT", "terraform"):
                            flow.ops.run(["terraform", "init", "private-argument"])
                self.assertEqual(caught.exception.exit_code, 17)
                self.assertEqual(caught.exception.category, category)
                text = output.getvalue()
                self.assertIn("[PLAN][BACKEND_INIT] FAIL component=terraform exit_code=17 category=" + category, text)
                self.assertNotIn(" PASS", text)
                for secret in ("synthetic-token", "synthetic-secret", "synthetic-sas", "synthetic-input", "203.0.113.17", "private-argument"):
                    self.assertNotIn(secret, text + str(caught.exception))

    def test_command_timeout_and_missing_tool_are_safe(self):
        for error, category in [(subprocess.TimeoutExpired(["private-token"], 2700, output=b"private-output"), "TIMEOUT"),
                                (OSError("private-password"), "TOOL_ERROR")]:
            with patch.object(flow.ops.subprocess, "run", side_effect=error):
                with self.assertRaises(flow.ops.CommandFailure) as caught:
                    flow.ops.run(["terraform", "version"])
            self.assertEqual(caught.exception.category, category)
            self.assertIsNone(caught.exception.exit_code)
            self.assertNotIn("private", str(caught.exception))

    def test_command_success_preserves_output_and_timeout(self):
        with patch.object(flow.ops.subprocess, "run", return_value=SimpleNamespace(returncode=0, stdout=b"private-json", stderr=b"")) as run:
            self.assertEqual(flow.ops.run(["terraform", "version"], cwd=self.work), b"private-json")
        self.assertEqual(run.call_args.kwargs["timeout"], 2700)
        self.assertTrue(run.call_args.kwargs["capture_output"])

    def test_unknown_exception_identifies_step_without_message(self):
        output = io.StringIO()
        with patch("sys.stdout", output):
            with self.assertRaises(RuntimeError):
                with flow.diagnostic("PRIVATE_CONTAINER", "azure-cli"):
                    raise RuntimeError("Bearer token password=sensitive ?sig=sensitive 203.0.113.17")
        self.assertIn("[PLAN][PRIVATE_CONTAINER] FAIL", output.getvalue())
        self.assertIn("category=UNKNOWN_ERROR", output.getvalue())
        self.assertNotIn("sensitive", output.getvalue())
        self.assertNotIn("203.0.113.17", output.getvalue())
        self.assertNotIn(" PASS", output.getvalue())

    def test_http_failure_diagnostic_without_url_headers_or_body(self):
        for status, expected in [(401, "AUTHENTICATION_ERROR"), (403, "AUTHORIZATION_ERROR"), (412, "PERSISTENCE_ERROR")]:
            output = io.StringIO()
            with patch("sys.stdout", output):
                with self.assertRaises(urllib.error.HTTPError):
                    with flow.diagnostic("BLOB_WRITE", "blob"):
                        raise urllib.error.HTTPError("https://private/?sig=synthetic-sas", status, "private-password", {}, None)
            self.assertIn("category=" + expected + " code=HTTP_" + str(status), output.getvalue())
            self.assertNotIn("synthetic-sas", output.getvalue())
            self.assertNotIn("private-password", output.getvalue())

    def test_integrity_failure_is_safe_and_not_success(self):
        output = io.StringIO()
        with patch("sys.stdout", output):
            with self.assertRaises(ContractError):
                with flow.diagnostic("STATE_AFTER", "terraform"):
                    raise ContractError("private state content")
        self.assertIn("category=INTEGRITY_ERROR", output.getvalue())
        self.assertNotIn("private state", output.getvalue())
        self.assertNotIn(" PASS", output.getvalue())

    def test_main_failure_stays_nonzero_and_finish_remains_separate(self):
        output, errors = io.StringIO(), io.StringIO()
        with patch.object(flow.sys, "argv", ["cd_plan_workflow.py", "plan"]), patch.object(flow, "execute_plan", side_effect=RuntimeError("private-password")), patch("sys.stdout", output), patch("sys.stderr", errors):
            self.assertEqual(flow.main(), 1)
        self.assertIn("[PLAN][EXECUTION] FAIL", output.getvalue())
        self.assertNotIn("private-password", output.getvalue() + errors.getvalue())
        value=yaml.load((Path(__file__).parents[1]/".github/workflows/azure-plan.yml").read_text(),Loader=yaml.BaseLoader)
        finish=next(step for step in value["jobs"]["plan"]["steps"] if step.get("run", "").endswith(" finish"))
        self.assertEqual(finish["if"], "${{ always() }}")

    def test_main_finish_success_remains_zero(self):
        with patch.object(flow.sys, "argv", ["cd_plan_workflow.py", "finish"]), patch.object(flow, "finish"), patch("sys.stdout", io.StringIO()):
            self.assertEqual(flow.main(), 0)


    def test_real_sequence_failure_reports_init_and_stops_before_generation(self):
        output = io.StringIO()
        # Intercept only the diagnostic context at init, preserving original exception semantics.
        original_diagnostic = flow.diagnostic
        from contextlib import contextmanager
        @contextmanager
        def injected(step, component):
            with original_diagnostic(step, component):
                if step == "BACKEND_INIT":
                    raise flow.ops.command_failure(["terraform"], 23, b"AuthorizationFailed private-secret")
                yield
        with patch.object(flow, "diagnostic", injected), patch("sys.stdout", output):
            with self.assertRaises(flow.ops.CommandFailure) as caught:
                self.planned_execution()
        self.assertEqual(caught.exception.exit_code, 23)
        self.assertIn("[PLAN][BACKEND_INIT] FAIL component=terraform exit_code=23", output.getvalue())
        self.assertNotIn("[PLAN][GENERATE] START", output.getvalue())
        self.assertNotIn("private-secret", output.getvalue())


    def test_diagnostic_operation_cannot_enter_plan(self):
        os.environ["PLAN_OPERATION"] = "diagnose-state"
        self.assertEqual(flow.config(), self.values)
        with patch.object(flow.ops, "run") as run, patch.object(flow, "publish") as publish:
            with self.assertRaises(ContractError): flow.execute_plan()
            run.assert_not_called(); publish.assert_not_called()
        os.environ["PLAN_OPERATION"] = "create"
        with patch.object(flow.ops, "run") as run:
            with self.assertRaises(ContractError): flow.diagnose_state()
            run.assert_not_called()

    def state_diagnostic_execution(self, direct_failure=False, blob_failure=False, wrong_identity=False, wrapper_failure=False, missing_blob=False, init_failure=False, invalid_state=False, changed_metadata=False):
        import base64
        os.environ["PLAN_OPERATION"] = "diagnose-state"
        work = self.work / "terraform"; work.mkdir()
        (work / ".terraform").mkdir(); (work / ".terraform.lock.hcl").write_bytes(b"synthetic-lock")
        (work / ".terraform/terraform.tfstate").write_bytes(canonical({"backend": {"type": "azurerm", "config": flow.BACKEND}}))
        raw = canonical({"version": 4, "lineage": "11111111-1111-4111-8111-111111111111", "serial": 1, "resources": []})
        props = {"contentLength": len(raw), "etag": '"0xABCD"', "lastModified": "2026-11-24T07:00:00+00:00", "lease": {"state": "available", "status": "unlocked"}}
        token = "header." + base64.urlsafe_b64encode(canonical({"appid": self.env["ARM_CLIENT_ID"], "oid": "synthetic-principal", "tid": self.values["tenant_id"]})).decode().rstrip("=") + ".synthetic"
        commands, wrapped, metadata_calls = [], [], []
        def az(*args):
            if args[:2] == ("account", "show"):
                return {"id": self.values["subscription_id"], "tenantId": self.values["tenant_id"], "state": "Enabled", "user": {"type": "servicePrincipal", "name": self.env["ARM_CLIENT_ID"]}}
            if args[:2] == ("identity", "show"):
                return {"clientId": self.env["DIAGNOSTIC_CLIENT_ID"] if wrong_identity else self.env["ARM_CLIENT_ID"], "principalId": "synthetic-principal", "tenantId": self.values["tenant_id"]}
            if args[:2] == ("account", "get-access-token"): return {"accessToken": token}
            if args[:3] == ("storage", "blob", "show"):
                self.assertIn("login", args)
                if missing_blob: raise RuntimeError("private missing blob")
                metadata_calls.append(True)
                current = dict(props, etag='"0xFFFF"') if changed_metadata and len(metadata_calls) > 1 else props
                return {"properties": current}
            raise AssertionError("Unexpected Azure operation")
        def direct(args, **kwargs):
            commands.append(args)
            self.assertEqual(kwargs["cwd"], work); self.assertEqual(kwargs["timeout"], 2700)
            self.assertTrue(kwargs["capture_output"])
            permitted = {"version", "init", "workspace", "state"}
            self.assertIn(args[1], permitted)
            if args[1] == "init":
                if init_failure: return SimpleNamespace(returncode=3, stdout=b"private-variables", stderr=b"failed to acquire token private-token")
                self.assertEqual(args[2:], ["-input=false", "-reconfigure", "-lockfile=readonly", "-backend-config=backend.hcl"])
            if args[1] == "state":
                self.assertEqual(args, ["terraform", "state", "pull"])
                if direct_failure: return SimpleNamespace(returncode=1, stdout=b"private-state", stderr=b"Error loading state: status code 403 AuthorizationPermissionMismatch Bearer secret-token ?sig=secret-sas")
                return SimpleNamespace(returncode=0, stdout=b"invalid-private-state" if invalid_state else raw, stderr=b"")
            return SimpleNamespace(returncode=0, stdout=b'{"terraform_version":"1.9.8"}' if args[1] == "version" else b"default", stderr=b"")
        def wrapper(args, **kwargs):
            wrapped.append(args); self.assertEqual(args, ["terraform", "state", "pull"]); self.assertEqual(kwargs["cwd"], work)
            if wrapper_failure: raise flow.ops.command_failure(args, 7, b"private-secret")
            return raw
        class Opener:
            def open(_, request, timeout):
                self.assertEqual(request.method, "GET"); self.assertEqual(request.get_header("If-match"), props["etag"])
                if blob_failure: raise urllib.error.HTTPError(request.full_url, 403, "secret-token", {}, None)
                return Response(raw, 200)
        # Response mock permits the ordinary urllib read() without leaking the body.
        class ReadResponse(Response):
            def read(self, size=-1): return self.raw if size == -1 else self.raw[:size]
        class SafeOpener(Opener):
            def open(_, request, timeout):
                response = super().open(request, timeout)
                return ReadResponse(response.raw, response.status)
        j = {"opening_verified": True, "baseline": self.baseline, "ip": "1.1.1.1", "inputs_sha256": digest(canonical(self.values))}
        output=io.StringIO(); failed=False
        with patch.object(flow, "workdir", return_value=self.work), patch.object(flow, "journal_for_run", return_value=j), patch.object(flow, "account", return_value={}), patch.object(flow, "boundary", return_value=flow.opened(self.baseline,"1.1.1.1")), patch.object(flow, "outward_ip", return_value="1.1.1.1"), patch.object(flow.ops,"az",side_effect=az), patch.object(flow.subprocess,"run",side_effect=direct), patch.object(flow.ops,"run",side_effect=wrapper), patch.object(flow.urllib.request,"build_opener",return_value=SafeOpener()), patch.object(flow,"publish") as publish, patch("sys.stdout",output):
            try: flow.diagnose_state()
            except ContractError: failed=True
            publish.assert_not_called()
        text=output.getvalue()
        for secret in (token, "secret-token", "secret-sas", "private-state", "private-secret", "synthetic-principal", self.values["tenant_id"]): self.assertNotIn(secret,text)
        return failed,commands,wrapped,text

    def test_diagnostic_complete_sequence_no_plan_or_publication(self):
        failed, commands, wrapped, text = self.state_diagnostic_execution()
        self.assertFalse(failed); self.assertEqual([a[1] for a in commands], ["version", "init", "workspace", "state"])
        self.assertEqual(len(wrapped),1); self.assertIn("DIAG_06_WRAPPER] PASS",text);self.assertIn("metadata unchanged",text)
        for phase in ("DIAG_01_IDENTITY", "DIAG_02_METADATA", "DIAG_03_BLOB_READ", "DIAG_04_INIT", "DIAG_05_DIRECT_PULL"):
            self.assertIn(phase+"] PASS",text)

    def test_diagnostic_direct_failure_skips_wrapper_and_keeps_metadata_check(self):
        failed, commands, wrapped, text = self.state_diagnostic_execution(direct_failure=True)
        self.assertTrue(failed);self.assertFalse(wrapped);self.assertIn('"http_status":["403"]',text)
        self.assertIn("REQUEST_AUTHORIZATION",text);self.assertIn("DIAG_METADATA_AFTER] PASS",text)

    def test_diagnostic_blob_read_failure_still_tests_independent_terraform(self):
        failed, commands, wrapped, text = self.state_diagnostic_execution(blob_failure=True)
        self.assertTrue(failed);self.assertTrue(wrapped);self.assertIn("DIAG_03_BLOB_READ] FAIL",text)
        self.assertIn("DIAG_05_DIRECT_PULL] PASS",text)

    def test_diagnostic_wrong_identity_stops_before_blob_or_terraform(self):
        failed, commands, wrapped, text = self.state_diagnostic_execution(wrong_identity=True)
        self.assertTrue(failed);self.assertFalse(commands);self.assertFalse(wrapped)

    def test_diagnostic_missing_blob_never_initializes_backend(self):
        failed, commands, wrapped, text = self.state_diagnostic_execution(missing_blob=True)
        self.assertTrue(failed);self.assertFalse(commands);self.assertFalse(wrapped)

    def test_diagnostic_wrapper_failure_is_distinct(self):
        failed, commands, wrapped, text = self.state_diagnostic_execution(wrapper_failure=True)
        self.assertTrue(failed);self.assertIn("DIAG_05_DIRECT_PULL] PASS",text);self.assertIn("DIAG_06_WRAPPER] FAIL",text)
        self.assertIn("exit_code=7",text)

    def test_state_error_details_unknown_still_has_restrictive_signals(self):
        raw=b"unknown backend credential token error password=secret-value ?sig=secret-sas 203.0.113.17 {resources: private-state}"
        result=flow.state_error_details(SimpleNamespace(returncode=19,stderr=raw))
        self.assertEqual(result["exit_code"],19);self.assertIn("backend",result["hints"]);self.assertTrue(result["details_withheld"])
        for value in ("secret-value","secret-sas","203.0.113.17","private-state"):self.assertNotIn(value,canonical(result).decode())

    def test_diagnostic_state_structure_resources_and_invalid(self):
        base={"version":4,"lineage":"11111111-1111-4111-8111-111111111111","serial":1,"resources":[]}
        self.assertEqual(flow.diagnostic_state_info(canonical(base))["managed_instances"],0)
        base["resources"]=[{"mode":"managed","instances":[{}]}]
        self.assertEqual(flow.diagnostic_state_info(canonical(base))["managed_instances"],1)
        for raw in (b"not-json",b"{}",canonical(dict(base,resources="private-state"))):
            with self.assertRaises((ContractError,KeyError)):flow.diagnostic_state_info(raw)

    def test_diagnostic_yaml_exclusive_routes_and_same_finish(self):
        w=yaml.load((Path(__file__).parents[1]/".github/workflows/azure-plan.yml").read_text(),Loader=yaml.BaseLoader)
        self.assertIn("diagnose-state",w["on"]["workflow_dispatch"]["inputs"]["operation"]["options"])
        steps=w["jobs"]["plan"]["steps"]
        diag=next(s for s in steps if s.get("run","").endswith(" diagnose-state"));plan=next(s for s in steps if s.get("run","").endswith(" plan"))
        self.assertEqual(diag["if"],"${{ inputs.operation == 'diagnose-state' }}")
        self.assertEqual(plan["if"],"${{ inputs.operation != 'diagnose-state' }}")
        self.assertEqual(next(s for s in steps if s.get("run","").endswith(" finish"))["if"],"${{ always() }}")


    def test_diagnostic_init_failure_skips_both_pulls_and_checks_preservation(self):
        failed, commands, wrapped, text = self.state_diagnostic_execution(init_failure=True)
        self.assertTrue(failed); self.assertFalse(wrapped)
        self.assertNotIn("state", [c[1] for c in commands])
        self.assertIn("TOKEN_ACQUISITION", text); self.assertIn("exit_code=3", text)
        self.assertIn("DIAG_METADATA_AFTER] PASS", text)

    def test_diagnostic_invalid_direct_state_never_calls_wrapper(self):
        failed, commands, wrapped, text = self.state_diagnostic_execution(invalid_state=True)
        self.assertTrue(failed); self.assertFalse(wrapped)
        self.assertIn("DIAG_05_DIRECT_PULL] FAIL", text)
        self.assertNotIn("invalid-private-state", text)

    def test_diagnostic_metadata_change_cannot_report_success(self):
        failed, commands, wrapped, text = self.state_diagnostic_execution(changed_metadata=True)
        self.assertTrue(failed); self.assertNotIn("metadata unchanged", text)

    def test_state_error_details_known_backend_and_empty_state_are_distinct(self):
        for raw, signature in [(b"No state file was found", "NO_STATE"),
                               (b'unsupported checkable object kind "private"', "STATE_FORMAT"),
                               (b"Please run az login private-token", "CLI_CONTEXT"),
                               (b"failed to acquire OIDC token StatusCode=401", "TOKEN_ACQUISITION")]:
            details=flow.state_error_details(SimpleNamespace(returncode=1,stderr=raw))
            self.assertIn(signature, details["signatures"])
            self.assertNotIn("private", canonical(details).decode())



class StateIntegrityTests(unittest.TestCase):
    def state(self, **changes):
        value = {"version": 4, "lineage": "11111111-1111-4111-8111-111111111111",
                 "serial": 1, "resources": [], "outputs": {}, "unknown": {"private": [1, 2]}}
        value.update(changes)
        return value

    def compare(self, left, right):
        flow.compare_state(flow.state_fingerprint(left), flow.state_fingerprint(right))

    def test_identical(self):
        raw = canonical(self.state()); self.compare(raw, raw)

    def test_whitespace_and_object_order(self):
        raw = canonical(self.state()); other = json.dumps(self.state(), indent=3).encode()
        with patch("sys.stdout", new_callable=io.StringIO) as output: self.compare(raw, other)
        self.assertIn("REPRESENTATION_ONLY", output.getvalue())
        self.assertNotIn("private", output.getvalue())
        self.assertNotEqual(flow.state_fingerprint(raw)["sha256"], flow.state_fingerprint(other)["sha256"])

    def test_lineage_serial_and_content_categories(self):
        for changes, code in [({"lineage":"22222222-2222-4222-8222-222222222222"},"STATE_LINEAGE_CHANGED"),
                              ({"serial":2},"STATE_SERIAL_CHANGED"),
                              ({"unknown":{"private":[1,3]}},"STATE_CONTENT_CHANGED")]:
            with self.subTest(code=code), self.assertRaises(flow.StateIntegrityError) as caught:
                self.compare(canonical(self.state()), canonical(self.state(**changes)))
            self.assertEqual(caught.exception.code, code)

    def test_types_array_order_added_removed_and_unknown_fields(self):
        before = self.state()
        variants = [self.state(unknown={"private":[True,2]}), self.state(unknown={"private":[2,1]}),
                    self.state(extra="sensitive"), self.state(outputs={"sensitive":{"value":"changed"}}),
                    self.state(resources=[{"mode":"managed","instances":[]}]), self.state(check_results=[])]
        removed = self.state(); del removed["unknown"]; variants.append(removed)
        for value in variants:
            with self.subTest(value=list(value)), self.assertRaises(flow.StateIntegrityError):
                self.compare(canonical(before),canonical(value))

    def test_duplicate_invalid_ambiguous_and_invalid_structure(self):
        for raw in [b'{', b'{"version":4,"version":4}', b'[]', b'{}',
                    canonical(self.state(serial=True)), canonical(self.state(resources={})),
                    canonical(self.state(lineage="invalid")), canonical(self.state(version=3)),
                    canonical(self.state())[:-1]+b',"x":NaN}',
                    canonical(self.state())[:-1]+b',"x":Infinity}',
                    canonical(self.state())[:-1]+b',"x":"\\ud800"}',
                    canonical(self.state())[:-1]+b',"x":{"duplicate":1,"duplicate":2}}']:
            with self.subTest(raw=raw[:10]), self.assertRaises(flow.StateIntegrityError) as caught:
                flow.state_fingerprint(raw)
            self.assertEqual(caught.exception.code,"STATE_STRUCTURE_INVALID")

    def test_exact_numbers_no_float_rounding(self):
        prefix=canonical(self.state())[:-1]+b',"precise":'
        self.compare(prefix+b'1.2300}',prefix+b'123e-2}')
        for a,b in [(b'9007199254740992',b'9007199254740993'),
                    (b'0.123456789012345678901',b'0.123456789012345678902'),
                    (b'1e10000',b'1e10001'),(b'1',b'1.0'),(b'1',b'true')]:
            with self.subTest(a=a), self.assertRaises(flow.StateIntegrityError):self.compare(prefix+a+b'}',prefix+b+b'}')

    def test_safe_failure_diagnostics(self):
        output=io.StringIO()
        for raw in [b'{"secret-token":',canonical(self.state(serial=-1))]:
            with patch("sys.stdout",output):
                try: flow.state_fingerprint(raw)
                except flow.StateIntegrityError as error: flow.diagnostic_failure("STATE_AFTER","terraform",error)
        self.assertIn("STATE_STRUCTURE_INVALID",output.getvalue());self.assertNotIn("secret-token",output.getvalue())
        self.assertNotIn("11111111",output.getvalue())

if __name__=="__main__": unittest.main(verbosity=2)
