"""Synthetic, offline tests. FixtureAuthority is NOT a GitHub approval implementation."""
from contextlib import closing
from copy import deepcopy
from datetime import datetime, timezone, timedelta
import json
import multiprocessing
from pathlib import Path
import sqlite3
import socket
import tempfile
import unittest
from unittest.mock import patch

from cd_plan_contract import (ArtifactStore, ContractError, PlanContract, RemoteTrustBlocked,
                              SqliteArtifactStore, build_manifest, canonical, decode, digest)

NOW = datetime(2026, 11, 23, 12, 5, tzinfo=timezone.utc)
PLAN = b"SYNTHETIC_NOT_A_REAL_TERRAFORM_PLAN\x00\x01"


def context():
    return {"operation": "create", "repository": "lromerob/wordle", "commit_sha": "a" * 40,
            "environment": "wordle-azure-infra", "terraform": {
                "version": "1.9.8", "provider": {"source": "hashicorp/azurerm", "version": "4.50.0"},
                "lock_sha256": "b" * 64, "configuration_sha256": "c" * 64, "variables_sha256": "d" * 64,
                "backend": {"type": "azurerm", "resource_group": "rg-wordle-state",
                            "account": "stwordletfgstate7c92d4", "container": "tfstate",
                            "key": "wordle/aks-demo.tfstate", "workspace": "default"},
                "state": {"lineage": "11111111-1111-4111-8111-111111111111", "serial": 3, "sha256": "e" * 64}},
            "targets": {"subscription_id": "22222222-2222-4222-8222-222222222222",
                        "tenant_id": "33333333-3333-4333-8333-333333333333", "resource_group": "rg-wordle-demo",
                        "node_resource_group": "rg-wordle-demo-nodes", "cluster": "aks-wordle-demo"}}


class FixtureAuthority:
    """Separate test-owned records, never loaded from the artifact metadata."""
    def __init__(self):
        self.origins = {}
        self.approvals = {}

    def origin(self, key):
        if key not in self.origins:
            raise RemoteTrustBlocked("No independently verified fixture provenance")
        return deepcopy(self.origins[key])

    def approval(self, reference):
        if reference not in self.approvals:
            raise RemoteTrustBlocked("No independent fixture approval")
        return deepcopy(self.approvals[reference])


def authorize(contract, authority, snapshot):
    m = snapshot.manifest()
    authority.origins[snapshot.manifest_sha256] = {"manifest_sha256": snapshot.manifest_sha256,
        "repository": m["repository"], "commit_sha": m["commit_sha"], "producer": m["producer"]}
    authority.approvals["fixture-review-1"] = {"reference": "fixture-review-1",
        "binding": contract._binding(snapshot, "200", "1"), "approver": "lromerob",
        "approved_at": "2026-11-23T12:01:00Z"}


def consumer_worker(path, expected, authority, plan_id, start, output):
    try:
        service = PlanContract(SqliteArtifactStore(path), authority)
        start.wait(10)
        service.begin(plan_id, expected, "200", "1", NOW)
        output.put("claimed")
    except ContractError:
        output.put("denied")
    except Exception as error:
        output.put(type(error).__name__)


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="wordle-plan-contract-")
        self.addCleanup(self.tmp.cleanup)
        # Any accidental network call fails the test, including a new trust implementation.
        self.guard = patch.object(socket.socket, "connect", side_effect=AssertionError("Network forbidden"))
        self.guard.start()
        self.addCleanup(self.guard.stop)
        self.path = Path(self.tmp.name) / "private.sqlite"
        self.store = SqliteArtifactStore(self.path)
        self.authority = FixtureAuthority()
        self.service = PlanContract(self.store, self.authority)
        self.expected = context()
        self.manifest = build_manifest(PLAN, self.expected,
            {"workflow": ".github/workflows/azure-demo.yml", "run_id": "100", "attempt": "1"},
            "2026-11-23T12:00:00Z", "2026-11-23T13:00:00Z")
        self.id = self.manifest["plan_id"]
        self.snapshot = self.service.publish(self.manifest, PLAN)
        authorize(self.service, self.authority, self.snapshot)

    def approve(self):
        return self.service.approve(self.id, self.expected, "fixture-review-1", "200", "1", NOW)

    def begin(self):
        self.approve()
        return self.service.begin(self.id, self.expected, "200", "1", NOW)

    def sql(self, statement, values):
        with closing(sqlite3.connect(self.path)) as db:
            with db:
                db.execute(statement, values)

    def test_valid_contract_and_canonical_digest(self):
        self.assertEqual(self.snapshot.manifest_sha256, digest(canonical(self.manifest)))
        self.assertEqual(self.snapshot.state, "PENDING_APPROVAL")
        self.assertEqual(self.snapshot.manifest()["terraform"]["provider"]["version"], "4.50.0")

    def test_round_trip_independent_store_instance(self):
        got = SqliteArtifactStore(self.path).get(self.id)
        self.assertEqual(got.plan, PLAN)
        self.assertEqual(got.manifest_raw, canonical(self.manifest))

    def test_one_plan_byte_changed(self):
        self.sql("UPDATE bundles SET plan=? WHERE id=?", (PLAN[:-1] + b"x", self.id))
        with self.assertRaises(ContractError): self.store.get(self.id)

    def test_manifest_byte_changed(self):
        self.sql("UPDATE bundles SET manifest=? WHERE id=?", (self.snapshot.manifest_raw + b" ", self.id))
        with self.assertRaises(ContractError): self.store.get(self.id)

    def test_plan_substitution_even_with_recomputed_internal_hashes(self):
        self.approve()
        m = deepcopy(self.manifest)
        other = b"OTHER_SYNTHETIC_PLAN"
        m["plan"] = {"sha256": digest(other), "size": len(other)}
        raw = canonical(m)
        self.sql("UPDATE bundles SET plan=?,manifest=?,digest=? WHERE id=?", (other, raw, digest(raw), self.id))
        with self.assertRaises(RemoteTrustBlocked): self.service.begin(self.id, self.expected, "200", "1", NOW)

    def test_manifest_substitution_with_recomputed_digest(self):
        self.approve()
        m = deepcopy(self.manifest)
        m["expires_at"] = "2026-11-23T13:30:00Z"
        raw = canonical(m)
        self.sql("UPDATE bundles SET manifest=?,digest=? WHERE id=?", (raw, digest(raw), self.id))
        with self.assertRaises(RemoteTrustBlocked): self.service.begin(self.id, self.expected, "200", "1", NOW)

    def test_overwrite_forbidden(self):
        with self.assertRaises(ContractError): self.store.create(self.manifest, PLAN)

    def test_expired_plan(self):
        with self.assertRaises(ContractError): self.service.validate(self.id, self.expected, NOW + timedelta(hours=2))
        self.assertEqual(self.service.expire(self.id, NOW + timedelta(hours=2)).state, "EXPIRED")

    def test_different_commit(self):
        expected = deepcopy(self.expected); expected["commit_sha"] = "f" * 40
        with self.assertRaises(ContractError): self.service.validate(self.id, expected, NOW)

    def test_different_environment(self):
        expected = deepcopy(self.expected); expected["environment"] = "wordle-azure-demo"
        with self.assertRaises(ContractError): self.service.validate(self.id, expected, NOW)

    def test_different_terraform_version(self):
        expected = deepcopy(self.expected); expected["terraform"]["version"] = "1.9.7"
        with self.assertRaises(ContractError): self.service.validate(self.id, expected, NOW)

    def test_different_provider_lock(self):
        expected = deepcopy(self.expected); expected["terraform"]["lock_sha256"] = "a" * 64
        with self.assertRaises(ContractError): self.service.validate(self.id, expected, NOW)

    def test_different_operation(self):
        expected = deepcopy(self.expected); expected["operation"] = "destroy"
        with self.assertRaises(ContractError): self.service.validate(self.id, expected, NOW)

    def test_backend_workspace_configuration_variables_state_targets(self):
        for field in ("backend", "configuration_sha256", "variables_sha256", "state", "provider"):
            expected = deepcopy(self.expected)
            expected["terraform"][field] = None
            with self.subTest(field=field), self.assertRaises(ContractError):
                self.service.validate(self.id, expected, NOW)
        expected = deepcopy(self.expected); expected["targets"]["cluster"] = "aks-wordle-other"
        with self.assertRaises(ContractError): self.service.validate(self.id, expected, NOW)

    def test_approval_missing(self):
        self.authority.approvals.clear()
        with self.assertRaises(RemoteTrustBlocked): self.approve()

    def test_approval_wrong_hash(self):
        self.authority.approvals["fixture-review-1"]["binding"]["manifest_sha256"] = "0" * 64
        with self.assertRaises(ContractError): self.approve()

    def test_approver_unauthorized(self):
        self.authority.approvals["fixture-review-1"]["approver"] = "other"
        with self.assertRaises(ContractError): self.approve()

    def test_approval_for_different_apply_run_or_attempt(self):
        for field in ("apply_run_id", "apply_attempt"):
            self.authority.approvals["fixture-review-1"]["binding"][field] = "999"
            with self.subTest(field=field), self.assertRaises(ContractError): self.approve()
            self.authority.approvals["fixture-review-1"]["binding"][field] = "200" if field == "apply_run_id" else "1"

    def test_consumed_plan_cannot_be_reused(self):
        claimed = self.begin()
        consumer = decode(claimed.metadata_raw)["consumer"]
        self.assertEqual(self.service.finish(self.id, consumer, True, NOW).state, "CONSUMED")
        with self.assertRaises(ContractError): self.service.begin(self.id, self.expected, "200", "1", NOW)

    def test_two_real_process_consumers(self):
        self.approve()
        ctx = multiprocessing.get_context("spawn")
        start, output = ctx.Event(), ctx.Queue()
        workers = [ctx.Process(target=consumer_worker, args=(str(self.path), self.expected, self.authority,
                                                           self.id, start, output)) for _ in range(2)]
        try:
            for worker in workers: worker.start()
            start.set()
            results = sorted(output.get(timeout=20) for _ in workers)
            self.assertEqual(results, ["claimed", "denied"])
            for worker in workers:
                worker.join(10)
                self.assertEqual(worker.exitcode, 0)
        finally:
            for worker in workers:
                if worker.is_alive(): worker.terminate(); worker.join(5)
            output.close(); output.join_thread()

    def test_interrupted_atomic_create_rolls_back(self):
        class InterruptedStore(SqliteArtifactStore):
            def _insert(self, db, values):
                super()._insert(db, values)
                raise OSError("Simulated interrupted storage write")
        m = deepcopy(self.manifest); m["plan_id"] = "44444444-4444-4444-8444-444444444444"
        with self.assertRaises(OSError): InterruptedStore(self.path).create(m, PLAN)
        with self.assertRaises(ContractError): self.store.get(m["plan_id"])
        self.assertEqual(self.service.publish(m, PLAN).state, "PENDING_APPROVAL")

    def test_incomplete_artifact(self):
        self.sql("UPDATE bundles SET plan=? WHERE id=?", (b"", self.id))
        with self.assertRaises(ContractError): self.store.get(self.id)

    def test_recover_complete_staging_without_approval(self):
        m = deepcopy(self.manifest); m["plan_id"] = "55555555-5555-4555-8555-555555555555"
        self.store.create(m, PLAN)
        self.assertEqual(self.service.recover_staged(m["plan_id"]).state, "PENDING_APPROVAL")

    def test_recovery_after_unknown_consumption_never_reopens_plan(self):
        self.begin()
        with self.assertRaises(ContractError): self.service.begin(self.id, self.expected, "200", "1", NOW)
        claimed = self.store.get(self.id)
        consumer = decode(claimed.metadata_raw)["consumer"]
        self.assertEqual(self.service.mark_unknown(self.id, consumer, "interrupted_unknown_outcome", NOW).state,
                         "OUTCOME_UNKNOWN")
        with self.assertRaises(ContractError): self.approve()

    def test_default_trust_is_fail_closed(self):
        service = PlanContract(self.store)
        with self.assertRaises(RemoteTrustBlocked):
            service.approve(self.id, self.expected, "invented-approval", "200", "1", NOW)

    def test_forged_approved_json_is_not_authority(self):
        self.sql("UPDATE bundles SET state=?,metadata=? WHERE id=?", ("APPROVED", canonical({"approved": True,
                 "approval": self.authority.approvals["fixture-review-1"]}), self.id))
        service = PlanContract(self.store)
        with self.assertRaises(RemoteTrustBlocked): service.begin(self.id, self.expected, "200", "1", NOW)

    def test_approval_revoked_after_approval(self):
        self.approve(); self.authority.approvals.clear()
        with self.assertRaises(RemoteTrustBlocked): self.service.begin(self.id, self.expected, "200", "1", NOW)

    def test_expiry_during_consumption_is_explicit(self):
        claimed = self.begin(); consumer = decode(claimed.metadata_raw)["consumer"]
        with self.assertRaises(ContractError): self.service.finish(self.id, consumer, True, NOW + timedelta(hours=2))
        self.assertEqual(self.store.get(self.id).state, "OUTCOME_UNKNOWN")
        self.assertEqual(decode(self.store.get(self.id).metadata_raw)["result"], "expired_during_consumption")

    def test_stale_cas_and_rejected_transition(self):
        approved = self.approve()
        with self.assertRaises(ContractError): self.store.transition(self.id, self.snapshot.version, "CONSUMING", {})
        rejected = self.service.reject(self.id, "operator_rejected")
        with self.assertRaises(ContractError): self.store.transition(self.id, rejected.version, "APPROVED", {})

    def test_retention_and_deletion_tombstone(self):
        with self.assertRaises(ContractError): self.service.deletion_ticket(self.id, NOW, NOW)
        self.service.reject(self.id, "operator_rejected")
        with self.assertRaises(ContractError): self.service.deletion_ticket(self.id, NOW, NOW + timedelta(days=1))
        ticket = self.service.deletion_ticket(self.id, NOW, NOW)
        self.store.delete_terminal(**ticket)
        with self.assertRaises(ContractError): self.store.create(self.manifest, PLAN)

    def test_missing_state_fingerprint_fails_closed(self):
        m = deepcopy(self.manifest); m["plan_id"] = "66666666-6666-4666-8666-666666666666"
        m["terraform"]["state"] = None
        self.service.publish(m, PLAN)
        expected = deepcopy(self.expected); expected["terraform"]["state"] = None
        with self.assertRaises(ContractError): self.service.validate(m["plan_id"], expected, NOW)

    def test_unknown_secret_field_and_duplicate_json_rejected(self):
        m = deepcopy(self.manifest); m["client_secret"] = "SYNTHETIC_FORBIDDEN_FIELD"
        with self.assertRaises(ContractError): self.store.create(m, PLAN)
        with self.assertRaises(ContractError): decode(b'{"schema_version":1,"schema_version":1}')


if __name__ == "__main__":
    multiprocessing.freeze_support()
    unittest.main(verbosity=2)
