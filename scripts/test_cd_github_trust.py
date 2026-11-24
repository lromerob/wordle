"""Offline, synthetic API response fixtures. These are not remotely authenticated evidence."""
from copy import deepcopy
from dataclasses import replace
from datetime import timedelta
from pathlib import Path
import socket
import tempfile
import unittest
from unittest.mock import patch

from cd_plan_contract import ContractError, PlanContract, SqliteArtifactStore, build_manifest, decode
from cd_github_trust import AuthorizationPolicy, Challenge, GitHubTrustVerifier, confirmation
from test_cd_plan_contract import context, NOW, PLAN


class FixtureGitHub:
    """Official-response-shaped bodies; a future adapter must fetch all pages, never bundle JSON."""
    def repository(self): return deepcopy(self.repo)
    def run(self, run_id): return deepcopy(self.runs[run_id])
    def environment(self, name): return deepcopy(self.env)
    def branch_policies(self, name): return deepcopy(self.policies)
    def permission(self, login): return deepcopy(self.permissions)
    def approvals(self, run_id): return deepcopy(self.reviews)
    def comments(self, issue): return deepcopy(self.issue_comments)
    def jobs(self, run_id, attempt): return deepcopy(self.run_jobs)


class FixtureReconciliation:
    """Independent test authority, never considered verified human input outside these tests."""
    def __init__(self, decision): self.value = decision
    def decision(self, reference): return deepcopy(self.value)


class TrustTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="wordle-trust-verifier-")
        self.addCleanup(self.tmp.cleanup)
        self.guard = patch.object(socket.socket, "connect", side_effect=AssertionError("Network forbidden"))
        self.guard.start(); self.addCleanup(self.guard.stop)
        self.store = SqliteArtifactStore(Path(self.tmp.name) / "private.sqlite")
        self.expected = context(); self.expected["environment"] = "wordle-azure-demo"
        self.manifest = build_manifest(PLAN, self.expected,
            {"workflow": ".github/workflows/azure-demo.yml", "run_id": "100", "attempt": "1"},
            "2026-11-23T12:00:00Z", "2026-11-23T13:00:00Z")
        self.id = self.manifest["plan_id"]
        self.snapshot = PlanContract(self.store).publish(self.manifest, PLAN)
        self.policy = AuthorizationPolicy(101, 202, "lromerob", 303, "wordle-azure-demo", 404,
                                          "codex/pg01-07-consolidation", 6)
        self.challenge = Challenge("200", "1", "f" * 32, "2026-11-23T12:02:00Z", 505)
        self.api = FixtureGitHub()
        user = {"id": 202, "login": "lromerob", "type": "User"}
        repo = {"id": 101, "full_name": "lromerob/wordle", "visibility": "public", "owner": user}
        self.api.repo = repo
        run = {"id": 100, "run_attempt": 1, "head_sha": "a" * 40,
               "head_branch": self.policy.branch, "repository": repo, "actor": user,
               "workflow_id": 404, "path": ".github/workflows/azure-demo.yml", "event": "workflow_dispatch",
               "status": "completed", "conclusion": "success", "created_at": "2026-11-23T11:59:00Z"}
        self.api.runs = {"100": deepcopy(run), "200": dict(run, id=200, status="in_progress",
                         conclusion=None, created_at="2026-11-23T12:01:00Z")}
        self.api.env = {"id": 303, "name": self.policy.environment_name, "can_admins_bypass": False,
            "deployment_branch_policy": {"protected_branches": False, "custom_branch_policies": True},
            "protection_rules": [{"type": "required_reviewers", "prevent_self_review": False,
                                  "reviewers": [{"type": "User", "reviewer": user}]}]}
        self.api.policies = {"total_count": 1, "branch_policies": [{"name": self.policy.branch, "type": "branch"}]}
        self.api.permissions = {"permission": "admin", "user": user}
        self.api.reviews = [{"state": "approved", "comment": "", "user": user,
                             "environments": [{"id": 303, "name": self.policy.environment_name,
                                               "can_admins_bypass": False}]}]
        self.api.run_jobs = {"total_count": 1, "jobs": [{"id": 505, "run_id": 200, "head_sha": "a" * 40,
            "name": "apply", "status": "in_progress", "conclusion": None, "started_at": "2026-11-23T12:01:30Z"}]}
        self.api.issue_comments = [{"id": 606, "body": confirmation(self.snapshot, self.policy, self.challenge),
            "user": user, "author_association": "OWNER", "issue_url": "https://api.github.com/repos/lromerob/wordle/issues/6",
            "created_at": "2026-11-23T12:03:00Z", "updated_at": "2026-11-23T12:03:00Z"}]
        self.trust = GitHubTrustVerifier(self.api, self.snapshot, self.expected, self.policy, self.challenge, lambda: NOW)
        self.service = PlanContract(self.store, self.trust)
        self.reference = "github:issue:6:comment:606"

    def approve(self):
        return self.service.approve(self.id, self.expected, self.reference, "200", "1", NOW)

    def claim(self):
        self.approve()
        got = self.service.begin(self.id, self.expected, "200", "1", NOW)
        return decode(got.metadata_raw)["consumer"]

    def denies(self):
        with self.assertRaises(ContractError): self.approve()
        self.assertEqual(self.store.get(self.id).state, "PENDING_APPROVAL")

    def test_valid_approval_and_consumption(self):
        consumer = self.claim()
        self.assertEqual(self.service.finish(self.id, consumer, True, NOW).state, "CONSUMED")

    def test_environment_approval_without_plan_confirmation(self):
        self.api.issue_comments = []; self.denies()

    def test_edited_confirmation(self):
        self.api.issue_comments[0]["updated_at"] = "2026-11-23T12:04:00Z"; self.denies()

    def test_duplicate_confirmations(self):
        self.api.issue_comments.append(dict(self.api.issue_comments[0], id=607)); self.denies()

    def test_confirmation_deleted_after_approval(self):
        self.approve(); self.api.issue_comments = []
        with self.assertRaises(ContractError): self.service.begin(self.id, self.expected, "200", "1", NOW)
        self.assertEqual(self.store.get(self.id).state, "APPROVED")

    def test_approval_before_plan(self):
        self.api.issue_comments[0].update(created_at="2026-11-23T11:59:00Z", updated_at="2026-11-23T11:59:00Z")
        self.denies()

    def test_approval_before_challenge(self):
        self.api.issue_comments[0].update(created_at="2026-11-23T12:01:59Z", updated_at="2026-11-23T12:01:59Z")
        self.denies()

    def test_future_confirmation(self):
        self.api.issue_comments[0].update(created_at="2026-11-23T12:06:00Z", updated_at="2026-11-23T12:06:00Z")
        self.denies()

    def test_duplicate_environment_reviews(self):
        self.api.reviews *= 2; self.denies()

    def test_environment_rejected(self):
        self.api.reviews[0]["state"] = "rejected"; self.denies()

    def test_environment_other_id(self):
        self.api.reviews[0]["environments"][0]["id"] = 999; self.denies()

    def test_permission_revoked(self):
        self.api.permissions["permission"] = "read"; self.denies()

    def test_approver_other_numeric_identity(self):
        self.api.issue_comments[0]["user"] = {"id": 999, "login": "lromerob", "type": "User"}; self.denies()

    def test_boolean_approver_id(self):
        self.api.issue_comments[0]["user"] = {"id": True, "login": "lromerob", "type": "User"}; self.denies()

    def test_wrong_repository(self):
        self.api.repo = dict(self.api.repo, id=999); self.denies()

    def test_apply_wrong_run_id(self):
        self.api.runs["200"]["id"] = 201; self.denies()

    def test_apply_rerun(self):
        self.api.runs["200"]["run_attempt"] = 2; self.denies()

    def test_producer_rerun(self):
        self.api.runs["100"]["run_attempt"] = 2; self.denies()

    def test_malformed_api(self):
        self.api.reviews = {"approved": True}; self.denies()

    def test_incomplete_api(self):
        del self.api.runs["200"]["created_at"]; self.denies()

    def test_unavailable_adapter_fails_closed(self):
        self.api.comments = lambda issue: (_ for _ in ()).throw(OSError("synthetic unavailable"))
        self.denies()

    def test_gate_ambiguous_jobs(self):
        self.api.run_jobs["total_count"] = 2; self.denies()

    def test_challenge_predates_job(self):
        self.api.run_jobs["jobs"][0]["started_at"] = "2026-11-23T12:04:00Z"; self.denies()

    def test_wrong_expected_context(self):
        self.trust.expected["operation"] = "destroy"; self.denies()

    def test_reference_substitution(self):
        self.reference = "github:issue:6:comment:999"; self.denies()

    def test_authorization_replayed_in_another_run(self):
        self.trust.challenge = replace(self.challenge, apply_run="201"); self.denies()

    def test_second_consumption_rejected(self):
        self.claim()
        with self.assertRaises(ContractError): self.service.begin(self.id, self.expected, "200", "1", NOW)

    def test_runner_lost_before_claim_requires_persistent_check(self):
        self.approve()
        self.assertEqual(self.store.get(self.id).state, "APPROVED")
        # No consumer token and no right to invoke APPLY. A new begin must reverify fresh evidence.
        self.api.issue_comments = []
        with self.assertRaises(ContractError): self.service.begin(self.id, self.expected, "200", "1", NOW)
        self.assertNotIn("consumer", decode(self.store.get(self.id).metadata_raw))

    def unknown(self, reason):
        consumer = self.claim()
        got = self.service.mark_unknown(self.id, consumer, reason, NOW)
        self.assertEqual(got.state, "OUTCOME_UNKNOWN")
        self.assertFalse(decode(got.metadata_raw)["recovery"]["replay_allowed"])
        with self.assertRaises(ContractError): self.service.begin(self.id, self.expected, "200", "1", NOW)
        with self.assertRaises(ContractError): self.service.finish(self.id, consumer, True, NOW)
        return consumer

    def test_runner_lost_after_claim_before_apply(self): self.unknown("runner_lost_before_apply")
    def test_runner_lost_during_apply(self): self.unknown("runner_lost_during_apply")
    def test_runner_lost_after_apply_before_receipt(self): self.unknown("receipt_write_failed")

    def test_partial_apply_failure(self):
        consumer = self.claim()
        self.assertEqual(self.service.finish(self.id, consumer, False, NOW).state, "OUTCOME_UNKNOWN")
        self.assertEqual(decode(self.store.get(self.id).metadata_raw)["result"], "partial_failure")

    def test_receipt_storage_failure_retains_consumption(self):
        consumer = self.claim()
        with patch.object(self.store, "transition", side_effect=OSError("synthetic write failure")):
            with self.assertRaises(OSError): self.service.finish(self.id, consumer, True, NOW)
        self.assertEqual(self.store.get(self.id).state, "CONSUMING")
        self.service.mark_unknown(self.id, consumer, "receipt_write_failed", NOW)
        self.assertEqual(self.store.get(self.id).state, "OUTCOME_UNKNOWN")

    def decision(self):
        consumer = self.unknown("runner_lost_during_apply")
        self.service.require_reconciliation(self.id)
        return {"reference": "human-review-1", "plan_id": self.id, "consumer": consumer, "reviewer": "lromerob",
                "reviewed_at": "2026-11-23T12:05:00Z", "checks": {"no_active_operation": True,
                "terraform_state": True, "azure_resources": True, "new_plan_required": True},
                "evidence": {"operation": "1" * 64, "state": "2" * 64, "resources": "3" * 64}}

    def test_complete_human_reconciliation(self):
        decision = self.decision()
        result = self.service.reconcile(self.id, "human-review-1", FixtureReconciliation(decision), NOW)
        self.assertEqual(result.state, "RECONCILED")
        with self.assertRaises(ContractError): self.approve()
        with self.assertRaises(ContractError): self.service.begin(self.id, self.expected, "200", "1", NOW)
        with self.assertRaises(ContractError): self.service.deletion_ticket(self.id, NOW, NOW)

    def test_incomplete_human_reconciliation(self):
        decision = self.decision(); decision["checks"]["no_active_operation"] = False
        with self.assertRaises(ContractError):
            self.service.reconcile(self.id, "human-review-1", FixtureReconciliation(decision), NOW)
        self.assertEqual(self.store.get(self.id).state, "RECONCILIATION_REQUIRED")

    def test_no_independent_reconciliation_authority(self):
        self.decision()
        with self.assertRaises(ContractError): self.service.reconcile(self.id, "human-review-1", None, NOW)

    def test_forged_reconciliation_reviewer(self):
        decision = self.decision(); decision["reviewer"] = "someone-else"
        with self.assertRaises(ContractError):
            self.service.reconcile(self.id, "human-review-1", FixtureReconciliation(decision), NOW)

    def test_reconciliation_missing_evidence(self):
        decision = self.decision(); decision["evidence"].pop("resources")
        with self.assertRaises(ContractError):
            self.service.reconcile(self.id, "human-review-1", FixtureReconciliation(decision), NOW)

    def test_changed_workflow(self):
        self.api.runs["200"]["path"] = ".github/workflows/unreviewed.yml"; self.denies()

    def test_environment_bypass_enabled(self):
        self.api.env["can_admins_bypass"] = True; self.denies()

    def test_missing_reviewer(self):
        self.api.env["protection_rules"] = []; self.denies()

    def test_widened_branch_policy(self):
        self.api.policies["branch_policies"][0]["name"] = "*"; self.denies()

    def test_permission_revoked_between_approve_and_claim(self):
        self.approve(); self.api.permissions["permission"] = "read"
        with self.assertRaises(ContractError): self.service.begin(self.id, self.expected, "200", "1", NOW)

    def test_wrong_consumer_cannot_record_unknown(self):
        self.claim()
        with self.assertRaises(ContractError):
            self.service.mark_unknown(self.id, "not-the-consumer", "runner_lost_during_apply", NOW)
        self.assertEqual(self.store.get(self.id).state, "CONSUMING")

    def test_claim_invalidated_before_return_cannot_start_apply(self):
        self.approve()
        transition = self.store.transition
        def invalidated_before_return(*args):
            got = transition(*args)
            if args[2] == "CONSUMING":
                return transition(self.id, got.version, "OUTCOME_UNKNOWN", decode(got.metadata_raw))
            return got
        with patch.object(self.store, "transition", side_effect=invalidated_before_return):
            with self.assertRaises(ContractError): self.service.begin(self.id, self.expected, "200", "1", NOW)
        self.assertEqual(self.store.get(self.id).state, "OUTCOME_UNKNOWN")

    def test_lost_receipt_ack_after_commit_does_not_reopen_plan(self):
        consumer = self.claim()
        transition = self.store.transition
        def committed_but_ack_lost(*args):
            transition(*args)
            raise OSError("Synthetic lost acknowledgement")
        with patch.object(self.store, "transition", side_effect=committed_but_ack_lost):
            with self.assertRaises(OSError): self.service.finish(self.id, consumer, True, NOW)
        self.assertEqual(self.store.get(self.id).state, "CONSUMED")
        with self.assertRaises(ContractError): self.service.begin(self.id, self.expected, "200", "1", NOW)

    def test_all_incomplete_reconciliation_checks_rejected(self):
        decision = self.decision()
        for check in decision["checks"]:
            with self.subTest(check=check):
                incomplete = deepcopy(decision); incomplete["checks"][check] = False
                with self.assertRaises(ContractError):
                    self.service.reconcile(self.id, "human-review-1", FixtureReconciliation(incomplete), NOW)

    def test_unknown_cannot_expire_or_reject_into_replay(self):
        self.unknown("runner_lost_during_apply")
        with self.assertRaises(ContractError): self.service.expire(self.id, NOW + timedelta(days=1))
        with self.assertRaises(ContractError): self.service.reject(self.id, "operator_rejected")


# Each strict-body corruption is a separate test, preserving explicit acceptance evidence.
def corrupt_body(old, new):
    def test(self):
        body = self.api.issue_comments[0]["body"]
        self.assertIn(old(self), body)
        self.api.issue_comments[0]["body"] = body.replace(old(self), new(self), 1)
        self.denies()
    return test


for name, before, after in [
    ("wrong_plan_hash", lambda s: "binary=" + s.manifest["plan"]["sha256"], lambda s: "binary=" + "0" * 64),
    ("wrong_manifest_hash", lambda s: "manifest=" + s.snapshot.manifest_sha256, lambda s: "manifest=" + "0" * 64),
    ("wrong_plan_id", lambda s: "plan=" + s.id, lambda s: "plan=11111111-1111-4111-8111-111111111111"),
    ("wrong_commit", lambda s: "commit=" + "a" * 40, lambda s: "commit=" + "b" * 40),
    ("wrong_run", lambda s: "apply=200:1", lambda s: "apply=201:1"),
    ("wrong_attempt", lambda s: "apply=200:1", lambda s: "apply=200:2"),
    ("wrong_environment", lambda s: "environment=wordle-azure-demo", lambda s: "environment=wordle-azure-infra"),
    ("wrong_nonce", lambda s: "nonce=" + "f" * 32, lambda s: "nonce=" + "e" * 32),
    ("wrong_operation", lambda s: "operation=create", lambda s: "operation=destroy"),
    ("extra_text", lambda s: "WORDLE-PLAN-APPROVE", lambda s: "PREFIX WORDLE-PLAN-APPROVE"),
    ("newline_not_normalized", lambda s: "WORDLE-PLAN-APPROVE", lambda s: "WORDLE-PLAN-APPROVE\n"),
]:
    setattr(TrustTests, "test_" + name, corrupt_body(before, after))


if __name__ == "__main__": unittest.main(verbosity=2)
