"""Async SQL adapter with explicit attempt transactions and PostgreSQL row locks."""
from uuid import UUID

from psycopg import DataError
from psycopg.types.json import Jsonb


def game_uuid(value):
    try:
        return UUID(str(value))
    except (ValueError, TypeError, AttributeError):
        # D05: malformed IDs remain internal errors (500), not invented 400/404.
        raise DataError("Invalid game identifier") from None


class WordleRepository:
    def __init__(self, connection):
        self.connection = connection

    def transaction(self):
        # With autocommit=True, this starts/commits one explicit transaction.
        return self.connection.transaction()

    async def _one(self, sql, parameters=()):
        async with self.connection.cursor() as cursor:
            await cursor.execute(sql, parameters)
            return await cursor.fetchone()

    async def _all(self, sql, parameters=()):
        async with self.connection.cursor() as cursor:
            await cursor.execute(sql, parameters)
            return await cursor.fetchall()

    async def _write(self, sql, parameters):
        async with self.connection.cursor() as cursor:
            await cursor.execute(sql, parameters)

    async def list_words(self):
        return await self._all("SELECT palabra FROM public.palabras")

    async def create_game(self, values):
        return await self._one(
            "INSERT INTO public.partidas (usuario_id, palabra_secreta, intentos_usados, estado) "
            "VALUES (%s, %s, %s, %s) RETURNING id",
            (values["usuario_id"], values["palabra_secreta"], values["intentos_usados"], values["estado"]),
        )

    async def get_game(self, partida_id):
        return await self._one("SELECT * FROM public.partidas WHERE id = %s LIMIT 1", (game_uuid(partida_id),))

    async def get_game_for_update(self, partida_id):
        # Only the attempt handler uses this, inside transaction(). GET stays read-only.
        return await self._one(
            "SELECT * FROM public.partidas WHERE id = %s LIMIT 1 FOR UPDATE", (game_uuid(partida_id),),
        )

    async def word_exists(self, word):
        return await self._one("SELECT palabra FROM public.palabras WHERE palabra = %s LIMIT 1", (word,))

    async def add_guess(self, values):
        await self._write(
            "INSERT INTO public.intentos (partida_id, usuario_id, numero, palabra, resultado) "
            "VALUES (%s, %s, %s, %s, %s)",
            (game_uuid(values["partida_id"]), values["usuario_id"], values["numero"], values["palabra"], Jsonb(values["resultado"])),
        )

    async def update_game(self, partida_id, values):
        await self._write(
            "UPDATE public.partidas SET intentos_usados = %s, estado = %s WHERE id = %s",
            (values["intentos_usados"], values["estado"], game_uuid(partida_id)),
        )

    async def get_guesses(self, partida_id):
        return await self._all(
            "SELECT * FROM public.intentos WHERE partida_id = %s ORDER BY numero ASC", (game_uuid(partida_id),),
        )

    async def get_stats(self, usuario_id):
        return await self._one("SELECT * FROM public.estadisticas WHERE usuario_id = %s LIMIT 1", (usuario_id,))

    async def get_stats_for_update(self, usuario_id):
        # UNIQUE(usuario_id) coordinates first creation across different games.
        # At READ COMMITTED the next statement sees a concurrent committed insert.
        await self._write(
            "INSERT INTO public.estadisticas (usuario_id) VALUES (%s) "
            "ON CONFLICT (usuario_id) DO NOTHING", (usuario_id,),
        )
        stats = await self._one(
            "SELECT * FROM public.estadisticas WHERE usuario_id = %s LIMIT 1 FOR UPDATE", (usuario_id,),
        )
        if stats is None:
            raise DataError("Statistics row unavailable")
        return stats

    async def create_stats(self, values):
        await self._write(
            "INSERT INTO public.estadisticas "
            "(usuario_id, partidas_jugadas, partidas_ganadas, racha_actual, racha_maxima, intentos_promedio) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            (values["usuario_id"], values["partidas_jugadas"], values["partidas_ganadas"], values["racha_actual"], values["racha_maxima"], values["intentos_promedio"]),
        )

    async def update_stats(self, usuario_id, values):
        await self._write(
            "UPDATE public.estadisticas SET partidas_jugadas = %s, partidas_ganadas = %s, "
            "intentos_promedio = %s, racha_actual = %s, racha_maxima = %s WHERE usuario_id = %s",
            (values["partidas_jugadas"], values["partidas_ganadas"], values["intentos_promedio"], values["racha_actual"], values["racha_maxima"], usuario_id),
        )

    async def ranking(self):
        return await self._all(
            "SELECT usuario_id, partidas_ganadas, racha_maxima, partidas_jugadas FROM public.estadisticas "
            "ORDER BY partidas_ganadas DESC LIMIT 10"
        )
