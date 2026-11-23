"""Offline CI/store/OIDC tests. Every API, registry and Git boundary is simulated."""
import copy
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import release_gate as gate
from private_store import require_store
from azure_supervised import validate_oidc
from operational_contract import verify_references, REQUIRED

SHA = "a" * 40
STORE = "11111111-1111-4111-8111-111111111111"


def store(root):
    (root / ".wordle-private-store.json").write_text(json.dumps({"format": 1, "repository": gate.REPOSITORY,
        "store_id": STORE, "durable_acknowledged": True}))
    for name in ("plans", "selections", "evidence", "backups"):
        (root / name).mkdir(mode=0o700)
    if os.name == "posix":
        (root / ".wordle-private-store.json").chmod(0o600)
    return root


class GateTests(unittest.TestCase):
    def setUp(self):
        lock = json.loads((gate.ROOT / gate.LOCK).read_text())
        self.render = patch.object(gate, "rendered_images", return_value=set(lock["images"].values()))
        self.render.start(); self.addCleanup(self.render.stop)
        self.run = {"id": 7, "head_sha": SHA, "head_branch": gate.BRANCH,
            "repository": {"full_name": gate.REPOSITORY}, "head_repository": {"full_name": gate.REPOSITORY},
            "path": ".github/workflows/ci.yml", "event": "push", "status": "completed", "conclusion": "success", "run_attempt": 1}
        self.jobs = {"total_count": 7, "jobs": [{"id": n, "run_id": 7, "run_attempt": 1, "head_sha": SHA,
            "name": name, "status": "completed", "conclusion": "success"} for n, name in enumerate(gate.JOBS)]}

    def query(self, path):
        return copy.deepcopy(self.jobs if "/jobs?" in path else self.run)

    def test_success_all_seven_jobs(self):
        self.assertEqual(gate.ci_evidence("7", SHA, self.query)["jobs"], list(gate.JOBS))

    def test_attempt_endpoint_does_not_require_undocumented_job_field(self):
        for row in self.jobs["jobs"]: row.pop("run_attempt")
        paths = []
        def query(path):
            paths.append(path)
            return self.query(path)
        gate.ci_evidence("7", SHA, query)
        self.assertIn("/repos/lromerob/wordle/actions/runs/7/attempts/1/jobs?per_page=100&page=1", paths)

    def test_wrong_sha(self):
        self.run["head_sha"] = "b" * 40
        with self.assertRaises(ValueError): gate.ci_evidence("7", SHA, self.query)

    def test_nonexistent_ci(self):
        with self.assertRaises(ValueError): gate.ci_evidence("7", SHA, lambda p: {})

    def test_in_progress(self):
        self.run["status"] = "in_progress"
        with self.assertRaises(ValueError): gate.ci_evidence("7", SHA, self.query)

    def test_failed_ci(self):
        self.run["conclusion"] = "failure"
        with self.assertRaises(ValueError): gate.ci_evidence("7", SHA, self.query)

    def test_missing_required_job(self):
        self.jobs["jobs"][0]["name"] = "other"
        with self.assertRaises(ValueError): gate.ci_evidence("7", SHA, self.query)

    def test_skipped_or_cancelled_job(self):
        for conclusion in ("skipped", "cancelled", "failure", None):
            with self.subTest(conclusion=conclusion):
                self.jobs["jobs"][0]["conclusion"] = conclusion
                with self.assertRaises(ValueError): gate.ci_evidence("7", SHA, self.query)

    def test_wrong_branch(self):
        self.run["head_branch"] = "other"
        with self.assertRaises(ValueError): gate.ci_evidence("7", SHA, self.query)

    def test_wrong_repository(self):
        self.run["repository"]["full_name"] = "other/wordle"
        with self.assertRaises(ValueError): gate.ci_evidence("7", SHA, self.query)

    def test_incomplete_api(self):
        for key in ("total_count", "jobs"):
            result = dict(self.jobs); result.pop(key)
            with self.assertRaises(ValueError): gate.ci_evidence("7", SHA, lambda p: result if "/jobs?" in p else self.run)

    def test_403_no_raw_token_or_error(self):
        with patch.dict(os.environ, {"GH_TOKEN": "synthetic-token"}), patch.object(gate.urllib.request, "build_opener") as opener:
            opener.return_value.open.side_effect = PermissionError("403 synthetic-token")
            with self.assertRaisesRegex(ValueError, "CI evidence unavailable or permission denied") as caught:
                gate.api("/repos/lromerob/wordle/actions/runs/7")
            self.assertNotIn("synthetic-token", str(caught.exception))

    def test_render_image_as_first_container_key_is_not_omitted(self):
        self.assertEqual(gate.parse_rendered_images("      - image: frontend@sha256:abc\n        image: backend@sha256:def\n"),
                         {"frontend@sha256:abc", "backend@sha256:def"})

    def test_effective_overlay_digest_mismatch(self):
        gate.rendered_images.return_value = {"foreign/image:latest"}
        with self.assertRaises(ValueError): gate.selected_images(SHA, lambda r: self.fail("Do not query incompatible images"))

    def test_digest_revision_mismatch(self):
        with patch.object(gate, "git", return_value="tree"):
            with self.assertRaises(ValueError): gate.selected_images(SHA, lambda ref: {"reference": ref, "revision": "b" * 40})

    def test_application_source_changed(self):
        with patch.object(gate, "git", side_effect=["old", "new"]), self.assertRaises(ValueError):
            gate.selected_images(SHA, lambda r: self.fail("Registry must not be queried"))

    def test_same_application_source_reuses_verified_images(self):
        lock = json.loads((gate.ROOT / gate.LOCK).read_text())
        def inspect(ref):
            return {"reference": ref, "revision": lock["source_commit"], "runtime_digests": [ref.split("@")[1]], "os": "linux", "architecture": "amd64"}
        with patch.object(gate, "git", return_value="same-tree"):
            self.assertEqual(len(gate.selected_images(SHA, inspect)[1]), 2)

    def test_rerun_during_selection(self):
        count = 0
        def query(path):
            nonlocal count
            if "/jobs?" in path: return self.jobs
            count += 1
            return dict(self.run, run_attempt=count)
        with self.assertRaises(ValueError): gate.ci_evidence("7", SHA, query)

    def test_store_missing_and_wrong_identity(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            with self.assertRaises(FileNotFoundError): require_store(root, STORE)
            store(root)
            self.assertEqual(require_store(root, STORE), root.resolve())
            with self.assertRaises(ValueError): require_store(root, "22222222-2222-4222-8222-222222222222")

    def test_selection_substitution(self):
        with tempfile.TemporaryDirectory() as d:
            root = store(Path(d)); receipt = root / "selections/1.json"
            content = {"release_sha": SHA, "repository": gate.REPOSITORY, "branch": gate.BRANCH,
                       "store_id": STORE, "files": {"example": "old"}}
            content["release_id"] = gate.digest(json.dumps(content, sort_keys=True).encode())
            raw = json.dumps(content).encode(); receipt.write_bytes(raw)
            env = {"WORDLE_AZURE_PRIVATE_DIR": str(root), "WORDLE_AZURE_STORE_ID": STORE,
                "WORDLE_RELEASE_SELECTION": str(receipt), "WORDLE_RELEASE_SELECTION_SHA256": gate.digest(raw)}
            with patch.object(gate, "environment", return_value=SHA), patch.object(gate, "source_hashes", return_value={"example": "old"}):
                gate.verify_selection(env)
                receipt.write_text(json.dumps(dict(content, release_sha="b" * 40)))
                with self.assertRaises(ValueError): gate.verify_selection(env)

    def test_missing_operational_reference(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError): verify_references(Path(d), REQUIRED)

    def test_oidc_noninteractive_wiring(self):
        env = {"GITHUB_ACTIONS": "true", "ARM_USE_OIDC": "true", "ARM_USE_AZUREAD": "true", "ARM_USE_CLI": "false",
            "ARM_SUBSCRIPTION_ID": STORE, "ARM_TENANT_ID": STORE, "ARM_CLIENT_ID": STORE,
            "WORDLE_APPROVED_CLIENT_ID": STORE, "ACTIONS_ID_TOKEN_REQUEST_URL": "https://example.actions.githubusercontent.com/idtoken",
            "ACTIONS_ID_TOKEN_REQUEST_TOKEN": "synthetic-ephemeral"}
        values = {"subscription_id": STORE, "tenant_id": STORE}
        validate_oidc(values, env)
        for key in ("ARM_USE_OIDC", "ARM_USE_AZUREAD", "ARM_USE_CLI", "ARM_CLIENT_ID", "ACTIONS_ID_TOKEN_REQUEST_TOKEN"):
            bad = dict(env); bad.pop(key)
            with self.subTest(key=key), self.assertRaises((ValueError, AttributeError)): validate_oidc(values, bad)
        for key in ("ARM_CLIENT_SECRET", "ARM_ACCESS_KEY", "ARM_SAS_TOKEN"):
            with self.subTest(key=key), self.assertRaises(ValueError): validate_oidc(values, dict(env, **{key: "forbidden-synthetic"}))
        validate_oidc(values, {})  # Human CLI path does not acquire CI-only requirements.


if __name__ == "__main__": unittest.main(verbosity=2)
