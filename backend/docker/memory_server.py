"""Compose-only in-memory harness, never the production entrypoint."""
import importlib.abc
import os
from pathlib import Path
import socket
import sys
from unittest.mock import patch

os.environ.pop("SUPABASE_URL", None)
os.environ.pop("SUPABASE_KEY", None)
sys.path.insert(0, "/app")
sys.path.insert(0, str(Path(__file__).resolve().parent))


class NoSupabase(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split(".")[0] == "supabase":
            raise RuntimeError("Supabase is forbidden in memory-test mode")


sys.meta_path.insert(0, NoSupabase())


original_connect = socket.socket.connect
original_connect_ex = socket.socket.connect_ex
original_dns = socket.getaddrinfo


def guard_connect(original):
    def guarded(sock, address):
        # Windows asyncio wakeups may use a loopback socketpair.
        if isinstance(address, tuple) and address[0] in ("127.0.0.1", "::1"):
            return original(sock, address)
        raise RuntimeError("External connections are forbidden in memory-test mode")
    return guarded


def local_dns(host, *args, **kwargs):
    if host in ("localhost", "127.0.0.1", "::1", "0.0.0.0", None):
        return original_dns(host, *args, **kwargs)
    raise RuntimeError("External DNS is forbidden in memory-test mode")


# Accepting inbound HTTP needs no outbound connect or DNS.
with patch("socket.socket.connect", new=guard_connect(original_connect)), patch(
    "socket.socket.connect_ex", new=guard_connect(original_connect_ex)
), patch("socket.getaddrinfo", new=local_dns), patch(
    "dotenv.load_dotenv", side_effect=RuntimeError(".env loading forbidden")
):
    from test_backend import MemoryDB
    from app.database import get_supabase
    from app.main import app
    from app.routers import game
    import uvicorn

    database = MemoryDB()
    app.dependency_overrides[get_supabase] = lambda: database
    # Deterministic solution for manual checks; no game-rule changes.
    game.random.choice = lambda entries: next(row for row in entries if row["palabra"] == "CASAS")
    uvicorn.run(app, host="0.0.0.0", port=8000, workers=1, loop="asyncio")
