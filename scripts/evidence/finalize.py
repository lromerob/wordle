"""Build an append-safe sanitized local evidence inventory (no infrastructure operations)."""
from pathlib import Path
import argparse, hashlib, json, os, shutil, struct, subprocess
from datetime import datetime, timezone
ROOT=Path(__file__).resolve().parents[2]
MAP={"EV-01":["A01","A50","A55"],"EV-04":["A10","A11","A12","A15"],"EV-06":["A20","A47"],"EV-07":["A21","A31"],"EV-08":["A22","A30","A48"],"EV-09":["A23","A26","A27"],"EV-10":["A24","A30"],"EV-11":["A25","A30"],"EV-12":["A28","A29","A30"],"EV-14":["A01","A50","A51"]}
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def finalize(run):
 out=ROOT/"docs/evidence/local"/run
 if (out/"manifest.json").exists():raise ValueError("Refuse manifest overwrite")
 source=Path(os.environ["LOCALAPPDATA"])/"WordleTFG/evidence"/run/"integrated"
 originals=[]
 if source.exists():
  for p in source.iterdir():
   if p.name not in ("summary.json","traffic.json","events.json","observability.json"):continue
   json.loads(p.read_text(encoding="utf-8"))
   dest=out/"results/integrated"/p.name;dest.parent.mkdir(parents=True,exist_ok=True)
   if dest.exists():raise ValueError("Refuse original overwrite")
   raw=p.read_text(encoding="utf-8")
   # Preserve original privately; redact unnecessary workstation paths in public derivative.
   for value in (str(ROOT),os.environ.get("USERPROFILE","__NONE__")):
    raw=raw.replace(value.replace("\\","\\\\"),"<local>").replace(value,"<local>")
   dest.write_text(raw,encoding="utf-8")
   json.loads(raw)
   originals.append({"path":dest.relative_to(out).as_posix(),"source":"%LOCALAPPDATA%/WordleTFG/evidence/"+run+"/integrated/"+p.name,"sha256":digest(dest),"original_sha256":digest(p),"sanitized_derivative":digest(p)!=digest(dest)})
 g=["git","-c","safe.directory="+ROOT.as_posix()]
 def git(*a):return subprocess.check_output(g+list(a),cwd=ROOT,stderr=subprocess.DEVNULL).decode().strip()
 items=[]
 for p in sorted((out/"results/capture").glob("*.json")) if (out/"results/capture").exists() else []:
  d=json.loads(p.read_text(encoding="utf-8"))
  for entry in d.get("screenshots",[]):
   file=out/entry["path"];b=file.read_bytes()
   assert b[:8]==bytes([137,80,78,71,13,10,26,10])
   assert list(struct.unpack(">II",b[16:24]))==[entry["width"],entry["height"]]
   assert digest(file)==entry["sha256"]
   items.append({**entry,"run_id":run,"branch":git("branch","--show-current"),"head":git("rev-parse","HEAD"),"working_tree":"Includes uncommitted capture hooks; not reproduced by HEAD alone","executor":"scripts/evidence/run_local.py","original_results":originals})
 summary=out/"results/integrated/summary.json"
 integrated=json.loads(summary.read_text()) if summary.exists() else {}
 covered=sorted(set(x["ev"] for x in items))
 manifest={"run_id":run,"utc":datetime.now(timezone.utc).isoformat(),"environment":"kind-local; NOT AKS","branch":git("branch","--show-current"),"head":git("rev-parse","HEAD"),"integrated_result":integrated.get("result","NOT RUN"),"screenshots":items,"originals":originals,"requirements":MAP,"historical":"historical/provenance.json" if (out/"historical/provenance.json").exists() else None,"limitations":["No Azure operations","Same application binary, Blue/Green configuration releases","Runtime local image metadata is recorded separately when available; no historical registry digest assigned","Signals are ephemeral; JSON exported before cluster cleanup by existing runner","Browser screenshots require human visual review"] }
 technical=[]
 for original in originals:
  name=Path(original["path"]).name
  ids={"events.json":["EV-04","EV-06","EV-07"],"traffic.json":["EV-06","EV-07"],"summary.json":["EV-06","EV-07","EV-14"],"observability.json":["EV-08","EV-09","EV-10","EV-11","EV-12"]}[name]
  technical.append({**original,"ev":ids,"requirements":sorted({a for ev in ids for a in MAP[ev]}),"run_id":run,"environment":"kind-local","persistence":"PostgreSQL 16 real","expected":"Existing real SQL/HTTP/observability assertions pass","observed":integrated.get("result","NOT RUN"),"status":integrated.get("result","NOT RUN"),"executor":"k8s/observability/run_observability.py","limitation":"Original private JSON retained; sanitized derivative identified where necessary"})
 manifest["technical_evidence"]=technical
 review_path=out/"visual-review.json"
 review=json.loads(review_path.read_text(encoding="utf-8")) if review_path.exists() else {}
 for item in items:
  finding=review.get("images",{}).get(item["path"])
  if finding:
   item["automated_status"]=item["status"]
   item["status"]=finding["status"]
   item["visual_review"]=finding
 manifest["visual_review"]=review
 manifest["dossier_result"]="PARTIAL" if any(x["status"]!="PASS" for x in items) or manifest.get("capture_failures") else integrated.get("result","NOT RUN")
 manifest["supporting_files"]=[]
 for file in sorted((out/"results").rglob("*.json")):
  if "/integrated/" in file.as_posix():continue
  ev={"kubernetes":["EV-04"],"capture":["EV-01","EV-04","EV-06","EV-07"],"persistence":["EV-14"],"tooling":[]}.get(file.parent.name,[])
  manifest["supporting_files"].append({"path":file.relative_to(out).as_posix(),"sha256":digest(file),"ev":ev,"requirements":sorted({a for ident in ev for a in MAP[ident]})})
 manifest["source_hash_scope"]="Source files at finalization; diagnostic attempts can predate subsequent fixes. Not a historical source snapshot."
 manifest["source_files_sha256"]={p.relative_to(ROOT).as_posix():digest(p) for p in [*(ROOT/"scripts/evidence").glob("*.py"),ROOT/"scripts/evidence/capture.cjs",ROOT/"k8s/observability/run_observability.py",ROOT/"k8s/observability/validation.py"]}
 manifest["capture_failures"]=[json.loads(p.read_text()) for p in (out/"results/capture").glob("*-failure.json")] if (out/"results/capture").exists() else []
 if manifest["capture_failures"]:manifest["dossier_result"]="PARTIAL"
 for p in out.rglob("*"):
  if p.suffix.lower()==".json":json.loads(p.read_text(encoding="utf-8"))
 (out/"manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
 (out/"summary.md").write_text("# Local evidence "+run+"\n\nIntegrated result: "+manifest["integrated_result"]+"\n\nDossier result: "+manifest["dossier_result"]+"\n\nScreenshots: "+str(len(items))+"; EV with browser evidence: "+", ".join(covered)+".\n\nSee original JSON for Blue-Green, rollback, alert deliveries and persistence; this is local kind, not Azure. Historical derivatives preserve separate provenance.\n",encoding="utf-8")
 files=sorted(p for p in out.rglob("*") if p.is_file() and p.name!="checksums.sha256")
 (out/"checksums.sha256").write_text("".join(digest(p)+"  "+p.relative_to(out).as_posix()+"\n" for p in files),encoding="utf-8")
 print(json.dumps({"run":run,"screenshots":len(items),"files":len(files),"integrated":manifest["integrated_result"],"covered":covered}))
def verify(run):
 out=ROOT/"docs/evidence/local"/run
 manifest=json.loads((out/"manifest.json").read_text(encoding="utf-8"))
 count=0
 listed=set()
 for line in (out/"checksums.sha256").read_text().splitlines():
  expected,name=line.split("  ",1)
  listed.add(name)
  target=(out/name).resolve()
  if out.resolve() not in target.parents:raise ValueError("Unsafe checksum path")
  assert target.is_file() and digest(target)==expected,name
  count+=1
 assert listed=={p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file() and p.name!="checksums.sha256"},"Uninventoried files"
 for p in out.rglob("*.json"):json.loads(p.read_text(encoding="utf-8"))
 for p in out.rglob("*.png"):
  b=p.read_bytes();assert b[:8]==bytes([137,80,78,71,13,10,26,10]),p.name
 for item in manifest["screenshots"]:
  b=(out/item["path"]).read_bytes();assert list(struct.unpack(">II",b[16:24]))==[item["width"],item["height"]]
 print(json.dumps({"verified":run,"files":count,"result":"PASS"}))
if __name__=="__main__":
 parser=argparse.ArgumentParser();parser.add_argument("run");parser.add_argument("--verify",action="store_true");args=parser.parse_args()
 if not args.run or any(c not in "abcdefghijklmnopqrstuvwxyz0123456789-_" for c in args.run):parser.error("Unique safe run ID required")
 verify(args.run) if args.verify else finalize(args.run)
