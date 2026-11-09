"""Offline tests using an async in-memory domain adapter, never a database."""
import ast
import copy
from contextlib import asynccontextmanager
import importlib.util
from pathlib import Path
import socket
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

_SOCKET_CONNECT = socket.socket.connect


def offline_connect(sock, address):
    # Windows asyncio uses a loopback socketpair for internal wakeups.
    if isinstance(address, tuple) and address[0] in ("127.0.0.1", "::1"):
        return _SOCKET_CONNECT(sock, address)
    raise AssertionError("External network forbidden")


BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))


def load_evaluator():
    # Run the actual pure function even when the web dependencies are unavailable.
    tree = ast.parse((BACKEND / "app/routers/game.py").read_text(encoding="utf-8"))
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "evaluar_intento")
    namespace = {}
    exec(compile(ast.Module(body=[node], type_ignores=[]), str(BACKEND / "app/routers/game.py"), "exec"), namespace)
    return namespace["evaluar_intento"]


class EvaluationTests(unittest.TestCase):
    def test_wordle_cases(self):
        evaluate = load_evaluator()
        cases = [
            ("CASAS", "CASAS", ["correcto"] * 5),
            ("CASAS", "PERRO", ["ausente"] * 5),
            ("CASAS", "SACAS", ["presente", "correcto", "presente", "correcto", "correcto"]),
            ("CASAS", "AAAAA", ["ausente", "correcto", "ausente", "correcto", "ausente"]),
            ("CASAS", "SSSSS", ["ausente", "ausente", "correcto", "ausente", "correcto"]),
        ]
        for secret, guess, expected in cases:
            with self.subTest(guess=guess):
                result = evaluate(secret, guess)
                self.assertEqual([r["estado"] for r in result], expected)
                self.assertEqual([r["letra"] for r in result], list(guess))

    def test_dependency_import_is_lazy(self):
        with patch("socket.socket", side_effect=AssertionError("Network forbidden")):
            import app.database as database
            self.assertTrue(callable(database.create_pool))
            self.assertFalse(hasattr(database, "pool"))


class MemoryDB:
    def __init__(self):
        self.rows = {
            "palabras": [{"palabra": w} for w in ("CASAS", "PERRO", "SACAS", "AAAAA")],
            "partidas": [{"id": "game-1", "usuario_id": "owner", "palabra_secreta": "CASAS", "intentos_usados": 0, "estado": "en_curso"}],
            "intentos": [], "estadisticas": [],
        }

    @asynccontextmanager
    async def transaction(self):
        # Snapshot for offline fault tests only, not a model of PostgreSQL locks.
        before = copy.deepcopy(self.rows)
        try:
            yield
        except BaseException:
            self.rows.clear()
            self.rows.update(before)
            raise

    async def get_game_for_update(self, partida_id):
        # Deliberately no concurrency guarantees in MemoryDB.
        return await self.get_game(partida_id)

    async def get_stats_for_update(self, usuario_id):
        return await self.get_stats(usuario_id)

    async def list_words(self):
        return copy.deepcopy(self.rows["palabras"])

    async def create_game(self, values):
        row = dict(copy.deepcopy(values), id=f"new-{len(self.rows['partidas']) + 1}")
        self.rows["partidas"].append(row)
        return copy.deepcopy(row)

    async def get_game(self, partida_id):
        return copy.deepcopy(next((r for r in self.rows["partidas"] if str(r["id"]) == str(partida_id)), None))

    async def word_exists(self, word):
        return any(r["palabra"] == word for r in self.rows["palabras"])

    async def add_guess(self, values):
        self.rows["intentos"].append(dict(copy.deepcopy(values), id=f"new-{len(self.rows['intentos']) + 1}"))

    async def update_game(self, partida_id, values):
        for row in self.rows["partidas"]:
            if str(row["id"]) == str(partida_id):
                row.update(copy.deepcopy(values))

    async def get_guesses(self, partida_id):
        return copy.deepcopy(sorted((r for r in self.rows["intentos"] if str(r["partida_id"]) == str(partida_id)), key=lambda r: r["numero"]))

    async def get_stats(self, usuario_id):
        return copy.deepcopy(next((r for r in self.rows["estadisticas"] if r["usuario_id"] == usuario_id), None))

    async def create_stats(self, values):
        self.rows["estadisticas"].append(copy.deepcopy(values))

    async def update_stats(self, usuario_id, values):
        for row in self.rows["estadisticas"]:
            if row["usuario_id"] == usuario_id:
                row.update(copy.deepcopy(values))

    async def ranking(self):
        columns = ("usuario_id", "partidas_ganadas", "racha_maxima", "partidas_jugadas")
        rows = sorted(self.rows["estadisticas"], key=lambda r: r["partidas_ganadas"], reverse=True)[:10]
        return [{key: row[key] for key in columns} for row in rows]


class HandlerTests(unittest.TestCase):
    """Exercise real handler bodies offline; HTTP/framework tests remain separate."""
    def setUp(self):
        import asyncio
        self.run_async = asyncio.run
        tree = ast.parse((BACKEND / "app/routers/game.py").read_text(encoding="utf-8"))
        functions = [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
        for node in functions:
            node.decorator_list = []
            for argument in node.args.args:
                argument.annotation = None
            node.args.defaults = [ast.Constant(None) if isinstance(d, ast.Call) else d for d in node.args.defaults]
        class HandlerError(Exception):
            def __init__(self, status_code, detail):
                self.status_code = status_code
        namespace = {"HTTPException": HandlerError, "MAX_INTENTOS": 6, "LONGITUD_PALABRA": 5}
        exec(compile(ast.fix_missing_locations(ast.Module(body=functions, type_ignores=[])), "game-handlers", "exec"), namespace)
        self.handlers, self.error, self.db = namespace, HandlerError, MemoryDB()
        network = patch("socket.socket.connect", new=offline_connect)
        network.start()
        self.addCleanup(network.stop)

    def guess(self, word="PERRO", owner="owner"):
        body = SimpleNamespace(partida_id="game-1", palabra=word, usuario_id=owner)
        return self.run_async(self.handlers["registrar_intento"](body, self.db))

    def test_six_failures_then_no_writes(self):
        for attempt in range(1, 7):
            result = self.guess()
            self.assertEqual(result["intentos_usados"], attempt)
            self.assertEqual(result["estado"], "perdida" if attempt == 6 else "en_curso")
            self.assertEqual(result["palabra_secreta"], "CASAS" if attempt == 6 else None)
        before = copy.deepcopy(self.db.rows)
        with self.assertRaises(self.error) as error:
            self.guess()
        self.assertEqual(error.exception.status_code, 400)
        self.assertEqual(self.db.rows, before)
        self.assertEqual(len(self.db.rows["intentos"]), 6)

    def test_sixth_attempt_can_win(self):
        for _ in range(5):
            self.guess()
        self.assertEqual(self.guess(" casas ")["estado"], "ganada")
        self.assertEqual(self.db.rows["estadisticas"][0]["partidas_ganadas"], 1)

    def test_owner_mismatch_has_no_side_effects(self):
        before = copy.deepcopy(self.db.rows)
        with self.assertRaises(self.error) as error:
            self.guess(owner="other")
        self.assertEqual(error.exception.status_code, 403)
        self.assertEqual(self.db.rows, before)

    def test_active_get_removes_answer_without_mutating_database(self):
        response = self.run_async(self.handlers["estado_partida"]("game-1", self.db))
        self.assertNotIn("palabra_secreta", response["partida"])
        self.assertEqual(self.db.rows["partidas"][0]["palabra_secreta"], "CASAS")

    def test_invalid_guess_has_no_side_effects(self):
        for word in ("CASA", "ZZZZZ"):
            before = copy.deepcopy(self.db.rows)
            with self.assertRaises(self.error) as error:
                self.guess(word)
            self.assertEqual(error.exception.status_code, 400)
            self.assertEqual(self.db.rows, before)

    def test_repeated_letters_through_handler(self):
        result = self.guess("AAAAA")
        self.assertEqual([r["estado"] for r in result["resultado"]], ["ausente", "correcto", "ausente", "correcto", "ausente"])


WEB_AVAILABLE = all(importlib.util.find_spec(m) for m in ("fastapi", "httpx"))


@unittest.skipUnless(WEB_AVAILABLE, "FastAPI and HTTPX are not installed")
class EndpointTests(unittest.TestCase):
    def setUp(self):
        from fastapi.testclient import TestClient
        from app.database import get_repository
        from app.main import app
        self.app, self.dependency = app, get_repository
        self.db = MemoryDB()
        self.app.dependency_overrides[get_repository] = lambda: self.db
        self.addCleanup(self.app.dependency_overrides.clear)
        self.client = self.enterContext(TestClient(app))
        # A mistaken SQL dependency must fail before libpq (which bypasses Python sockets).
        self.enterContext(patch("psycopg.AsyncConnection.connect", side_effect=AssertionError("Database forbidden")))
        # Any accidental production pool or external socket fails the test.
        self.network = patch("socket.socket.connect", new=offline_connect)
        self.network.start()
        self.addCleanup(self.network.stop)
        self.factory = patch("app.database.create_pool", side_effect=AssertionError("Production pool forbidden"))
        self.factory.start()
        self.addCleanup(self.factory.stop)

    def guess(self, word="PERRO", user="owner", game="game-1"):
        return self.client.post("/game/intento", json={"partida_id": game, "usuario_id": user, "palabra": word})

    def test_health_and_new_game(self):
        self.assertEqual(self.client.get("/health").json(), {"status": "ok"})
        response = self.client.post("/game/nueva", params={"usuario_id": "owner"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("partida_id", response.json())
        self.assertNotIn("palabra_secreta", response.json())

    def test_active_game_never_exposes_answer_and_keeps_storage(self):
        response = self.client.get("/game/game-1")
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("palabra_secreta", response.json()["partida"])
        self.assertEqual(self.db.rows["partidas"][0]["palabra_secreta"], "CASAS")

    def test_completed_game_retains_existing_response(self):
        self.db.rows["partidas"][0]["estado"] = "perdida"
        self.assertEqual(self.client.get("/game/game-1").json()["partida"]["palabra_secreta"], "CASAS")

    def test_owner_mismatch_writes_nothing(self):
        before = copy.deepcopy(self.db.rows)
        self.assertEqual(self.guess(user="other").status_code, 403)
        self.assertEqual(self.db.rows, before)

    def test_win_normalizes_and_blocks_further_guesses(self):
        result = self.guess(" casas ")
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json()["estado"], "ganada")
        self.assertEqual(result.json()["intentos_usados"], 1)
        self.assertEqual([r["estado"] for r in result.json()["resultado"]], ["correcto"] * 5)
        before = copy.deepcopy(self.db.rows)
        self.assertEqual(self.guess().status_code, 400)
        self.assertEqual(self.db.rows, before)
        self.assertEqual(self.db.rows["estadisticas"][0]["usuario_id"], "owner")

    def test_sixth_failure_loses_and_seventh_writes_nothing(self):
        for number in range(1, 7):
            result = self.guess()
            self.assertEqual(result.status_code, 200)
            self.assertEqual(result.json()["intentos_usados"], number)
            self.assertEqual(result.json()["estado"], "perdida" if number == 6 else "en_curso")
            self.assertEqual(result.json()["palabra_secreta"], "CASAS" if number == 6 else None)
        before = copy.deepcopy(self.db.rows)
        self.assertEqual(self.guess().status_code, 400)
        self.assertEqual(self.db.rows, before)
        self.assertEqual(len(self.db.rows["intentos"]), 6)

    def test_win_on_sixth_attempt(self):
        for _ in range(5):
            self.assertEqual(self.guess().status_code, 200)
        result = self.guess("CASAS")
        self.assertEqual(result.json()["estado"], "ganada")
        self.assertEqual(result.json()["intentos_usados"], 6)

    def test_inconsistent_active_game_at_limit_is_rejected(self):
        self.db.rows["partidas"][0]["intentos_usados"] = 6
        before = copy.deepcopy(self.db.rows)
        self.assertEqual(self.guess().status_code, 400)
        self.assertEqual(self.db.rows, before)

    def test_invalid_guesses_write_nothing(self):
        for word in ("CASA", "ZZZZZ"):
            with self.subTest(word=word):
                before = copy.deepcopy(self.db.rows)
                self.assertEqual(self.guess(word).status_code, 400)
                self.assertEqual(self.db.rows, before)

    def test_unknown_game(self):
        self.assertEqual(self.guess(game="missing").status_code, 404)
        self.assertEqual(self.client.get("/game/missing").status_code, 404)

    def test_repeated_letters_in_endpoint(self):
        result = self.guess("AAAAA")
        self.assertEqual([r["estado"] for r in result.json()["resultado"]], ["ausente", "correcto", "ausente", "correcto", "ausente"])

    def test_stats_and_ranking_use_overridden_dependency(self):
        self.assertEqual(self.client.get("/stats/owner").json()["partidas_jugadas"], 0)
        self.guess("CASAS")
        self.assertEqual(self.client.get("/stats/owner").json()["porcentaje_victorias"], 100)
        self.assertEqual(self.client.get("/stats/ranking/global").json()["ranking"][0]["usuario_id"], "owner")


if __name__ == "__main__":
    unittest.main()
