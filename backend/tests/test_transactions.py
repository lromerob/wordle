"""PG-03 offline tests: control flow/SQL intent only, never PostgreSQL locking proof."""
import asyncio
import copy
from contextlib import asynccontextmanager
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, patch
from uuid import UUID

import test_backend as fixtures
import test_postgres_adapter as adapter_fixtures
from app.repository import WordleRepository
from app.routers import game
from fastapi import HTTPException
from fastapi.testclient import TestClient
from psycopg import DataError, OperationalError


class TransactionAdapterTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.connection = adapter_fixtures.Connection()
        self.repo = WordleRepository(self.connection)
        self.enterContext(patch("psycopg.AsyncConnection.connect", side_effect=AssertionError("Native DB forbidden")))

    async def test_transaction_delegates_to_driver_context(self):
        sentinel = object()
        with patch.object(self.connection, "transaction", return_value=sentinel) as transaction:
            self.assertIs(self.repo.transaction(), sentinel)
        transaction.assert_called_once_with()

    async def test_attempt_lock_is_parameterized_and_get_stays_read_only(self):
        self.connection.one = {"id": UUID(adapter_fixtures.GAME)}
        await self.repo.get_game_for_update(adapter_fixtures.GAME)
        sql, params = self.connection.calls[-1]
        self.assertEqual(sql, "SELECT * FROM public.partidas WHERE id = %s LIMIT 1 FOR UPDATE")
        self.assertEqual(params, (UUID(adapter_fixtures.GAME),))
        await self.repo.get_game(adapter_fixtures.GAME)
        self.assertNotIn("FOR UPDATE", self.connection.calls[-1][0])
        self.assertEqual(self.connection.calls[-1][1], params)

    async def test_stats_initialize_using_unique_then_lock_before_calculation(self):
        self.connection.one = {"usuario_id": "text-user", "partidas_jugadas": 3, "partidas_ganadas": 2}
        result = await self.repo.get_stats_for_update("text-user")
        self.assertEqual(self.connection.calls, [
            ("INSERT INTO public.estadisticas (usuario_id) VALUES (%s) ON CONFLICT (usuario_id) DO NOTHING", ("text-user",)),
            ("SELECT * FROM public.estadisticas WHERE usuario_id = %s LIMIT 1 FOR UPDATE", ("text-user",)),
        ])
        self.assertEqual(result, self.connection.one)
        self.assertEqual(result["partidas_jugadas"], 3)  # initialization must not overwrite existing counters
        self.assertEqual(self.connection.cursor_exits, 2)

    async def test_unavailable_stats_row_aborts_instead_of_reinserting(self):
        with self.assertRaises(DataError):
            await self.repo.get_stats_for_update("text-user")
        self.assertEqual(len(self.connection.calls), 2)


class AttemptTransactionTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.db = fixtures.MemoryDB()
        self.body = game.IntentoPeticion(partida_id="game-1", usuario_id="owner", palabra="CASAS")
        self.enterContext(patch("psycopg.AsyncConnection.connect", side_effect=AssertionError("Native DB forbidden")))

    async def test_failed_writes_request_rollback_of_all_attempt_changes(self):
        # Snapshot is only the fixture's rollback contract, not an SQL transaction emulator.
        for method, fail_after, existing_stats in (
            ("add_guess", True, False),
            ("update_game", False, False),
            ("create_stats", True, False),
            ("update_stats", True, True),
        ):
            with self.subTest(method=method):
                self.db = fixtures.MemoryDB()
                if existing_stats:
                    self.db.rows["estadisticas"].append({"usuario_id": "owner", "partidas_jugadas": 2, "partidas_ganadas": 1, "racha_actual": 1, "racha_maxima": 1, "intentos_promedio": 2})
                before = copy.deepcopy(self.db.rows)
                original = getattr(self.db, method)
                async def fail(*args):
                    if fail_after:
                        await original(*args)
                    raise OperationalError("synthetic SQL failure")
                with patch.object(self.db, method, side_effect=fail) as operation:
                    with self.assertRaises(OperationalError):
                        await game.registrar_intento(self.body, self.db)
                    self.assertEqual(operation.await_count, 1)  # no replay
                self.assertEqual(self.db.rows, before)

    async def test_cancellation_exits_transaction_without_partial_fixture_writes(self):
        before = copy.deepcopy(self.db.rows)
        with patch.object(self.db, "update_game", side_effect=asyncio.CancelledError()):
            with self.assertRaises(asyncio.CancelledError):
                await game.registrar_intento(self.body, self.db)
        self.assertEqual(self.db.rows, before)

    async def test_lock_read_and_every_write_are_inside_context_commit_before_result(self):
        events = []
        active = False
        original_transaction = self.db.transaction
        @asynccontextmanager
        async def transaction():
            nonlocal active
            events.append("begin")
            active = True
            try:
                async with original_transaction():
                    yield
            except BaseException:
                events.append("rollback")
                raise
            else:
                events.append("commit")
            finally:
                active = False
        self.enterContext(patch.object(self.db, "transaction", new=transaction))
        for name in ("get_game_for_update", "word_exists", "add_guess", "update_game", "get_stats_for_update", "create_stats"):
            original = getattr(self.db, name)
            async def traced(*args, _name=name, _original=original):
                self.assertTrue(active, _name)
                events.append(_name)
                return await _original(*args)
            self.enterContext(patch.object(self.db, name, side_effect=traced))
        result = await game.registrar_intento(self.body, self.db)
        self.assertFalse(active)
        self.assertEqual(result["estado"], "ganada")
        self.assertEqual(events, ["begin", "get_game_for_update", "word_exists", "add_guess", "update_game", "get_stats_for_update", "create_stats", "commit"])

    async def test_new_zero_stats_row_uses_unchanged_win_and_loss_formulas(self):
        # PostgreSQL initialization returns defaults; exercise that branch explicitly.
        for won in (True, False):
            with self.subTest(won=won):
                self.db = fixtures.MemoryDB()
                zero = {"usuario_id": "owner", "partidas_jugadas": 0, "partidas_ganadas": 0, "racha_actual": 0, "racha_maxima": 0, "intentos_promedio": 0}
                self.db.rows["estadisticas"].append(zero)
                with patch.object(self.db, "create_stats", new=AsyncMock()) as create:
                    await game._actualizar_estadisticas("owner", won, 3, self.db)
                create.assert_not_awaited()
                self.assertEqual(zero, {"usuario_id": "owner", "partidas_jugadas": 1, "partidas_ganadas": int(won), "racha_actual": int(won), "racha_maxima": int(won), "intentos_promedio": 3 if won else 0})

    async def test_finalized_or_sixth_attempt_state_is_validated_from_locked_read(self):
        # Simulates a newer row returned after lock acquisition, not simultaneous DB requests.
        for state, used, detail in (("ganada", 1, "La partida ya terminó: ganada"), ("perdida", 6, "La partida ya terminó: perdida"), ("en_curso", 6, "No quedan intentos")):
            with self.subTest(state=state):
                row = dict(self.db.rows["partidas"][0], estado=state, intentos_usados=used)
                before = copy.deepcopy(self.db.rows)
                with patch.object(self.db, "get_game_for_update", new=AsyncMock(return_value=row)) as locked:
                    with self.assertRaises(HTTPException) as error:
                        await game.registrar_intento(self.body, self.db)
                self.assertEqual((error.exception.status_code, error.exception.detail), (400, detail))
                locked.assert_awaited_once_with("game-1")
                self.assertEqual(self.db.rows, before)


class CommitFailureTests(unittest.TestCase):
    def test_commit_failure_cannot_return_http_success_or_replay(self):
        from app.main import app
        connection = adapter_fixtures.Connection()
        connection.one = {"id": UUID(adapter_fixtures.GAME), "usuario_id": "owner", "palabra_secreta": "CASAS", "intentos_usados": 0, "estado": "en_curso"}
        events = []
        @asynccontextmanager
        async def transaction():
            events.append("begin")
            yield
            events.append("commit-attempt")
            raise OperationalError("synthetic-sensitive-marker")
        connection.transaction = transaction
        pool = SimpleNamespace(open=AsyncMock(), close=AsyncMock())
        @asynccontextmanager
        async def checkout():
            try:
                yield connection
            finally:
                events.append("returned-to-pool")
        pool.connection = checkout
        with patch("app.database.create_pool", return_value=pool), patch("psycopg.AsyncConnection.connect", side_effect=AssertionError("Native DB forbidden")):
            with TestClient(app) as client:
                response = client.post("/game/intento", json={"partida_id": adapter_fixtures.GAME, "usuario_id": "owner", "palabra": "PERRO"})
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json(), {"detail": "Base de datos no disponible"})
        self.assertEqual(events, ["begin", "commit-attempt", "returned-to-pool"])
        inserts = [sql for sql, params in connection.calls if sql.startswith("INSERT INTO public.intentos")]
        self.assertEqual(len(inserts), 1)
        self.assertEqual(len(connection.calls), 4)  # locked read, word lookup, insert, update
        pool.close.assert_awaited_once_with()
