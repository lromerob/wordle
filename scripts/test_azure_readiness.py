"""Focused offline guards; no real cloud, database, Terraform or Kubernetes calls."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import azure_preflight as preflight
import azure_supervised as supervised
import aks_recovery as recovery
import azure_release as release


class ReadinessTests(unittest.TestCase):
    def setUp(self):
        self.values = {"subscription_id": "11111111-1111-4111-8111-111111111111",
            "tenant_id": "22222222-2222-4222-8222-222222222222", "resource_group_name": "rg-wordle-academic",
            "node_resource_group_name": "rg-wordle-academic-nodes", "cluster_name": "aks-wordle-academic",
            "admin_group_object_ids": ["33333333-3333-4333-8333-333333333333"],
            # Public-address syntax fixture only; never an approved deployment input.
            "api_authorized_cidrs": ["1.1.1.1/32"], "api_access_approved": True}
        self.backend = {"resource_group_name": "rg-wordle-state", "storage_account_name": "wordleteststate",
            "container_name": "tfstate", "key": "wordle/aks-demo.tfstate", "use_azuread_auth": True}

    def test_supplied_variables_are_checked_offline(self):
        with tempfile.TemporaryDirectory() as folder:
            file=Path(folder)/"variables.json";file.write_text(json.dumps(self.values))
            result=preflight.assess(offline=True,variables=file)
            self.assertTrue(result["local"]["supplied_variables_valid"])
            self.assertIsNone(result["authenticated"])
            file.write_text(json.dumps(dict(self.values,api_authorized_cidrs=["0.0.0.0/0"])))
            self.assertFalse(preflight.assess(offline=True,variables=file)["local"]["supplied_variables_valid"])

    def test_selected_subscription_mismatch_stops_provider_queries(self):
        with tempfile.TemporaryDirectory() as folder:
            file=Path(folder)/"variables.json";file.write_text(json.dumps(self.values))
            with patch.object(preflight.shutil,"which",return_value="az"),patch.object(preflight,"query",return_value={"id":"other","tenantId":self.values["tenant_id"],"state":"Enabled"}) as query:
                result=preflight.assess(variables=file)
                self.assertFalse(result["selected_subscription_matches_variables"])
                self.assertEqual(query.call_count,1)

    def test_pool_parameters_reject_invalid_counts_and_b_series(self):
        for values in (dict(self.values,node_count=1),dict(self.values,node_count=True),dict(self.values,node_vm_size="Standard_B2s")):
            with self.assertRaises(ValueError):supervised.validate_inputs(values,self.backend)

    def test_preflight_uses_the_explicit_terraform_region_and_sku(self):
        with tempfile.TemporaryDirectory() as folder:
            file=Path(folder)/"variables.json";file.write_text(json.dumps(dict(self.values,location="northeurope",node_vm_size="Standard_D4as_v5",node_count=3)))
            result=preflight.assess(offline=True,variables=file)
            self.assertEqual((result["location"],result["sku"],result["nodes"]),("northeurope","Standard_D4as_v5",3))

    def test_default_region_is_read_from_terraform(self):
        with patch.object(preflight, "query") as query:
            result = preflight.assess(offline=True)
        self.assertEqual(result["location"], "swedencentral")
        self.assertEqual(result["local"]["terraform_defaults"],
                         {"region": "swedencentral", "sku": "Standard_D4s_v5", "nodes": 2})
        query.assert_not_called()

    def test_api_requires_one_public_host_and_explicit_approval(self):
        for ranges in ([], ["0.0.0.0/0"], ["0.0.0.0/32"], ["192.0.2.1/32"],
                       ["10.0.0.1/32"], ["127.0.0.1/32"], ["::1/128"],
                       ["PENDING"], [None], ["1.1.1.1"], ["1.1.1.0/24"], ["1.1.1.1/32", "1.0.0.1/32"]):
            with self.subTest(ranges=ranges), self.assertRaises(ValueError):
                supervised.validate_inputs(dict(self.values, api_authorized_cidrs=ranges), self.backend)
        for approval in (False, None, "true", 1):
            with self.subTest(approval=approval), self.assertRaises(ValueError):
                supervised.validate_inputs(dict(self.values, api_access_approved=approval), self.backend)
        missing = dict(self.values)
        missing.pop("api_access_approved")
        with self.assertRaises(ValueError):
            supervised.validate_inputs(missing, self.backend)
        supervised.validate_inputs(self.values, self.backend)

    def test_terraform_api_filter_rejects_private_and_reserved_hosts(self):
        # Read the exact HCL regex literal, not a duplicate Python implementation.
        # This tests the filter; Terraform fmt separately parses the HCL syntax.
        import re
        source = (supervised.TF / "variables.tf").read_text(encoding="utf-8")
        block = source.split('variable "api_authorized_cidrs" {', 1)[1].split('variable "api_access_approved"', 1)[0]
        pattern = json.loads(re.search(r'regex\(("(?:[^"\\]|\\.)*")', block)[1])
        rejected = ["0.0.0.0/32", "10.10.0.1/32", "100.64.0.1/32", "100.127.255.254/32",
                    "127.0.0.1/32", "169.254.1.1/32", "172.16.0.1/32", "172.31.255.254/32",
                    "192.0.0.1/32", "192.0.2.1/32", "192.88.99.1/32", "192.168.1.1/32",
                    "198.18.0.1/32", "198.19.255.254/32", "198.51.100.1/32", "203.0.113.1/32",
                    "224.0.0.1/32", "239.255.255.254/32", "240.0.0.1/32", "255.255.255.255/32"]
        for cidr in rejected:
            with self.subTest(cidr=cidr):
                self.assertIsNotNone(re.search(pattern, cidr))
        for cidr in ("1.1.1.1/32", "100.63.255.254/32", "100.128.0.1/32",
                     "172.15.255.254/32", "172.32.0.1/32", "223.255.255.254/32"):
            with self.subTest(cidr=cidr):
                self.assertIsNone(re.search(pattern, cidr))

    def test_missing_cli_does_not_login(self):
        with patch.object(preflight.shutil, "which", return_value=None), patch.object(preflight, "query") as query:
            self.assertFalse(preflight.assess()["authenticated"])
            query.assert_not_called()

    def test_state_must_be_independent(self):
        backend = dict(self.backend, resource_group_name=self.values["resource_group_name"])
        with self.assertRaises(ValueError):supervised.validate_inputs(self.values, backend)

    def test_no_backend_credentials_or_open_api(self):
        with self.assertRaises(ValueError):supervised.validate_inputs(self.values, dict(self.backend, access_key="synthetic-not-a-key"))
        with self.assertRaises(ValueError):supervised.validate_inputs(dict(self.values, api_authorized_cidrs=["0.0.0.0/0"]), self.backend)

    def test_local_prepare_only_and_drift_detection(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);v=root/"v.json";b=root/"b.json";work=root/"work"
            v.write_text(json.dumps(self.values));b.write_text(json.dumps(self.backend))
            with patch.object(supervised, "run") as run:
                supervised.prepare(work,v,b);run.assert_not_called()
            marker=json.loads((work/"workspace.json").read_text())
            self.assertEqual(marker["fingerprint"],supervised.fingerprint(work))
            with (work/"main.tf").open("a") as file:file.write("\n# changed\n")
            self.assertNotEqual(marker["fingerprint"],supervised.fingerprint(work))

    def test_no_deletion_in_create_plan(self):
        plan={"resource_changes":[{"mode":"managed","address":"azurerm_resource_group.wordle",
            "change":{"actions":["delete"],"before":{"name":"rg-wordle-academic"}}}]}
        with self.assertRaises(ValueError):supervised.check_plan(plan,"deploy",self.values)
        supervised.check_plan(plan,"destroy",self.values)

    def test_unknown_resource_and_wrong_group_rejected(self):
        for address,group in (("azurerm_storage_account.unrelated","rg-wordle-academic"),
                              ("azurerm_kubernetes_cluster.wordle","wrong-group")):
            plan={"resource_changes":[{"address":address,"change":{"actions":["create"],"after":{
                "name":"aks-wordle-academic","resource_group_name":group}}}]}
            with self.assertRaises(ValueError):supervised.check_plan(plan,"deploy",self.values)

    def test_kind_and_persistent_contexts_refused_before_azure(self):
        with patch.object(recovery,"az") as az:
            for context in ("kind-wordle", "wordle-pg06-00f26f1f", "pg05"):
                with self.assertRaises(ValueError):recovery.Cluster("unused",context,self.values["subscription_id"],"rg-wordle","aks-wordle")
            az.assert_not_called()

    def test_aks_endpoint_default_https_port_and_wrong_target(self):
        with patch.object(recovery, "az", return_value={"tags":{"project":"wordle"},"fqdn":"approved.example", "id":"/subscriptions/"+self.values["subscription_id"]+"/resourceGroups/rg-wordle/providers/Microsoft.ContainerService/managedClusters/aks-wordle", "name":"aks-wordle", "resourceGroup":"rg-wordle"}):
            with patch.object(recovery.Cluster, "call", return_value=b"https://approved.example:443"):
                recovery.Cluster("unused", "aks-demo", self.values["subscription_id"], "rg-wordle", "aks-wordle")
            with patch.object(recovery.Cluster, "call", return_value=b"https://other.example:443"):
                with self.assertRaises(ValueError):
                    recovery.Cluster("unused", "aks-demo", self.values["subscription_id"], "rg-wordle", "aks-wordle")

    def test_wrong_subscription_rejected_without_context_change(self):
        with patch.object(supervised, "az", return_value={"id":"other","tenantId":self.values["tenant_id"],"state":"Enabled"}):
            with self.assertRaises(ValueError):supervised.authenticate(self.values)

    def test_execute_without_reviewed_hash_never_applies(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);v=root/"v.json";b=root/"b.json";work=root/"work"
            v.write_text(json.dumps(self.values));b.write_text(json.dumps(self.backend));supervised.prepare(work,v,b)
            (work/"review.json").write_text("{}")
            with patch.object(supervised.shutil,"which",return_value="terraform"), patch.object(supervised,"authenticate"), patch.object(supervised,"run") as run:
                with self.assertRaises(ValueError):
                    supervised.operate("execute",work,"EXECUTE rg-wordle-academic/aks-wordle-academic")
                run.assert_not_called()

    def test_private_workspace_outside_repository(self):
        with self.assertRaises(ValueError):supervised.external(supervised.ROOT/"private")

    def test_release_integrity_and_tampering(self):
        with tempfile.TemporaryDirectory() as folder:
            target=Path(folder)/"package";release.create(target);release.verify(target)
            with (target/"source.tar").open("ab") as file:file.write(b"tamper")
            with self.assertRaises(ValueError):release.verify(target)


if __name__ == "__main__":
    unittest.main(verbosity=2)
