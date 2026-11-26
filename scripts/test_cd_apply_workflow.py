"""Synthetic distributed CAS/consumer tests. No Azure, Terraform or real plan."""
from copy import deepcopy
from pathlib import Path
import io
import os
import socket
import tempfile
import threading
import unittest
from unittest.mock import patch

import yaml
import cd_apply_workflow as app
from cd_plan_contract import PlanContract, ContractError, canonical, decode, digest, build_manifest
from test_cd_plan_contract import context, FixtureAuthority, authorize, NOW, PLAN


class BlobFixture:
    def __init__(self): self.objects={};self.serial=0;self.lock=threading.Lock()
    def __call__(self, method, name, data=None, headers=None):
        with self.lock:
            if method=="GET":
                if name not in self.objects: raise FileNotFoundError()
                raw,etag=self.objects[name]
                if headers and headers.get("If-Match")!=etag:raise ContractError("Condition rejected")
                return raw,etag
            self.assert_put(method,headers)
            current=self.objects.get(name)
            if headers.get("If-None-Match")=="*" and current:raise ContractError("Concurrent create")
            if "If-Match" in headers and (not current or headers["If-Match"]!=current[1]):raise ContractError("Concurrent update")
            self.serial+=1;etag='"'+str(self.serial)+'"';self.objects[name]=(data,etag);return b"",etag
    def assert_put(self, method,headers):
        assert method=="PUT" and headers and ("If-Match" in headers or headers.get("If-None-Match")=="*")
    def seed(self,name,data):
        self(name and "PUT",name,data,{"If-None-Match":"*"});return self.objects[name][1]


class ApplyTests(unittest.TestCase):
    def setUp(self):
        self.guard=patch.object(socket.socket,"connect",side_effect=AssertionError("Network forbidden"));self.guard.start();self.addCleanup(self.guard.stop)
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.work=Path(self.tmp.name)
        self.expected=context();self.expected["environment"]="wordle-azure-demo"
        self.m=build_manifest(PLAN,self.expected,{"workflow":".github/workflows/azure-plan.yml","run_id":"100","attempt":"1"},"2026-11-23T12:00:00Z","2026-11-23T13:00:00Z")
        self.http=BlobFixture();self.store=app.BlobStore("synthetic-token",self.m["plan_id"],digest(canonical(self.m)),"f"*64,self.http)
        prefix="plans/"+self.m["plan_id"]+"/";objects={"manifest.json":canonical(self.m),"approved.tfplan":PLAN,"challenge.json":canonical({"plan_id":self.m["plan_id"],"manifest_sha256":self.store.manifest_sha,"plan_sha256":digest(PLAN),"purpose":"PLAN_REVIEW_ONLY_NOT_APPLY_AUTHORIZATION"})};receipts={}
        for name,raw in objects.items():
            etag=self.http.seed(prefix+name,raw);receipts[name]={"etag":etag,"size":len(raw),"sha256":digest(raw)}
        self.http.seed(prefix+"complete.json",canonical({"plan_id":self.m["plan_id"],"state":"PENDING_APPROVAL","objects":receipts}))
        self.store.coordinate({"apply_run":"200","nonce":"f"*32});self.authority=FixtureAuthority();self.contract=PlanContract(self.store,self.authority);authorize(self.contract,self.authority,self.store.get(self.store.plan_id))
        self.env=patch.dict(os.environ,{"GITHUB_RUN_ID":"200"});self.env.start();self.addCleanup(self.env.stop)

    def consume(self, execute=None, expected=None, clock=lambda:NOW):
        with patch.object(app.ops,"fingerprint",return_value=self.expected["terraform"]["configuration_sha256"]),patch.object(app.ops,"inventory",return_value=["synthetic-private-resource"]),patch.object(app,"summary"):
            return app.consume(self.contract,self.store,expected or self.expected,"fixture-review-1",self.work,execute or (lambda *a:None),clock)

    def test_saved_binary_only_success(self):
        calls=[]
        def execute(args,work,remaining):
            calls.append(args);self.assertEqual((work/"approved.tfplan").read_bytes(),PLAN);self.assertGreater(remaining,0)
            self.assertTrue(decode(self.store.get(self.store.plan_id).metadata_raw)["apply_started"])
        self.consume(execute);self.assertEqual(calls,[["terraform","apply","-input=false","-lock-timeout=60s","approved.tfplan"]]);self.assertEqual(self.store.get(self.store.plan_id).state,"CONSUMED")
        with self.assertRaises(ContractError):self.consume()

    def test_real_inventory_after_apply_reaches_consumed(self):
        targets=self.expected["targets"];commands=[];executions=[]
        def az(*args):
            commands.append(args)
            self.assertEqual(args[:2],("resource","list"))
            self.assertEqual(args[4:],("--subscription",targets["subscription_id"]))
            self.assertIn(args[3],(targets["resource_group"],targets["node_resource_group"]))
            return [{"id":"SYNTHETIC/"+args[3]}]
        with patch.object(app.ops,"fingerprint",return_value=self.expected["terraform"]["configuration_sha256"]),patch.object(app.ops,"az",side_effect=az),patch.object(app,"summary"):
            app.consume(self.contract,self.store,self.expected,"fixture-review-1",self.work,
                        lambda *args:executions.append(args),lambda:NOW)
        self.assertEqual(len(executions),1)
        self.assertEqual([args[3] for args in commands],[targets["resource_group"],targets["node_resource_group"]])
        snapshot=self.store.get(self.store.plan_id)
        self.assertEqual(snapshot.state,"CONSUMED")
        self.assertEqual(decode(snapshot.metadata_raw)["resource_count"],2)
        raw,_=self.http("GET","coordination/backends/"+self.store.backend_key+".json")
        self.assertEqual(decode(raw)["state"],"CONSUMED")
        raw,_=self.http("GET","coordination/inventories/"+self.store.plan_id+".json")
        self.assertEqual(decode(raw)["resources"],sorted(["synthetic/"+targets["resource_group"],"synthetic/"+targets["node_resource_group"]]))

    def test_real_inventory_failure_keeps_uncertain_consumption(self):
        executions=[]
        with patch.object(app.ops,"fingerprint",return_value=self.expected["terraform"]["configuration_sha256"]),patch.object(app.ops,"az",side_effect=RuntimeError("private-inventory-error")) as az,patch.object(app,"summary"),self.assertRaises(RuntimeError):
            app.consume(self.contract,self.store,self.expected,"fixture-review-1",self.work,
                        lambda *args:executions.append(args),lambda:NOW)
        self.assertEqual(len(executions),1);az.assert_called_once()
        self.assertEqual(self.store.get(self.store.plan_id).state,"OUTCOME_UNKNOWN")
        raw,_=self.http("GET","coordination/backends/"+self.store.backend_key+".json")
        self.assertEqual(decode(raw)["state"],"CONSUMING")
        with self.assertRaises(ContractError):self.consume()

    def test_expired_rejected_before_execution(self):
        with self.assertRaises(ContractError):self.consume(clock=lambda:NOW.replace(hour=14))
        self.assertFalse((self.work/"approved.tfplan").exists())

    def test_wrong_context_rejected(self):
        for key in ["commit_sha","operation"]:
            expected=deepcopy(self.expected);expected[key]="b"*40 if key=="commit_sha" else "update"
            with self.subTest(key=key),self.assertRaises(ContractError):self.consume(expected=expected)

    def test_missing_approval_rejected(self):
        self.authority.approvals.clear()
        with self.assertRaises(ContractError):self.consume()
        self.assertEqual(self.store.get(self.store.plan_id).state,"PENDING_APPROVAL")

    def test_binary_hash_mismatch_rejected(self):
        self.store.loaded=None;name="plans/"+self.store.plan_id+"/approved.tfplan";_,etag=self.http.objects[name];self.http.objects[name]=(b"tampered-secret",etag)
        with self.assertRaises(ContractError):self.store.bundle()

    def test_concurrent_claim_only_one_wins(self):
        snap=self.contract.approve(self.store.plan_id,self.expected,"fixture-review-1","200","1",NOW)
        barrier=threading.Barrier(2);results=[]
        def worker():
            barrier.wait()
            try:self.contract.begin(self.store.plan_id,self.expected,"200","1",NOW);results.append("win")
            except ContractError:results.append("lose")
        threads=[threading.Thread(target=worker) for _ in range(2)]
        for thread in threads:thread.start()
        for thread in threads:thread.join()
        self.assertEqual(sorted(results),["lose","win"])

    def test_failure_and_timeout_block_replay_and_backend(self):
        def fail(*args):raise TimeoutError("sensitive-private")
        output=io.StringIO()
        with patch("sys.stdout",output),self.assertRaises(TimeoutError):self.consume(fail)
        self.assertEqual(self.store.get(self.store.plan_id).state,"OUTCOME_UNKNOWN")
        raw,_=self.http("GET","coordination/backends/"+self.store.backend_key+".json");self.assertEqual(decode(raw)["state"],"CONSUMING")
        with self.assertRaises(ContractError):self.consume()
        self.assertNotIn("sensitive-private",output.getvalue())

    def test_lost_coordination_write_cannot_execute(self):
        original=self.store.request
        def request(method,name,data=None,headers=None):
            if method=="PUT" and name==self.store.path() and decode(data)["state"]=="CONSUMING":
                original(method,name,data,headers);raise TimeoutError("uncertain")
            return original(method,name,data,headers)
        self.store.request=request;calls=[]
        with self.assertRaises(TimeoutError):self.consume(lambda *args:calls.append(args))
        self.assertFalse(calls);self.assertEqual(self.store.get(self.store.plan_id).state,"CONSUMING")

    def test_nonce_cannot_be_replaced(self):
        with self.assertRaises(ContractError):self.store.coordinate({"apply_run":"201","nonce":"e"*32})

    def test_invalid_approval_binding_rejected(self):
        self.authority.approvals["fixture-review-1"]["binding"]["apply_run_id"]="201"
        with self.assertRaises(ContractError):self.consume()
        self.assertEqual(self.store.get(self.store.plan_id).state,"PENDING_APPROVAL")

    def test_revoked_after_claim_stops_before_execution(self):
        original=self.contract._verify_trust;count=[]
        def trust(*args):
            count.append(1)
            if len(count)==3:raise ContractError("revoked")
            return original(*args)
        calls=[]
        with patch.object(self.contract,"_verify_trust",side_effect=trust),self.assertRaises(ContractError):
            self.consume(lambda *args:calls.append(args))
        self.assertFalse(calls);self.assertEqual(self.store.get(self.store.plan_id).state,"OUTCOME_UNKNOWN")

    def test_changed_local_workspace_stops_before_execution(self):
        calls=[]
        with patch.object(app.ops,"fingerprint",return_value="wrong"),patch.object(app,"summary"),self.assertRaises(ContractError):
            app.consume(self.contract,self.store,self.expected,"fixture-review-1",self.work,lambda *args:calls.append(args),lambda:NOW)
        self.assertFalse(calls)

    def test_cli_failure_is_sanitized_and_finish_available(self):
        output=io.StringIO()
        with patch.object(app,"apply",side_effect=RuntimeError("sensitive-secret")),patch("sys.argv",["apply","apply"]),patch("sys.stderr",output):
            self.assertEqual(app.main(),1)
        self.assertNotIn("sensitive-secret",output.getvalue())
        with patch.object(app.flow,"finish") as finish,patch("sys.argv",["apply","finish"]):
            self.assertEqual(app.main(),0);finish.assert_called_once()

    def test_configuration_disabled(self):
        with patch.dict(os.environ,{"WORDLE_APPLY_ENABLED":"false"}),self.assertRaises(ContractError):app.config()

    def test_configuration_plan_identity_rejected(self):
        from test_cd_plan_workflow import PlanTests
        fixture=PlanTests("test_valid_configuration");fixture.setUp()
        try:
            env=dict(fixture.env,WORDLE_APPLY_ENABLED="true",APPLY_COSTS_APPROVED="true",PLAN_ID=self.store.plan_id,
                     MANIFEST_SHA256=self.store.manifest_sha,APPLY_WORKFLOW_ID="404",APPLY_ENVIRONMENT_ID="303",
                     GITHUB_WORKFLOW_REF="lromerob/wordle/"+app.WORKFLOW+"@"+app.flow.BRANCH,
                     INFRA_CLIENT_ID=fixture.env["ARM_CLIENT_ID"],PLAN_CLIENT_ID=fixture.env["ARM_CLIENT_ID"])
            with patch.dict(os.environ,env,clear=True),self.assertRaises(ContractError):app.config()
            env["PLAN_CLIENT_ID"]="66666666-6666-4666-8666-666666666666"
            with patch.dict(os.environ,env,clear=True):self.assertEqual(app.config(),fixture.values)
        finally:fixture.doCleanups()

    def test_other_plan_cannot_enter_uncertain_backend(self):
        self.store.claim_backend("first-consumer")
        other=app.BlobStore("synthetic", "22222222-2222-4222-8222-222222222222", "a"*64,self.store.backend_key,self.http)
        with self.assertRaises(ContractError):other.claim_backend("other-consumer")

    def test_yaml_independent_gate_finish_and_single_job(self):
        value=yaml.load((Path(__file__).parents[1]/".github/workflows/azure-demo.yml").read_text(),Loader=yaml.BaseLoader)
        self.assertEqual(len(value["jobs"]),1);job=value["jobs"]["supervised"]
        self.assertIn("WORDLE_APPLY_ENABLED",job["if"]);steps=job["steps"]
        finish=next(s for s in steps if s.get("run","").endswith("cd_apply_workflow.py finish"));self.assertIn("always()",finish["if"])
        for s in steps:
            if s.get("run","").endswith("cd_apply_workflow.py apply"):self.assertIn("apply-reviewed",s["if"])

if __name__=="__main__":unittest.main(verbosity=2)
