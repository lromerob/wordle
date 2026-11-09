"""Lazy PostgreSQL pool and replaceable request-scoped data access."""
import os
from contextlib import asynccontextmanager

from fastapi import HTTPException, Request
from psycopg import Error
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool, PoolClosed, PoolTimeout, TooManyRequests

from app.repository import WordleRepository


def create_pool():
    # Explicit parameters avoid implicit libpq user/database/password-file defaults.
    # No dotenv reads, connection, DNS lookup or pool worker starts here.
    return AsyncConnectionPool(
        kwargs={
            "host": os.environ.get("PGHOST", "127.0.0.1"),
            "port": os.environ.get("PGPORT", "5432"),
            "dbname": os.environ.get("PGDATABASE", "wordle"),
            "user": os.environ.get("PGUSER", "wordle"),
            "password": os.environ.get("PGPASSWORD", ""),
            "passfile": os.devnull,
            "sslmode": os.environ.get("PGSSLMODE", "prefer"),
            "connect_timeout": 3,
            "options": "-c statement_timeout=5000 -c idle_in_transaction_session_timeout=5000",
            "autocommit": True,
            "row_factory": dict_row,
        },
        open=False, min_size=0, max_size=4, timeout=3.0, max_waiting=8,
        reconnect_timeout=3.0, num_workers=2, name="wordle",
    )


@asynccontextmanager
async def lifespan(app):
    # Memory-only tests/harness override the dependency: no production pool needed.
    if get_repository in app.dependency_overrides:
        yield
        return
    pool = create_pool()
    app.state.db_pool = pool
    try:
        # min_size=0: opening starts workers but makes no connection for /health.
        await pool.open(wait=False)
        yield
    finally:
        await pool.close()
        del app.state.db_pool


async def get_repository(request: Request):
    pool = getattr(request.app.state, "db_pool", None)
    if pool is None:
        raise HTTPException(status_code=500, detail="Base de datos no disponible")
    try:
        # One borrowed connection per request; returned even on error/cancellation.
        async with pool.connection() as connection:
            yield WordleRepository(connection)
    except (Error, PoolTimeout, PoolClosed, TooManyRequests):
        # Never expose driver messages, SQL, parameters, DSNs or credentials.
        # No automatic replay of a possibly committed application write.
        raise HTTPException(status_code=500, detail="Base de datos no disponible") from None
