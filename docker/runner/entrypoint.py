"""Default: offline tool validation. Registration/removal require explicit future approval."""
import json
import os
from pathlib import Path
import platform
import signal
import subprocess
import sys
import time
from private_store import require_store

RUNNER = Path("/home/runner/actions")
REPOSITORY = "https://github.com/lromerob/wordle"


def require_runtime_store(allow_fixture=False):
    model = os.environ.get("WORDLE_STORE_MODEL", "posix")
    if model == "windows-supervised-test" and not allow_fixture:
        raise ValueError("Synthetic fixture can never register or run a listener")
    return require_store(os.environ.get("WORDLE_AZURE_PRIVATE_DIR", "/wordle-private"),
                         os.environ.get("WORDLE_AZURE_STORE_ID", ""))


def token_operation(action):
    if os.environ.get("WORDLE_RUNNER_AUTHORIZED_ACTION") not in (("REGISTER", "REGISTER_RUN") if action == "REGISTER" else (action,)):
        raise ValueError("Explicit owner authorization required")
    if os.getuid() == 0:
        raise ValueError("Runner must not run as root")
    if action == "REGISTER":
        require_runtime_store()
    # Token arrives only at activation via stdin, never a Docker build arg/env file.
    token = sys.stdin.readline().strip()
    if not token or any(c.isspace() for c in token):
        raise ValueError("Ephemeral token must be provided privately on stdin")
    env = dict(os.environ, ACTIONS_RUNNER_INPUT_TOKEN=token)
    if action == "REGISTER":
        if (RUNNER/".runner").exists(): raise ValueError("Existing registration must be preserved")
        args = ["./config.sh", "--unattended", "--url", REPOSITORY, "--name", "wordle-docker-azure",
                "--labels", "wordle-azure", "--work", "/home/runner/_work", "--ephemeral", "--disableupdate"]
    else:
        args = ["./config.sh", "remove", "--unattended"]
    r = subprocess.run(args, cwd=RUNNER, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    token = None; env.pop("ACTIONS_RUNNER_INPUT_TOKEN", None)
    if r.returncode: raise RuntimeError("Runner configuration failed; raw credential-bearing output suppressed")
    print("Runner configuration completed; this command did not start a listener")


def validate():
    if os.getuid() == 0 or platform.system() != "Linux" or platform.machine() not in ("x86_64", "amd64"):
        raise ValueError("Non-root Linux x64 required")
    if Path("/var/run/docker.sock").exists(): raise ValueError("Docker socket forbidden")
    checked = False
    if os.environ.get("WORDLE_STORE_MODEL", "posix") != "posix":
        require_runtime_store(allow_fixture=True)
        checked = True
    commands = {"git":["git","--version"], "python":["python","--version"], "node":["node","--version"],
        "terraform":["terraform","version","-json"], "azure_cli":["az","version","-o","json"],
        "kubectl":["kubectl","version","--client=true","-o","json"], "kubelogin":["kubelogin","--version"],
        "runner":[str(RUNNER/"bin/Runner.Listener"),"--version"]}
    versions = {}
    for name, args in commands.items():
        r=subprocess.run(args,capture_output=True,text=True,timeout=40)
        if r.returncode: raise RuntimeError("Unavailable tool: "+name)
        versions[name]=r.stdout.strip()
    store=Path(os.environ.get("WORDLE_AZURE_PRIVATE_DIR", "/wordle-private"))
    print(json.dumps({"mode":"validate","registered":(RUNNER/".runner").exists(),"uid":os.getuid(),
        "system":platform.system(),"architecture":platform.machine(),"versions":versions,
        "store_validated":checked,"store_model":os.environ.get("WORDLE_STORE_MODEL", "posix"),"store_present":store.is_dir(),"store_mode":oct(store.stat().st_mode & 0o777) if store.is_dir() else None}))


def main():
    mode=sys.argv[1] if len(sys.argv)>1 else "validate"
    if mode in ("validate","validate-hold"):
        validate()
        if mode == "validate-hold":
            signal.signal(signal.SIGTERM,lambda *args:sys.exit(0))
            signal.signal(signal.SIGINT,lambda *args:sys.exit(0))
            while True:time.sleep(1)
    elif mode == "activate":
        if os.environ.get("WORDLE_RUNNER_AUTHORIZED_ACTION") != "REGISTER_RUN":
            raise ValueError("Separate owner authorization for registration and listening required")
        token_operation("REGISTER")
        os.execv("./run.sh",["./run.sh"])
    elif mode in ("register","remove"): token_operation("REGISTER" if mode=="register" else "REMOVE")
    elif mode == "run":
        if os.environ.get("WORDLE_RUNNER_AUTHORIZED_ACTION") != "RUN" or not (RUNNER/".runner").is_file():
            raise ValueError("Explicit future RUN authorization and registration required")
        require_runtime_store()
        os.execv("./run.sh",["./run.sh"])
    else: raise ValueError("Unknown runner action")


if __name__ == "__main__":
    try: main()
    except Exception as error:
        print("Runner refused: "+type(error).__name__,file=sys.stderr);sys.exit(1)
