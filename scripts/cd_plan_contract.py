"""Versioned plan transport contract. No network, Terraform execution or implicit trust."""
from contextlib import closing, contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
import hashlib
import json
from pathlib import Path
import re
import sqlite3
from typing import Protocol
import uuid

REPOSITORY = "lromerob/wordle"
WORKFLOW = ".github/workflows/azure-demo.yml"
PRODUCER_WORKFLOWS = {WORKFLOW, ".github/workflows/azure-plan.yml"}
MAX_PLAN = 64 * 1024 * 1024
TRANSITIONS = {
    "CREATED": {"STORED", "EXPIRED", "REJECTED"},
    "STORED": {"PENDING_APPROVAL", "EXPIRED", "REJECTED"},
    "PENDING_APPROVAL": {"APPROVED", "EXPIRED", "REJECTED"},
    "APPROVED": {"CONSUMING", "EXPIRED", "REJECTED"},
    "CONSUMING": {"CONSUMED", "OUTCOME_UNKNOWN"},
    "OUTCOME_UNKNOWN": {"RECONCILIATION_REQUIRED"},
    "RECONCILIATION_REQUIRED": {"RECONCILED"},
    "RECONCILED": set(),
    "CONSUMED": set(), "EXPIRED": set(), "REJECTED": set(),
}
CONTEXT_KEYS = {"operation", "repository", "commit_sha", "environment", "terraform", "targets"}


class ContractError(ValueError):
    """Safe diagnostics deliberately exclude artifact contents."""


class RemoteTrustBlocked(ContractError):
    pass


def require(condition, message):
    if not condition:
        raise ContractError(message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
                      allow_nan=False).encode("ascii")


def decode(raw):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, "Duplicate JSON key")
            result[key] = value
        return result
    try:
        return json.loads(raw, object_pairs_hook=unique,
                          parse_constant=lambda _: (_ for _ in ()).throw(ContractError("Non-finite JSON")))
    except (UnicodeError, json.JSONDecodeError) as error:
        raise ContractError("Malformed JSON") from error


def keys(value, expected):
    require(isinstance(value, dict) and set(value) == set(expected), "Unexpected schema fields")


def matching(pattern, value):
    require(isinstance(value, str) and re.fullmatch(pattern, value) is not None, "Invalid identifier")


def sha256(value):
    matching(r"[a-f0-9]{64}", value)


def identifier(value):
    try:
        require(isinstance(value, str) and str(uuid.UUID(value)) == value, "Invalid UUID")
    except (ValueError, AttributeError) as error:
        raise ContractError("Invalid UUID") from error


def timestamp(value):
    matching(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", value)
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError as error:
        raise ContractError("Invalid timestamp") from error


def utc(value):
    require(isinstance(value, datetime) and value.tzinfo is not None, "Timezone required")
    return value.astimezone(timezone.utc)


def validate_manifest(m):
    keys(m, CONTEXT_KEYS | {"schema_version", "plan_id", "producer", "created_at", "expires_at", "plan"})
    require(type(m["schema_version"]) is int and m["schema_version"] == 1, "Unsupported schema")
    identifier(m["plan_id"])
    require(m["operation"] in {"create", "update", "destroy"}, "Invalid operation")
    require(m["repository"] == REPOSITORY, "Unauthorized repository")
    matching(r"[a-f0-9]{40}", m["commit_sha"])
    require(m["environment"] in {"wordle-azure-demo", "wordle-azure-infra"}, "Unauthorized environment")
    keys(m["producer"], {"workflow", "run_id", "attempt"})
    require(m["producer"]["workflow"] in PRODUCER_WORKFLOWS, "Unauthorized producer workflow")
    for key in ("run_id", "attempt"):
        matching(r"[1-9][0-9]*", m["producer"][key])
    start, end = timestamp(m["created_at"]), timestamp(m["expires_at"])
    require(timedelta(0) < end - start <= timedelta(hours=24), "Invalid expiry interval")
    keys(m["plan"], {"sha256", "size"})
    sha256(m["plan"]["sha256"])
    require(type(m["plan"]["size"]) is int and 0 < m["plan"]["size"] <= MAX_PLAN, "Invalid plan size")
    t = m["terraform"]
    keys(t, {"version", "provider", "lock_sha256", "backend", "configuration_sha256", "variables_sha256", "state"})
    matching(r"[0-9]+\.[0-9]+\.[0-9]+", t["version"])
    keys(t["provider"], {"source", "version"})
    require(t["provider"]["source"] == "hashicorp/azurerm", "Unauthorized provider")
    matching(r"[0-9]+\.[0-9]+\.[0-9]+", t["provider"]["version"])
    for key in ("lock_sha256", "configuration_sha256", "variables_sha256"):
        sha256(t[key])
    keys(t["backend"], {"type", "resource_group", "account", "container", "key", "workspace"})
    require(t["backend"]["type"] == "azurerm" and t["backend"]["account"] == "stwordletfgstate7c92d4"
            and t["backend"]["container"] == "tfstate" and t["backend"]["workspace"] == "default"
            and t["backend"]["resource_group"] == "rg-wordle-state", "Unauthorized backend")
    matching(r"wordle/[a-zA-Z0-9_./-]+\.tfstate", t["backend"]["key"])
    require(".." not in t["backend"]["key"].split("/"), "Invalid backend key")
    if t["state"] is not None:
        keys(t["state"], {"lineage", "serial", "sha256"})
        identifier(t["state"]["lineage"])
        require(type(t["state"]["serial"]) is int and t["state"]["serial"] >= 0, "Invalid state serial")
        sha256(t["state"]["sha256"])
    keys(m["targets"], {"subscription_id", "tenant_id", "resource_group", "node_resource_group", "cluster"})
    for key in ("subscription_id", "tenant_id"):
        identifier(m["targets"][key])
    for key in ("resource_group", "node_resource_group", "cluster"):
        matching(r"[a-zA-Z0-9_-]*wordle[a-zA-Z0-9_-]*", m["targets"][key])
    require(m["targets"]["resource_group"] != "rg-wordle-state"
            and m["targets"]["node_resource_group"] != "rg-wordle-state", "Backend lifecycle must be separate")
    return m


def build_manifest(plan, context, producer, created_at, expires_at, plan_id=None):
    keys(context, CONTEXT_KEYS)
    value = dict(context, schema_version=1, plan_id=plan_id or str(uuid.uuid4()), producer=producer,
                 created_at=created_at, expires_at=expires_at, plan={"sha256": digest(plan), "size": len(plan)})
    return validate_manifest(decode(canonical(value)))


@dataclass(frozen=True)
class Snapshot:
    manifest_raw: bytes
    plan: bytes
    manifest_sha256: str
    version: int
    state: str
    metadata_raw: bytes

    def manifest(self):
        require(len(self.manifest_raw) <= 65536 and digest(self.manifest_raw) == self.manifest_sha256,
                "Manifest integrity failed")
        m = validate_manifest(decode(self.manifest_raw))
        require(canonical(m) == self.manifest_raw, "Manifest must use canonical encoding")
        require(len(self.plan) == m["plan"]["size"] and digest(self.plan) == m["plan"]["sha256"],
                "Plan integrity failed")
        require(self.state in TRANSITIONS, "Invalid lifecycle state")
        return m


def approval_binding(snapshot, apply_run, attempt):
    matching(r"[1-9][0-9]*", apply_run)
    matching(r"[1-9][0-9]*", attempt)
    m = snapshot.manifest()
    return {"plan_id": m["plan_id"], "manifest_sha256": snapshot.manifest_sha256,
            "plan_sha256": m["plan"]["sha256"], "operation": m["operation"],
            "repository": m["repository"], "commit_sha": m["commit_sha"], "environment": m["environment"],
            "apply_workflow": WORKFLOW, "apply_run_id": apply_run, "apply_attempt": attempt}


class ArtifactStore(Protocol):
    """Future remote backend must provide atomic create and durable conditional transitions."""
    def create(self, manifest, plan): ...
    def get(self, plan_id): ...
    def transition(self, plan_id, version, state, metadata): ...
    def delete_terminal(self, plan_id, version, manifest_sha256): ...


class SqliteArtifactStore:
    """Local-only backend: transactions serialize independent local processes, not Azure runs."""
    def __init__(self, path):
        raw = Path(path).absolute()
        require(not any(p.is_symlink() or (hasattr(p, "is_junction") and p.is_junction())
                        for p in (raw, *raw.parents)), "Redirected store path forbidden")
        self.path = raw.resolve()
        root = Path(__file__).resolve().parents[1]
        require(root != self.path and root not in self.path.parents, "Store must be outside checkout")
        require(self.path.parent.is_dir() and not Path(path).is_symlink(), "Existing external parent required")
        with closing(self._connect()) as db:
            db.execute("CREATE TABLE IF NOT EXISTS tombstones (id TEXT PRIMARY KEY)")
            db.execute("CREATE TABLE IF NOT EXISTS bundles (id TEXT PRIMARY KEY, manifest BLOB NOT NULL, "
                       "plan BLOB NOT NULL, digest TEXT NOT NULL, revision INTEGER NOT NULL, state TEXT NOT NULL, metadata BLOB NOT NULL)")

    def _connect(self):
        db = sqlite3.connect(str(self.path), timeout=10, isolation_level=None)
        db.execute("PRAGMA synchronous=FULL")
        return db

    @contextmanager
    def _transaction(self):
        with closing(self._connect()) as db:
            db.execute("BEGIN IMMEDIATE")
            try:
                yield db
                db.execute("COMMIT")
            except BaseException:
                db.execute("ROLLBACK")
                raise

    def _insert(self, db, values):
        db.execute("INSERT INTO bundles VALUES (?,?,?,?,?,?,?)", values)

    def create(self, manifest, plan):
        validate_manifest(manifest)
        raw = canonical(manifest)
        snapshot = Snapshot(raw, plan, digest(raw), 1, "CREATED", b"{}")
        snapshot.manifest()
        try:
            with self._transaction() as db:
                require(db.execute("SELECT 1 FROM tombstones WHERE id=?", (manifest["plan_id"],)).fetchone() is None,
                        "Retired artifact identifier cannot be reused")
                self._insert(db, (manifest["plan_id"], raw, plan, digest(raw), 1, "CREATED", b"{}"))
        except sqlite3.IntegrityError as error:
            raise ContractError("Overwrite forbidden") from error
        return self.get(manifest["plan_id"])

    def get(self, plan_id):
        identifier(plan_id)
        with closing(self._connect()) as db:
            row = db.execute("SELECT manifest,plan,digest,revision,state,metadata FROM bundles WHERE id=?", (plan_id,)).fetchone()
        require(row is not None, "Artifact missing or incomplete")
        snapshot = Snapshot(*row)
        require(snapshot.manifest()["plan_id"] == plan_id, "Artifact identity mismatch")
        return snapshot

    def transition(self, plan_id, version, state, metadata):
        identifier(plan_id)
        with self._transaction() as db:
            row = db.execute("SELECT state,revision FROM bundles WHERE id=?", (plan_id,)).fetchone()
            require(row is not None and row[1] == version, "Concurrent modification")
            require(state in TRANSITIONS.get(row[0], set()), "Forbidden state transition")
            result = db.execute("UPDATE bundles SET state=?,revision=revision+1,metadata=? WHERE id=? AND revision=?",
                                (state, canonical(metadata), plan_id, version))
            require(result.rowcount == 1, "Concurrent modification")
        return self.get(plan_id)

    def delete_terminal(self, plan_id, version, manifest_sha256):
        with self._transaction() as db:
            row = db.execute("SELECT state,revision,digest FROM bundles WHERE id=?", (plan_id,)).fetchone()
            require(row is not None and row[0] in {"CONSUMED", "REJECTED", "EXPIRED"}
                    and row[1] == version and row[2] == manifest_sha256, "Deletion ticket no longer valid")
            db.execute("INSERT INTO tombstones VALUES (?)", (plan_id,))
            db.execute("DELETE FROM bundles WHERE id=?", (plan_id,))


class TrustSource(Protocol):
    """Must query independent, authoritative provenance and human approval; never bundle JSON alone."""
    def origin(self, manifest_sha256): ...
    def approval(self, reference): ...


class ReconciliationAuthority(Protocol):
    """Independent human decision verifier; never a producer-controlled recovery JSON file."""
    def decision(self, reference): ...


class UnavailableTrustSource:
    def origin(self, manifest_sha256):
        raise RemoteTrustBlocked("Independent producer provenance not verified")

    def approval(self, reference):
        raise RemoteTrustBlocked("Independent human approval not verified")


class PlanContract:
    def __init__(self, store: ArtifactStore, trust=None, approvers=("lromerob",)):
        self.store = store
        self.trust = trust if trust is not None else UnavailableTrustSource()
        self.approvers = frozenset(approvers)

    def publish(self, manifest, plan):
        self.store.create(manifest, plan)
        return self.recover_staged(manifest["plan_id"])

    def recover_staged(self, plan_id):
        snapshot = self.store.get(plan_id)
        if snapshot.state == "CREATED":
            snapshot = self.store.transition(plan_id, snapshot.version, "STORED", {})
        if snapshot.state == "STORED":
            snapshot = self.store.transition(plan_id, snapshot.version, "PENDING_APPROVAL", {})
        require(snapshot.state == "PENDING_APPROVAL", "Only complete staged artifacts can be recovered")
        return snapshot

    def validate(self, plan_id, expected, now):
        snapshot = self.store.get(plan_id)
        m = snapshot.manifest()
        keys(expected, CONTEXT_KEYS)
        require({k: m[k] for k in CONTEXT_KEYS} == expected, "Execution context differs from reviewed context")
        require(m["terraform"]["state"] is not None, "Observed state fingerprint unavailable")
        require(timestamp(m["created_at"]) <= utc(now) < timestamp(m["expires_at"]), "Artifact expired or not yet valid")
        return snapshot

    def _binding(self, snapshot, apply_run, attempt):
        return approval_binding(snapshot, apply_run, attempt)

    def _verify_trust(self, snapshot, reference, apply_run, attempt, now):
        m = snapshot.manifest()
        origin = self.trust.origin(snapshot.manifest_sha256)
        require(origin == {"manifest_sha256": snapshot.manifest_sha256, "repository": m["repository"],
                           "commit_sha": m["commit_sha"], "producer": m["producer"]}, "Producer provenance mismatch")
        approval = self.trust.approval(reference)
        keys(approval, {"reference", "binding", "approver", "approved_at"})
        require(approval["reference"] == reference and approval["binding"] == self._binding(snapshot, apply_run, attempt),
                "Independent approval is not bound to this exact execution")
        require(approval["approver"] in self.approvers, "Approver not authorized")
        require(timestamp(m["created_at"]) <= timestamp(approval["approved_at"]) <= utc(now), "Invalid approval time")
        return approval

    def approve(self, plan_id, expected, reference, apply_run, attempt, now):
        snapshot = self.validate(plan_id, expected, now)
        require(snapshot.state == "PENDING_APPROVAL", "Artifact is not pending approval")
        approval = self._verify_trust(snapshot, reference, apply_run, attempt, now)
        return self.store.transition(plan_id, snapshot.version, "APPROVED", {"approval": approval})

    def begin(self, plan_id, expected, apply_run, attempt, now):
        snapshot = self.validate(plan_id, expected, now)
        require(snapshot.state == "APPROVED", "Artifact cannot be consumed")
        receipt = decode(snapshot.metadata_raw)
        approval = receipt["approval"]
        require(self._verify_trust(snapshot, approval["reference"], apply_run, attempt, now) == approval,
                "Approval changed after review")
        receipt.update(consumer=str(uuid.uuid4()), apply_run_id=apply_run, apply_attempt=attempt,
                       claimed_at=utc(now).strftime("%Y-%m-%dT%H:%M:%SZ"))
        claimed = self.store.transition(plan_id, snapshot.version, "CONSUMING", receipt)
        # Returned immutable bytes are the bytes validated above, not a later path read.
        require(claimed.manifest_sha256 == snapshot.manifest_sha256 and claimed.plan == snapshot.plan
                and claimed.state == "CONSUMING" and decode(claimed.metadata_raw).get("consumer") == receipt["consumer"],
                "Artifact or consumption right changed during claim")
        return claimed

    def finish(self, plan_id, consumer, success, now):
        require(type(success) is bool, "Explicit boolean result required")
        snapshot = self.store.get(plan_id)
        require(snapshot.state == "CONSUMING", "No active consumption")
        receipt = decode(snapshot.metadata_raw)
        require(receipt.get("consumer") == consumer, "Consumer mismatch")
        expired = utc(now) >= timestamp(snapshot.manifest()["expires_at"])
        if not success or expired:
            result = self.mark_unknown(plan_id, consumer,
                "expired_during_consumption" if expired else "partial_failure", now)
            require(not expired, "Artifact expired during consumption; reconciliation required")
            return result
        receipt.update(result="success")
        return self.store.transition(plan_id, snapshot.version, "CONSUMED", receipt)

    def mark_unknown(self, plan_id, consumer, reason, now):
        require(reason in {"runner_lost_before_apply", "runner_lost_during_apply", "receipt_write_failed",
                           "partial_failure", "expired_during_consumption", "interrupted_unknown_outcome"},
                "Invalid uncertainty reason")
        snapshot = self.store.get(plan_id)
        require(snapshot.state == "CONSUMING", "No active consumption")
        receipt = decode(snapshot.metadata_raw)
        require(receipt.get("consumer") == consumer, "Consumer mismatch")
        require(utc(now) >= timestamp(receipt["claimed_at"]), "Invalid uncertainty time")
        receipt.update(result=reason, unknown_at=utc(now).strftime("%Y-%m-%dT%H:%M:%SZ"),
                       recovery={"required": ["no_active_operation", "terraform_state", "azure_resources", "human_review"],
                                 "next_action": "reconcile_then_new_plan", "replay_allowed": False})
        return self.store.transition(plan_id, snapshot.version, "OUTCOME_UNKNOWN", receipt)

    def require_reconciliation(self, plan_id):
        snapshot = self.store.get(plan_id)
        require(snapshot.state == "OUTCOME_UNKNOWN", "Outcome is not uncertain")
        return self.store.transition(plan_id, snapshot.version, "RECONCILIATION_REQUIRED", decode(snapshot.metadata_raw))

    def reconcile(self, plan_id, reference, authority: ReconciliationAuthority, now):
        # The authority must independently verify a human decision; receipt JSON alone is insufficient.
        require(authority is not None, "Independent reconciliation authority unavailable")
        matching(r"[A-Za-z0-9_-]{1,128}", reference)
        snapshot = self.store.get(plan_id)
        require(snapshot.state == "RECONCILIATION_REQUIRED", "Reconciliation not requested")
        receipt = decode(snapshot.metadata_raw)
        decision = authority.decision(reference)
        keys(decision, {"reference", "plan_id", "consumer", "reviewer", "reviewed_at", "checks", "evidence"})
        require(decision["reference"] == reference and decision["plan_id"] == plan_id
                and decision["consumer"] == receipt["consumer"] and decision["reviewer"] in self.approvers,
                "Reconciliation identity mismatch")
        keys(decision["checks"], {"no_active_operation", "terraform_state", "azure_resources", "new_plan_required"})
        require(all(value is True for value in decision["checks"].values()), "Reconciliation incomplete")
        keys(decision["evidence"], {"operation", "state", "resources"})
        for value in decision["evidence"].values():
            sha256(value)
        require(timestamp(receipt["unknown_at"]) <= timestamp(decision["reviewed_at"]) <= utc(now),
                "Invalid reconciliation time")
        receipt["reconciliation"] = decision
        return self.store.transition(plan_id, snapshot.version, "RECONCILED", receipt)

    def reject(self, plan_id, reason):
        require(reason in {"operator_rejected", "interrupted_unknown_outcome", "integrity_incident"}, "Invalid rejection reason")
        snapshot = self.store.get(plan_id)
        require(snapshot.state != "CONSUMING", "Consumption requires explicit uncertainty recording")
        receipt = decode(snapshot.metadata_raw)
        receipt["result"] = reason
        return self.store.transition(plan_id, snapshot.version, "REJECTED", receipt)

    def expire(self, plan_id, now):
        snapshot = self.store.get(plan_id)
        require(utc(now) >= timestamp(snapshot.manifest()["expires_at"]), "Artifact has not expired")
        return self.store.transition(plan_id, snapshot.version, "EXPIRED", decode(snapshot.metadata_raw))

    def deletion_ticket(self, plan_id, now, retain_until):
        snapshot = self.store.get(plan_id)
        require(snapshot.state in {"CONSUMED", "REJECTED", "EXPIRED"} and utc(now) >= utc(retain_until)
                and utc(retain_until) >= timestamp(snapshot.manifest()["created_at"]), "Retention or lifecycle blocks deletion")
        return {"plan_id": plan_id, "version": snapshot.version, "manifest_sha256": snapshot.manifest_sha256}
