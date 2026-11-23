"""Focused offline regressions; no Azure, GitHub, DNS or Blob connections."""
import json
import unittest
import urllib.error
from unittest.mock import patch
import storage_connectivity_test as diagnostic


class SafetyTests(unittest.TestCase):
    base = "https://api.github.com/repos/lromerob/wordle/issues/123"
    started = "2026-11-23T10:00:00Z"
    phrase = "WORDLE-STORAGE-READY 123 2 " + "a" * 40 + " 8.8.8.8 " + "b" * 32

    def comment(self):
        return {"id": 987, "user": {"login": "lromerob", "type": "User"},
                "author_association": "OWNER", "issue_url": self.base, "body": self.phrase,
                "created_at": "2026-11-23T10:00:01Z", "updated_at": "2026-11-23T10:00:01Z"}

    def matches(self, comment):
        return diagnostic.confirmation_matches(comment, self.phrase, self.started, self.base)

    def test_public_ipv4(self):
        self.assertEqual(diagnostic.public_ipv4("8.8.8.8"), "8.8.8.8")

    def test_reject_non_public_or_ranges(self):
        for value in ("::1", "2606:4700:4700::1111", "10.0.0.1", "127.0.0.1", "192.0.2.1",
                      "0.0.0.0", "224.0.0.1", "255.255.255.255", "8.8.8.8/32", "0.0.0.0/0", "bad"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                diagnostic.public_ipv4(value)

    def test_exact_owner_confirmation_accepted(self):
        self.assertTrue(self.matches(self.comment()))

    def test_other_author_or_association_rejected(self):
        for change in ({"user": {"login": "attacker", "type": "User"}},
                       {"user": {"login": "lromerob", "type": "Bot"}},
                       {"author_association": "CONTRIBUTOR"}):
            self.assertFalse(self.matches(self.comment() | change))

    def test_other_issue_or_repository_rejected(self):
        for url in (self.base + "4", self.base.replace("wordle", "other")):
            self.assertFalse(self.matches(self.comment() | {"issue_url": url}))

    def test_old_or_edited_confirmation_rejected(self):
        for change in ({"created_at": "2026-11-22T10:00:00Z", "updated_at": "2026-11-22T10:00:00Z"},
                       {"updated_at": "2026-11-23T10:01:00Z"}, {"updated_at": None}):
            self.assertFalse(self.matches(self.comment() | change))

    def test_partial_or_whitespace_confirmation_rejected(self):
        for body in (self.phrase + " extra", "prefix " + self.phrase, self.phrase + " ", self.phrase + "\n"):
            self.assertFalse(self.matches(self.comment() | {"body": body}))

    def test_other_run_attempt_sha_ip_nonce_rejected(self):
        for index in range(1, 6):
            parts = self.phrase.split()
            parts[index] = "different"
            self.assertFalse(self.matches(self.comment() | {"body": " ".join(parts)}))

    def test_wait_accepts_expected_comment(self):
        with patch.object(diagnostic, "public_get", return_value=json.dumps([self.comment()]).encode()), \
             patch.object(diagnostic.time, "monotonic", return_value=0):
            self.assertEqual(diagnostic.wait_for_confirmation(self.base, self.phrase, self.started)["id"], 987)

    def test_wait_api_error_fails_closed(self):
        error = urllib.error.HTTPError(self.base, 403, "rate limited", {}, None)
        with patch.object(diagnostic, "public_get", side_effect=error), self.assertRaises(urllib.error.HTTPError):
            diagnostic.wait_for_confirmation(self.base, self.phrase, self.started)

    def test_wait_timeout_is_bounded(self):
        clock = [0]
        def sleep(seconds):
            clock[0] += seconds
        with patch.object(diagnostic, "public_get", return_value=b"[]"), \
             patch.object(diagnostic.time, "monotonic", side_effect=lambda: clock[0]), \
             patch.object(diagnostic.time, "sleep", side_effect=sleep), self.assertRaises(TimeoutError):
            diagnostic.wait_for_confirmation(self.base, self.phrase, self.started, wait_seconds=3)
        self.assertEqual(clock[0], 3)

    def test_redirects_fail_closed(self):
        with self.assertRaises(ValueError):
            diagnostic.NoRedirect().redirect_request(None, None, None, None, None, None)

    def test_changed_azure_context_rejected(self):
        env = {"TEST_SUBSCRIPTION_ID": "expected", "TEST_TENANT_ID": "expected", "TEST_CLIENT_ID": "expected"}
        with patch.dict(diagnostic.os.environ, env), patch.object(diagnostic, "az_json", return_value={
                "id": "other", "tenantId": "expected", "user": {"type": "servicePrincipal", "name": "expected"}}), \
             self.assertRaises(ValueError):
            diagnostic.validate_context()


if __name__ == "__main__":
    unittest.main(verbosity=2)
