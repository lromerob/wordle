"""PG-02 offline evidence only: real driver/pool API, simulated connections/rows."""
import asyncio
import copy
from contextlib import asynccontextmanager
from datetime import datetime
from decimal import Decimal
import os
import subprocess
import sys
import time
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, patch
from uuid import UUID

import test_backend as fixtures
from app import database
from app.repository import WordleRepository
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from psycopg import DataError, OperationalError
from psycopg.pq import TransactionStatus
from psycopg_pool import PoolClosed, PoolTimeout, TooManyRequests

GAME = "00000000-0000-4000-8000-000000000001"


class Cursor:
    def __init__(self, connection):
        self.connection = connection

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        self.connection.cursor_exits += 1

    async def execute(self, sql, parameters):
        self.connection.calls.append((sql, parameters))
        if self.connection.failure:
            raise self.connection.failure

    async def fetchone(self):
        return self.connection.one

    async def fetchall(self):
        return self.connection.many


class Connection:
    """Only the protocol needed by psycopg_pool and the adapter; no libpq socket."""
    def __init__(self):
        self.calls, self.cursor_exits = [], 0
        self.one, self.many, self.failure = None, [], None
        self.pgconn = SimpleNamespace(transaction_status=TransactionStatus.IDLE)
        self._created_at = time.monotonic()
        self._expire_at = self._created_at + 3600
        self._pool, self.closed = None, False

    @asynccontextmanager
    async def transaction(self):
        # Protocol stub only: real commit/rollback belongs to PG-04.
        yield

    def cursor(self):
        return Cursor(self)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        pass

    async def close(self):
        self.closed = True
        self.pgconn.transaction_status = TransactionStatus.UNKNOWN


class AdapterTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.connection = Connection()
        self.repo = WordleRepository(self.connection)
        self.enterContext(patch("psycopg.AsyncConnection.connect", side_effect=AssertionError("Database forbidden")))

    async def test_reads_are_parameterized_and_missing_rows_return_none(self):
        hostile = "user'; DROP TABLE public.partidas; --"
        self.assertIsNone(await self.repo.get_stats(hostile))
        self.assertEqual(self.connection.calls[-1][1], (hostile,))
        self.assertNotIn(hostile, self.connection.calls[-1][0])
        self.assertIsNone(await self.repo.word_exists(hostile))
        self.assertEqual(self.connection.calls[-1][1], (hostile,))
        self.assertIsNone(await self.repo.get_game(GAME))
        self.assertEqual(self.connection.calls[-1][1], (UUID(GAME),))
        self.assertNotIn("FOR UPDATE", self.connection.calls[-1][0])
        self.assertEqual(await self.repo.list_words(), [])
        self.assertEqual(self.connection.cursor_exits, 4)

    async def test_insert_game_returns_uuid_and_preserves_explicit_values(self):
        self.connection.one = {"id": UUID(GAME)}
        result = await self.repo.create_game({"usuario_id": "text-user", "palabra_secreta": "CASAS", "intentos_usados": 0, "estado": "en_curso"})
        sql, params = self.connection.calls[-1]
        self.assertIn("RETURNING id", sql)
        self.assertEqual(params, ("text-user", "CASAS", 0, "en_curso"))
        self.assertNotIn("CASAS", sql)
        self.assertEqual(result["id"], UUID(GAME))

    async def test_jsonb_is_adapted_once_and_game_update_is_parameterized(self):
        result = [{"letra": "Ñ", "estado": "ausente"}]
        await self.repo.add_guess({"partida_id": GAME, "usuario_id": "text-user", "numero": 2, "palabra": "NIÑOS", "resultado": result})
        sql, params = self.connection.calls[-1]
        self.assertEqual(params[:4], (UUID(GAME), "text-user", 2, "NIÑOS"))
        self.assertEqual(params[4].obj, result)
        self.assertIsInstance(params[4].obj, list)
        self.assertNotIn("NIÑOS", sql)
        await self.repo.update_game(GAME, {"intentos_usados": 2, "estado": "en_curso"})
        self.assertEqual(self.connection.calls[-1][1], (2, "en_curso", UUID(GAME)))

    async def test_stats_decimal_and_projection_order_limits(self):
        values = {"usuario_id": "user", "partidas_jugadas": 3, "partidas_ganadas": 2, "racha_actual": 2, "racha_maxima": 2, "intentos_promedio": Decimal("1.5")}
        await self.repo.create_stats(values)
        self.assertEqual(self.connection.calls[-1][1], ("user", 3, 2, 2, 2, Decimal("1.5")))
        await self.repo.update_stats("user", values)
        self.assertEqual(self.connection.calls[-1][1], (3, 2, Decimal("1.5"), 2, 2, "user"))
        self.assertNotIn("updated_at", self.connection.calls[-1][0])
        await self.repo.get_guesses(GAME)
        self.assertIn("ORDER BY numero ASC", self.connection.calls[-1][0])
        self.assertEqual(self.connection.calls[-1][1], (UUID(GAME),))
        await self.repo.ranking()
        self.assertEqual(self.connection.calls[-1][0], "SELECT usuario_id, partidas_ganadas, racha_maxima, partidas_jugadas FROM public.estadisticas ORDER BY partidas_ganadas DESC LIMIT 10")

    async def test_bad_uuid_is_not_a_missing_row_or_interpolated_sql(self):
        for value in ("missing", "x'; --", "", None):
            with self.subTest(value=value):
                with self.assertRaises(DataError):
                    await self.repo.get_game(value)
        self.assertEqual(self.connection.calls, [])

    async def test_cursor_closes_after_driver_exception(self):
        self.connection.failure = OperationalError("synthetic driver failure")
        with self.assertRaises(OperationalError):
            await self.repo.list_words()
        self.assertEqual(self.connection.cursor_exits, 1)


class PoolTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.enterContext(patch.dict(os.environ, {}, clear=True))
        self.enterContext(patch("psycopg.AsyncConnection.connect", side_effect=AssertionError("Native database connection forbidden")))
        self.enterContext(patch("socket.socket.connect_ex", side_effect=AssertionError("Network forbidden")))
        self.enterContext(patch("socket.getaddrinfo", side_effect=AssertionError("DNS forbidden")))

    async def test_real_pool_is_bounded_lazy_and_closes(self):
        pool = database.create_pool()
        self.assertTrue(pool.closed)
        self.assertEqual((pool.min_size, pool.max_size, pool.timeout, pool.max_waiting), (0, 4, 3.0, 8))
        self.assertTrue(pool.kwargs["autocommit"])
        self.assertEqual(pool.kwargs["connect_timeout"], 3)
        await pool.open(wait=False)
        self.assertEqual(pool.get_stats()["pool_size"], 0)
        await pool.close()
        self.assertTrue(pool.closed)

    async def test_actual_pool_saturation_timeout_and_reuse_with_fake_connections(self):
        pool = database.create_pool()
        created = []
        async def connect():
            conn = Connection()
            created.append(conn)
            return conn
        with patch.object(pool, "_connect", side_effect=connect):
            await pool.open(wait=False)
            try:
                held = [await pool.getconn() for _ in range(4)]
                with self.assertRaises(PoolTimeout):
                    await pool.getconn(timeout=0.02)
                self.assertEqual(len(created), 4)
                for conn in held:
                    await pool.putconn(conn)
                async with pool.connection() as reused:
                    self.assertIn(reused, held)
                self.assertEqual(len(created), 4)
                self.assertEqual(pool.get_stats()["pool_available"], 4)
            finally:
                await pool.close()
        self.assertTrue(all(conn.closed for conn in created))

    async def test_dependency_releases_connection_on_error_and_cancellation(self):
        pool = database.create_pool()
        async def connect():
            return Connection()
        with patch.object(pool, "_connect", side_effect=connect):
            await pool.open(wait=False)
            request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(db_pool=pool)))
            try:
                dependency = database.get_repository(request)
                self.assertIsInstance(await anext(dependency), WordleRepository)
                with self.assertRaises(HTTPException) as error:
                    await dependency.athrow(OperationalError("synthetic-sensitive-marker"))
                self.assertEqual(error.exception.status_code, 500)
                self.assertEqual(error.exception.detail, "Base de datos no disponible")
                self.assertNotIn("synthetic-sensitive-marker", str(error.exception.detail))
                self.assertEqual(pool.get_stats()["pool_available"], 1)
                dependency = database.get_repository(request)
                await anext(dependency)
                with self.assertRaises(asyncio.CancelledError):
                    await dependency.athrow(asyncio.CancelledError())
                self.assertEqual(pool.get_stats()["pool_available"], 1)
                async with pool.connection():
                    pass
            finally:
                await pool.close()

    async def test_pool_timeout_closed_overload_are_sanitized(self):
        for failure in (PoolTimeout("synthetic-sensitive-marker"), PoolClosed("synthetic-sensitive-marker"), TooManyRequests("synthetic-sensitive-marker")):
            with self.subTest(failure=type(failure).__name__):
                pool = SimpleNamespace(connection=lambda: self.failed_checkout(failure))
                request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(db_pool=pool)))
                with self.assertRaises(HTTPException) as error:
                    await anext(database.get_repository(request))
                self.assertEqual(error.exception.status_code, 500)
                self.assertEqual(error.exception.detail, "Base de datos no disponible")

    @staticmethod
    def failed_checkout(failure):
        from contextlib import asynccontextmanager
        @asynccontextmanager
        async def checkout():
            raise failure
            yield
        return checkout()

    async def test_lifespan_opens_once_and_closes_even_when_handler_fails(self):
        pool = SimpleNamespace(open=AsyncMock(), close=AsyncMock())
        app = FastAPI()
        with patch("app.database.create_pool", return_value=pool) as factory:
            with self.assertRaises(RuntimeError):
                async with database.lifespan(app):
                    self.assertIs(app.state.db_pool, pool)
                    raise RuntimeError("synthetic handler failure")
        factory.assert_called_once_with()
        pool.open.assert_awaited_once_with(wait=False)
        pool.close.assert_awaited_once_with()
        self.assertFalse(hasattr(app.state, "db_pool"))


class ContractTests(unittest.TestCase):
    setUp = fixtures.EndpointTests.setUp
    guess = fixtures.EndpointTests.guess

    def test_empty_dictionary_and_framework_validation(self):
        self.db.rows["palabras"].clear()
        before = copy.deepcopy(self.db.rows)
        response = self.client.post("/game/nueva", params={"usuario_id": ""})
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json(), {"detail": "No hay palabras disponibles"})
        self.assertEqual(self.db.rows, before)
        self.assertEqual(self.client.post("/game/nueva").status_code, 422)
        for body in ({}, {"partida_id": GAME, "usuario_id": "owner"}, {"partida_id": GAME, "usuario_id": "owner", "palabra": 12345}):
            response = self.client.post("/game/intento", json=body)
            self.assertEqual(response.status_code, 422)
            self.assertIsInstance(response.json()["detail"], list)
        self.assertEqual(self.db.rows, before)

    def test_new_game_uuid_is_json_string_and_reusable(self):
        async def create(values):
            self.assertEqual(values["usuario_id"], "text-user")
            self.assertEqual(values["estado"], "en_curso")
            self.assertEqual(values["intentos_usados"], 0)
            self.db.rows["partidas"].append(dict(values, id=UUID(GAME)))
            return {"id": UUID(GAME)}
        with patch.object(self.db, "create_game", side_effect=create):
            response = self.client.post("/game/nueva", params={"usuario_id": "text-user"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"partida_id": GAME})
        self.assertEqual(self.client.get(f"/game/{GAME}").status_code, 200)
        self.assertNotIn("palabra_secreta", self.client.get(f"/game/{GAME}").json()["partida"])

    def test_precedence_and_exact_error_details(self):
        self.db.rows["partidas"][0]["estado"] = "ganada"
        before = copy.deepcopy(self.db.rows)
        for kwargs, code, detail in (
            ({"word": "12345", "user": "other", "game": "missing"}, 400, "La palabra debe tener 5 letras de A a Z o Ñ"),
            ({"user": "other"}, 403, "El usuario no coincide con la partida"),
            ({}, 400, "La partida ya terminó: ganada"),
        ):
            response = self.guess(**kwargs)
            self.assertEqual((response.status_code, response.json()), (code, {"detail": detail}))
        self.assertEqual(self.db.rows, before)
        self.db.rows["partidas"][0].update(estado="en_curso", intentos_usados=6)
        self.assertEqual(self.guess().json(), {"detail": "No quedan intentos"})
        self.db.rows["partidas"][0]["intentos_usados"] = 0
        self.assertEqual(self.guess("ZZZZZ").json(), {"detail": "Palabra no válida"})

    def test_native_uuid_datetime_jsonb_and_decimal_json_shapes(self):
        row = self.db.rows["partidas"][0]
        row.update(id=UUID(GAME), created_at=datetime(2026, 1, 2, 3, 4, 5))
        self.db.rows["intentos"] = [
            {"id": UUID(int=n), "partida_id": UUID(GAME), "usuario_id": "owner", "numero": n, "palabra": "PERRO", "resultado": [{"letra": "P", "estado": "ausente"}], "created_at": None}
            for n in (2, 1)
        ]
        response = self.client.get(f"/game/{GAME}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["partida"]["id"], GAME)
        self.assertEqual(data["partida"]["created_at"], "2026-01-02T03:04:05")
        self.assertNotIn("palabra_secreta", data["partida"])
        self.assertEqual([r["numero"] for r in data["intentos"]], [1, 2])
        self.assertIsInstance(data["intentos"][0]["resultado"], list)
        self.assertIsNone(data["intentos"][0]["created_at"])
        self.db.rows["estadisticas"] = [{"id": UUID(int=4), "usuario_id": "owner", "partidas_jugadas": 4, "partidas_ganadas": 2, "racha_actual": 0, "racha_maxima": 2, "intentos_promedio": Decimal("1.5"), "updated_at": None}]
        data = self.client.get("/stats/owner").json()
        self.assertEqual(data["intentos_promedio"], 1.5)
        self.assertIsInstance(data["intentos_promedio"], (float, int))
        self.assertEqual(data["id"], str(UUID(int=4)))
        self.assertIsNone(data["updated_at"])
        self.assertEqual(data["porcentaje_victorias"], 50)

    def test_empty_stats_ranking_projection_and_ten_limit(self):
        self.assertEqual(self.client.get("/stats/new-user").json(), dict.fromkeys(("partidas_jugadas", "partidas_ganadas", "racha_actual", "racha_maxima", "porcentaje_victorias"), 0))
        self.assertEqual(self.client.get("/stats/ranking/global").json(), {"ranking": []})
        for i in range(14):
            self.db.rows["estadisticas"].append({"usuario_id": f"user-{i}", "partidas_ganadas": i // 2, "partidas_jugadas": 20, "racha_maxima": 1, "intentos_promedio": Decimal("1.5")})
        ranking = self.client.get("/stats/ranking/global").json()["ranking"]
        self.assertEqual(len(ranking), 10)
        self.assertEqual([r["partidas_ganadas"] for r in ranking], sorted([r["partidas_ganadas"] for r in ranking], reverse=True))
        for row in ranking:
            self.assertEqual(set(row), {"usuario_id", "partidas_ganadas", "partidas_jugadas", "racha_maxima"})

    def test_two_wins_fractional_average_then_loss_and_won_get_contract(self):
        self.assertEqual(self.guess("CASAS").json()["palabra_secreta"], None)
        self.assertEqual(self.client.get("/game/game-1").json()["partida"]["palabra_secreta"], "CASAS")
        self.db.rows["partidas"][0].update(estado="en_curso", intentos_usados=0)
        self.guess()
        self.assertEqual(self.guess("CASAS").json()["estado"], "ganada")
        stats = self.db.rows["estadisticas"][0]
        self.assertEqual(stats["intentos_promedio"], 1.5)
        self.assertEqual((stats["partidas_jugadas"], stats["partidas_ganadas"], stats["racha_actual"], stats["racha_maxima"]), (2, 2, 2, 2))
        self.db.rows["partidas"][0].update(estado="en_curso", intentos_usados=5)
        self.assertEqual(self.guess().json()["estado"], "perdida")
        self.assertEqual(stats["intentos_promedio"], 1.5)
        self.assertEqual((stats["partidas_jugadas"], stats["partidas_ganadas"], stats["racha_actual"], stats["racha_maxima"]), (3, 2, 0, 2))


class ImportAndErrorTests(unittest.TestCase):
    def test_fresh_import_and_lazy_pool_without_network_or_dotenv(self):
        script = """
import os, socket
from unittest.mock import patch
original = socket.socket.connect
def offline(sock, address):
    if isinstance(address, tuple) and address[0] in ('127.0.0.1', '::1'):
        return original(sock, address)
    raise AssertionError('Network forbidden')
with patch.dict(os.environ, {}, clear=True), patch('socket.socket.connect', new=offline), patch('socket.socket.connect_ex', side_effect=AssertionError('Network forbidden')), patch('socket.getaddrinfo', side_effect=AssertionError('DNS forbidden')), patch('dotenv.load_dotenv', side_effect=AssertionError('dotenv forbidden')), patch('psycopg.AsyncConnection.connect', side_effect=AssertionError('Native DB forbidden')):
    from app.main import app
    from app.database import create_pool
    import sys
    assert not any(n == 'supabase' or n.startswith('supabase.') for n in sys.modules)
    pool = create_pool()
    assert pool.closed and pool.min_size == 0
    from fastapi.testclient import TestClient
    with TestClient(app) as client:
        assert client.get('/health').json() == {'status': 'ok'}
        assert app.state.db_pool.get_stats()['pool_size'] == 0
    assert not hasattr(app.state, 'db_pool')
"""
        env = {"PATH": os.environ.get("PATH", ""), "SYSTEMROOT": os.environ.get("SYSTEMROOT", ""), "PYTHONPATH": str(fixtures.BACKEND), "PYTHONDONTWRITEBYTECODE": "1"}
        result = subprocess.run([sys.executable, "-B", "-c", script], capture_output=True, text=True, env=env, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_http_driver_errors_and_uuid_missing_vs_malformed(self):
        from app.main import app
        conn = Connection()
        pool = SimpleNamespace(open=AsyncMock(), close=AsyncMock())
        from contextlib import asynccontextmanager
        @asynccontextmanager
        async def checkout():
            try:
                yield conn
            finally:
                pool.returned += 1
        pool.connection, pool.returned = checkout, 0
        with patch.dict(os.environ, {}, clear=True), patch("app.database.create_pool", return_value=pool), patch("psycopg.AsyncConnection.connect", side_effect=AssertionError("Native DB forbidden")):
            with TestClient(app) as client:
                for url in (f"/game/{GAME}",):
                    response = client.get(url)
                    self.assertEqual(response.status_code, 404)
                    self.assertEqual(response.json(), {"detail": "Partida no encontrada"})
                for method, url, kwargs in (("GET", "/game/not-a-uuid", {}), ("POST", "/game/intento", {"json": {"partida_id": "bad", "usuario_id": "owner", "palabra": "PERRO"}})):
                    response = client.request(method, url, **kwargs)
                    self.assertEqual((response.status_code, response.json()), (500, {"detail": "Base de datos no disponible"}))
                conn.failure = OperationalError("synthetic-sensitive-marker")
                response = client.post("/game/nueva", params={"usuario_id": "owner"})
                self.assertEqual((response.status_code, response.json()), (500, {"detail": "Base de datos no disponible"}))
                self.assertEqual(len(conn.calls), 2)  # valid lookup + failed list, no replay
                self.assertEqual(pool.returned, 4)
                self.assertEqual(client.get("/health").status_code, 200)
                conn.failure = None
                self.assertEqual(client.get(f"/game/{GAME}").status_code, 404)
                self.assertEqual(pool.returned, 5)
