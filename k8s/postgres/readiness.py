"""Read-only PG-06 exec probe; /health remains process-only. No credential output."""
import asyncio
import os
import sys
import psycopg


async def ready():
    async with await psycopg.AsyncConnection.connect(
        host=os.environ["PGHOST"], port=os.environ["PGPORT"],
        dbname=os.environ["PGDATABASE"], user=os.environ["PGUSER"],
        password=os.environ["PGPASSWORD"], passfile=os.devnull,
        sslmode=os.environ["PGSSLMODE"], connect_timeout=2,
        options="-c statement_timeout=2000 -c default_transaction_read_only=on",
        autocommit=True,
    ) as connection:
        for table in ("palabras", "partidas", "intentos", "estadisticas"):
            await connection.execute("SELECT 1 FROM public." + table + " LIMIT 0")
        row = await (await connection.execute("SELECT EXISTS (SELECT 1 FROM public.palabras)")).fetchone()
        if not row[0]:
            raise RuntimeError("Empty dictionary")


if __name__ == "__main__":
    try:
        asyncio.run(asyncio.wait_for(ready(), timeout=5))
    except Exception:
        print("Database readiness failed", file=sys.stderr)
        raise SystemExit(1) from None
