"""No network or real gh process: mocked CLI responses feed the existing verifier."""
from copy import deepcopy
import json
import subprocess
import unittest

from cd_github_adapter import GitHubReadAdapter
from cd_github_trust import GitHubTrustVerifier
from cd_plan_contract import ContractError, PlanContract, RemoteTrustBlocked
import test_cd_github_trust as fixtures
from test_cd_plan_contract import NOW


class AdapterTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.TrustTests()
        self.fixture.setUp(); self.addCleanup(self.fixture.doCleanups)
        f = self.fixture; api = f.api
        self.base = "repos/lromerob/wordle"
        self.responses = {"": api.repo, "/actions/runs/100": api.runs["100"], "/actions/runs/200": api.runs["200"],
            "/environments/wordle-azure-demo": api.env, "/collaborators/lromerob/permission": api.permissions,
            "/actions/runs/200/approvals": api.reviews, "/issues/6/comments": api.issue_comments,
            "/actions/runs/200/attempts/1/jobs": api.run_jobs,
            "/environments/wordle-azure-demo/deployment-branch-policies": api.policies}
        self.responses = deepcopy(self.responses)
        self.responses["/environments/wordle-azure-demo/deployment-branch-policies"]["branch_policies"][0]["id"] = 707
        self.calls = []; self.failure = None; self.raw = None; self.auth_ok = True
        self.adapter = GitHubReadAdapter("synthetic-gh", self.runner)
        trust = GitHubTrustVerifier(self.adapter, f.snapshot, f.expected, f.policy, f.challenge, lambda: NOW)
        self.service = PlanContract(f.store, trust)

    def runner(self, command, **kwargs):
        self.calls.append(command)
        self.assertEqual(command[0], "synthetic-gh")
        self.assertTrue(kwargs["capture_output"]); self.assertEqual(kwargs["timeout"], 90)
        if command[1:3] == ["auth", "status"]:
            return subprocess.CompletedProcess(command, 0 if self.auth_ok else 1, "", "authentication required")
        self.assertEqual(command[1], "api")
        self.assertEqual(command[command.index("--method") + 1], "GET")
        self.assertEqual(command[command.index("--hostname") + 1], "github.com")
        if self.failure:
            return subprocess.CompletedProcess(command, 1, "sensitive response must not leak", "HTTP " + self.failure)
        endpoint = next(arg for arg in command if arg.startswith(self.base))
        suffix = endpoint[len(self.base):].split("?")[0]
        value = self.responses[suffix]
        if "--slurp" in command: value = [value]
        return subprocess.CompletedProcess(command, 0, self.raw if self.raw is not None else json.dumps(value), "")

    def approve(self):
        f = self.fixture
        return self.service.approve(f.id, f.expected, f.reference, "200", "1", NOW)

    def denies(self):
        with self.assertRaises(ContractError): self.approve()
        self.assertEqual(self.fixture.store.get(self.fixture.id).state, "PENDING_APPROVAL")

    def test_valid_adapter_to_verifier_and_contract(self):
        self.assertEqual(self.approve().state, "APPROVED")
        f = self.fixture
        self.assertEqual(self.service.begin(f.id, f.expected, "200", "1", NOW).state, "CONSUMING")

    def test_missing_run_http_404(self):
        self.failure = "404"
        with self.assertRaisesRegex(RemoteTrustBlocked, "404"): self.adapter.run("999")

    def test_wrong_attempt(self):
        self.responses["/actions/runs/200"]["run_attempt"] = 2; self.denies()

    def test_wrong_sha(self):
        self.responses["/actions/runs/200"]["head_sha"] = "0" * 40; self.denies()

    def test_wrong_environment(self):
        self.responses["/environments/wordle-azure-demo"]["id"] = 999; self.denies()

    def test_no_approval(self):
        self.responses["/actions/runs/200/approvals"] = []; self.denies()

    def test_unauthorized_approver(self):
        self.responses["/collaborators/lromerob/permission"]["permission"] = "read"; self.denies()

    def test_no_comment(self):
        self.responses["/issues/6/comments"] = []; self.denies()

    def test_edited_comment(self):
        self.responses["/issues/6/comments"][0]["updated_at"] = "2026-11-23T12:04:00Z"; self.denies()

    def test_duplicated_comment(self):
        comments = self.responses["/issues/6/comments"]
        comments.append(dict(comments[0], id=607)); self.denies()

    def test_malformed_json(self):
        self.raw = "not JSON"; self.denies()

    def test_http_error(self):
        self.failure = "500"; self.denies()

    def test_insufficient_permissions(self):
        self.failure = "403"; self.denies()

    def test_incomplete_response(self):
        del self.responses["/actions/runs/200"]["created_at"]; self.denies()

    def test_wrong_collection_shape(self):
        self.responses["/issues/6/comments"] = {"approved": True}; self.denies()

    def test_duplicate_json_keys(self):
        self.raw = '{"id":101,"id":999}'; self.denies()

    def test_incomplete_job_pages(self):
        self.responses["/actions/runs/200/attempts/1/jobs"]["total_count"] = 2; self.denies()

    def test_multiple_pages_aggregated(self):
        first = self.responses["/issues/6/comments"][0]
        self.raw = json.dumps([[first], [dict(first, id=607, body="unrelated")]])
        self.assertEqual(len(self.adapter.comments(6)), 2)

    def test_second_page_duplicate_confirmation_rejected(self):
        self.approve()
        # Exercise adapter paging separately; the verifier rejects equal confirmations across the flattened list.
        first = self.responses["/issues/6/comments"][0]
        self.raw = json.dumps([[first], [dict(first, id=607)]])
        comments = self.adapter.comments(6)
        self.assertEqual(len(comments), 2)
        self.raw = None; self.responses["/issues/6/comments"] = comments
        f = self.fixture
        with self.assertRaises(ContractError): self.service.begin(f.id, f.expected, "200", "1", NOW)

    def test_duplicate_page_object_ids_fail_closed(self):
        first = self.responses["/issues/6/comments"][0]
        self.raw = json.dumps([[first], [first]])
        with self.assertRaises(ContractError): self.adapter.comments(6)

    def test_timeout(self):
        def timeout(*args, **kwargs): raise subprocess.TimeoutExpired("gh", 90)
        with self.assertRaises(RemoteTrustBlocked): GitHubReadAdapter("synthetic-gh", timeout)

    def test_missing_authentication(self):
        self.auth_ok = False
        with self.assertRaises(RemoteTrustBlocked): GitHubReadAdapter("synthetic-gh", self.runner)

    def test_error_payload_not_exposed(self):
        self.failure = "403"
        with self.assertRaises(RemoteTrustBlocked) as caught: self.adapter.repository()
        self.assertNotIn("sensitive", str(caught.exception))

    def test_path_injection_rejected_before_request(self):
        before = len(self.calls)
        for call in (lambda: self.adapter.run("200/../../secrets"), lambda: self.adapter.environment("../secrets"),
                     lambda: self.adapter.permission("other-user")):
            with self.assertRaises(ContractError): call()
        self.assertEqual(len(self.calls), before)


if __name__ == "__main__": unittest.main(verbosity=2)
