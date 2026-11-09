"""Real PG16/API tests. Execute only with run_pg04.py, not offline discovery."""
import asyncio
from contextlib import AsyncExitStack
from decimal import Decimal
import os
import time
import unittest
from unittest.mock import patch
from uuid import UUID, uuid4

import httpx
import psycopg
from app.main import app
from app.repository import WordleRepository

CONFIG = None


class PostgreSQLIntegrationTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        if CONFIG is None:
            self.skipTest("Use the explicit disposable runner; no arbitrary DSN accepted")
        self.stack = AsyncExitStack()
        self.addAsyncCleanup(self.stack.aclose)
        self.enterContext(patch.dict(os.environ, CONFIG["environment"]))
        self.admin = await self.stack.enter_async_context(await psycopg.AsyncConnection.connect(**CONFIG["admin"]))
        await self.admin.execute("TRUNCATE public.intentos, public.partidas, public.estadisticas, public.palabras RESTART IDENTITY")
        await self.admin.execute("INSERT INTO public.palabras (palabra) VALUES (%s),(%s),(%s),(%s),(%s)", ("CASAS", "PERRO", "SACAS", "AAAAA", "NIÑOS"))
        assert not app.dependency_overrides
        self.enterContext(patch("app.routers.game.random.choice", side_effect=lambda rows: next(r for r in rows if r["palabra"] == "CASAS")))
        await self.stack.enter_async_context(app.router.lifespan_context(app))
        self.pool = app.state.db_pool
        self.client = await self.stack.enter_async_context(httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test", trust_env=False))

    async def asyncTearDown(self):
        if CONFIG is None:
            return
        await self.admin.execute("TRUNCATE public.intentos, public.partidas, public.estadisticas, public.palabras RESTART IDENTITY")
        await self.stack.aclose()
        self.assertTrue(self.pool.closed)
        self.assertFalse(hasattr(app.state, "db_pool"))

    async def rows(self, query, params=()):
        return await (await self.admin.execute(query, params)).fetchall()

    async def new(self, user="owner"):
        response = await self.client.post("/game/nueva", params={"usuario_id": user})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(set(response.json()), {"partida_id"})
        identifier = response.json()["partida_id"]
        self.assertEqual(str(UUID(identifier)), identifier)
        return identifier

    async def guess(self, identifier, word="PERRO", user="owner"):
        return await asyncio.wait_for(self.client.post("/game/intento", json={"partida_id": identifier, "usuario_id": user, "palabra": word}), timeout=10)

    async def state(self, identifier):
        response = await self.client.get("/game/" + identifier)
        self.assertEqual(response.status_code, 200)
        return response.json()

    async def test_lifecycle_health_and_persisted_types(self):
        self.assertFalse(self.pool.closed)
        self.assertEqual(self.pool.get_stats()["pool_size"], 0)
        self.assertEqual((await self.client.get("/health")).json(), {"status": "ok"})
        self.assertEqual(self.pool.get_stats()["pool_size"], 0)
        identifier = await self.new("user'; SELECT 1; --")
        response = await self.guess(identifier, "AAAAA", "user'; SELECT 1; --")
        self.assertEqual(response.status_code, 200)
        self.assertEqual([r["estado"] for r in response.json()["resultado"]], ["ausente", "correcto", "ausente", "correcto", "ausente"])
        self.assertIsNone(response.json()["palabra_secreta"])
        state = await self.state(identifier)
        self.assertNotIn("palabra_secreta", state["partida"])
        stored = (await self.rows("SELECT * FROM public.partidas WHERE id=%s", (UUID(identifier),)))[0]
        attempts = await self.rows("SELECT * FROM public.intentos WHERE partida_id=%s ORDER BY numero", (UUID(identifier),))
        self.assertIsInstance(stored["id"], UUID)
        self.assertEqual(stored["usuario_id"], "user'; SELECT 1; --")
        self.assertIsNone(stored["created_at"].tzinfo)
        self.assertEqual(state["partida"]["created_at"], stored["created_at"].isoformat())
        self.assertEqual((stored["intentos_usados"], stored["estado"]), (1, "en_curso"))
        self.assertEqual(attempts[0]["resultado"], response.json()["resultado"])
        self.assertIsInstance(attempts[0]["resultado"], list)
        self.assertEqual(state["intentos"][0]["id"], str(attempts[0]["id"]))
        self.assertEqual(state["intentos"][0]["numero"], 1)
        self.assertEqual(self.pool.get_stats()["pool_available"], self.pool.get_stats()["pool_size"])
        async with self.pool.connection() as connection:
            row = await (await connection.execute("SELECT current_user AS u, current_setting('transaction_isolation') AS isolation, (SELECT rolsuper FROM pg_roles WHERE rolname=current_user) AS superuser")).fetchone()
            self.assertEqual(row, {"u": "wordle_pg04_app", "isolation": "read committed", "superuser": False})

    async def test_empty_dictionary_and_framework_validation(self):
        await self.admin.execute("TRUNCATE public.palabras")
        response = await self.client.post("/game/nueva", params={"usuario_id": ""})
        self.assertEqual((response.status_code, response.json()), (500, {"detail": "No hay palabras disponibles"}))
        self.assertEqual(await self.rows("SELECT * FROM public.partidas"), [])
        self.assertEqual((await self.client.post("/game/nueva")).status_code, 422)
        for body in ({}, {"partida_id": str(uuid4()), "usuario_id": "owner"}, {"partida_id": str(uuid4()), "usuario_id": "owner", "palabra": 12345}):
            self.assertEqual((await self.client.post("/game/intento", json=body)).status_code, 422)

    async def test_rejections_uuid_states_and_no_writes(self):
        identifier = await self.new()
        for word in ("CASA", "12345", "CAS S", "CAFÉS", "CAßS", "ßAAAA"):
            response = await self.guess(identifier, word)
            self.assertEqual((response.status_code, response.json()), (400, {"detail": "La palabra debe tener 5 letras de A a Z o Ñ"}))
        self.assertEqual((await self.guess(identifier, "ZZZZZ")).json(), {"detail": "Palabra no válida"})
        for method in ("get", "post"):
            response = await self.client.get("/game/" + str(uuid4())) if method == "get" else await self.guess(str(uuid4()))
            self.assertEqual((response.status_code, response.json()), (404, {"detail": "Partida no encontrada"}))
            response = await self.client.get("/game/not-a-uuid") if method == "get" else await self.guess("not-a-uuid")
            self.assertEqual((response.status_code, response.json()), (500, {"detail": "Base de datos no disponible"}))
        await self.admin.execute("UPDATE public.partidas SET estado='ganada' WHERE id=%s", (UUID(identifier),))
        self.assertEqual((await self.guess(identifier, user="other")).json(), {"detail": "El usuario no coincide con la partida"})
        self.assertEqual((await self.guess(identifier, user="other")).status_code, 403)
        for state in (None, "pendiente", ""):
            await self.admin.execute("UPDATE public.partidas SET estado=%s WHERE id=%s", (state, UUID(identifier)))
            self.assertNotIn("palabra_secreta", (await self.state(identifier))["partida"])
            self.assertEqual((await self.guess(identifier)).status_code, 400)
        await self.admin.execute("UPDATE public.partidas SET estado='en_curso', intentos_usados=6 WHERE id=%s", (UUID(identifier),))
        self.assertEqual((await self.guess(identifier)).json(), {"detail": "No quedan intentos"})
        self.assertEqual(await self.rows("SELECT * FROM public.intentos"), [])
        self.assertEqual(await self.rows("SELECT * FROM public.estadisticas"), [])

    async def test_repeated_letters_enye_win_and_final_get(self):
        identifier = await self.new()
        response = await self.guess(identifier, "SACAS")
        self.assertEqual([r["estado"] for r in response.json()["resultado"]], ["presente", "correcto", "presente", "correcto", "correcto"])
        self.assertEqual((await self.guess(identifier, " niños ")).status_code, 200)
        response = await self.guess(identifier, " casas ")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(set(response.json()), {"resultado", "estado", "intentos_usados", "palabra_secreta"})
        self.assertEqual((response.json()["estado"], response.json()["intentos_usados"], response.json()["palabra_secreta"]), ("ganada", 3, None))
        state = await self.state(identifier)
        self.assertEqual(state["partida"]["palabra_secreta"], "CASAS")
        self.assertEqual([r["numero"] for r in state["intentos"]], [1, 2, 3])
        self.assertEqual(state["intentos"][1]["palabra"], "NIÑOS")
        self.assertEqual((await self.guess(identifier)).status_code, 400)
        self.assertEqual(len((await self.state(identifier))["intentos"]), 3)

    async def test_sixth_loss_and_sixth_win(self):
        for wins in (False, True):
            user = "sixth-" + str(wins)
            identifier = await self.new(user)
            for number in range(1, 7):
                response = await self.guess(identifier, "CASAS" if wins and number == 6 else "PERRO", user)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json()["intentos_usados"], number)
            self.assertEqual(response.json()["estado"], "ganada" if wins else "perdida")
            self.assertEqual(response.json()["palabra_secreta"], None if wins else "CASAS")
            self.assertEqual((await self.guess(identifier, user=user)).status_code, 400)
            self.assertEqual(len((await self.state(identifier))["intentos"]), 6)

    async def test_stats_numeric_fraction_loss_and_ranking(self):
        self.assertEqual((await self.client.get("/stats/owner")).json(), dict.fromkeys(("partidas_jugadas", "partidas_ganadas", "racha_actual", "racha_maxima", "porcentaje_victorias"), 0))
        self.assertEqual((await self.client.get("/stats/ranking/global")).json(), {"ranking": []})
        identifier = await self.new()
        await self.guess(identifier, "CASAS")
        identifier = await self.new()
        await self.guess(identifier)
        await self.guess(identifier, "CASAS")
        identifier = await self.new()
        for _ in range(6):
            await self.guess(identifier)
        stats = (await self.client.get("/stats/owner")).json()
        self.assertEqual((stats["partidas_jugadas"], stats["partidas_ganadas"], stats["racha_actual"], stats["racha_maxima"], stats["intentos_promedio"], stats["porcentaje_victorias"]), (3, 2, 0, 2, 1.5, 67))
        self.assertIsInstance(stats["intentos_promedio"], (int, float))
        stored = (await self.rows("SELECT * FROM public.estadisticas WHERE usuario_id=%s", ("owner",)))[0]
        self.assertIsInstance(stored["intentos_promedio"], Decimal)
        self.assertEqual(stored["intentos_promedio"], Decimal("1.5"))
        self.assertEqual(stats["id"], str(stored["id"]))
        self.assertEqual(stats["updated_at"], stored["updated_at"].isoformat())
        for number in range(12):
            await self.admin.execute("INSERT INTO public.estadisticas (usuario_id,partidas_jugadas,partidas_ganadas) VALUES (%s,20,%s)", ("rank-" + str(number), number // 2))
        ranking = (await self.client.get("/stats/ranking/global")).json()["ranking"]
        self.assertEqual(len(ranking), 10)
        self.assertEqual([r["partidas_ganadas"] for r in ranking], sorted([r["partidas_ganadas"] for r in ranking], reverse=True))
        for row in ranking:
            self.assertEqual(set(row), {"usuario_id", "partidas_jugadas", "partidas_ganadas", "racha_maxima"})

    async def test_real_sql_failure_rolls_back_attempt_game_and_stats(self):
        for stage in ("update_game", "get_stats_for_update", "update_stats"):
            user = "fault-" + stage
            if stage == "update_stats":
                seed = await self.new(user)
                await self.guess(seed, "CASAS", user)
            identifier = await self.new(user)
            before_game = await self.rows("SELECT * FROM public.partidas WHERE id=%s", (UUID(identifier),))
            before_stats = await self.rows("SELECT * FROM public.estadisticas WHERE usuario_id=%s", (user,))
            original = getattr(WordleRepository, stage)
            async def fail(repository, *args):
                if stage != "update_game":
                    await original(repository, *args)
                await repository.connection.execute("SELECT 1 / 0")  # real server-side error, test-only hook
            with patch.object(WordleRepository, stage, new=fail):
                response = await self.guess(identifier, "CASAS", user)
            self.assertEqual((response.status_code, response.json()), (500, {"detail": "Base de datos no disponible"}))
            self.assertEqual(await self.rows("SELECT * FROM public.intentos WHERE partida_id=%s", (UUID(identifier),)), [])
            self.assertEqual(await self.rows("SELECT * FROM public.partidas WHERE id=%s", (UUID(identifier),)), before_game)
            self.assertEqual(await self.rows("SELECT * FROM public.estadisticas WHERE usuario_id=%s", (user,)), before_stats)
            self.assertEqual((await self.guess(identifier, "PERRO", user)).status_code, 200)

    async def contended_pair(self, method, first_request, second_request):
        # First holds a real PG row lock. Observe the second waiting in pg_stat_activity.
        first_locked, second_started, release = asyncio.Event(), asyncio.Event(), asyncio.Event()
        original = getattr(WordleRepository, method)
        calls, pids = 0, []
        async def held(repository, *args):
            nonlocal calls
            calls += 1
            index = calls
            pid = (await (await repository.connection.execute("SELECT pg_backend_pid() AS pid")).fetchone())["pid"]
            pids.append(pid)
            if index == 2:
                second_started.set()
            result = await original(repository, *args)
            if index == 1:
                first_locked.set()
                await asyncio.wait_for(release.wait(), timeout=4)
            return result
        tasks = []
        with patch.object(WordleRepository, method, new=held):
            try:
                tasks.append(asyncio.create_task(first_request()))
                await asyncio.wait_for(first_locked.wait(), timeout=3)
                tasks.append(asyncio.create_task(second_request()))
                await asyncio.wait_for(second_started.wait(), timeout=3)
                self.assertEqual(len(set(pids)), 2)
                deadline = time.monotonic() + 2
                observed = False
                while time.monotonic() < deadline:
                    rows = await self.rows("SELECT wait_event_type FROM pg_stat_activity WHERE pid=%s", (pids[1],))
                    if rows and rows[0]["wait_event_type"] == "Lock":
                        observed = True
                        break
                    await asyncio.sleep(0.02)
                self.assertTrue(observed, "Second real connection must be waiting on a PostgreSQL lock")
                release.set()
                return await asyncio.wait_for(asyncio.gather(*tasks), timeout=8)
            finally:
                release.set()
                for task in tasks:
                    if not task.done():
                        task.cancel()
                await asyncio.gather(*tasks, return_exceptions=True)

    async def test_concurrent_attempts_have_distinct_numbers(self):
        identifier = await self.new()
        responses = await self.contended_pair("get_game_for_update", lambda: self.guess(identifier), lambda: self.guess(identifier))
        self.assertEqual([r.status_code for r in responses], [200, 200])
        self.assertEqual([r.json()["intentos_usados"] for r in responses], [1, 2])
        state = await self.state(identifier)
        self.assertEqual([r["numero"] for r in state["intentos"]], [1, 2])
        self.assertEqual(state["partida"]["intentos_usados"], 2)

    async def test_concurrent_last_attempt_and_wins_finalize_only_once(self):
        for winning in (False, True):
            user = "last-" + str(winning)
            identifier = await self.new(user)
            if not winning:
                for _ in range(5):
                    await self.guess(identifier, user=user)
            word = "CASAS" if winning else "PERRO"
            responses = await self.contended_pair("get_game_for_update", lambda: self.guess(identifier, word, user), lambda: self.guess(identifier, word, user))
            self.assertEqual([r.status_code for r in responses], [200, 400])
            state = await self.state(identifier)
            self.assertEqual([r["numero"] for r in state["intentos"]], list(range(1, (1 if winning else 6) + 1)))
            self.assertEqual(state["partida"]["estado"], "ganada" if winning else "perdida")
            stats = (await self.client.get("/stats/" + user)).json()
            self.assertEqual(stats["partidas_jugadas"], 1)
            self.assertEqual(stats["partidas_ganadas"], int(winning))

    async def test_concurrent_first_statistics_creation(self):
        first, second = await self.new(), await self.new()
        await self.guess(second)
        responses = await self.contended_pair("get_stats_for_update", lambda: self.guess(first, "CASAS"), lambda: self.guess(second, "CASAS"))
        self.assertEqual([r.status_code for r in responses], [200, 200])
        rows = await self.rows("SELECT * FROM public.estadisticas WHERE usuario_id='owner'")
        self.assertEqual(len(rows), 1)
        self.assertEqual((rows[0]["partidas_jugadas"], rows[0]["partidas_ganadas"], rows[0]["intentos_promedio"], rows[0]["racha_maxima"]), (2, 2, Decimal("1.5"), 2))

    async def test_concurrent_existing_statistics_win_then_loss(self):
        seed = await self.new()
        await self.guess(seed, "CASAS")
        first, second = await self.new(), await self.new()
        await self.guess(first)
        for _ in range(5):
            await self.guess(second)
        responses = await self.contended_pair("get_stats_for_update", lambda: self.guess(first, "CASAS"), lambda: self.guess(second))
        self.assertEqual([r.status_code for r in responses], [200, 200])
        row = (await self.rows("SELECT * FROM public.estadisticas WHERE usuario_id='owner'"))[0]
        self.assertEqual((row["partidas_jugadas"], row["partidas_ganadas"], row["intentos_promedio"], row["racha_actual"], row["racha_maxima"]), (3, 2, Decimal("1.5"), 0, 2))
