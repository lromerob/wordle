# PG-02 — Implementación del acceso PostgreSQL directo

Fecha: 08/11/2026. Preparado para revisión; sin commit/push ni despliegue. Rama conservada: `codex/devops-04a1-hardening`, HEAD de referencia `a666b17680781a24889ea774778019995d3fca45`. Los documentos/SQL locales previos se preservan. FIN-01 continúa pendiente. Este incremento no implementa PG-03 ni PG-04.

## Fuentes y autorización

Lectura íntegra de los tres documentos PG-01, FIN-01C-DEPENDENCY-INVENTORY, FIN-01C-MIGRATION-PLAN y baseline `supabase/migrations/20261108000100_initial_wordle.sql`; inspección de backend, pruebas, Dockerfile, lock y procedimiento del README. Las referencias históricas a implementar transacciones/concurrencia se acotan por la autorización PG-02 actual, que las difiere expresamente. No se encontró contradicción de contrato que exigiera cambiar reglas.

El propietario aclaró expresamente que se permite descargar únicamente desde PyPI los paquetes necesarios. No se consultaron Supabase, Azure, bases externas ni registros Docker. No se leyeron archivos de secretos ni se inició ningún servidor de aplicación, PostgreSQL o contenedor. TestClient ejecuta la aplicación en proceso con datos simulados.

## Archivos de implementación

| Archivo | Cambio |
|---|---|
| `backend/app/database.py` | Fábrica de pool async sin conexión/import-time; lifespan; dependencia async con conexión prestada y error sanitizado. |
| `backend/app/repository.py` (nuevo) | Adaptador de dominio con 11 operaciones SQL async, cursores cerrados, parámetros separados y JSONB. |
| `backend/app/main.py` | Registra lifespan; necesario para apertura/cierre; rutas, CORS y health conservados. |
| `backend/app/routers/game.py` | Sustituye llamadas SDK por await del adaptador; helper de estadísticas async. Reglas/evaluador/modelo conservados. |
| `backend/app/routers/stats.py` | Lectura de estadísticas y ranking mediante adaptador. |
| `backend/requirements.txt`, `backend/requirements.lock` | Driver/pool fijados; lock regenerado por uv con hashes; SDK y transitivas exclusivas retirados. |
| `backend/tests/test_backend.py` | Doble async de dominio, override nuevo, lifecycle TestClient y bloqueo de entrada nativa de libpq. Conserva los 20 casos. |
| `backend/tests/test_stabilization.py` | Conserva seis regresiones; ausencia de fila se prueba como None, sin emular single() del SDK. |
| `backend/tests/test_postgres_adapter.py` (nuevo) | 19 casos adicionales de SQL/cursores, tipos, contratos, errores y pool. Sin PostgreSQL. |
| `backend/docker/memory_server.py` | Adaptación del entrypoint de pruebas al nuevo override y bloqueo nativo de psycopg. Necesario para preservar el modo memoria existente; no cambia Dockerfile ni infraestructura. |

Documentación nueva: este informe, [resultados](PG-02-TEST-RESULTS.md) y [traspaso PG-03](PG-02-PG03-HANDOFF.md), exclusivamente en esta carpeta. No se modifican frontend, Compose, Kubernetes, Terraform, Actions, SQL, informes anteriores ni plan FIN. El Dockerfile no necesita cambios: la distribución binaria trae libpq.

## D01–D09: decisiones técnicas

- **D01:** Python 3.12.14 de ensayo; `psycopg[binary]==3.3.8` y `psycopg-pool==3.3.3`, versiones estables disponibles en PyPI con wheels Windows CPython 3.12 y Linux x86_64. FastAPI 0.111.0, Uvicorn 0.30.0, Pydantic 2.7.1 y HTTPX 0.27.0 conservados. Se conserva python-dotenv 1.0.1 porque los bloqueos existentes de CI/harness lo parchean y Uvicorn lo utiliza; el nuevo acceso no carga .env. El SDK, PostgREST, gotrue, realtime, storage3, supafunc y transitivas ya innecesarias desaparecen del lock. El entorno .venv previo no se purga; una instalación nueva prueba que no se requiere el SDK.
- **D02:** pool por proceso; mínimo 0, máximo 4, cola máxima 8, espera de adquisición 3 s, connect_timeout 3 s, reconnect_timeout 3 s, dos workers internos. statement_timeout e idle_in_transaction_session_timeout de 5 s por conexión. Una conexión por request de datos, reutilizada entre sus consultas. No existe conexión global compartida. Blue+Green con W procesos cada una puede consumir hasta 8W conexiones; dimensionar el presupuesto global después.
- **D03:** open=False en construcción; apertura `open(wait=False)` y cierre await en lifespan. Mínimo 0 evita conexión inicial para health. `/health` continúa 200/status ok sin consulta DB; no es readiness de persistencia. Si hay override explícito del repositorio, lifespan omite el pool de producción, conservando el entorno puramente en memoria.
- **D04:** configuración exclusivamente del entorno de proceso, tabla siguiente. No se carga .env ni se consulta configuración Supabase. passfile se fija al dispositivo nulo para no leer archivos de contraseña implícitos. El rol operativo debe ser distinto del migrador; no se crean roles/permisos ahora.
- **D05:** UUID malformado se convierte en DataError interno y HTTP 500 genérico, nunca un 404 de fila ausente ni un 400/422 nuevo. UUID válido sin fila conserva 404/Partida no encontrada. Errores psycopg, timeout, pool cerrado o cola llena devuelven 500 `{"detail":"Base de datos no disponible"}`. Se define la forma genérica antes no especificada; no se afirma que Supabase devolviera este JSON. No se incluyen mensajes/SQL/DSN/parámetros del driver, ni se reintentan escrituras de aplicación.
- **D06:** dict_row, UUID nativo para parámetros, Jsonb de lista para escritura; filas con UUID/datetime/Decimal se serializan mediante FastAPI. Se verifican cadenas UUID, JSON no doblemente codificado, media fraccionaria numérica y timestamp sin zona/sufijo inventado. Esto no acredita todavía adaptación PostgreSQL real.
- **D07:** autocommit=True conserva operaciones SQL independientes como las llamadas anteriores. Cada sentencia termina antes de continuar; no se mantiene una transacción idle entre consultas. Un intento completo NO es atómico. La conexión se devuelve por el context manager del pool incluso al fallar/cancelar; las escrituras ya confirmadas no se revierten. PG-03 debe establecer la unidad transaccional, sin retries ciegos.
- **D08:** adaptador pequeño de dominio, sin ORM ni clon fluent del SDK. Los 26 métodos de prueba previos conservan o incrementan sus aserciones. La garantía de import lazy se refuerza con proceso nuevo y bloqueo de conexión nativa.
- **D09:** solo datos/conexiones simulados y uso de API real del pool sin sockets PostgreSQL. No se inicia una DB ni se reaplica SQL. La integración real queda para PG-04 autorizado.

## Configuración y ejecución futura

| Variable | Default no sensible | Uso |
|---|---|---|
| PGHOST | 127.0.0.1 | Host de la DB nueva autorizada. |
| PGPORT | 5432 | Puerto PostgreSQL. |
| PGDATABASE | wordle | Nombre de base. |
| PGUSER | wordle | Rol técnico de aplicación. |
| PGPASSWORD | Vacío | Inyectar externamente; nunca versionar, imprimir ni reutilizar claves Supabase. |
| PGSSLMODE | prefer | En una conexión remota futura debe definirse una política TLS con verificación de identidad/certificados; prefer no la garantiza. |

No introducir una DSN en VITE ni copiar credenciales a la imagen. No hay prueba de configuración de roles/TLS en esta fase. Estos defaults permiten construir/abrir un pool vacío sin credenciales, pero no demuestran que las operaciones de datos funcionen.

Con DB nueva y permisos autorizados en una fase posterior: inyectar PG* en el proceso y ejecutar desde backend `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 1 --loop asyncio`. No se ejecutó este comando. En Windows, psycopg async requiere un loop Selector: para una ejecución con DB real deberá configurarse `asyncio.WindowsSelectorEventLoopPolicy()` antes de uvicorn.run; no se ha probado una conexión Windows real. Linux es el objetivo del Dockerfile.

El arranque NO ejecuta migraciones, seeds, CREATE TABLE ni crea usuarios. La baseline queda donde estaba; la base debe inicializarse posteriormente por un procedimiento autorizado. No existe fallback Supabase ni doble escritura. Compose de producción sigue declarando configuración antigua y necesitará PG-05; no se presenta como ejecutable con PG solo por cambiar el driver. El harness de pruebas sigue en memoria; k8s/CI conservan ese significado. El diccionario de demostración y la identidad de usuarios siguen pendientes.

## Los 12 criterios PG-02

CUMPLIDO (offline) significa evidencia con dobles; no integración PostgreSQL ni autorización de despliegue.

| ID | Resultado | Evidencia / pendiente |
|---|---|---|
| P2-01 | PARCIAL | Driver/pool/lock y 40 wheels Linux con hashes verificados; instalación limpia sin SDK. Imagen Linux y DB real pendientes. |
| P2-02 | CUMPLIDO (offline) | Import nuevo sin conexiones; pool real abre/cierra vacío; conexión simulada se devuelve ante excepción y cancelación; lifespan cierra ante fallo. |
| P2-03 | PARCIAL | Límites/timeouts explícitos, cuatro préstamos del pool real, quinto agota timeout y posterior reutilización. Falta disponibilidad/carga con PostgreSQL. Health independiente comprobado. |
| P2-04 | CUMPLIDO (offline) | 200 con solo UUID string reutilizable, valores de insert y error de diccionario vacío. SQL real pendiente PG-04. |
| P2-05 | CUMPLIDO (offline) | 400/403/404, precedencia/textos, no writes al rechazo y framework 422. |
| P2-06 | CUMPLIDO (offline) | Repetidas, normalización, seis intentos, victoria sexta, derrota y bloqueo posterior; solución null salvo derrota. |
| P2-07 | CUMPLIDO (offline) | GET oculta solución activa/desconocida/null, conserva final ganada/perdida, no altera fila y ordena intentos. |
| P2-08 | CUMPLIDO (offline) | Rama de cinco ceros, media de victorias 1.5 conservada al perder, rachas, ranking cuatro campos/máximo diez. |
| P2-09 | CUMPLIDO (offline) | UUID/datetime/Decimal/JSON y null de filas simuladas serializan como se documenta; no transporte DB probado. |
| P2-10 | PARCIAL | UUID inválido/ausente y fallos sanitizados, retorno de conexión y petición posterior comprobados con dobles; recuperación real de libpq pendiente. |
| P2-11 | PARCIAL | 45 tests aprobados, cero omitidos; 26 originales conservados. Los casos de driver sobre PG real están expresamente diferidos a PG-04. |
| P2-12 | CUMPLIDO | Scope auditado con hashes; baseline y archivos previos fuera del backend intactos. Sin Auth nuevo/infraestructura/commit/push. |

No se declara aceptación completa de integración: PG-02 queda implementado para revisión con las limitaciones anteriores. FIN-01 sigue pendiente. Los riesgos de transacción/concurrencia están en el handoff y no se resuelven silenciosamente aquí.
