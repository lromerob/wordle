"""Capture the existing independent PostgreSQL restore test without changing it."""
from pathlib import Path
import json, os, subprocess, sys
ROOT=Path(__file__).resolve().parents[2]
run=sys.argv[1]
if any(c not in "abcdefghijklmnopqrstuvwxyz0123456789-_" for c in run):raise ValueError("Safe run ID required")
out=ROOT/"docs/evidence/local"/run/"results/persistence"
out.mkdir(parents=True,exist_ok=True)
p=out/"restore.json"
if p.exists():raise ValueError("Refuse evidence overwrite")
r=subprocess.run([sys.executable,"-B",str(ROOT/"backend/integration/run_fin02b.py"),"--run-disposable-postgres"],cwd=ROOT,capture_output=True,text=True)
lines=[x for x in r.stdout.splitlines() if x.startswith("{")]
if not lines:raise RuntimeError("Restore produced no sanitized JSON")
d=json.loads(lines[-1]);p.write_text(json.dumps(d,indent=2),encoding="utf-8")
print(json.dumps({"restore_exit":r.returncode,"result":d.get("result"),"cleanup":d.get("cleanup")}))
raise SystemExit(r.returncode)
