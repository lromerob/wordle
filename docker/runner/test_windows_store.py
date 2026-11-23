"""Windows-supervised receipt checks; host trust is procedural, never cryptographic."""
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import private_store as store
sys.path.insert(0, str(ROOT / "docker/runner"))
import entrypoint

UID = "11111111-1111-4111-8111-111111111111"

class WindowsReceiptTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="wordle-windows-unit-")
        self.addCleanup(self.temp.cleanup)
        base = Path(self.temp.name)
        self.root = base / "store"; self.root.mkdir()
        self.control = base / "host"; self.control.mkdir()
        self.marker = self.root / ".wordle-private-store.json"
        self.marker.write_text(json.dumps({"format":1,"repository":"lromerob/wordle","store_id":UID,
            "durable_acknowledged":False,"synthetic_fixture":True}))
        for name in ("plans", "selections", "evidence", "backups"): (self.root / name).mkdir()
        self.receipt_path = self.control / "approval.json"
        now = int(time.time())
        self.receipt = {"format":1,"repository":"lromerob/wordle","issuer":"Invoke-WordleRunner.ps1",
            "policy":"owner-system-administrators-v1","store_id":UID,"host_path":"C:/synthetic-store",
            "container_path":str(self.root),"marker_sha256":hashlib.sha256(self.marker.read_bytes()).hexdigest(),
            "acl_sha256":"a"*64,"session_id":UID,"issued_at":now-1,"expires_at":now+300,"fixture_only":True}
        self.save()
        self.mounts = f"1 0 0:1 / {self.control} ro - synthetic synthetic rw\n2 0 0:2 / {self.root} rw - synthetic synthetic rw\n"
        self.env = {"WORDLE_STORE_MODEL":"windows-supervised-test"}
        self.start(patch.object(store, "os", SimpleNamespace(name="posix", environ=self.env)))
        self.start(patch.object(store, "STORE_MOUNT", self.root))
        self.start(patch.object(store, "HOST_APPROVAL", self.receipt_path))
        original = Path.read_text
        self.start(patch.object(Path,"read_text",lambda path,*a,**kw:self.mounts if path.as_posix()=="/proc/self/mountinfo" else original(path,*a,**kw)))

    def start(self, patcher):
        patcher.start(); self.addCleanup(patcher.stop)

    def save(self): self.receipt_path.write_text(json.dumps(self.receipt))
    def verify(self): return store.require_store(self.root, UID)
    def reject(self):
        with self.assertRaises((ValueError,FileNotFoundError)): self.verify()

    def test_explicit_test_mode_valid_separate_read_only_receipt(self):
        self.assertEqual(self.verify(), self.root.resolve())
    def test_env_without_receipt_mount(self): self.mounts=""; self.reject()
    def test_receipt_mount_writable(self): self.mounts=self.mounts.replace(" ro -", " rw -"); self.reject()
    def test_no_dedicated_store_mount(self): self.mounts=self.mounts.splitlines()[0]; self.reject()
    def test_wrong_mounted_store_path(self):
        with patch.object(store,"STORE_MOUNT",self.root.parent): self.reject()
    def test_wrong_receipt_container_path(self): self.receipt["container_path"]="/another-store";self.save();self.reject()
    def test_wrong_receipt_uuid(self): self.receipt["store_id"]="22222222-2222-4222-8222-222222222222";self.save();self.reject()
    def test_marker_changed(self): self.marker.write_text("{}");self.reject()
    def test_marker_hash_changed(self): self.receipt["marker_sha256"]="b"*64;self.save();self.reject()
    def test_marker_absent(self): self.marker.unlink();self.reject()
    def test_fixture_cannot_masquerade_as_durable(self):
        value=json.loads(self.marker.read_text());value["durable_acknowledged"]=True
        self.marker.write_text(json.dumps(value));self.reject()
    def test_missing_required_directory(self): (self.root/"plans").rmdir();self.reject()
    def test_receipt_absent(self): self.receipt_path.unlink();self.reject()
    def test_self_created_store_receipt_is_not_host_receipt(self):
        (self.root/"approval.json").write_bytes(self.receipt_path.read_bytes());self.receipt_path.unlink();self.reject()
    def test_expired_receipt(self): self.receipt["expires_at"]=int(time.time())-1;self.save();self.reject()
    def test_future_receipt(self): self.receipt["issued_at"]=int(time.time())+60;self.save();self.reject()
    def test_excessive_validity(self): self.receipt["expires_at"]=self.receipt["issued_at"]+21601;self.save();self.reject()
    def test_unknown_receipt_fields(self): self.receipt["approved"]=True;self.save();self.reject()
    def test_invalid_windows_host_path(self): self.receipt["host_path"]="relative";self.save();self.reject()
    def test_production_mode_rejects_synthetic_fixture(self): self.env["WORDLE_STORE_MODEL"]="windows-supervised";self.reject()
    def test_unknown_model_refused(self): self.env["WORDLE_STORE_MODEL"]="windows-auto";self.reject()
    def test_registration_refuses_fixture_before_reading_token(self):
        with patch.dict(os.environ,{"WORDLE_STORE_MODEL":"windows-supervised-test","WORDLE_RUNNER_AUTHORIZED_ACTION":"REGISTER_RUN"}), patch.object(entrypoint.os,"getuid",return_value=10001,create=True),patch.object(entrypoint.sys,"stdin") as stream:
            with self.assertRaises(ValueError):entrypoint.token_operation("REGISTER")
            stream.readline.assert_not_called()

if __name__ == "__main__": unittest.main(verbosity=2)
