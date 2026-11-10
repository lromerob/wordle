"""Real HTTP/query/notification checks for the disposable observability profile."""
import base64
import json
import os
from pathlib import Path
import secrets
import socket
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request

IMAGES = ["otel/opentelemetry-collector-contrib:0.165.0", "prom/prometheus:v3.16.0",
          "prom/alertmanager:v0.35.0", "prom/node-exporter:v1.12.1", "grafana/grafana:13.3.0",
          "grafana/loki:3.6.20", "grafana/tempo:2.10.10"]
OBS = "wordle-observability"


def prepare(command, prefix):
    namespace = {"apiVersion": "v1", "kind": "Namespace", "metadata": {"name": OBS,
        "labels": {"wordle.environment": "private-observability-demo", "pod-security.kubernetes.io/enforce": "privileged"}}}
    command([*prefix, "create", "-f", "-"], data=json.dumps(namespace).encode())
    password = os.environ.get("WORDLE_GRAFANA_DEMO_PASSWORD") or secrets.token_urlsafe(36)
    if len(password) < 32:
        raise ValueError("Use a synthetic external Grafana password of at least 32 characters")
    obj = {"apiVersion": "v1", "kind": "Secret", "metadata": {"name": "wordle-grafana", "namespace": OBS},
           "type": "Opaque", "data": {"admin-password": base64.b64encode(password.encode()).decode()}}
    command([*prefix, "create", "-f", "-"], data=json.dumps(obj).encode())
    return password


def wait_stack(command, prefix):
    for name in ("collector", "loki", "tempo", "prometheus", "alertmanager", "grafana", "notifications"):
        command([*prefix, "-n", OBS, "rollout", "status", "deployment/" + name, "--timeout=240s"], timeout=260)
    command([*prefix, "-n", OBS, "rollout", "status", "daemonset/node-exporter", "--timeout=120s"], timeout=140)
    print("PASS: observability stack Ready", flush=True)


def validate(command, prefix, query, database_hash, game_id, password, evidence, record):
    forwards = []
    results = {}
    def kube(*args):
        return command([*prefix, "-n", OBS, *args])
    def forward(service, port, namespace=OBS, deployment=False):
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0)); local = sock.getsockname()[1]
        p = subprocess.Popen([*map(str, prefix), "-n", namespace, "port-forward", "--address", "127.0.0.1",
            ("deployment/" if deployment else "service/") + service, f"{local}:{port}"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        forwards.append(p)
        for _ in range(80):
            if p.poll() is not None:raise RuntimeError("Owned observability forward stopped")
            try:
                with socket.create_connection(("127.0.0.1", local), timeout=.2):return local
            except OSError:time.sleep(.1)
        raise RuntimeError("Observability forward timeout")
    def get(port, path, *, auth=False, data=None):
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        if auth:headers["Authorization"] = "Basic " + base64.b64encode(("demo:" + password).encode()).decode()
        req = urllib.request.Request(f"http://127.0.0.1:{port}" + path,
            data=json.dumps(data).encode() if data is not None else None, headers=headers)
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        try:r=opener.open(req,timeout=10)
        except urllib.error.HTTPError as error:r=error
        with r:
            raw=r.read()
            value=json.loads(raw) if r.headers.get_content_type()=="application/json" else raw.decode(errors="replace")
            return r.status,value
    def eventually(fn, name, timeout=120):
        deadline=time.monotonic()+timeout; last=None
        while time.monotonic()<deadline:
            try:
                value=fn()
                if value:return value
            except Exception as error:last=type(error).__name__
            time.sleep(2)
        raise RuntimeError("Validation timeout: " + name + (" ("+last+")" if last else ""))
    def prom_query(expr):
        code,data=get(prom,"/api/v1/query?"+urllib.parse.urlencode({"query":expr}))
        assert code==200 and data["status"]=="success"
        return data["data"]["result"]
    def logs(expr):
        code,data=get(loki,"/loki/api/v1/query_range?"+urllib.parse.urlencode({"query":expr,"limit":1000,"since":"15m"}))
        assert code==200 and data["status"]=="success"
        return [json.loads(line) for stream in data["data"]["result"] for _,line in stream["values"]]
    try:
        prom=forward("prometheus",9090);loki=forward("loki",3100);tempo=forward("tempo",3200)
        graf=forward("grafana",3000);sink=forward("notifications",8080);am=forward("alertmanager",9093)
        backend=forward("backend-green",8000,"wordle-demo",True)
        metric=eventually(lambda:prom_query("wordle_http_requests_total"),"OTLP request counter")
        duration=eventually(lambda:prom_query("wordle_http_duration_seconds"),"OTLP duration gauge")
        node=eventually(lambda:prom_query("node_memory_MemTotal_bytes"),"Node Exporter")
        container=eventually(lambda:prom_query('container_memory_working_set_bytes{namespace="wordle-demo",container!=""}'),"kubelet cAdvisor")
        code,targets=get(prom,"/api/v1/targets");assert code==200
        health={t["labels"].get("job")+":"+t["labels"].get("instance",""):t["health"] for t in targets["data"]["activeTargets"]}
        assert health and all(v=="up" for v in health.values()),health
        results.update(targets=health,http_metric_series=len(metric),duration_series=len(duration),http_metrics=metric,duration_metrics=duration,node_metric=node,wordle_container_metrics=container,wordle_container_series=len(container))
        backend_logs=eventually(lambda:logs('{service_name="wordle-backend"}'),"backend logs")
        frontend_logs=eventually(lambda:logs('{service_name="wordle-frontend"}'),"frontend filelog agent")
        attempts=[x for x in backend_logs if x.get("route")=="/game/intento" and x.get("status")==200]
        assert attempts
        trace_id=attempts[0]["trace_id"]
        trace=eventually(lambda:get(tempo,"/api/traces/"+trace_id)[1] if get(tempo,"/api/traces/"+trace_id)[0]==200 else None,"attempt trace")
        assert "POST /game/intento" in json.dumps(trace)
        results["attempt_trace"] = trace
        deploy_logs=eventually(lambda:logs('{service_name="wordle-deploy"}'),"deployment event logs")
        assert any(x.get("event")=="automatic_rollback_verified" for x in deploy_logs)
        results["deployment_events"] = deploy_logs
        results["operational_samples"] = attempts[:3]+[x for x in frontend_logs if x.get("status",0)>=500][:5]
        results.update(attempt_trace_id=trace_id,backend_log_count=len(backend_logs),frontend_log_count=len(frontend_logs))
        code,dashboard=get(graf,"/api/dashboards/uid/wordle-demo",auth=True)
        assert code==200 and len(dashboard["dashboard"]["panels"])==8
        code,ds=get(graf,"/api/datasources",auth=True)
        assert code==200 and {x["uid"] for x in ds}=={"prometheus","loki","tempo"}
        code,panel=get(graf,"/api/datasources/proxy/uid/prometheus/api/v1/query?"+urllib.parse.urlencode({"query":"wordle_http_requests_total"}),auth=True)
        assert code==200 and panel["data"]["result"]
        code,logpanel=get(graf,"/api/datasources/proxy/uid/loki/loki/api/v1/query_range?"+urllib.parse.urlencode({"query":'{service_name="wordle-frontend"}',"limit":5,"since":"15m"}),auth=True)
        assert code==200 and logpanel["data"]["result"]
        results["grafana"]={"dashboard":"wordle-demo","panels":8,"datasources":["prometheus","loki","tempo"],"queries_with_data":True}
        record("signals_verified", trace_id=trace_id, targets_up=len(health), dashboard_panels=8)
        # Let previous Blue-Green log errors age out; normal must precede this new fault.
        time.sleep(25)
        eventually(lambda:not [a for a in get(am,"/api/v2/alerts?active=true")[1]
            if a["labels"].get("alertname") in ("WordleUnavailable","WordleCriticalLog")],"normal alert state")
        eventually(lambda:all(float(r["value"][1])==1 for r in prom_query('up{job="wordle"}')),"normal backend targets")
        prior=get(sink,"/events")[1]; boundary=time.time()
        before=database_hash()
        denied=False
        try:
            query("REVOKE SELECT ON public.partidas FROM wordle_app;");denied=True
            code,error=get(backend,"/game/intento",data={"partida_id":game_id,"usuario_id":"fin0809-synthetic","palabra":"CASAS"})
            assert code==500
            errors=eventually(lambda:[x for x in logs('{service_name="wordle-backend"}') if x.get("status")==500],"sanitized backend ERROR")
            error_trace=errors[0]["trace_id"]
            error_span=eventually(lambda:get(tempo,"/api/traces/"+error_trace)[1] if get(tempo,"/api/traces/"+error_trace)[0]==200 else None,"error trace")
            results["error_trace"] = error_span
            def firings():
                events=[x for x in get(sink,"/events")[1] if x["time"]>=boundary and x["status"]=="firing"]
                return events if {"WordleUnavailable","WordleCriticalLog"}<={x["alertname"] for x in events} else None
            firing=eventually(firings,"both alert classes delivered",timeout=100)
            results.update(error_trace_id=error_trace,error_http_status=500,firing_notifications=firing)
            record("notifications_firing_delivered", names=[x["alertname"] for x in firing])
        finally:
            if denied:query("GRANT SELECT ON public.partidas TO wordle_app;")
        def resolutions():
            events=[x for x in get(sink,"/events")[1] if x["time"]>=boundary and x["status"]=="resolved"]
            return events if all(any(x["alertname"]==f["alertname"] and x["startsAt"]==f["startsAt"] for x in events) for f in firing) else None
        resolved=eventually(resolutions,"both alert classes resolved and delivered",timeout=120)
        eventually(lambda:all(float(r["value"][1])==1 for r in prom_query('up{job="wordle"}')),"availability recovered")
        code,game=get(backend,"/game/"+game_id);assert code==200 and game["partida"]["estado"]=="ganada"
        assert database_hash()==before
        results.update(resolved_notifications=resolved,database_unchanged=True,
            memory_working_set=prom_query('sum(container_memory_working_set_bytes{namespace=~"wordle-demo|wordle-observability",container!="",container!="POD"})'),
            cpu_cores=prom_query('sum(rate(container_cpu_usage_seconds_total{namespace=~"wordle-demo|wordle-observability",container!="",container!="POD"}[1m]))'))
        pods=json.loads(command([*prefix,"get","pods","-A","-o","json"]).stdout)["items"]
        assert not any(c.get("lastState",{}).get("terminated",{}).get("reason")=="OOMKilled" for p in pods for c in p["status"].get("containerStatuses",[]))
        results["resources"]=[{"namespace":p["metadata"]["namespace"],"pod":p["metadata"]["name"],"containers":[{"name":c["name"],**c.get("resources",{})} for c in p["spec"]["containers"]]} for p in pods]
        nodes=json.loads(command([*prefix,"get","nodes","-o","json"]).stdout)["items"]
        results["node_capacity"]=[{"name":n["metadata"]["name"],"allocatable":n["status"]["allocatable"]} for n in nodes]
        node_name=nodes[0]["metadata"]["name"]
        results["node_disk_df"]=command(["docker","exec",node_name,"df","-B1","/var/lib/containerd"]).stdout.decode().strip()
        results["database_size_bytes"]=int(query("SELECT pg_database_size(current_database());"))
        results["no_oom_observed"]=True
        record("observability_integrated_pass", alerts_resolved=True, database_unchanged=True, no_oom=True)
        return results
    finally:
        (Path(evidence)/"observability.json").write_text(json.dumps(results,indent=2)+"\n",encoding="utf-8")
        for p in forwards:
            if p.poll() is None:
                p.terminate()
                try:p.wait(timeout=8)
                except subprocess.TimeoutExpired:p.kill();p.wait(timeout=5)
