"""Focused adapters/guards, real promotion controller, no Azure/Kubernetes/network."""
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch, MagicMock

import aks_run as runner
import azure_dispatch as dispatch
import ghcr_check
import azure_preflight


class ClusterDouble:
    prefix=["kubectl","--kubeconfig","not-used","--context","aks-double"]
    def __init__(self):
        self.active="blue";self.green=0;self.fault=False;self.pvc="same-pvc";self.operations=[]
    def snapshot(self):return "same-database"
    def sql(self, query):return "unused"
    def kube(self,*args,data=None):
        self.operations.append(args)
        action=args[0]
        if action=="scale":self.green=1;return b""
        if action=="patch":
            body=json.loads(args[-1])
            if args[1]=="service":
                self.active=body[-1]["value"]
            else:self.fault="fault" in body[0]["value"]
            return b""
        if args[1]=="service/frontend" or args[1:3]==("service","frontend"):
            return json.dumps({"spec":{"selector":{"wordle.slot":self.active}}}).encode()
        if args[1]=="configmaps":return json.dumps({"items":[{"metadata":{"name":"wordle-nginx-blue-fault-hash"}}]}).encode()
        if args[1]=="pvc":return json.dumps({"items":[{"metadata":{"uid":self.pvc}}]}).encode()
        if args[1]=="deployment/frontend-blue":
            return json.dumps({"spec":{"template":{"spec":{"volumes":[{"configMap":{"name":"wordle-nginx-blue-normal"}}]}}}}).encode()
        if args[1]=="deployment":
            return json.dumps({"metadata":{"generation":1},"spec":{"replicas":1,"template":{"spec":{"containers":[{"image":"pinned-double"}]}}},
                               "status":{"updatedReplicas":1,"availableReplicas":1}}).encode()
        if action=="exec":return b"PVC filesystem only"
        raise AssertionError("Unexpected double operation")


class ScenarioDouble(runner.Session):
    def __init__(self, cluster):
        self.cluster=cluster;self.events=[];self.telemetry=None;self.evidence=Path("unused")
    def verify(self):self.public_port=1;self.pvc_uid="same-pvc";return "11111111-1111-4111-8111-111111111111"
    def forward(self,name,port=8080,namespace="wordle-demo"):
        if name=="frontend-green" and self.cluster.green==0:
            raise AssertionError("Must scale Green before forwarding")
        return {"frontend-blue":2,"frontend-green":3,"collector":4}[name]
    def record(self,event,**fields):self.events.append({"event":event,**fields})
    def wait(self):self.pvc_uid=self.cluster.pvc
    def verify_images(self):pass
    def fetch(self,port,path,**kwargs):
        release=self.cluster.active if port==1 else ("blue" if port==2 else "green")
        code=503 if self.cluster.fault and release=="blue" and "/game/" in path else 200
        body={"status":"ok"} if path=="/api/health" else {"partida":{"estado":"ganada"}}
        return code,release,body


class AdapterTests(unittest.TestCase):
    def test_optional_captures_follow_authorized_phases_without_changing_controller(self):
        cluster=ClusterDouble(); captured=[]
        def validate_double(*args,**kwargs):
            kwargs["capture"]("signals",trace_id="a"*32)
            return {"database_unchanged":True}
        self.run_scenario(cluster, validate_side=validate_double, capture_hook=lambda stage,**fields: captured.append(stage))
        self.assertEqual(captured,["stable-blue","promoted-green","rollback-green","signals"])
        self.assertEqual(cluster.active,"green")

    def test_explicit_confirmation_and_costs_required(self):
        values={"resource_group_name":"rg-wordle","cluster_name":"aks-wordle"}
        with self.assertRaises(ValueError):runner.authorize("deploy",values,"DEPLOY rg-other/aks-wordle",True)
        with self.assertRaises(ValueError):runner.authorize("deploy",values,"DEPLOY rg-wordle/aks-wordle",False)
        runner.authorize("deploy",values,"DEPLOY rg-wordle/aks-wordle",True)

    def test_offline_preflight_never_queries_azure(self):
        with patch.object(azure_preflight,"query") as query:
            result=azure_preflight.assess(offline=True)
            self.assertTrue(result["local"]["immutable_images"]);query.assert_not_called()

    def test_registry_rejects_unpinned_or_foreign_before_network(self):
        with patch.object(ghcr_check.urllib.request,"urlopen") as request:
            for ref in ("ghcr.io/lromerob/wordle-backend:latest","ghcr.io/other/repository@sha256:"+"a"*64):
                with self.assertRaises(ValueError):ghcr_check.inspect(ref)
            request.assert_not_called()

    def registry_fixture(self, corrupt=False):
        config=json.dumps({"os":"linux","architecture":"amd64","config":{"Labels":{"org.opencontainers.image.revision":"a"*40}}}).encode()
        cd="sha256:"+hashlib.sha256(config).hexdigest()
        manifest=json.dumps({"config":{"digest":cd}}).encode();md="sha256:"+hashlib.sha256(manifest).hexdigest()
        def opened(request,**kwargs):
            url=request if isinstance(request,str) else request.full_url
            if "/token?" in url:return io.BytesIO(b'{"token":"synthetic-anonymous-double"}')
            if "/blobs/" in url:return io.BytesIO(config)
            return io.BytesIO(manifest+b"tamper" if corrupt else manifest)
        return "ghcr.io/lromerob/wordle-backend@"+md,opened,cd

    def test_registry_content_and_config_hashes_verified(self):
        ref,opened,cd=self.registry_fixture()
        with patch.object(ghcr_check.urllib.request,"urlopen",side_effect=opened):info=ghcr_check.inspect(ref)
        self.assertIn(cd,info["runtime_digests"]);self.assertEqual(info["revision"],"a"*40)

    def test_registry_corruption_rejected(self):
        ref,opened,_=self.registry_fixture(corrupt=True)
        with patch.object(ghcr_check.urllib.request,"urlopen",side_effect=opened):
            with self.assertRaises(ValueError):ghcr_check.inspect(ref)

    def test_shared_otlp_event_wire_format(self):
        response=MagicMock();opener=MagicMock();opener.open.return_value=response
        with patch.object(runner.ship_event.__globals__["urllib"].request,"build_opener",return_value=opener):
            runner.ship_event(1234,{"event":"automatic_rollback_verified"})
        packet=json.loads(opener.open.call_args.args[0].data)
        self.assertEqual(packet["resourceLogs"][0]["resource"]["attributes"][0]["value"]["stringValue"],"wordle-deploy")
        self.assertIn("automatic_rollback_verified",json.dumps(packet))

    def run_scenario(self, cluster, validate_side=None, capture_hook=None):
        session=ScenarioDouble(cluster)
        if capture_hook: session.capture_hook=capture_hook
        def cmd(args,**kwargs):
            args=list(map(str,args))
            # Controller commands include the fixed prefix and namespace.
            if "rollout" in args:return SimpleNamespace(stdout=b"")
            start=len(cluster.prefix)+2
            return SimpleNamespace(stdout=cluster.kube(*args[start:]))
        with patch.dict(runner.os.environ,{"WORDLE_GRAFANA_DEMO_PASSWORD":"synthetic-"*4}),patch.object(runner,"command",side_effect=cmd),patch.object(runner,"validate",side_effect=validate_side,return_value={"database_unchanged":True}) as validate:
            session.exercise()
        return session,validate

    def test_real_controller_promotion_post_switch_failure_and_rollback(self):
        cluster=ClusterDouble();session,validate=self.run_scenario(cluster)
        self.assertEqual(cluster.active,"green");self.assertFalse(cluster.fault)
        self.assertEqual([e["event"] for e in session.events].count("automatic_rollback_verified"),1)
        validate.assert_called_once();self.assertIn("disk_reader",validate.call_args.kwargs)

    def test_wrong_initial_color_stops_before_mutation(self):
        cluster=ClusterDouble();cluster.active="green"
        with self.assertRaises(ValueError):self.run_scenario(cluster)
        self.assertFalse(any(a[0] in ("scale","patch") for a in cluster.operations))

    def test_changed_pvc_is_not_masked_by_wait(self):
        cluster=ClusterDouble();cluster.pvc="different-pvc"
        with self.assertRaises(AssertionError):self.run_scenario(cluster)

    def test_runtime_image_digest_mismatch_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            cluster=MagicMock();cluster.call.return_value=json.dumps({"items":[{"metadata":{},"status":{"containerStatuses":[{"name":"backend","ready":True,"imageID":"sha256:"+"f"*64}]},
                "spec":{"containers":[{"name":"backend","image":"unapproved-image:latest"}]}}]}).encode()
            session=runner.Session(cluster,Path(folder)/"evidence")
            with self.assertRaises(RuntimeError):session.verify_images()

    def test_dispatch_blocks_wrong_target_and_path_traversal(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder);(p/"variables.json").write_text(json.dumps({"resource_group_name":"rg-wordle","cluster_name":"aks-wordle"}))
            with self.assertRaises(ValueError):dispatch.commands("deploy",p,"123",{"confirm":"DEPLOY wrong"},"a"*40)
            with self.assertRaises(ValueError):dispatch.commands("backup",p,"123",{"confirm":"BACKUP rg-wordle/aks-wordle","backup":"../elsewhere"},"a"*40)
            args=dispatch.commands("deploy",p,"123",{"confirm":"DEPLOY rg-wordle/aks-wordle","costs":True},"a"*40)
            self.assertIn("--ack-costs",args[0])


if __name__=="__main__":unittest.main(verbosity=2)
