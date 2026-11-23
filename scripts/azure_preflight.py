"""Read-only Azure readiness. Never logs in, registers providers or prints identifiers."""
import argparse
import fnmatch
import json
import os
import shutil
import subprocess
from pathlib import Path
import re

from azure_supervised import terraform_defaults


def query(az, *args):
    env = dict(os.environ, AZURE_CORE_COLLECT_TELEMETRY="no")
    try:
        result = subprocess.run([az, *args, "--only-show-errors", "--output", "json"],
                                capture_output=True, text=True, timeout=90, env=env)
        return json.loads(result.stdout) if result.returncode == 0 else None
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return None  # Raw CLI diagnostics may contain identifiers; never print them.


def local_assessment(check_ghcr=False, variables=None, backend=None):
    root=Path(__file__).resolve().parents[1]
    lock=json.loads((root/"k8s/aks-full/images.lock.json").read_text())
    values=(root/"infra/terraform/variables.tf").read_text(encoding="utf-8")
    module=(root/"infra/terraform/main.tf").read_text(encoding="utf-8")
    defaults=terraform_defaults()
    result={"immutable_images":all(re.search(r"@sha256:[0-9a-f]{64}$", r) for r in lock["images"].values()),
        "image_count":len(lock["images"]),"terraform_defaults":{"region":defaults["location"],"sku":defaults["node_vm_size"],"nodes":defaults["node_count"]},
        "terraform_default_values_present":all(defaults.get(k) is not None for k in ("location","node_vm_size","node_count")),
        "api_cidr_variable_present":"api_authorized_cidrs" in module,
        "remote_backend_declared":'backend "azurerm"' in (root/"infra/terraform/versions.tf").read_text(),
        "state_access_and_lock_tested":False,"budget_approved":False,
        "persistent_postgres":"one instance, managed-csi 8Gi; Azure CSI not exercised",
        "residual_costs":["VM/surge","OS and PostgreSQL disks","outbound Load Balancer/public IP","egress","remote state storage and retention"]}
    if variables:
        try:
            from azure_supervised import validate_inputs
            supplied=json.loads(Path(variables).read_text(encoding="utf-8"))
            coordinates=json.loads(Path(backend).read_text(encoding="utf-8")) if backend else {
                "resource_group_name":"rg-wordle-state-preflight","storage_account_name":"wordlepreflightstate",
                "container_name":"tfstate","key":"wordle/preflight.tfstate","use_azuread_auth":True}
            validate_inputs(supplied,coordinates)
            result["supplied_variables_valid"]=True
            result["supplied_backend_valid"]=bool(backend)
        except Exception:
            result["supplied_variables_valid"]=False
    else:
        result["supplied_variables_valid"]="not supplied"
    result["ghcr"]={}
    if check_ghcr:
        from ghcr_check import inspect
        for ref in lock["images"].values():
            if ref.startswith("ghcr.io/lromerob/wordle-"):
                try:
                    info=inspect(ref)
                    result["ghcr"][ref]={"revision_matches":info["revision"]==lock["source_commit"],"linux_amd64":True,"manifest_hash_verified":True}
                except Exception:
                    result["ghcr"][ref]={"verified":False,"reason":"Registry access or content check failed; no credential fallback"}
    return result


def assess(location=None, sku=None, nodes=None, *, offline=False, check_ghcr=False, variables=None, backend=None):
    defaults=terraform_defaults()
    location=defaults["location"] if location is None else location
    sku=defaults["node_vm_size"] if sku is None else sku
    nodes=defaults["node_count"] if nodes is None else nodes
    if variables:
        try:
            supplied=json.loads(Path(variables).read_text(encoding="utf-8"))
            location=supplied.get("location",location)
            sku=supplied.get("node_vm_size",sku)
            nodes=supplied.get("node_count",nodes)
        except Exception:
            pass  # Local validation reports malformed explicit input without printing it.
    az = shutil.which("az") or shutil.which("az.cmd")
    result = {"read_only": True, "location": location, "sku": sku, "nodes": nodes,
              "tools": {name: bool(shutil.which(name)) for name in ("terraform", "kubectl", "kubelogin")},
              "azure_cli": bool(az), "authenticated": False}
    result["local"] = local_assessment(check_ghcr, variables, backend)
    if result["local"].get("supplied_variables_valid") is False:
        result.update(authenticated=None,azure_checks="skipped invalid explicit variables")
        return result
    if offline:
        result.update(authenticated=None, azure_checks="skipped offline")
        return result
    if not az:
        return result
    account = query(az, "account", "show")
    if not account or not account.get("id"):
        return result
    result.update(authenticated=True, subscription_enabled=account.get("state") == "Enabled")
    if variables:
        try:
            selected=json.loads(Path(variables).read_text(encoding="utf-8"))
            result["selected_subscription_matches_variables"]=account["id"]==selected["subscription_id"] and account.get("tenantId")==selected["tenant_id"]
            if not result["selected_subscription_matches_variables"]:
                return result
        except Exception:
            result["selected_subscription_matches_variables"]=False
            return result
    subscription = account["id"]  # Used as command data, never emitted.
    providers = ("Microsoft.ContainerService", "Microsoft.Network", "Microsoft.Compute",
                 "Microsoft.ManagedIdentity", "Microsoft.Storage")
    result["providers"] = {}
    for provider in providers:
        value = query(az, "provider", "show", "--namespace", provider, "--subscription", subscription)
        result["providers"][provider] = value.get("registrationState", "unknown") if value else "unknown"
    permissions = query(az, "rest", "--method", "get", "--url",
        "https://management.azure.com/subscriptions/" + subscription +
        "/providers/Microsoft.Authorization/permissions?api-version=2022-04-01")
    required = ("Microsoft.ContainerService/managedClusters/write",
                "Microsoft.Network/virtualNetworks/write",
                "Microsoft.ManagedIdentity/userAssignedIdentities/write",
                "Microsoft.Authorization/roleAssignments/write")
    def allowed(action):
        if permissions is None:
            return "unknown"
        return any(any(fnmatch.fnmatchcase(action.lower(), a.lower()) for a in entry.get("actions", []))
                   and not any(fnmatch.fnmatchcase(action.lower(), a.lower()) for a in entry.get("notActions", []))
                   for entry in permissions.get("value", []))
    result["subscription_action_checks"] = {action: allowed(action) for action in required}
    result["rbac_limit"] = "Subscription action checks only; not proof of effective scoped/data-plane access or absence of deny assignments"
    sizes = query(az, "vm", "list-skus", "--location", location, "--size", sku,
                  "--all", "--resource-type", "virtualMachines", "--subscription", subscription)
    selected = next((s for s in sizes or [] if s.get("name") == sku), None)
    usage = query(az, "vm", "list-usage", "--location", location, "--subscription", subscription)
    family = (selected or {}).get("family", "standardDSv5Family" if sku == "Standard_D4s_v5" else "").lower()
    result["quotas"] = [{"name": v["name"]["value"], "used": v["currentValue"], "limit": v["limit"]}
        for v in usage or [] if v.get("name", {}).get("value", "").lower() in (family, "cores")]
    result["quota_query_succeeded"] = usage is not None
    if selected:
        capabilities = {c["name"]: c["value"] for c in selected.get("capabilities", [])}
        result["sku_readiness"] = {"listed": True, "vcpus": capabilities.get("vCPUs"),
            "memory_gb": capabilities.get("MemoryGB"), "architecture":capabilities.get("CpuArchitectureType","unknown"), "restriction_count": len(selected.get("restrictions", [])),
            "restrictions": [{"type":r.get("type"),"reason":r.get("reasonCode"),
                "locations":r.get("restrictionInfo",{}).get("locations",[]),"zones":r.get("restrictionInfo",{}).get("zones",[])}
                for r in selected.get("restrictions",[])]}
        result["nominal_vcpus"] = nodes * int(capabilities.get("vCPUs", "0"))
        result["quota_limit"] = "Allow extra capacity for upgrade surge; regional quota does not guarantee AKS SKU capacity"
    else:
        result["sku_readiness"] = {"listed": False, "status": "unknown or unavailable"}
    versions = query(az, "aks", "get-versions", "--location", location, "--subscription", subscription)
    rows = (versions or {}).get("values", (versions or {}).get("orchestrators", []))
    result["aks_versions"] = sorted({str(v.get("version", v.get("orchestratorVersion"))) for v in rows})
    result["entra_admin_group"] = "Owner must select an existing security group and verify membership; not inferred from CLI login"
    result["remote_state"] = "No approved backend coordinates supplied; access and blob lease not tested"
    result["budget"] = "Not approved; no quoted price or automatic spending cap"
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--location", help="Defaults to the Terraform location variable")
    parser.add_argument("--sku", help="Defaults to the Terraform node_vm_size variable")
    parser.add_argument("--nodes", type=int, help="Defaults to the Terraform node_count variable")
    parser.add_argument("--offline", action="store_true", help="Skip Azure entirely")
    parser.add_argument("--check-ghcr", action="store_true", help="Read and verify pinned public GHCR manifests")
    parser.add_argument("--variables", type=Path, help="Explicit private Terraform variables JSON")
    parser.add_argument("--backend", type=Path, help="Explicit secret-free backend coordinates JSON")
    args = parser.parse_args()
    result=assess(args.location, args.sku, args.nodes, offline=args.offline, check_ghcr=args.check_ghcr, variables=args.variables, backend=args.backend)
    print(json.dumps(result, indent=2))
    local=result["local"]
    if (local.get("supplied_variables_valid") is False or result.get("selected_subscription_matches_variables") is False
            or not local["immutable_images"] or any(v.get("verified") is False or v.get("revision_matches") is False for v in local["ghcr"].values())):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
