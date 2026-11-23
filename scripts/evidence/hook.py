"""Optional capture hook for the existing disposable-kind runner; stdin is private."""
import json, os, pathlib, subprocess, sys
ctx=json.load(sys.stdin)
root=pathlib.Path(__file__).resolve().parents[2]
out=pathlib.Path(os.environ["WORDLE_CAPTURE_DIR"]).resolve()
prefix=ctx["prefix"]
if not any(str(x).startswith("kind-wordle-fin1015-") for x in prefix):
    raise ValueError("Capture requires the runner's isolated kind context")
def kube(*args,data=None):
    p=subprocess.run([*prefix,*args],input=data,capture_output=True,timeout=180)
    if p.returncode:raise RuntimeError("Capture Kubernetes read failed")
    return p.stdout
if ctx["stage"] in ("stable-blue","rollback-green"):
    records={}
    for ns in ("wordle-demo","wordle-observability"):
        records[ns]={}
        for kind in ("pods","services","ingresses","deployments","statefulsets","pvc"):
            items=json.loads(kube("-n",ns,"get",kind,"-o","json"))["items"]
            # Whitelist fields: never serialize pod env, Secret or ConfigMap bodies.
            records[ns][kind]=[{"name":x["metadata"]["name"],"kind":x["kind"],
                "ready":[c.get("ready") for c in x.get("status",{}).get("containerStatuses",[])],
                "phase":x.get("status",{}).get("phase"),
                "selector":x.get("spec",{}).get("selector"),
                "type":x.get("spec",{}).get("type"),
                "replicas":x.get("spec",{}).get("replicas"),
                "images":[{"name":c.get("name"),"image":c.get("image"),"imageID":next((z.get("imageID") for z in x.get("status",{}).get("containerStatuses",[]) if z["name"]==c["name"]),None)} for c in x.get("spec",{}).get("containers",[])]} for x in items]
    p=out/"results/kubernetes";p.mkdir(parents=True,exist_ok=True)
    (p/(ctx["stage"]+".json")).write_text(json.dumps(records,indent=2),encoding="utf-8")
# Browser receives credentials only through stdin, never argv/files/logs.
p=subprocess.run(["node",str(root/"scripts/evidence/capture.cjs"),"--capture"],
    input=json.dumps(ctx).encode(),capture_output=True,timeout=180)
if p.returncode:
    message=p.stderr.decode(errors="replace")[-1200:].replace(str(root), "<repo>").replace(os.environ.get("USERPROFILE", "__NONE__"), "<user>")
    message=message.replace(ctx.get("password", "__NO_PASSWORD__"), "[REDACTED]")
    target=out/"results/capture";target.mkdir(parents=True,exist_ok=True)
    (target/(ctx["stage"]+"-failure.json")).write_text(json.dumps({"status":"FAIL","stage":ctx["stage"],"diagnostic":message}),encoding="utf-8")
    raise RuntimeError("Browser capture failed; sanitized diagnostic preserved")
print(p.stdout.decode().strip())
