"""Future supervised AKS deploy/acceptance/recovery. Never invoked implicitly.

Reuses the existing Blue-Green controller, observability validators and recovery
helpers. No cluster creation/deletion here; Terraform has its own plan approvals.
"""
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import json
import hashlib
import os
from pathlib import Path
import socket
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid

from azure_supervised import ROOT, authenticate, external
from aks_recovery import Cluster, WORKLOADS, bootstrap, recover
from ghcr_check import inspect as inspect_registry

sys.path.insert(0, str(ROOT / "k8s/blue-green"))
sys.path.insert(0, str(ROOT / "k8s/observability"))
from promotion import PromotionController
from validation import wait_stack, validate, ship_event


def authorize(action, values, confirmation, costs=False):
    target = values["resource_group_name"] + "/" + values["cluster_name"]
    if confirmation != action.upper() + " " + target:
        raise ValueError("Explicit operation and exact target confirmation required")
    if action in ("deploy", "restore-deploy") and not costs:
        raise ValueError("Explicit acknowledgement of PVC/infrastructure costs required")


def command(args, *, data=None, timeout=300):
    args=list(map(str,args));args[0]=shutil.which(args[0]) or args[0]
    r = subprocess.run(args, input=data, capture_output=True, timeout=timeout)
    if r.returncode:
        raise RuntimeError("Operation failed; raw diagnostics suppressed")
    return r


class Session:
    def __init__(self, cluster, evidence):
        self.cluster = cluster
        self.evidence = external(evidence)
        if self.evidence.exists() and any(self.evidence.iterdir()):
            raise ValueError("Evidence directory must be empty")
        self.evidence.mkdir(parents=True, exist_ok=True)
        self.started = time.monotonic()
        self.events = []
        self.forwards = []
        self.telemetry = None

    def record(self, event, **fields):
        item = {"event":event,"elapsed":round(time.monotonic()-self.started,3),
                "utc":datetime.now(timezone.utc).isoformat(),**fields}
        self.events.append(item)
        (self.evidence/"events.json").write_text(json.dumps(self.events,indent=2),encoding="utf-8")
        print(event, flush=True)  # No identifiers, payloads, passwords or raw errors.
        if self.telemetry:
            try:ship_event(self.telemetry,item)
            except Exception:pass  # The validator independently checks receipt in Loki.

    def forward(self, name, port=8080, namespace="wordle-demo"):
        with socket.socket() as sock:
            sock.bind(("127.0.0.1",0));local=sock.getsockname()[1]
        p = subprocess.Popen([*self.cluster.prefix,"-n",namespace,"port-forward","--address","127.0.0.1",
            "service/"+name,f"{local}:{port}"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        self.forwards.append(p)
        for _ in range(100):
            if p.poll() is not None:raise RuntimeError("Owned port-forward stopped")
            try:
                with socket.create_connection(("127.0.0.1",local),timeout=.2):return local
            except OSError:time.sleep(.1)
        raise RuntimeError("Loopback port-forward timeout")

    def fetch(self, port, path, *, method="GET", payload=None):
        request=urllib.request.Request(f"http://127.0.0.1:{port}"+path,method=method,
            data=json.dumps(payload).encode() if payload is not None else None,
            headers={"Host":"wordle.test","Content-Type":"application/json"})
        opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
        try:response=opener.open(request,timeout=5)
        except urllib.error.HTTPError as error:response=error
        with response:
            raw=response.read()
            body=json.loads(raw) if response.headers.get_content_type()=="application/json" else raw
            return response.status,response.headers.get("X-Wordle-Release"),body

    def wait(self):
        command([*self.cluster.prefix,"-n","wordle-demo","rollout","status","statefulset/postgres","--timeout=600s"],timeout=620)
        for name in (*WORKLOADS,"ingress"):
            d=json.loads(self.cluster.kube("get","deployment",name,"-o","json"))
            if d["spec"].get("replicas",1)>0:
                command([*self.cluster.prefix,"-n","wordle-demo","rollout","status","deployment/"+name,"--timeout=300s"],timeout=320)
        wait_stack(command,self.cluster.prefix)
        pvcs=json.loads(self.cluster.kube("get","pvc","-o","json"))["items"]
        if len(pvcs)!=1 or pvcs[0]["status"]["phase"]!="Bound" or pvcs[0]["spec"]["storageClassName"]!="managed-csi":
            raise RuntimeError("Expected one Bound Azure CSI PostgreSQL PVC")
        self.pvc_uid=pvcs[0]["metadata"]["uid"]
        for namespace in ("wordle-demo","wordle-observability"):
            services=json.loads(self.cluster.call("-n",namespace,"get","services","-o","json"))["items"]
            if any(s["spec"].get("type","ClusterIP")!="ClusterIP" for s in services):
                raise RuntimeError("Unexpected public Service exposure")

    def verify_images(self):
        lock=json.loads((ROOT/"k8s/aks-full/images.lock.json").read_text())
        allowed=set(lock["images"].values());registry={};records=[]
        for namespace in ("wordle-demo","wordle-observability"):
            pods=json.loads(self.cluster.call("-n",namespace,"get","pods","-o","json"))["items"]
            for pod in pods:
                if pod["metadata"].get("deletionTimestamp"):continue
                states={s["name"]:s for s in pod["status"].get("containerStatuses",[])}
                for c in pod["spec"]["containers"]:
                    ref=c["image"];state=states.get(c["name"],{})
                    if ref not in allowed or not state.get("ready") or not state.get("imageID"):
                        raise RuntimeError("Runtime container not ready or image not in immutable lock")
                    if ref.startswith("ghcr.io/lromerob/wordle-"):
                        if ref not in registry:registry[ref]=inspect_registry(ref)
                        info=registry[ref]
                        if info["revision"]!=lock["source_commit"] or not any(state["imageID"].endswith(d) for d in info["runtime_digests"]):
                            raise RuntimeError("Runtime image does not correspond to pinned source/manifest")
                    records.append({"namespace":namespace,"container":c["name"],"reference":ref,"image_id":state["imageID"]})
        if len(registry)!=2:raise RuntimeError("Both application images must be running")
        (self.evidence/"images.json").write_text(json.dumps({"source_commit":lock["source_commit"],"containers":records},indent=2))
        self.record("runtime_digests_verified")

    def verify(self):
        self.wait();self.verify_images()
        self.cluster.sql((ROOT/"supabase/tests/schema_contracts.sql").read_text(encoding="utf-8"))
        expected=json.loads(self.cluster.kube("get","service/frontend","-o","json"))["spec"]["selector"]["wordle.slot"]
        assert expected in ("blue","green")
        self.public_port=self.forward("ingress")
        code,release,html=self.fetch(self.public_port,"/");assert code==200 and release==expected and b'<div id="root">' in html
        assert self.fetch(self.public_port,"/api/health")== (200,expected,{"status":"ok"})
        code,_,game=self.fetch(self.public_port,"/api/game/nueva?usuario_id=fin0809-synthetic",method="POST");assert code==200
        game_id=str(uuid.UUID(game["partida_id"]));path="/api/game/"+game_id
        active=self.fetch(self.public_port,path);assert active[0]==200 and active[1]==expected and "palabra_secreta" not in active[2]["partida"]
        assert self.cluster.sql("SELECT count(*) FROM public.partidas WHERE id='"+game_id+"';")=="1"
        before=self.cluster.snapshot()
        payload={"partida_id":game_id,"usuario_id":"fin0809-synthetic","palabra":"ZZZZZ"}
        assert self.fetch(self.public_port,"/api/game/intento",method="POST",payload=payload)[0]==400
        assert before==self.cluster.snapshot()
        # Read the synthetic solution in memory only; never emit it in evidence/logs.
        payload["palabra"]=self.cluster.sql("SELECT palabra_secreta FROM public.partidas WHERE id='"+game_id+"';")
        answer=self.fetch(self.public_port,"/api/game/intento",method="POST",payload=payload)
        assert answer[0]==200 and answer[1]==expected and answer[2]["estado"]=="ganada"
        assert self.cluster.sql("SELECT count(*) FROM public.intentos WHERE partida_id='"+game_id+"';")=="1"
        self.record("ingress_sql_http_pass",active=answer[1])
        return game_id

    def exercise(self):
        password=os.environ.get("WORDLE_GRAFANA_DEMO_PASSWORD","")
        if len(password)<32:raise ValueError("External synthetic Grafana credential required before acceptance")
        initial=json.loads(self.cluster.kube("get","service/frontend","-o","json"))["spec"]["selector"]["wordle.slot"]
        if initial!="blue":raise ValueError("Fault fixture requires Blue initially active; no mutation performed")
        game_id=self.verify();path="/api/game/"+game_id
        capture = getattr(self, "capture_hook", None)
        if capture: capture("stable-blue")
        original_pvc=self.pvc_uid
        self.telemetry=self.forward("collector",4318,"wordle-observability")
        self.record("acceptance_started")
        ports={}
        def candidate_fetch(slot,path):
            if slot not in ports:ports[slot]=self.forward("frontend-"+slot)
            return self.fetch(ports[slot],path)
        def kube(*args,**kwargs):
            return command([*self.cluster.prefix,"-n","wordle-demo",*args],**kwargs)
        controller=PromotionController(kube,lambda p:self.fetch(self.public_port,p),
            {s:lambda p,s=s:candidate_fetch(s,p) for s in ("blue","green")},self.record,path,
            lambda phase:self.record("phase",phase=phase))
        stable=controller.active();candidate="green" if stable=="blue" else "blue"
        self.cluster.kube("scale","deployment/backend-"+candidate,"deployment/frontend-"+candidate,"--replicas=1")
        promoted=controller.promote(candidate);assert promoted["outcome"]=="promoted"
        if capture: capture("promoted-green")
        before=self.cluster.snapshot()
        # Both colors remain available. Fault only the formerly active candidate.
        d=json.loads(self.cluster.kube("get","deployment/frontend-"+stable,"-o","json"))
        volumes=d["spec"]["template"]["spec"]["volumes"]
        index=next(i for i,v in enumerate(volumes) if v.get("configMap",{}).get("name","").startswith("wordle-nginx-"+stable+"-"))
        normal=volumes[index]["configMap"]["name"]
        cms=json.loads(self.cluster.kube("get","configmaps","-o","json"))["items"]
        # The existing fixture is blue-only. Reverse initial direction if needed.
        if stable!="blue":raise ValueError("Full fault demonstration requires Blue initially active; no silent selector reset")
        fault=next(c["metadata"]["name"] for c in cms if c["metadata"]["name"].startswith("wordle-nginx-blue-fault-"))
        def patch(value):
            self.cluster.kube("patch","deployment/frontend-blue","--type=json","-p",json.dumps([
                {"op":"replace","path":f"/spec/template/spec/volumes/{index}/configMap/name","value":value}]))
        observed=[]
        def fail_after_switch():
            patch(fault);command([*self.cluster.prefix,"-n","wordle-demo","rollout","status","deployment/frontend-blue","--timeout=180s"],timeout=200)
            for _ in range(80):
                status,release,_=self.fetch(self.public_port,path)
                if (status,release)==(503,"blue"):
                    observed.append(True);self.record("controlled_fault_observed",status=503);return
                time.sleep(.25)
            raise RuntimeError("Expected post-promotion fault was not observed")
        try:
            result=controller.promote(stable,after_switch=fail_after_switch)
            assert result["outcome"]=="rolled-back" and observed and controller.active()==candidate
        finally:
            patch(normal)  # Repair the inactive fixture; never change the stable selector.
        assert before==self.cluster.snapshot()
        self.wait();self.verify_images()
        self.record("rollback_and_persistence_pass",active=candidate)
        if capture: capture("rollback-green")
        result=validate(command,self.cluster.prefix,self.cluster.sql,self.cluster.snapshot,game_id,password,
            self.evidence,self.record,capture=capture,disk_reader=lambda:{"scope":"PostgreSQL PVC only; not host OS disk",
                "df_kib":self.cluster.kube("exec","postgres-0","--","df","-k","/var/lib/postgresql/data").decode().strip()})
        assert result["database_unchanged"]
        uid=json.loads(self.cluster.kube("get","pvc","-o","json"))["items"][0]["metadata"]["uid"]
        assert uid==original_pvc
        self.record("aks_acceptance_pass")

    def close(self):
        for p in self.forwards:
            if p.poll() is None:
                p.terminate()
                try:p.wait(timeout=8)
                except subprocess.TimeoutExpired:p.kill();p.wait(timeout=5)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action",choices=("credentials","deploy","restore-deploy","verify","acceptance","backup","restore"))
    parser.add_argument("--variables",required=True,type=Path)
    parser.add_argument("--kubeconfig",required=True,type=Path)
    parser.add_argument("--context",required=True)
    parser.add_argument("--evidence",required=True,type=Path)
    parser.add_argument("--directory",type=Path)
    parser.add_argument("--confirm",required=True)
    parser.add_argument("--ack-costs",action="store_true")
    parser.add_argument("--capture",action="store_true",help="Read-only captures during already authorized acceptance")
    args=parser.parse_args();session=None
    if not __debug__:parser.error("Acceptance checks require normal, non-optimized Python")
    try:
        if args.capture and args.action != "acceptance": raise ValueError("Capture hooks require explicit acceptance action")
        values=json.loads(args.variables.read_text(encoding="utf-8"))
        authorize(args.action,values,args.confirm,args.ack_costs)
        if args.action in ("backup","restore") and not args.directory:raise ValueError("External backup directory required")
        kubeconfig=external(args.kubeconfig)
        authenticate(values)
        if args.action=="credentials":
            if kubeconfig.exists():raise ValueError("Refusing to overwrite a kubeconfig")
            kubeconfig.parent.mkdir(parents=True,exist_ok=True)
            command(["az","aks","get-credentials","--subscription",values["subscription_id"],"--resource-group",values["resource_group_name"],
                "--name",values["cluster_name"],"--file",kubeconfig,"--context",args.context,"--only-show-errors"])
            command(["kubelogin","convert-kubeconfig","-l","azurecli","--kubeconfig",kubeconfig])
            print("User kubeconfig prepared; no admin credentials, default kubeconfig or interactive login used")
            return
        cluster=Cluster(kubeconfig,args.context,values["subscription_id"],values["resource_group_name"],values["cluster_name"])
        session=Session(cluster,args.evidence)
        if args.capture:
            from types import SimpleNamespace
            from evidence.aks_capture import capture as capture_aks
            def capture_hook(stage, **fields):
                capture_aks(SimpleNamespace(stage=stage, export_id="aks-"+os.environ["GITHUB_RUN_ID"]+"-"+os.environ["GITHUB_RUN_ATTEMPT"]+"-"+stage,
                    subscription=values["subscription_id"], group=values["resource_group_name"], cluster=values["cluster_name"],
                    context=args.context, confirm="CAPTURE "+values["resource_group_name"]+"/"+values["cluster_name"], trace_id=fields.get("trace_id", "")))
            session.capture_hook=capture_hook
        if args.action in ("deploy","restore-deploy"):
            bootstrap(cluster,args.action=="restore-deploy")
            profile="aks-restore" if args.action=="restore-deploy" else "aks-full"
            command([*cluster.prefix,"apply","--dry-run=server","-k",ROOT/"k8s"/profile])
            command([*cluster.prefix,"apply","-k",ROOT/"k8s"/profile])
            session.record("profile_applied",profile=profile)
            if args.action=="deploy":session.verify()
            else:
                session.record("empty_restore_prepared",application_replicas=0)
                # Do not await SQL readiness before restoring the empty database.
        elif args.action=="verify":session.verify()
        elif args.action=="acceptance":session.exercise()
        elif args.action=="backup":
            replicas={n:json.loads(cluster.kube("get","deployment",n,"-o","json"))["spec"].get("replicas",1) for n in WORKLOADS}
            active=json.loads(cluster.kube("get","service/frontend","-o","json"))["spec"]["selector"]["wordle.slot"]
            try:
                cluster.kube("scale",*["deployment/"+n for n in WORKLOADS],"--replicas=0")
                for _ in range(100):
                    try:cluster.quiesced();break
                    except ValueError:time.sleep(1)
                else:raise RuntimeError("Application quiesce timeout")
                recover(cluster,"backup",args.directory)
                meta_path=external(args.directory)/"recovery.json";meta=json.loads(meta_path.read_text())
                meta.update(replicas=replicas,active_slot=active,image_lock_sha256=hashlib.sha256((ROOT/"k8s/aks-full/images.lock.json").read_bytes()).hexdigest())
                meta_path.write_text(json.dumps(meta,indent=2))
            finally:
                for name,count in replicas.items():cluster.kube("scale","deployment/"+name,"--replicas="+str(count))
            session.wait();session.record("backup_complete_application_resumed")
        elif args.action=="restore":
            # Wait for the NEW PG process, not readiness (tables intentionally absent).
            for _ in range(300):
                try:
                    cluster.kube("exec","postgres-0","--","sh","-c",'pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB"');break
                except RuntimeError:time.sleep(2)
            else:raise RuntimeError("New PostgreSQL process did not start")
            folder=external(args.directory);meta=json.loads((folder/"recovery.json").read_text())
            if meta.get("image_lock_sha256")!=hashlib.sha256((ROOT/"k8s/aks-full/images.lock.json").read_bytes()).hexdigest():
                raise ValueError("Recovery package image lock differs from selected release")
            replicas=meta["replicas"];slot=meta["active_slot"]
            if set(replicas)!=set(WORKLOADS) or slot not in ("blue","green") or any(type(n)!=int or n not in (0,1) for n in replicas.values()):
                raise ValueError("Invalid desired state in recovery metadata")
            if not all(replicas[n+"-"+slot]==1 for n in ("backend","frontend")):
                raise ValueError("Restored active slot must have both workloads")
            recover(cluster,"restore",args.directory)
            cluster.kube("patch","service/frontend","--type=merge","-p",json.dumps({"spec":{"selector":{"app":"wordle-frontend","wordle.slot":slot}}}))
            for name,count in replicas.items():cluster.kube("scale","deployment/"+name,"--replicas="+str(count))
            session.wait()
            assert cluster.snapshot()==meta["dataset_sha256"]
            port=session.forward("ingress");game=cluster.sql("SELECT id FROM public.partidas ORDER BY id LIMIT 1;")
            if game:
                game=str(uuid.UUID(game));assert session.fetch(port,"/api/game/"+game)[0]==200
            session.verify()  # Includes actual SQL/HTTP writes after checking restored equality.
            (folder/"restored-http.json").write_text(json.dumps({"sql_verified":True,"http_verified":True,"backup_sha256":meta["sha256"]}))
            session.record("restore_sql_http_pass")
        session.record("operation_complete",action=args.action)
        (session.evidence/"result.json").write_text(json.dumps({"result":"PASS","action":args.action}))
    except Exception as error:
        if session:
            (session.evidence/"result.json").write_text(json.dumps({"result":"FAIL","action":args.action,"category":type(error).__name__}))
        parser.exit(1,"Operation refused or failed; raw errors and sensitive values suppressed.\n")
    finally:
        if session:session.close()


if __name__=="__main__":main()
