"""Explicit operational recovery roots, distinct from full Git application sources."""
import ast
from pathlib import Path
import re

REQUIRED = (
    ".github/workflows/azure-demo.yml", "scripts/azure_release.py", "scripts/azure_dispatch.py",
    "scripts/azure_supervised.py", "scripts/azure_preflight.py", "scripts/ghcr_check.py",
    "scripts/aks_run.py", "scripts/aks_recovery.py", "scripts/configure_demo_secrets.py",
    "scripts/release_gate.py", "scripts/private_store.py", "scripts/operational_contract.py",
    "scripts/evidence/aks_capture.py", "scripts/evidence/capture.cjs", "scripts/evidence/capture_policy.cjs",
    "scripts/evidence/test_capture_policy.cjs",
    "scripts/evidence/hook.py", "scripts/evidence/finalize.py", "scripts/evidence/README.md",
    "scripts/evidence/run_local.py", "scripts/evidence/run_persistence.py",
    "infra/scripts/Invoke-AksEmergencyTeardown.ps1", "infra/scripts/Test-AksEmergencyTeardown.ps1",
    "infra/scripts/Test-AksEmergencyAzureResolution.ps1", "infra/terraform/emergency-target.example.json",
    "infra/terraform/azure-variables.example.json", "infra/terraform/azure-backend.example.json",
    "k8s/aks-full/kustomization.yaml", "k8s/aks-full/images.lock.json", "k8s/aks-restore/kustomization.yaml",
    "docs/operations/FIN-AKS-DEPLOYMENT-RUNBOOK.md", "docs/operations/FIN-AKS-EMERGENCY-TEARDOWN.md",
    "docs/operations/FIN-AKS-FRIDAY-DEPLOYMENT-CHECKLIST.md",
    "docs/operations/azure-demo.md", "docs/operations/release-gates.md",
    # Windows-supervised storage now relies on this host/container procedure.
    "docker/runner/Dockerfile", "docker/runner/.dockerignore", "docker/runner/compose.yaml",
    "docker/runner/install_tools.py", "docker/runner/entrypoint.py", "docker/runner/runner.env.example",
    "docker/runner/Invoke-WordleRunner.ps1", "docker/runner/Test-WordlePrivateStore.ps1",
    "docker/runner/Test-WordleSupervisedStore.ps1", "docker/runner/test_runner.py",
    "docker/runner/test_private_store.py", "docker/runner/test_windows_store.py",
    "docker/runner/validate_persistence.py",
    "docs/operations/wordle-docker-runner.md",
    "scripts/test_release_gate.py", "scripts/test_aks_capture.py", "scripts/test_aks_run.py", "scripts/test_azure_readiness.py")


def verify_references(root, paths):
    """No imports executed. Check required roots, local Python imports and literal paths."""
    paths = set(paths)
    if not set(REQUIRED) <= paths:
        raise ValueError("Missing required operational source in recovery package")
    for name in paths:
        p = root / name
        if not p.is_file() or p.is_symlink():
            raise ValueError("Missing/linked operational source: " + name)
    modules = {}
    for scope in ("scripts", "k8s"):
        for p in (root / scope).rglob("*.py"):
            if not any(x in p.parts for x in ("__pycache__", ".venv", "node_modules")):
                modules.setdefault(p.stem, []).append(p.relative_to(root).as_posix())
    for name in paths:
        file = root / name
        if file.suffix == ".py":
            tree = ast.parse(file.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                imports = ([node.module.split(".")[0]] if isinstance(node, ast.ImportFrom) and node.module
                           else [x.name.split(".")[0] for x in node.names] if isinstance(node, ast.Import) else [])
                for module in imports:
                    candidates = modules.get(module, [])
                    if candidates and not any(p in paths for p in candidates):
                        raise ValueError("Local import absent from recovery package: " + module)
                if isinstance(node, ast.Constant) and isinstance(node.value, str):
                    value = node.value
                    if re.fullmatch(r"(?:scripts|k8s|infra|docker|supabase)/[A-Za-z0-9_./-]+", value):
                        target = root / value
                        if not target.exists():
                            raise ValueError("Operational reference is absent: " + value)
                        if target.is_file() and value not in paths:
                            raise ValueError("Referenced file is outside recovery package: " + value)
        if file.suffix == ".cjs":
            for relative in re.findall(r"require\(['\"](\./[^'\"]+)['\"]\)", file.read_text(encoding="utf-8")):
                dependency = file.parent / relative
                if not dependency.suffix: dependency = dependency.with_suffix(".cjs")
                if not dependency.is_file() or dependency.relative_to(root).as_posix() not in paths:
                    raise ValueError("Local JavaScript dependency absent from recovery package")
    # Local Kustomize resources and generator files must be present in this kit.
    for name in paths:
        if Path(name).name != "kustomization.yaml":
            continue
        for line in (root / name).read_text(encoding="utf-8").splitlines():
            match = re.match(r"\s*(?:-\s+|path:\s+)(?:[A-Za-z0-9_.-]+=)?([A-Za-z0-9_./-]+)\s*$", line)
            if match and not match[1].startswith("/") and (match[1].startswith(".") or "/" in match[1] or match[1].endswith((".yaml", ".sql", ".conf"))):
                target = (root / name).parent / match[1]
                if not target.exists():
                    raise ValueError("Missing Kustomize reference")
                if target.is_file() and target.resolve().relative_to(root.resolve()).as_posix() not in paths:
                    raise ValueError("Kustomize file absent from recovery package")
