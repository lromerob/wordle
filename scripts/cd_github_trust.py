"""Offline GitHub evidence verifier. No HTTP implementation and no trusted JSON-file loader."""
from dataclasses import dataclass
from typing import Protocol

from cd_plan_contract import (ContractError, RemoteTrustBlocked, REPOSITORY, WORKFLOW, CONTEXT_KEYS,
                              approval_binding, canonical, decode, matching, require, timestamp, utc)


class GitHubEvidenceSource(Protocol):
    """Future authenticated adapter supplies fresh official API response bodies, not producer files."""
    def repository(self): ...
    def run(self, run_id): ...
    def environment(self, name): ...
    def branch_policies(self, name): ...
    def permission(self, login): ...
    def approvals(self, run_id): ...
    def comments(self, issue): ...
    def jobs(self, run_id, attempt): ...


@dataclass(frozen=True)
class AuthorizationPolicy:
    repository_id: int
    approver_id: int
    approver_login: str
    environment_id: int
    environment_name: str
    workflow_id: int
    branch: str
    issue: int
    job_name: str = "apply"
    producer_workflow_id: int | None = None


@dataclass(frozen=True)
class Challenge:
    """Trusted coordinator input, issued after the protected job starts; not part of the bundle."""
    apply_run: str
    attempt: str
    nonce: str
    issued_at: str
    job_id: int


def confirmation(snapshot, policy, challenge):
    m = snapshot.manifest()
    return (f"WORDLE-PLAN-APPROVE v1 repo={policy.repository_id} plan={m['plan_id']} "
            f"manifest={snapshot.manifest_sha256} binary={m['plan']['sha256']} commit={m['commit_sha']} "
            f"operation={m['operation']} environment={m['environment']} "
            f"producer={m['producer']['run_id']}:1 apply={challenge.apply_run}:1 nonce={challenge.nonce}")


class GitHubTrustVerifier:
    """TrustSource interface. Fixture results only establish logic, never remote provenance."""
    def __init__(self, source, snapshot, expected, policy, challenge, now):
        require(source is not None, "Independent GitHub evidence source required")
        self.source, self.snapshot = source, snapshot
        self.expected = decode(canonical(expected))
        self.policy, self.challenge, self.now = policy, challenge, now

    @staticmethod
    def _user(value, policy):
        require(isinstance(value, dict) and type(value.get("id")) is int
                and value["id"] == policy.approver_id and value.get("login") == policy.approver_login
                and value.get("type") == "User", "GitHub identity mismatch")

    def _run(self, value, run_id, producer=False):
        p, m = self.policy, self.snapshot.manifest()
        require(type(value.get("id")) is int and str(value["id"]) == run_id
                and type(value.get("run_attempt")) is int and value["run_attempt"] == 1,
                "Wrong run or rerun unsupported")
        require(value["repository"]["id"] == p.repository_id
                and value["repository"]["full_name"] == REPOSITORY, "Run repository mismatch")
        require(value["head_sha"] == m["commit_sha"] and value["head_branch"] == p.branch
                and value["workflow_id"] == (p.producer_workflow_id or p.workflow_id if producer else p.workflow_id)
                and value["path"] == (m["producer"]["workflow"] if producer else WORKFLOW)
                and value["event"] == "workflow_dispatch", "Run context mismatch")
        self._user(value["actor"], p)
        if producer:
            require(value["status"] == "completed" and value["conclusion"] == "success",
                    "Producer did not finish successfully")
        else:
            require(value["status"] == "in_progress" and value["conclusion"] is None,
                    "APPLY run not active")
        return timestamp(value["created_at"])

    def _verify(self, reference=None):
        try:
            return self._verify_responses(reference)
        except ContractError:
            raise
        except Exception:
            # Missing/deleted/API failures are not approvals. Never expose response bodies.
            raise RemoteTrustBlocked("GitHub evidence missing, malformed or unavailable") from None

    def _verify_responses(self, reference):
        p, c, m = self.policy, self.challenge, self.snapshot.manifest()
        require({k: m[k] for k in self.expected} == self.expected
                and set(self.expected) == CONTEXT_KEYS,
                "Plan differs from trusted expected context")
        for value in (p.repository_id, p.approver_id, p.environment_id, p.workflow_id, p.issue, c.job_id):
            require(type(value) is int and value > 0, "Invalid policy identifier")
        require(m["environment"] == p.environment_name and m["producer"]["attempt"] == "1"
                and c.attempt == "1", "Environment mismatch or rerun unsupported")
        matching(r"[1-9][0-9]*", c.apply_run)
        matching(r"[a-f0-9]{32}", c.nonce)
        require(c.apply_run != m["producer"]["run_id"], "PLAN and APPLY must be independent runs")
        now = utc(self.now())
        require(timestamp(m["created_at"]) <= timestamp(c.issued_at) <= now < timestamp(m["expires_at"]),
                "Invalid challenge or plan lifetime")
        repo = self.source.repository()
        require(repo["id"] == p.repository_id and repo["full_name"] == REPOSITORY
                and repo["visibility"] == "public", "Repository identity or public-policy mismatch")
        self._user(repo["owner"], p)
        producer_started = self._run(self.source.run(m["producer"]["run_id"]), m["producer"]["run_id"], True)
        apply_started = self._run(self.source.run(c.apply_run), c.apply_run)
        require(producer_started <= timestamp(m["created_at"]) <= apply_started <= timestamp(c.issued_at),
                "Invalid run event ordering")
        jobs = self.source.jobs(c.apply_run, "1")
        require(type(jobs["total_count"]) is int and jobs["total_count"] == 1 and len(jobs["jobs"]) == 1,
                "Ambiguous or incomplete job evidence")
        job = jobs["jobs"][0]
        require(job["id"] == c.job_id and str(job["run_id"]) == c.apply_run
                and job["head_sha"] == m["commit_sha"] and job["name"] == p.job_name
                and job["status"] == "in_progress" and job["conclusion"] is None,
                "Protected job mismatch")
        require(apply_started <= timestamp(job["started_at"]) <= timestamp(c.issued_at), "Challenge predates protected job")
        env = self.source.environment(p.environment_name)
        require(env["id"] == p.environment_id and env["name"] == p.environment_name
                and env["can_admins_bypass"] is False, "Environment identity or bypass mismatch")
        require(env["deployment_branch_policy"] == {"protected_branches": False, "custom_branch_policies": True},
                "Unexpected environment branch policy")
        reviewers = [rule for rule in env["protection_rules"] if rule["type"] == "required_reviewers"]
        require(len(reviewers) == 1 and type(reviewers[0]["prevent_self_review"]) is bool
                and len(reviewers[0]["reviewers"]) == 1, "Reviewer policy missing or ambiguous")
        reviewer = reviewers[0]["reviewers"][0]
        require(reviewer["type"] == "User", "Unexpected reviewer type")
        self._user(reviewer["reviewer"], p)
        if reviewers[0]["prevent_self_review"]:
            raise RemoteTrustBlocked("Single-owner policy cannot self-approve with self-review prevention")
        policies = self.source.branch_policies(p.environment_name)
        require(policies["total_count"] == 1 and len(policies["branch_policies"]) == 1
                and policies["branch_policies"][0]["name"] == p.branch
                and policies["branch_policies"][0]["type"] == "branch", "Branch scope differs from approved policy")
        permission = self.source.permission(p.approver_login)
        require(permission["permission"] == "admin", "Approver not currently authorized")
        self._user(permission["user"], p)
        approvals = self.source.approvals(c.apply_run)
        require(isinstance(approvals, list) and len(approvals) == 1, "Approval history missing or ambiguous")
        review = approvals[0]
        require(review["state"] == "approved" and len(review["environments"]) == 1,
                "Deployment not unambiguously approved")
        self._user(review["user"], p)
        require(review["environments"][0]["id"] == p.environment_id
                and review["environments"][0]["name"] == p.environment_name
                and review["environments"][0]["can_admins_bypass"] is False, "Review environment mismatch")
        comments = self.source.comments(p.issue)
        require(isinstance(comments, list), "Malformed comments response")
        exact = [item for item in comments if item["body"] == confirmation(self.snapshot, p, c)]
        require(len(exact) == 1, "Confirmation missing or duplicated")
        comment = exact[0]
        require(type(comment["id"]) is int and comment["id"] > 0, "Invalid comment identifier")
        computed_reference = f"github:issue:{p.issue}:comment:{comment['id']}"
        require(reference is None or reference == computed_reference, "Approval reference mismatch")
        require(comment["issue_url"] == f"https://api.github.com/repos/{REPOSITORY}/issues/{p.issue}"
                and comment["author_association"] == "OWNER", "Confirmation scope mismatch")
        self._user(comment["user"], p)
        require(comment["updated_at"] == comment["created_at"], "Edited confirmation rejected")
        require(timestamp(c.issued_at) <= timestamp(comment["created_at"]) <= now,
                "Confirmation predates challenge or is in the future")
        return {"reference": computed_reference, "binding": approval_binding(self.snapshot, c.apply_run, "1"),
                "approver": p.approver_login, "approved_at": comment["created_at"]}

    def origin(self, manifest_sha256):
        self._verify()
        require(manifest_sha256 == self.snapshot.manifest_sha256, "Manifest origin mismatch")
        m = self.snapshot.manifest()
        # Human confirmation of both hashes plus verified producer metadata; not a build attestation.
        return {"manifest_sha256": manifest_sha256, "repository": m["repository"],
                "commit_sha": m["commit_sha"], "producer": m["producer"]}

    def approval(self, reference):
        return self._verify(reference)
