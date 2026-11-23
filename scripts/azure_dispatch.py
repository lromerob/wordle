"""Manual workflow adapter; private plans remain on the approved durable private mount."""
import json
import os
from pathlib import Path
import re
import subprocess
import sys

from azure_supervised import ROOT, external

ACTIONS=("preflight","plan","plan-destroy","execute-infra","credentials","deploy","restore-deploy","verify","acceptance","backup","restore")


def commands(operation, private, run_id, inputs, source_sha):
    if operation not in ACTIONS or not re.fullmatch(r"[0-9]+",run_id):
        raise ValueError("Invalid action/run identifier")
    private=external(private);py=[sys.executable,"-B"]
    variables=private/"variables.json";backend=private/"backend.json"
    values=json.loads(variables.read_text(encoding="utf-8"))
    target=values["resource_group_name"]+"/"+values["cluster_name"]
    context="wordle-azure-supervised"
    if operation=="preflight":
        return [py+[str(ROOT/"scripts/azure_preflight.py"),"--check-ghcr","--variables",str(variables),"--backend",str(backend)]]
    if inputs.get("confirm")!=("EXECUTE" if operation=="execute-infra" else operation.upper())+" "+target:
        raise ValueError("Explicit action/target confirmation required")
    if operation in ("plan","plan-destroy"):
        work=private/"plans"/run_id
        # No plan data is uploaded to public GitHub artifacts.
        return [py+[str(ROOT/"scripts/azure_supervised.py"),"prepare","--workdir",str(work),"--variables",str(variables),"--backend",str(backend)],
            py+[str(ROOT/"scripts/azure_supervised.py"),operation,"--workdir",str(work),"--confirm",inputs["confirm"]]]
    if operation=="execute-infra":
        plan_run=inputs.get("plan_run","");digest=inputs.get("plan_sha256","")
        if not re.fullmatch(r"[0-9]+",plan_run) or not re.fullmatch(r"[a-f0-9]{64}",digest):
            raise ValueError("Exact reviewed plan run/hash required")
        work=private/"plans"/plan_run
        if json.loads((work/"source.json").read_text())["commit"]!=source_sha:
            raise ValueError("Plan source commit differs from selected workflow commit")
        intent=inputs.get("intent","")
        if intent not in ("CREATE","DESTROY"):raise ValueError("Explicit CREATE/DESTROY intent required")
        args=py+[str(ROOT/"scripts/azure_supervised.py"),"execute","--workdir",str(work),"--confirm",inputs["confirm"],
                 "--approve-intent",intent+" "+target,"--plan-sha256",digest]
        if inputs.get("costs") is True:args.append("--budget-approved")
        if intent=="DESTROY":
            inv=inputs.get("inventory_sha256","")
            if not re.fullmatch(r"[a-f0-9]{64}",inv):raise ValueError("Reviewed inventory hash required")
            args.extend(["--inventory-sha256",inv])
        return [args]
    args=py+[str(ROOT/"scripts/aks_run.py"),operation,"--variables",str(variables),"--kubeconfig",str(private/"aks.kubeconfig"),
        "--context",context,"--evidence",str(private/"evidence"/run_id),"--confirm",inputs["confirm"]]
    if inputs.get("costs") is True:args.append("--ack-costs")
    if inputs.get("capture") is True:
        if operation != "acceptance": raise ValueError("Captures are only enabled with separately authorized acceptance")
        args.append("--capture")
    if operation in ("backup","restore"):
        backup=inputs.get("backup","")
        if not re.fullmatch(r"[a-zA-Z0-9_-]+",backup):raise ValueError("Private backup identifier required")
        args.extend(["--directory",str(private/"backups"/backup)])
    return [args]


def main():
    event=json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text())
    inputs=event["inputs"];operation=inputs["operation"]
    private=external(os.environ["WORDLE_AZURE_PRIVATE_DIR"])
    run_id=os.environ["GITHUB_RUN_ID"];source=os.environ["GITHUB_SHA"]
    normalized={"confirm":inputs.get("confirm",""),"intent":inputs.get("intent",""),"plan_run":inputs.get("plan_run",""),
        "plan_sha256":inputs.get("plan_sha256",""),"inventory_sha256":inputs.get("inventory_sha256",""),
        "backup":inputs.get("backup",""),"capture":inputs.get("capture",False) in (True,"true"),"costs":inputs.get("approve_costs",False) in (True,"true")}
    try:
        from release_gate import verify_selection
        from azure_supervised import validate_oidc
        selection = verify_selection()
        validate_oidc(json.loads((private / "variables.json").read_text(encoding="utf-8")))
        if operation == "execute-infra":
            plan_run = normalized["plan_run"]
            if not re.fullmatch(r"[0-9]+", plan_run):
                raise ValueError("Invalid private plan identifier")
            receipt = json.loads((private / "plans" / plan_run / "source.json").read_text(encoding="utf-8"))
            if receipt != {"commit": source, "release_id": selection["release_id"], "store_id": selection["store_id"]}:
                raise ValueError("Reviewed plan belongs to a different release or store")
        selected=commands(operation,private,run_id,normalized,source)
        if "--check-inputs" in sys.argv:
            print("Inputs validated locally; no Azure authentication or operation executed")
            return
        for args in selected:
            verify_selection()  # Recheck immediately before each operational boundary.
            result=subprocess.run(args,capture_output=True,timeout=3000)
            if operation=="preflight" and result.returncode==0:print(result.stdout.decode())
            if result.returncode:raise RuntimeError("Supervised step failed; inspect private evidence")
        if operation in ("plan","plan-destroy"):
            work=private/"plans"/run_id
            (work/"source.json").write_text(json.dumps({"commit": source, "release_id": selection["release_id"], "store_id": selection["store_id"]}))
            receipt=json.loads((work/"review.json").read_text())
            print("Review private plan before execution. Plan SHA-256:",receipt["plan_sha256"])
            if "inventory_sha256" in receipt:print("Inventory SHA-256:",receipt["inventory_sha256"])
        print("Supervised operation completed; evidence remains in the private runner workspace")
    except Exception:
        raise SystemExit("Operation refused or failed; no private plan, credentials or raw logs emitted")


if __name__=="__main__":main()
