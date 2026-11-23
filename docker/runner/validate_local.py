"""Explicit local-only runner validation; owns and removes only its synthetic resources."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
import uuid
ROOT=Path(__file__).resolve().parents[2]
IMAGE="wordle-actions-runner:fin17-local"


def docker(*args,check=True):
    r=subprocess.run(["docker",*map(str,args)],capture_output=True,text=True,timeout=180)
    if check and r.returncode:raise RuntimeError("Local Docker validation failed: "+r.stderr[-600:])
    return r


def validate():
    run=uuid.uuid4().hex[:12];name="wordle-runner-validation-"+run
    folder=Path(tempfile.mkdtemp(prefix=".validation-",dir=ROOT/"docker/runner")).resolve()
    owned=False;result={"run":run,"image":IMAGE}
    try:
        store=folder/"synthetic-store";store.mkdir()
        for n in ("plans","selections","evidence","backups"):(store/n).mkdir()
        (store/"fixture.txt").write_text("SYNTHETIC RUNNER VALIDATION ONLY",encoding="utf-8")
        # Explicitly NOT an approved durable store. No real UUID, secrets or inputs.
        (store/".wordle-private-store.json").write_text(json.dumps({"format":1,"repository":"lromerob/wordle","store_id":"SYNTHETIC-NOT-APPROVED","durable_acknowledged":False}))
        probe=folder/"probe";probe.mkdir();(probe/"scripts").mkdir()
        for source in ("scripts/private_store.py","scripts/azure_supervised.py","scripts/evidence/capture.cjs","scripts/evidence/capture_policy.cjs"):
            shutil.copyfile(ROOT/source,(probe/"scripts" if source.startswith("scripts/private_store") or source.startswith("scripts/azure_supervised") else probe)/Path(source).name)
        (probe/"scripts/probe.py").write_text(PROBE,encoding="utf-8")
        # No project .env, credentials, checkout or Docker socket is mounted.
        docker("run","--detach","--name",name,"--label","wordle.tfg.validation="+run,
               "--network","none","--cap-drop","ALL","--security-opt","no-new-privileges=true","--shm-size","512m",
               "--mount",f"type=bind,source={store},target=/wordle-private",
               "--mount",f"type=bind,source={probe},target=/validation",IMAGE,"validate-hold")
        owned=True
        for _ in range(60):
            output=docker("logs",name).stdout.strip()
            if output:
                result["tools"]=json.loads(output);break
            if docker("inspect","--format","{{.State.Running}}",name).stdout.strip()!="true":
                raise RuntimeError("Validation container exited before tool checks")
            time.sleep(1)
        else:raise RuntimeError("Tool validation timeout")
        info=json.loads(docker("inspect",name).stdout)[0]
        assert not info["HostConfig"]["Privileged"] and not info["HostConfig"]["PortBindings"]
        assert info["HostConfig"]["CapDrop"]==["ALL"] and info["Config"]["User"]=="10001:10001"
        assert not any(m["Destination"]=="/var/run/docker.sock" for m in info["Mounts"])
        assert not result["tools"]["registered"]
        result["security"]={"non_root":True,"privileged":False,"docker_socket":False,"ports_published":False,"network":"none","registered":False}
        result["store"]=json.loads(docker("exec",name,"python","/validation/scripts/probe.py").stdout)
        assert (store/"container-write.txt").read_text()=="SYNTHETIC WRITE ONLY"
        result["browser"]=json.loads(docker("exec",name,"node","/validation/capture.cjs","--smoke","/validation/browser").stdout)
        docker("stop","--time","10",name)
        result["clean_stop_exit_code"]=int(docker("inspect","--format","{{.State.ExitCode}}",name).stdout.strip())
        assert result["clean_stop_exit_code"]==0
        result["image_id"]=docker("image","inspect","--format","{{.Id}}",IMAGE).stdout.strip()
        result["image_bytes"]=int(docker("image","inspect","--format","{{.Size}}",IMAGE).stdout.strip())
    finally:
        if owned:
            # Label and unique name must still belong to this invocation before cleanup.
            label=docker("inspect","--format",'{{index .Config.Labels "wordle.tfg.validation"}}',name,check=False)
            if label.returncode==0:
                if label.stdout.strip()!=run:raise RuntimeError("Refuse cleanup of foreign container")
                docker("stop","--time","10",name,check=False);docker("rm",name)
        if folder.parent!=(ROOT/"docker/runner").resolve() or not folder.name.startswith(".validation-"):
            raise RuntimeError("Refuse unsafe fixture cleanup")
        shutil.rmtree(folder)
    result["cleanup"]="owned container and synthetic fixture removed; image retained"
    return result


PROBE = r'''import json,os,shutil
from pathlib import Path
from unittest.mock import patch
from private_store import require_store
p=Path('/wordle-private');assert (p/'fixture.txt').read_text()=='SYNTHETIC RUNNER VALIDATION ONLY'
(p/'container-write.txt').write_text('SYNTHETIC WRITE ONLY')
uid='11111111-1111-4111-8111-111111111111' # Synthetic fixture, never an approved installation ID.
try:require_store('/absent-wordle-validation-store',uid)
except (ValueError,FileNotFoundError):missing=True
else:raise AssertionError('Missing store accepted')
try:require_store(p,uid)
except ValueError:unapproved=True
else:raise AssertionError('Unapproved marker accepted')
# Exercise real POSIX stat checks with ONLY marker deserialization simulated in memory.
# The on-disk marker remains false/unapproved throughout.
marker={'format':1,'repository':'lromerob/wordle','store_id':uid,'durable_acknowledged':True}
with patch('private_store.json.loads',return_value=marker):
 try:require_store(p,uid);posix='accepted actual mount modes (marker synthetic)'
 except ValueError as e:
  if str(e)!='Store must be private to the runner account':raise
  posix='rejected actual mount modes: group/other access'
assert shutil.which('docker') is None
print(json.dumps({'read_write_round_trip':True,'missing_rejected':missing,'unapproved_marker_rejected':unapproved,
 'root_mode':oct(p.stat().st_mode&0o777),'marker_mode':oct((p/'.wordle-private-store.json').stat().st_mode&0o777),
 'posix_contract':posix,'physical_durability':'NOT VERIFIED','no_docker_cli':True,'fixture_only':True}))
'''

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run-local-validation',action='store_true',required=True);p.parse_args()
    print(json.dumps(validate(),indent=2))
