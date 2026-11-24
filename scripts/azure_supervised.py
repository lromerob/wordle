"""Future supervised Terraform operations. No operation is implicit; never auto-login.

Do not invoke cloud actions until separately authorized. prepare is entirely local.
Plans, inputs, inventory and state metadata stay in an external private workspace.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import uuid

ROOT = Path(__file__).resolve().parents[1]
TF = ROOT / "infra/terraform"
ADDRESSES = {"azurerm_resource_group.wordle", "azurerm_virtual_network.wordle", "azurerm_subnet.aks",
             "azurerm_user_assigned_identity.aks", "azurerm_role_assignment.aks_network",
             "azurerm_kubernetes_cluster.wordle"}
BACKEND_KEYS = {"resource_group_name", "storage_account_name", "container_name", "key", "use_azuread_auth"}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def external(path):
    path = Path(path).resolve()
    if path == ROOT or ROOT in path.parents:
        raise ValueError("Use a private workspace outside the repository")
    return path


def terraform_defaults():
    """Read the existing literal pool/region defaults; no Terraform execution."""
    source = (TF / "variables.tf").read_text(encoding="utf-8")
    defaults = {}
    for name in ("location", "node_vm_size", "node_count"):
        block = re.search(r'variable "' + name + r'"\s*\{([^}]+)', source)
        value = re.search(r'^\s*default\s*=\s*([^\n]+)', block[1], re.MULTILINE) if block else None
        if value is None:
            raise ValueError("Explicit Terraform default missing; review configuration")
        defaults[name] = json.loads(value[1])
    return defaults


def validate_inputs(values, backend):
    allowed = set(re.findall(r'variable "([^" ]+)"', (TF / "variables.tf").read_text(encoding="utf-8")))
    if not set(values) <= allowed:
        raise ValueError("Unexpected variables; credentials do not belong in Terraform input files")
    count=values.get("node_count",2)
    disk=values.get("os_disk_size_gb",64)
    if type(count) is not int or count<2 or type(disk) is not int or disk<30:
        raise ValueError("Node count and OS disk must satisfy the Terraform integer minimums")
    sku=values.get("node_vm_size","Standard_D4s_v5")
    if not isinstance(sku,str) or not sku or sku.lower().startswith("standard_b"):
        raise ValueError("Unsupported system-pool SKU input")
    if not re.fullmatch(r"[a-zA-Z0-9]+",values.get("location",terraform_defaults()["location"])):
        raise ValueError("Invalid Azure location input")
    for key in ("subscription_id", "tenant_id"):
        uuid.UUID(values[key])
    for key in ("resource_group_name", "node_resource_group_name", "cluster_name"):
        if not re.fullmatch(r"[a-zA-Z0-9_-]*wordle[a-zA-Z0-9_-]*", values[key]):
            raise ValueError("Dedicated Wordle target names required")
    groups = values.get("admin_group_object_ids", [])
    if not groups:
        raise ValueError("An explicitly selected Entra group is required")
    for group in groups:
        uuid.UUID(group)
    import ipaddress
    ranges = values.get("api_authorized_cidrs", [])
    if (not isinstance(ranges, list) or len(ranges) != 1
            or not isinstance(ranges[0], str) or not ranges[0].endswith("/32")
            or values.get("api_access_approved") is not True):
        raise ValueError("One explicitly approved public IPv4 API /32 is required")
    address = ipaddress.ip_network(ranges[0])
    if address.version != 4 or address.prefixlen != 32 or not address.network_address.is_global:
        raise ValueError("API access requires a public IPv4 /32, not a placeholder or broader network")
    if set(backend) != BACKEND_KEYS or backend["use_azuread_auth"] is not True:
        raise ValueError("Only secret-free Entra backend coordinates are accepted")
    if backend["resource_group_name"] in (values["resource_group_name"], values["node_resource_group_name"]):
        raise ValueError("State storage must be independent of both disposable resource groups")
    if not all(isinstance(backend[k], str) and re.fullmatch(r"[a-zA-Z0-9_./-]+", backend[k]) for k in BACKEND_KEYS - {"use_azuread_auth"}):
        raise ValueError("Invalid backend coordinates")
    if not backend["key"].startswith("wordle/"):
        raise ValueError("Dedicated Wordle state key required")


def fingerprint(work):
    files = sorted([*work.glob("*.tf"), work / ".terraform.lock.hcl", work / "variables.tfvars.json", work / "backend.hcl"])
    return sha(json.dumps({p.name: sha(p.read_bytes()) for p in files}, sort_keys=True).encode())


def prepare(work, variables, backend_file):
    values = json.loads(Path(variables).read_text(encoding="utf-8"))
    backend = json.loads(Path(backend_file).read_text(encoding="utf-8"))
    validate_inputs(values, backend)
    work = external(work)
    if work.exists() and any(work.iterdir()):
        raise ValueError("Refusing to overwrite a non-empty workspace")
    work.mkdir(parents=True, exist_ok=True)
    for path in [*TF.glob("*.tf"), TF / ".terraform.lock.hcl"]:
        shutil.copy2(path, work / path.name)
    (work / "variables.tfvars.json").write_text(json.dumps(values, indent=2), encoding="utf-8")
    (work / "backend.hcl").write_text("".join(k + " = " + json.dumps(v) + "\n" for k, v in sorted(backend.items())), encoding="utf-8")
    (work / "workspace.json").write_text(json.dumps({"format": 1, "fingerprint": fingerprint(work)}), encoding="utf-8")
    print("Prepared isolated workspace; no Azure or Terraform command executed")


class CommandFailure(RuntimeError):
    """Only fixed diagnostic metadata survives; command output/arguments are discarded."""
    def __init__(self, component, exit_code, category, code):
        super().__init__("Operation failed; raw output suppressed")
        self.component = component
        self.exit_code = exit_code
        self.category = category
        self.code = code


def command_failure(args, exit_code, raw=b""):
    # Match only known signatures. Never echo a captured substring or command argument.
    text = raw.decode("utf-8", errors="replace") if isinstance(raw, bytes) else str(raw)
    signatures = (
        (r"\bAADSTS700213\b", "AUTHENTICATION_ERROR", "AADSTS700213"),
        (r"\bAADSTS70021\b", "AUTHENTICATION_ERROR", "AADSTS70021"),
        (r"\bAuthenticationFailed\b|\bInvalidAuthenticationToken\b", "AUTHENTICATION_ERROR", "AuthenticationFailed"),
        (r"\bAuthorizationPermissionMismatch\b", "AUTHORIZATION_ERROR", "AuthorizationPermissionMismatch"),
        (r"\bAuthorizationFailure\b", "AUTHORIZATION_ERROR", "AuthorizationFailure"),
        (r"\bAuthorizationFailed\b", "AUTHORIZATION_ERROR", "AuthorizationFailed"),
        (r"\bLeaseAlreadyPresent\b|Error acquiring the state lock", "BACKEND_LOCK_ERROR", "STATE_LOCK"),
        (r"Failed to query available provider packages|Failed to install provider", "PROVIDER_ERROR", "PROVIDER_INSTALL"),
        (r"Unsupported argument|Missing required argument|Invalid value for", "CONFIGURATION_ERROR", "INVALID_CONFIGURATION"),
        (r"Connection refused|Name or service not known|no such host|Could not resolve host", "CONNECTIVITY_ERROR", "CONNECTION_FAILED"),
        (r"timed out|context deadline exceeded", "TIMEOUT", "TIMEOUT"),
    )
    category, code = "UNKNOWN_ERROR", "UNCLASSIFIED"
    for pattern, known_category, known_code in signatures:
        if re.search(pattern, text, re.IGNORECASE):
            category, code = known_category, known_code
            break
    executable = str(args[0]).replace("\\", "/").rsplit("/", 1)[-1].lower()
    component = "terraform" if executable in {"terraform", "terraform.exe"} else "azure-cli" if executable in {"az", "az.cmd", "az.exe"} else "subprocess"
    return CommandFailure(component, exit_code, category, code)


def run(args, *, cwd=None):
    try:
        result = subprocess.run(list(map(str, args)), cwd=cwd, capture_output=True, timeout=2700)
    except subprocess.TimeoutExpired:
        failure = command_failure(args, None)
        failure.category, failure.code = "TIMEOUT", "TIMEOUT"
        raise failure from None
    except OSError:
        failure = command_failure(args, None)
        failure.category, failure.code = "TOOL_ERROR", "EXECUTABLE_UNAVAILABLE"
        raise failure from None
    if result.returncode:
        raise command_failure(args, result.returncode, result.stderr + b"\n" + result.stdout) from None
    return result.stdout


def az(*args):
    binary = shutil.which("az") or shutil.which("az.cmd")
    if not binary:
        raise ValueError("Azure CLI is required; no installation attempted")
    return json.loads(run([binary, *args, "--only-show-errors", "--output", "json"]))


def validate_oidc(values, env=None):
    """Validate wiring only; federation and Blob RBAC require external verification."""
    env = os.environ if env is None else env
    if env.get("GITHUB_ACTIONS") != "true":
        return  # Human CLI recovery remains a separate, interactive procedure.
    required = {"ARM_USE_OIDC": "true", "ARM_USE_AZUREAD": "true", "ARM_USE_CLI": "false",
                "ARM_SUBSCRIPTION_ID": values["subscription_id"], "ARM_TENANT_ID": values["tenant_id"]}
    if any(env.get(k) != v for k, v in required.items()):
        raise ValueError("Explicit Terraform OIDC backend/provider configuration required")
    uuid.UUID(env.get("ARM_CLIENT_ID", ""))
    if env.get("ARM_CLIENT_ID") != env.get("WORDLE_APPROVED_CLIENT_ID"):
        raise ValueError("Federated client differs from approved environment identity")
    from urllib.parse import urlsplit
    endpoint = urlsplit(env.get("ACTIONS_ID_TOKEN_REQUEST_URL", ""))
    if (endpoint.scheme != "https" or not endpoint.hostname
            or not endpoint.hostname.endswith(".actions.githubusercontent.com")
            or endpoint.username or endpoint.password or endpoint.port not in (None, 443)
            or not env.get("ACTIONS_ID_TOKEN_REQUEST_TOKEN")):
        raise ValueError("GitHub runtime OIDC request environment unavailable")
    forbidden = ("ARM_CLIENT_SECRET", "ARM_CLIENT_SECRET_FILE_PATH", "ARM_ACCESS_KEY", "ARM_SAS_TOKEN",
                 "ARM_CLIENT_CERTIFICATE_PATH", "ARM_CLIENT_CERTIFICATE_PASSWORD", "ARM_OIDC_TOKEN",
                 "ARM_OIDC_TOKEN_FILE_PATH", "ARM_OIDC_REQUEST_URL", "ARM_OIDC_REQUEST_TOKEN")
    if any(env.get(k) for k in forbidden) or env.get("ARM_USE_MSI", "false").lower() != "false":
        raise ValueError("Persistent or alternative Terraform credentials forbidden in CI")


def authenticate(values):
    account = az("account", "show")
    if (account.get("id") != values["subscription_id"] or account.get("tenantId") != values["tenant_id"]
            or account.get("state") != "Enabled"):
        raise ValueError("Active subscription/tenant does not match the approved target; no context switched")


def inventory(values):
    ids = []
    for name in (values["resource_group_name"], values["node_resource_group_name"]):
        rows = az("resource", "list", "--resource-group", name, "--subscription", values["subscription_id"])
        ids.extend(r["id"].lower() for r in rows)
    return sorted(ids)  # Private review file only, never emitted to stdout.


def check_plan(plan, intent, values):
    for change in plan.get("resource_changes", []):
        if change.get("mode") == "data":
            continue
        if change["address"] not in ADDRESSES:
            raise ValueError("Plan contains an unexpected managed resource")
        actions = change["change"]["actions"]
        permitted = {"no-op", "delete"} if intent == "destroy" else {"no-op", "create", "update"}
        if not set(actions) <= permitted:
            raise ValueError("Unexpected replacement/deletion/creation in plan")
        side = change["change"].get("before" if intent == "destroy" else "after") or {}
        resource_group = side.get("resource_group_name")
        if resource_group and resource_group != values["resource_group_name"]:
            raise ValueError("Resource outside the dedicated resource group")
        resource_id = side.get("scope") or side.get("id")
        if resource_id and not resource_id.lower().startswith(("/subscriptions/" + values["subscription_id"] +
                "/resourcegroups/" + values["resource_group_name"]).lower()):
            raise ValueError("Resource outside the approved subscription/group")
        if change["address"] == "azurerm_resource_group.wordle" and side.get("name") != values["resource_group_name"]:
            raise ValueError("Wrong resource group in plan")
        if change["address"] == "azurerm_kubernetes_cluster.wordle":
            if side.get("name") != values["cluster_name"] or side.get("resource_group_name") != values["resource_group_name"]:
                raise ValueError("Wrong AKS target in plan")


def operate(action, work, confirmation, approved_sha=None, budget=False, inventory_sha=None, approval=""):
    work = external(work)
    marker = json.loads((work / "workspace.json").read_text())
    values = json.loads((work / "variables.tfvars.json").read_text())
    if marker["fingerprint"] != fingerprint(work):
        raise ValueError("Workspace configuration changed; prepare and review again")
    target = values["resource_group_name"] + "/" + values["cluster_name"]
    if confirmation != action.upper() + " " + target:
        raise ValueError("Explicit action and exact target confirmation required")
    binary = shutil.which("terraform")
    if not binary:
        raise ValueError("Native Terraform is unavailable; no installation attempted")
    validate_oidc(values)
    authenticate(values)
    def tf(*args):
        return run([binary, *args], cwd=work)
    plan_file = work / "approved.tfplan"
    if action in ("plan", "plan-destroy"):
        if plan_file.exists() or (work / "review.json").exists():
            raise ValueError("Existing plan must be preserved; use another prepared workspace")
        tf("init", "-input=false", "-backend-config=backend.hcl")
        # init may complete platform hashes in this private copy only.
        marker["fingerprint"] = fingerprint(work)
        (work / "workspace.json").write_text(json.dumps(marker))
        if tf("workspace", "show").strip() != b"default":
            raise ValueError("Unexpected Terraform workspace")
        args = ["plan", "-input=false", "-lock-timeout=60s", "-var-file=variables.tfvars.json", "-out=approved.tfplan"]
        intent = "destroy" if action == "plan-destroy" else "deploy"
        if intent == "destroy":
            args.append("-destroy")
        tf(*args)
        plan = json.loads(tf("show", "-json", "approved.tfplan"))
        check_plan(plan, intent, values)
        (work / "review.txt").write_bytes(tf("show", "-no-color", "approved.tfplan"))
        receipt = {"intent": intent, "plan_sha256": sha(plan_file.read_bytes()), "fingerprint": fingerprint(work)}
        if intent == "destroy":
            data = json.dumps(inventory(values), indent=2).encode()
            (work / "inventory.json").write_bytes(data)
            receipt["inventory_sha256"] = sha(data)
        (work / "review.json").write_text(json.dumps(receipt, indent=2))
        print("Private plan and review receipt created; no apply executed. Review files privately before approval")
    elif action == "execute":
        receipt = json.loads((work / "review.json").read_text())
        if not approved_sha or approved_sha != sha(plan_file.read_bytes()) or approved_sha != receipt["plan_sha256"]:
            raise ValueError("Explicit reviewed plan SHA-256 required")
        if receipt["fingerprint"] != fingerprint(work):
            raise ValueError("Plan configuration changed after review")
        plan = json.loads(tf("show", "-json", "approved.tfplan"))
        check_plan(plan, receipt["intent"], values)
        if receipt["intent"] == "destroy":
            current = sha(json.dumps(inventory(values), indent=2).encode())
            if inventory_sha != receipt.get("inventory_sha256") or current != inventory_sha:
                raise ValueError("Reviewed inventory missing or target resources changed")
            expected = "DESTROY " + target
        else:
            if not budget:
                raise ValueError("Explicit externally approved budget acknowledgement required")
            expected = "CREATE " + target
        # A second, intent-specific confirmation is supplied through a separate flag.
        if approval != expected:
            raise ValueError("Creation/destruction confirmation does not match the saved plan intent")
        tf("init", "-input=false", "-reconfigure", "-backend-config=backend.hcl")
        if tf("workspace", "show").strip() != b"default" or fingerprint(work) != receipt["fingerprint"]:
            raise ValueError("Backend/workspace or platform lock changed after review")
        tf("apply", "-input=false", "-lock-timeout=60s", "approved.tfplan")
        print("Reviewed saved plan executed; collect evidence and inspect residual costs separately")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "plan", "plan-destroy", "execute"))
    parser.add_argument("--workdir", type=Path, required=True)
    parser.add_argument("--variables", type=Path)
    parser.add_argument("--backend", type=Path)
    parser.add_argument("--confirm", default="")
    parser.add_argument("--approve-intent", default="")
    parser.add_argument("--plan-sha256")
    parser.add_argument("--inventory-sha256")
    parser.add_argument("--budget-approved", action="store_true")
    args = parser.parse_args()
    try:
        if args.action == "prepare":
            if not args.variables or not args.backend:
                parser.error("prepare requires external --variables and --backend JSON files")
            prepare(args.workdir, args.variables, args.backend)
        else:
            operate(args.action, args.workdir, args.confirm, args.plan_sha256, args.budget_approved, args.inventory_sha256, args.approve_intent)
    except Exception:
        parser.exit(1, "Operation refused or failed; inspect private inputs; no credentials or raw errors emitted.\n")


if __name__ == "__main__":
    main()
