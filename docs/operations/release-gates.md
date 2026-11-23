# Release gates and private custody

This is a preparation contract, not evidence of a configured Azure federation or a live deployment.

## Release and CI

`azure-demo.yml` remains manual, serialized, restricted to `lromerob/wordle` and
`codex/pg01-07-consolidation`, and protected by `wordle-azure-demo` reviewers.
Supply `ci_run` for the exact checked-out release SHA. The seven named CI jobs
must be completed/success in the same run attempt; missing/skipped jobs, partial
API results, permission failures and mismatched repository/branch/SHA fail closed.
`GITHUB_TOKEN` needs Actions read, never a PAT. Image pulls use the public registry.

The source SHA in `images.lock.json` identifies application images, not necessarily
the later operational release commit. Reusing those images requires identical Git
trees for both complete Docker contexts (`backend` and `frontend`), verified OCI
revision and pinned registry digests. Any application change requires new images
and a reviewed lock. The selected release SHA, CI run/attempt, application SHA,
registry identities and operational file hashes form a private immutable receipt.
Every dispatch rechecks its receipt and source files. A later plan execution must
use the same CI run/attempt, release ID, source SHA and store ID as the reviewed plan.
A CI rerun changes this identity and requires preparing/reviewing a new plan.

## Operator-provisioned durable private store

Before enabling CD, provision an **existing external durable mount**, independent
of source checkout and runner lifetime. Same runner labels do not imply same disk.
No storage is provisioned by these scripts. Owner must approve access controls,
encryption, backup/retention, restore testing and single-writer custody. A marker
is an explicit operator acknowledgment, not a technical proof of physical durability.

Create privately (never in Git) `.wordle-private-store.json` containing:

```json
{"format":1,"repository":"lromerob/wordle","store_id":"REPLACE_WITH_APPROVED_STORE_UUID","durable_acknowledged":true}
```

Precreate `plans/`, `selections/`, `evidence/`, `backups/`; on Linux use owner-only
permissions for root, marker and these directories. Do not use symlinks. Put the
reviewed `variables.json`, secret-free `backend.json`, and later user kubeconfig
here. Configure protected `WORDLE_AZURE_PRIVATE_DIR` and `WORDLE_AZURE_STORE_ID`.
Missing mount/marker/ID/directories causes refusal before Azure login. Guard the
entire mount against modification by untrusted users; plan/selection hashes alone
cannot protect against a compromised runner. Plans, source.json, reviews,
fingerprints, inventories, kubeconfig and backups stay private; never upload them
to public artifacts. Keep them across plan and execute runs, and preserve failed
exports for diagnosis. No cleanup is automatic.

## Terraform federation

The workflow explicitly supplies `ARM_USE_OIDC=true`, `ARM_USE_AZUREAD=true`,
`ARM_USE_CLI=false`, client/tenant/subscription IDs and the approved client ID.
GitHub's ephemeral `ACTIONS_ID_TOKEN_REQUEST_URL/TOKEN` remain in process memory.
No token is written into HCL, plans, receipts or logs. Runtime validation checks
identity consistency and rejects client secrets, Storage keys/SAS, certificate or
persisted OIDC tokens and alternative identity sources. `azure/login` is still
needed for explicit CLI context operations; its session is not proof of provider
or backend authentication. Human CLI recovery remains separate.

Terraform 1.9.8 backend supports the GitHub OIDC request variables and Entra Blob
authentication: [pinned backend implementation](https://github.com/hashicorp/terraform/blob/v1.9.8/internal/backend/remote-state/azure/backend.go).
AzureRM 4.50.0 supports service-principal OIDC:
[pinned provider guide](https://github.com/hashicorp/terraform-provider-azurerm/blob/v4.50.0/website/docs/guides/service_principal_oidc.html.markdown).

**PENDING EXTERNAL VERIFICATION:** issuer/audience and exact protected-environment
subject, federated client ownership, tenant/subscription match, ARM permissions
(including the existing subnet role assignment), separate Blob data-plane roles
at the independent state storage, firewalls and runner reachability. No broad
RBAC is prescribed or granted here. Both backend and provider must be tested with
the real federated identity in a separately authorized window. Versions must be
preinstalled on the runner, not downloaded by this procedure.

## Human emergency recovery (independent of CD)

Use an external copy of `infra/terraform/emergency-target.example.json`, fill all
placeholders with the previously approved installation and human operator UUIDs.
Keep this file private; no existing private configuration is overwritten. Prepare
an external Terraform working copy with the reviewed sources/lock and the already
initialized, independently verified Entra/CLI backend. Do not use the pipeline's
OIDC backend cache as the human emergency cache.

```powershell
& ./infra/scripts/Invoke-AksEmergencyTeardown.ps1 -Preflight -TargetFile $privateTarget -WorkDirectory $privateWork -TerraformPath $terraform
# Only with separate owner authorization:
& ./infra/scripts/Invoke-AksEmergencyTeardown.ps1 -Teardown -TargetFile $privateTarget -WorkDirectory $privateWork -VariablesFile $privateVariables -TerraformPath $terraform
```

The script checks the exact human account/tenant/subscription, target resource
IDs, independent state backend/lease, plan hash, input fingerprint (including the
target file), inventory/ETag and concurrent Terraform process. It still requires
`PLAN WORDLE AKS` then `DESTRUIR WORDLE AKS`; no auto-login, context switch,
force-unlock or resource-group-delete fallback. Original behavior of deleting only
its newly created emergency plan on completion is retained; sanitized audit stays
in the user's private emergency directory. Pipeline plans remain in the durable
store. Incomplete ARM cleanup/MFA/locks require stopping and reviewing, not blind retries.

## AKS visual evidence

Use the same authorized checkout/receipt and private mounted store on a configured
capture host (Linux or Windows). Preinstall Node, Playwright and a browser; set
`WORDLE_PLAYWRIGHT_ROOT` and either `WORDLE_BROWSER_EXECUTABLE` or
`WORDLE_BROWSER_CHANNEL`. No downloads or public exposure are required.

```text
python -B scripts/evidence/aks_capture.py --subscription <approved UUID> --group <approved RG> --cluster <approved cluster> --context wordle-azure-supervised --confirm "CAPTURE <RG>/<cluster>" --export-id <unique-id> --stage stable-blue
```

For automated snapshots at the correct phase, select `capture=true` only with
an already separately authorized `acceptance` workflow operation (or pass
`--capture` to `aks_run.py acceptance`). The executor invokes read-only hooks
at stable Blue, promoted Green, recovered Green and existing validated signals.
The capture adapter ignores any executor-owned ports and opens/closes its own.
Without the flag, acceptance behavior is unchanged. No capture request alone
authorizes acceptance or any fault injection.

Other read-only stages: `promoted-green`, `rollback-green`, `signals` (the latter
needs an existing trace ID via `--trace-id` and ephemeral Grafana password in the
existing environment variable). Run stages only after the separately authorized
executor has performed promotion/rollback/validation. A screenshot never performs
SQL, pod deletion, promotion, rollback, restore or alert injection. It proves visual
observation, not functional acceptance of those operations. The unchanged local
`hook.py` continues to require its isolated kind context.

AKS identity/FQDN, target/context, two namespaces, registry/runtime identities,
owned loopback ports and navigation allowlist are checked. Only this invocation's
port-forwards are stopped. Originals, PNG hashes and an Azure-specific manifest
are written under private `evidence/<unique-id>/` and verified in
`evidence/<unique-id>.tar` **before teardown**. Existing files are never overwritten.
Export failure is a failed capture, not PASS. Do not destroy infrastructure until
an owner has verified the external archive and reviewed screenshots for accidental
sensitive content. Publishing sanitized derivatives is a separate review.

## Operational recovery kit

`azure_release.py` produces an operational recovery kit, **not** a complete
application source bundle or an academic submission. Its reference checker fails
on absent local dependencies. Recover full application sources separately from
the verified Git release SHA; the lock records the image source revision. Private
inputs, initialized state, tools and evidence originals are never packaged. A local
kit containing pending files is explicitly not reproducible from HEAD alone.
