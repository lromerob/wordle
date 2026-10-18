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
Kubernetes configuration or deployment is included. Local containers are
documented below.


## Docker and Compose (local v1.0)

Requires a running Docker engine in Linux-container mode and Docker Compose.
Only Nginx is published, at http://localhost:8080 and bound to loopback.
The browser uses same-origin /api; Nginx strips that prefix and forwards to
backend:8000 on the Compose network. Do not put Docker service names into a
browser URL. The frontend image fixes VITE_API_BASE_URL=/api at build time.
Neither the backend game logic nor the database schema is changed here.

### Safe local validation, without Supabase

From the repository root (PowerShell or a shell), always include both files:

```sh
docker compose -f compose.yaml -f compose.test.yaml config --quiet
docker compose -f compose.yaml -f compose.test.yaml build --pull
docker compose -f compose.yaml -f compose.test.yaml up -d --wait
docker compose -f compose.yaml -f compose.test.yaml ps
curl http://localhost:8080/healthz
curl http://localhost:8080/api/health
docker compose -f compose.yaml -f compose.test.yaml logs --tail=100
docker compose -f compose.yaml -f compose.test.yaml down
```

On Windows PowerShell, use curl.exe rather than its Invoke-WebRequest alias.
Open http://localhost:8080 to play. The memory fixture solution is CASAS; the
valid dictionary also contains PERRO, SACAS and AAAAA. ZZZZZ must be rejected.
Check a win using CASAS and a loss using PERRO six times. New games reset the
board. Data is ephemeral, shared by the single test worker, and lost when the
backend restarts. This is a test fixture, not an offline production database.
The test override selects the memory-test image target, clears both Supabase
environment variables, blocks Supabase imports, .env loading, external DNS and
outbound external socket connections. FastAPI joins only the internal default
network and publishes no host ports. Nginx joins both that network and the
non-internal ingress bridge, which enables loopback port publication on Windows.
Only Nginx is exposed at 127.0.0.1:8080. Its ingress network permits outbound
traffic; backend isolation and the memory-mode guards remain in place.
Builds still need access to package registries and image registries.

### Normal runtime configuration (not exercised against Supabase)

```sh
docker compose build --pull
docker compose up -d --wait
docker compose ps
docker compose down
```

The default backend uses app.main and the existing lazy Supabase dependency.
Provide SUPABASE_URL and SUPABASE_KEY only to the backend at runtime via your
local shell or a private untracked environment file. Do not put real values in
Compose, Dockerfiles, build arguments or any VITE_ variable. No credential files
are copied into either image or mounted into the containers. Runtime environment
values are visible to users with Docker administrative access. Avoid printing
`docker compose config` without --quiet when real environment values are set.
Without configuration /health works but gameplay requires Supabase; use the
memory override above for all validation that must avoid real database calls.
Do not switch from memory to normal mode to continue a test.

Both runtime images run as non-root users with read-only filesystems, a /tmp
mount, dropped capabilities, healthchecks and restart: unless-stopped. The
frontend waits for backend startup health. Backend /health checks process
availability, not database readiness; frontend /healthz checks Nginx, while
/api/health checks the proxy path. Health status alone does not restart an
unhealthy container; restart policy applies when the process exits. Nginx uses
Docker DNS to refresh the backend address. SPA routes fall back to index.html.
This is a local HTTP environment; no TLS or deployment infrastructure is added.

### Reproducible dependencies and validation limits

Backend requirements.lock pins transitive dependencies with hashes for Python
3.12 and Linux x86_64. Docker installs wheels with --require-hashes and
--only-binary. To intentionally update the lock, use uv 0.13.0 in an isolated
environment and review the resulting changes:

```sh
uv pip compile backend/requirements.txt --python-version 3.12 --python-platform x86_64-unknown-linux-gnu --generate-hashes --no-emit-index-url --index-url https://pypi.org/simple --output-file backend/requirements.lock
```

The Linux lock is not a Windows development requirements file. Frontend uses
npm ci and the existing package-lock.json. Base images use version tags
(python:3.12-slim-bookworm, node:24-bookworm-slim, nginx:1.28-alpine), which can
move; digest pinning remains necessary for byte-identical image rebuilds. Other
architectures have not been validated.

Validation completed locally with Docker Desktop 29.4.1, Linux containers and
WSL2: both images built, both services healthy, Nginx configuration valid, and
GET /, GET /api/health and game creation plus a win passed from Windows at
127.0.0.1:8080. Invalid guesses, evaluation colors, a six-attempt loss and seventh
attempt rejection also passed through Nginx in the memory environment. No real
Supabase calls or credentials were used. The original single internal network
prevented host port publication; the two-network test topology above fixes it.
Temporary test containers and networks were removed without deleting volumes
or unrelated resources. The 20 backend and 12 frontend tests and the /api build
also passed. Production Supabase integration, other architectures and cloud
deployments have not been validated.
