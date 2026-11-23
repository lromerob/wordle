"""Offline AKS screenshot guards; no browser, Kubernetes or Azure process invoked."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from azure_supervised import ROOT
from test_release_gate import store, STORE
spec = importlib.util.spec_from_file_location("aks_capture", ROOT / "scripts/evidence/aks_capture.py")
capture = importlib.util.module_from_spec(spec); spec.loader.exec_module(capture)


class CaptureTests(unittest.TestCase):
    def setUp(self):
        self.target = dict(subscription_id=STORE, resource_group_name="rg-wordle-test", cluster_name="aks-wordle-test", context="wordle-azure-supervised")
        self.metadata = {"mode": "aks", "environment": "azure-aks", "release_sha": "a" * 40,
            "release_id": "b" * 64, "target_verified": True,
            "runtime_images": [{"image": "ghcr.io/lromerob/wordle-backend@sha256:" + "c" * 64, "imageID": "containerd://sha256:" + "c" * 64}]}

    def test_explicit_authorization_required(self):
        with self.assertRaises(ValueError): capture.validate_request("aks", False, self.target, self.target, capture.NAMESPACES)

    def test_subscription_mismatch(self):
        bad = dict(self.target, subscription_id="other")
        with self.assertRaises(ValueError): capture.validate_request("aks", True, bad, self.target, capture.NAMESPACES)

    def test_group_mismatch(self):
        with self.assertRaises(ValueError): capture.validate_request("aks", True, dict(self.target, resource_group_name="other"), self.target, capture.NAMESPACES)

    def test_cluster_mismatch(self):
        with self.assertRaises(ValueError): capture.validate_request("aks", True, dict(self.target, cluster_name="other"), self.target, capture.NAMESPACES)

    def test_context_mismatch(self):
        with self.assertRaises(ValueError): capture.validate_request("aks", True, dict(self.target, context="kind-other"), self.target, capture.NAMESPACES)

    def test_azure_target_mismatch_stops_before_kubernetes(self):
        import aks_recovery
        good = {"tags":{"project":"wordle"}, "name":self.target["cluster_name"], "resourceGroup":self.target["resource_group_name"],
                "id":"/subscriptions/"+STORE+"/resourceGroups/"+self.target["resource_group_name"]+"/providers/Microsoft.ContainerService/managedClusters/"+self.target["cluster_name"], "fqdn":"approved.example"}
        for field in ("id", "name", "resourceGroup"):
            bad = dict(good); bad[field] = "other"
            with self.subTest(field=field), patch.object(aks_recovery, "az", return_value=bad), patch.object(aks_recovery.Cluster, "call") as call:
                with self.assertRaises(ValueError): aks_recovery.Cluster("unused", self.target["context"], STORE, self.target["resource_group_name"], self.target["cluster_name"])
                call.assert_not_called()

    def test_namespace_mismatch(self):
        with self.assertRaises(ValueError): capture.validate_request("aks", True, self.target, self.target, ("default",))

    def test_capture_mutation_forbidden(self):
        for action in ("delete", "patch", "sql", "promote", "restore"):
            with self.subTest(action=action), self.assertRaises(ValueError):
                capture.validate_request("aks", True, self.target, self.target, capture.NAMESPACES, action)

    def test_unowned_port(self):
        self.assertFalse(capture.allowed_url("http://127.0.0.1:1235/", [1234]))
        self.assertTrue(capture.allowed_url("http://127.0.0.1:1234/", [1234]))

    def test_external_host_and_credentials(self):
        for url in ("https://example.com:1234", "http://127.0.0.1.example.com:1234", "http://user:pass@localhost:1234"):
            with self.subTest(url=url): self.assertFalse(capture.allowed_url(url, [1234]))

    def test_absent_durable_store(self):
        with tempfile.TemporaryDirectory() as d, self.assertRaises(FileNotFoundError):
            capture.require_store(Path(d), STORE)

    def test_incomplete_metadata(self):
        for key in self.metadata:
            value = dict(self.metadata); value.pop(key)
            with self.subTest(key=key), self.assertRaises(ValueError): capture.validate_metadata(value)

    def test_export_success_and_checksums(self):
        with tempfile.TemporaryDirectory() as d:
            root = store(Path(d)); folder = root / "evidence/run"; folder.mkdir(); (folder / "synthetic.txt").write_text("offline fixture, not a screenshot")
            self.assertEqual(len(capture.export_evidence(folder, root / "evidence/run.tar", self.metadata)), 64)
            manifest = json.loads((folder / "manifest.json").read_text())
            self.assertEqual(manifest["metadata"]["environment"], "azure-aks")
            self.assertEqual(manifest["metadata"]["release_sha"], "a" * 40)

    def test_export_failure_does_not_report_success(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); folder = root / "run"; folder.mkdir(); (folder / "fixture").write_text("test")
            with patch.object(capture.tarfile, "open", side_effect=OSError("synthetic export failure")), self.assertRaises(OSError):
                capture.export_evidence(folder, root / "out.tar", self.metadata)

    def test_existing_files_preserved(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); folder = root / "run"; folder.mkdir(); (folder / "fixture").write_text("test")
            target = root / "existing.tar"; target.write_bytes(b"original")
            with self.assertRaises(ValueError): capture.export_evidence(folder, target, self.metadata)
            self.assertEqual(target.read_bytes(), b"original")
            self.assertFalse((folder / "manifest.json").exists())


if __name__ == "__main__": unittest.main(verbosity=2)
