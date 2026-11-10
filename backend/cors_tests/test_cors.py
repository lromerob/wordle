"""Focused CORS suite. Separate discovery preserves the existing CI 55-case guard."""
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tests"))
import test_backend as fixtures
from app.main import cors_origins


class CorsTests(unittest.TestCase):
    setUp = fixtures.EndpointTests.setUp

    def preflight(self, origin, method="POST", headers="content-type"):
        return self.client.options("/game/intento", headers={
            "Origin": origin, "Access-Control-Request-Method": method,
            "Access-Control-Request-Headers": headers,
        })

    def test_allowed_origins_exact_and_without_credentials(self):
        for origin in ("http://localhost:5173", "http://127.0.0.1:5173"):
            response = self.client.get("/health", headers={"Origin": origin})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.headers["access-control-allow-origin"], origin)
            self.assertIn("Origin", response.headers["vary"])
            self.assertNotIn("access-control-allow-credentials", response.headers)

    def test_untrusted_origin_get_200_is_not_browser_permission(self):
        for origin in ("https://untrusted.invalid", "http://localhost:5174", "http://localhost:5173.evil.invalid", "null"):
            response = self.client.get("/health", headers={"Origin": origin})
            self.assertEqual(response.status_code, 200)
            self.assertNotIn("access-control-allow-origin", response.headers)

    def test_allowed_preflight(self):
        response = self.preflight("http://localhost:5173")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["access-control-allow-origin"], "http://localhost:5173")
        self.assertEqual(response.headers["access-control-allow-methods"], "GET, POST")
        self.assertIn("content-type", response.headers["access-control-allow-headers"].lower())
        self.assertNotIn("access-control-allow-credentials", response.headers)

    def test_untrusted_preflight_denied(self):
        response = self.preflight("https://untrusted.invalid")
        self.assertEqual(response.status_code, 400)
        self.assertNotIn("access-control-allow-origin", response.headers)

    def test_extra_methods_and_headers_denied(self):
        self.assertEqual(self.preflight("http://localhost:5173", method="DELETE").status_code, 400)
        self.assertEqual(self.preflight("http://localhost:5173", headers="x-unneeded").status_code, 400)

    def test_request_without_origin_unchanged(self):
        response = self.client.get("/health")
        self.assertEqual(response.json(), {"status": "ok"})
        self.assertNotIn("access-control-allow-origin", response.headers)

    def test_game_flow_with_allowed_origin(self):
        headers = {"Origin": "http://localhost:5173"}
        created = self.client.post("/game/nueva", params={"usuario_id": "cors-demo"}, headers=headers)
        self.assertEqual(created.status_code, 200)
        self.assertEqual(created.headers["access-control-allow-origin"], headers["Origin"])
        response = self.client.post("/game/intento", json={"partida_id":"game-1","usuario_id":"owner","palabra":"CASAS"}, headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["estado"], "ganada")

    def test_environment_allowlist_and_empty(self):
        with patch.dict(os.environ, {"WORDLE_CORS_ORIGINS": " https://demo.example:8443,https://demo.example:8443 "}):
            self.assertEqual(cors_origins(), ["https://demo.example:8443"])
        with patch.dict(os.environ, {"WORDLE_CORS_ORIGINS": ""}):
            self.assertEqual(cors_origins(), [])

    def test_invalid_configuration_refused(self):
        for value in ("*", "https://*.example", "null", "http://localhost:5173/", "http://localhost/path", "http://user:password@example", "https://example?x=1", "http://example:bad"):
            with self.subTest(value=value), patch.dict(os.environ, {"WORDLE_CORS_ORIGINS": value}):
                with self.assertRaises(ValueError): cors_origins()


if __name__ == "__main__":
    unittest.main()
