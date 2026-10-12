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


## Frontend Wordle v1.0 (React + Vite, JavaScript)

Requirements: Node.js 22.12+ (validated on Node 24). From the repository root:

```sh
cd frontend
npm ci
# Copy .env.example to .env.local and set your backend URL, if needed.
npm run dev
```

Vite serves the application at http://localhost:5173. Set
`VITE_API_BASE_URL=http://localhost:8000` in frontend/.env.local; the default is
localhost:8000. This is a public API URL, not a secret. All VITE_ variables are
embedded in browser assets: never put Supabase keys or other credentials there.
The URL is selected at build time; changing it requires rebuilding the frontend.
An HTTPS frontend requires an HTTPS backend to avoid mixed-content errors.

```sh
npm test
npm run build
npm run preview
```

Tests replace fetch with simulated API responses; they do not contact FastAPI
or Supabase. The board uses the backend's correcto/presente/ausente evaluation,
not a client-side dictionary or secret word. Six attempts, virtual/physical
keyboards, loading/error states and a new game after completion are included.
If a guess response is lost or the server returns a 5xx error, input is locked
until GET /game/{partida_id} recovers the authoritative game state. There is no
automatic retry of writes. Reloading the page does not resume the game in v1.0.

API contract: POST /game/nueva?usuario_id=... returns partida_id;
POST /game/intento accepts partida_id, usuario_id and palabra and returns
resultado, estado, intentos_usados and palabra_secreta (only on loss).
GET /game/{partida_id} returns partida and intentos, used for recovery.
The UI accepts A-Z and Ñ; accents are not normalized because the backend does
not define such a policy. The dictionary must match that alphabet and uppercase
lookup convention. No backend changes were required.

A random UUID is stored as wordle-user-id in localStorage and used for both
creation and guesses. This is an anonymous compatibility identifier, NOT login
or verified authorization. If database constraints require pre-existing users,
user provisioning or verified authentication must be resolved separately.
A configured backend with a populated dictionary is required for real games;
no real database integration was exercised during frontend development.

This is the initial Wordle v1.0 UI for a future Blue release. No Green variant,
container, Kubernetes configuration or deployment is included.
