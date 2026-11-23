"""Focused rejection regressions. Synthetic fixtures never authorize a real store."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import private_store

STORE = "11111111-1111-4111-8111-111111111111"

class StoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="wordle-store-unit-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.marker = self.root / ".wordle-private-store.json"
        self.marker.write_text(json.dumps({"format": 1, "repository": "lromerob/wordle",
            "store_id": STORE, "durable_acknowledged": True}))
        for name in ("plans", "selections", "evidence", "backups"):
            (self.root / name).mkdir()

    def mode(self, permissions):
        original = Path.stat
        def stat(path, *args, **kwargs):
            actual = original(path, *args, **kwargs)
            values = list(actual)
            values[0] = (actual.st_mode & ~0o777) | permissions
            return os.stat_result(values)
        # Model only permission bits here. Real Linux modes are tested in Docker separately.
        return patch.object(Path, "stat", stat)

    def verify(self):
        return private_store.require_store(self.root, STORE)

    def test_posix_private_permissions(self):
        with patch.object(private_store, "os", SimpleNamespace(name="posix", environ=os.environ)), self.mode(0o700):
            self.assertEqual(self.verify(), self.root)

    def test_posix_excessive_permissions(self):
        with patch.object(private_store, "os", SimpleNamespace(name="posix", environ=os.environ)), self.mode(0o777):
            with self.assertRaisesRegex(ValueError, "private to the runner"): self.verify()

    def test_0777_never_enables_windows_automatically(self):
        with patch.object(private_store, "os", SimpleNamespace(name="posix", environ=os.environ)), self.mode(0o777):
            with self.assertRaises(ValueError): self.verify()

    def test_environment_assertion_does_not_authorize_windows(self):
        with patch.dict(os.environ, {"WORDLE_STORE_MODEL": "windows", "WORDLE_HOST_ACL_APPROVED": "true"}), patch.object(private_store, "os", SimpleNamespace(name="posix", environ=os.environ)), self.mode(0o777):
            with self.assertRaises(ValueError): self.verify()

    def test_self_created_approval_cannot_bypass_posix(self):
        (self.root / "host-approval.json").write_text(json.dumps({"approved": True, "store_id": STORE}))
        with patch.object(private_store, "os", SimpleNamespace(name="posix", environ=os.environ)), self.mode(0o777):
            with self.assertRaises(ValueError): self.verify()

    def test_missing_path(self):
        with self.assertRaises(FileNotFoundError): private_store.require_store(self.root / "absent", STORE)

    def test_checkout_path(self):
        with self.assertRaisesRegex(ValueError, "independent"): private_store.require_store(ROOT, STORE)

    def test_wrong_uuid(self):
        with self.assertRaises(ValueError): private_store.require_store(self.root, "22222222-2222-4222-8222-222222222222")

    def test_missing_marker(self):
        self.marker.unlink()
        with self.assertRaises(FileNotFoundError): self.verify()

    def test_unapproved_marker(self):
        value = json.loads(self.marker.read_text()); value["durable_acknowledged"] = False
        self.marker.write_text(json.dumps(value))
        with self.assertRaisesRegex(ValueError, "Unapproved"): self.verify()

    def test_marker_extra_keys(self):
        value = json.loads(self.marker.read_text()); value["host_acl_approved"] = True
        self.marker.write_text(json.dumps(value))
        with self.assertRaises(ValueError): self.verify()

    def test_missing_directory(self):
        (self.root / "backups").rmdir()
        with self.assertRaisesRegex(ValueError, "Missing"): self.verify()

    @unittest.skipUnless(os.name == "nt", "Native Windows host metadata test")
    def test_windows_host_diagnostic_rejects_missing_path(self):
        self.host_diagnostic(str(self.root / "missing"), "BLOCKED")

    @unittest.skipUnless(os.name == "nt", "Native Windows host metadata test")
    def test_windows_host_diagnostic_rejects_checkout(self):
        self.host_diagnostic(str(ROOT), "BLOCKED")

    @unittest.skipUnless(os.name == "nt", "Native Windows host metadata test")
    def test_windows_host_preflight_rejects_unapproved_legacy_fixture(self):
        self.host_diagnostic(str(self.root), "BLOCKED")

    def host_diagnostic(self, path, status):
        p = subprocess.run(["pwsh", "-NoProfile", "-File", str(ROOT / "docker/runner/Test-WordlePrivateStore.ps1"), "-StorePath", path], capture_output=True, text=True, timeout=30)
        self.assertEqual(p.returncode, 2, p.stderr)
        value = json.loads(p.stdout)
        self.assertEqual(value["status"], status)

        if status == "NOT VERIFIED":
            self.assertTrue(value["path_checked"])
            self.assertTrue(value["acl_checked"])

if __name__ == "__main__": unittest.main(verbosity=2)
