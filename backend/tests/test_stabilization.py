"""Focused regressions using the existing offline HTTP fixture."""
import copy
import unittest

import test_backend as fixtures


@unittest.skipUnless(fixtures.WEB_AVAILABLE, "FastAPI and HTTPX are not installed")
class StabilizationTests(unittest.TestCase):
    setUp = fixtures.EndpointTests.setUp
    guess = fixtures.EndpointTests.guess

    def test_invalid_characters_even_if_present_in_dictionary(self):
        for word in ("12345", "CAS S", "CAS-S", "CAFÉS", "CAßS", "ßAAAA"):
            with self.subTest(word=word):
                self.db.rows["palabras"].append({"palabra": word.upper()})
                before = copy.deepcopy(self.db.rows)
                self.assertEqual(self.guess(word).status_code, 400)
                self.assertEqual(self.db.rows, before)

    def test_spanish_enye_and_case_remain_supported(self):
        self.db.rows["palabras"].append({"palabra": "NIÑOS"})
        response = self.guess(" niños ")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.db.rows["intentos"][0]["palabra"], "NIÑOS")

    def test_unknown_state_does_not_disclose_answer(self):
        for state in ("pendiente", "", None):
            with self.subTest(state=state):
                self.db.rows["partidas"][0]["estado"] = state
                response = self.client.get("/game/game-1")
                self.assertEqual(response.status_code, 200)
                self.assertNotIn("palabra_secreta", response.json()["partida"])
                before = copy.deepcopy(self.db.rows)
                self.assertEqual(self.guess().status_code, 400)
                self.assertEqual(self.db.rows, before)

    def test_missing_game_does_not_use_provider_single(self):
        from unittest.mock import patch
        with patch.object(fixtures.MemoryQuery, "single", side_effect=AssertionError("single must not be used")):
            self.assertEqual(self.guess(game="missing").status_code, 404)
            self.assertEqual(self.client.get("/game/missing").status_code, 404)

    def test_average_updates_on_win_and_stays_on_loss(self):
        self.db.rows["estadisticas"].append({
            "usuario_id": "owner", "partidas_jugadas": 3,
            "partidas_ganadas": 2, "racha_actual": 1,
            "racha_maxima": 2, "intentos_promedio": 4,
        })
        self.assertEqual(self.guess("CASAS").status_code, 200)
        stats = self.db.rows["estadisticas"][0]
        self.assertEqual(stats["intentos_promedio"], 3)
        self.assertEqual(stats["partidas_ganadas"], 3)
        self.db.rows["partidas"][0].update(estado="en_curso", intentos_usados=5)
        self.assertEqual(self.guess().json()["estado"], "perdida")
        self.assertEqual(stats["intentos_promedio"], 3)
        self.assertEqual(stats["partidas_jugadas"], 5)
        self.assertEqual(stats["racha_actual"], 0)

    def test_first_win_after_losses_sets_average(self):
        self.db.rows["estadisticas"].append({
            "usuario_id": "owner", "partidas_jugadas": 1,
            "partidas_ganadas": 0, "racha_actual": 0,
            "racha_maxima": 0, "intentos_promedio": 0,
        })
        self.assertEqual(self.guess().status_code, 200)
        self.assertEqual(self.guess("CASAS").status_code, 200)
        self.assertEqual(self.db.rows["estadisticas"][0]["intentos_promedio"], 2)
