# wordle
Wordle project for the CI/CD


## Backend tests (no Supabase)

From the repository root, with the backend dependencies already installed:

```sh
python -m unittest discover -s backend/tests -v
```

The suite uses the standard-library unittest runner. HTTP tests use FastAPI
TestClient and the pinned HTTPX dependency from backend/requirements.txt.
They override get_supabase with an isolated in-memory double and block outbound
socket connections. No .env file is loaded and no Supabase client is created.
Without FastAPI/HTTPX, HTTP tests are explicitly skipped; a skipped suite is not
full validation. Pure evaluation and handler-body tests still run directly from the source AST.
Handler-body tests inject the in-memory database and an HTTPException stand-in;
they validate game behavior but do not replace HTTP/framework integration tests.

Supabase configuration is loaded lazily on the first database-backed request.
Production continues to use SUPABASE_URL and SUPABASE_KEY. /health does not
initialize Supabase. Tests replace app.database.get_supabase using FastAPI's
app.dependency_overrides.

## Security boundaries and pending work

Active game retrieval omits palabra_secreta without changing the stored row.
Submitting a guess rejects usuario_id when it differs from the stored owner.
This is only a consistency check, NOT effective authorization: usuario_id is
client-controlled, there is no verified authentication, and a caller who knows
the owner's identifier can impersonate that owner. New games, game retrieval
and statistics also lack verified authorization. Add verified identity and
owner-scoped access before exposing the API to untrusted users.

Writes across guesses, games and statistics remain non-transactional and subject
to concurrency races. Supabase .single() errors are not yet translated reliably
to HTTP 404 (the in-memory double does not model transport/provider errors).
Other pending work includes statistics average updates, restrictive CORS,
stronger validation and avoiding synchronous database I/O in async handlers.
No database schema or RLS changes are part of this iteration.
