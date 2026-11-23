# Local academic evidence capture

This helper reuses the existing disposable-kind observability/Blue-Green runner.
The local entry points never target AKS or existing PG-05/PG-06 installations.

Prerequisites: Docker Linux engine, kind, kubectl, Python with the existing backend
dependencies, Node, Microsoft Edge and Playwright already available in the tools
runtime. No frontend dependency is added. Set WORDLE_PLAYWRIGHT_ROOT to an existing
node_modules directory if the runtime is elsewhere; no package installation is automatic.

Use a new lowercase run ID each time. Never rerun a completed ID or overwrite evidence.

From the Wordle repository in PowerShell:

~~~powershell
$run = 'YYYYMMDD-capture-unique'
node scripts/evidence/capture.cjs --smoke "docs/evidence/local/$run/results/tooling"
.venv/Scripts/python.exe -B scripts/evidence/run_local.py $run
.venv/Scripts/python.exe -B scripts/evidence/run_persistence.py $run
.venv/Scripts/python.exe -B scripts/evidence/finalize.py $run
~~~

The smoke page is a tool diagnostic, never a simulated Wordle evidence.
The integrated runner creates its own kind cluster and synthetic credentials, builds
local runtimes and uses a shared real PostgreSQL. It always removes its own cluster
and forwards. Browser contexts are isolated, closed in finally and have no saved profile.
Only this test's PostgreSQL pod is replaced to verify persistence; restoration uses
the existing independent FIN-02B test.

Original integrated JSON is retained durably outside Git:
%LOCALAPPDATA%/WordleTFG/evidence/<run>/integrated/.
The dossier docs/evidence/local/<run>/ contains genuine PNGs, capture assertions,
whitelisted Kubernetes metadata, original JSON copies or clearly marked sanitized
derivatives, a manifest and SHA-256 inventory. No Secret, kubeconfig, DSN, password,
Terraform state or browser storageState is exported. Private credentials pass via stdin
or process environment only. Local image references/runtime imageIDs are recorded:
they are not labelled as registry digests without verification.

A capture error is recorded independently of the existing technical assertions.
Inspect all failure JSON and capture_failed events: integrated PASS alone does not
mean all screenshots passed. The final report must mark missing scenarios PARTIAL.
Do not generate a manifest until all intended results for that ID are present.
Finalize refuses overwriting an existing manifest.

For future AKS use, the browser helper accepts loopback-forward ports and reuses
the same UI/observability assertions. The current hook deliberately rejects non-kind
contexts. Supporting an explicitly approved AKS context requires a separate guarded
adapter; never bypass that guard or run the disposable-kind runner against AKS.

These are real browser actions and SQL/HTTP checks, not intercepted/mock API results.
Blue/Green currently distinguish configuration releases of the same application code.
The existing rollback recovers Green after deliberately promoting a faulty Blue:
do not relabel it as recovery of Blue. Screenshots do not prove zero downtime.
Observability data is ephemeral; the original JSON and PNG exports must survive cleanup.

Historical JPG originals and PNG derivatives are separate provenance records. A PNG
derivative of an old JPEG is not a fresh execution and must retain its original context.
Before publishing any dossier, review every image and JSON for secrets and legibility.
No git add/commit/push or Azure/GHCR operation is performed by these helpers.


## Explicit AKS adapter

`aks_capture.py` reuses `capture.cjs`; it does not invoke the mutating kind hook.
Use the [release and capture runbook](../../docs/operations/release-gates.md#aks-visual-evidence).
The strict `hook.py` kind guard remains unchanged. AKS mode is screenshot-only:
SQL writes, pod replacement and selector changes remain in separately authorized
executors. Supply an existing Node/Playwright installation and browser executable
or channel explicitly; Linux requires no Windows paths or automatic installation.
Verified private exports identify `azure-aks`, release SHA, image identities and
checksums, and must be preserved before a separately authorized teardown.
No AKS capture has been executed during local preparation.
