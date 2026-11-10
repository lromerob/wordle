import os
from urllib.parse import urlsplit

from app.database import lifespan
from app.routers import game, stats
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

def cors_origins():
    """Exact browser origins; empty env disables cross-origin access."""
    value = os.environ.get(
        "WORDLE_CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
    )
    origins = list(dict.fromkeys(item.strip() for item in value.split(",") if item.strip()))
    for origin in origins:
        parsed = urlsplit(origin)
        if (parsed.scheme not in ("http", "https") or not parsed.hostname
                or parsed.username is not None or parsed.password is not None
                or parsed.path or parsed.query or parsed.fragment
                or "*" in origin or origin != f"{parsed.scheme}://{parsed.netloc}"):
            raise ValueError("WORDLE_CORS_ORIGINS requires exact HTTP(S) origins without paths or wildcards")
        # Invalid/non-numeric ports must fail configuration rather than broaden access.
        parsed.port
    return origins


app = FastAPI(title="Wordle ES API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins(),
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
    allow_credentials=False,
)

app.include_router(game.router)
app.include_router(stats.router)

@app.get("/health")
async def health():
    return {"status": "ok"}