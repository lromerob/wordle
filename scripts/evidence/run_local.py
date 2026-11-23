"""Run existing integrated demo with durable private originals and public capture hooks."""
from pathlib import Path
import os, subprocess, secrets, sys, json
ROOT=Path(__file__).resolve().parents[2]
run=sys.argv[1] if len(sys.argv)>1 else None
if not run or any(c not in "abcdefghijklmnopqrstuvwxyz0123456789-_" for c in run):
    raise SystemExit("Supply a unique lowercase run ID")
out=ROOT/"docs/evidence/local"/run
original=Path(os.environ["LOCALAPPDATA"])/"WordleTFG/evidence"/run/"integrated"
if original.exists():raise SystemExit("Refuse original evidence overwrite")
env=os.environ.copy();env["WORDLE_CAPTURE_DIR"]=str(out)
env["PYTHONDONTWRITEBYTECODE"]="1"
env["WORDLE_GRAFANA_DEMO_PASSWORD"]=secrets.token_urlsafe(36)
args=[sys.executable,"-B",str(ROOT/"k8s/observability/run_observability.py"),"--run-disposable-kind",
 "--evidence-dir",str(original),"--capture-script",str(ROOT/"scripts/evidence/hook.py")]
result=subprocess.run(args,cwd=ROOT,env=env)
print(json.dumps({"integrated_exit":result.returncode,"original_location":"%LOCALAPPDATA%/WordleTFG/evidence/"+run+"/integrated"}))
raise SystemExit(result.returncode)
