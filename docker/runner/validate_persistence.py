"""Two disposable, offline containers share one synthetic Windows bind. No approval."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import uuid

IMAGE = "wordle-actions-runner:fin17-private-store-02"

def docker(*args, check=True):
    p = subprocess.run(["docker", *map(str, args)], capture_output=True, text=True, timeout=120)
    if check and p.returncode:
        raise RuntimeError("Local Docker operation failed: " + p.stderr[-500:])
    return p

def validate():
    run = uuid.uuid4().hex
    prefix = "wordle-store-test-" + run[:12]
    temp_root = Path(tempfile.gettempdir()).resolve()
    folder = Path(tempfile.mkdtemp(prefix=prefix + "-", dir=temp_root)).resolve()
    names = []
    result = {"fixture_only": True, "run": run, "network": "none", "durability": "NOT VERIFIED"}
    try:
        (folder / ".wordle-private-store.json").write_text(json.dumps({"fixture_only": True, "durable_acknowledged": False}), encoding="utf-8")
        probe = folder / "probe" / "scripts"
        probe.mkdir(parents=True)
        repo = Path(__file__).resolve().parents[2]
        for source in ("private_store.py", "azure_supervised.py"):
            shutil.copyfile(repo / "scripts" / source, probe / source)
        payload = "WORDLE SYNTHETIC PERSISTENCE " + run
        expected = hashlib.sha256(payload.encode()).hexdigest()
        for phase in ("write", "read"):
            name = prefix + "-" + phase
            names.append(name)
            code = ("from pathlib import Path;import hashlib,json;"
                    "exec(" + repr(POSIX_PROBE) + ");" +
                    "p=Path('/wordle-private/synthetic.txt');" +
                    ("p.write_text(" + repr(payload) + ",encoding='utf-8');" if phase == "write" else "") +
                    "print(json.dumps({'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'mode':oct(p.parent.stat().st_mode&0o777),'real_posix_checks':2}))")
            response = docker("run", "--name", name, "--label", "wordle.tfg.persistence=" + run,
                "--network", "none", "--cap-drop", "ALL", "--security-opt", "no-new-privileges=true",
                "--user", "10001:10001", "--mount", f"type=bind,source={folder},target=/wordle-private",
                "--mount", f"type=bind,source={folder / 'probe'},target=/validation,readonly",
                "--entrypoint", "python3", IMAGE, "-B", "-c", code)
            evidence = json.loads(response.stdout)
            if evidence["sha256"] != expected:
                raise RuntimeError("Container hash mismatch")
            if hashlib.sha256((folder / "synthetic.txt").read_bytes()).hexdigest() != expected:
                raise RuntimeError("Windows host hash mismatch")
            info = json.loads(docker("inspect", name).stdout)[0]
            if info["HostConfig"]["NetworkMode"] != "none" or info["HostConfig"]["PortBindings"]:
                raise RuntimeError("Unexpected container exposure")
            result[phase] = dict(evidence, container_id=info["Id"], host_hash_matches=True, exit_code=info["State"]["ExitCode"])
            if info["State"]["ExitCode"] != 0:
                raise RuntimeError("Container did not finish cleanly")
            if info["Config"]["Labels"].get("wordle.tfg.persistence") != run:
                raise RuntimeError("Container ownership mismatch")
            docker("rm", name)  # Completed process; remove before creating the next container.
        result["persistence_between_independent_containers"] = True
        result["image_id"] = docker("image", "inspect", "--format", "{{.Id}}", IMAGE).stdout.strip()
    finally:
        for name in names:
            inspect = docker("inspect", name, check=False)
            if inspect.returncode == 0:
                info = json.loads(inspect.stdout)[0]
                if info["Config"]["Labels"].get("wordle.tfg.persistence") != run:
                    raise RuntimeError("Refuse cleanup of foreign container")
                docker("stop", "--time", "5", name, check=False)
                docker("rm", name)
        if folder.parent != temp_root or not folder.name.startswith(prefix + "-"):
            raise RuntimeError("Unsafe fixture cleanup target")
        shutil.rmtree(folder)
    result["cleanup"] = "Both owned containers and external synthetic fixture removed; image retained"
    return result


POSIX_PROBE = r'''import sys, tempfile
from pathlib import Path
import json
sys.path.insert(0, '/validation/scripts')
from private_store import require_store
uid='11111111-1111-4111-8111-111111111111'
with tempfile.TemporaryDirectory(prefix='wordle-synthetic-posix-') as tmp:
    root=Path(tmp);root.chmod(0o700)
    marker=root/'.wordle-private-store.json'
    marker.write_text(json.dumps({'format':1,'repository':'lromerob/wordle','store_id':uid,'durable_acknowledged':True}))
    marker.chmod(0o600)
    for name in ('plans','selections','evidence','backups'):(root/name).mkdir(mode=0o700)
    assert require_store(root,uid)==root.resolve()
    root.chmod(0o777)
    try:require_store(root,uid)
    except ValueError as e:
        assert str(e)=='Store must be private to the runner account'
    else:raise AssertionError('Real POSIX 0777 accepted')
'''

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-local-validation", action="store_true", required=True)
    parser.parse_args()
    print(json.dumps(validate(), indent=2))
