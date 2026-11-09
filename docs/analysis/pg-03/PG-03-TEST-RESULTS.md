# PG-03 — Resultados de pruebas

Fecha: 09/11/2026. Exclusivamente unitarias/HTTP en proceso con dobles, sin servicios ni PostgreSQL real. Entorno .venv existente: Python 3.12.14, psycopg 3.3.8, psycopg_pool 3.3.3, FastAPI 0.111.0 y HTTPX 0.27.0. No se instalaron paquetes en PG-03.

## Ejecuciones reales

| Comprobación | Resultado |
|---|---|
| Referencia PG-02 antes de modificar | 45 pruebas aprobadas, cero omitidas; 1.211 s. |
| Primera ejecución PG-03 | 54 pruebas aprobadas, cero omitidas; 1.388 s. |
| Ejecución final, con caso de stats inicializadas a cero | **55 pruebas aprobadas, cero omitidas; 1.212 s.** |
| Preservación de PG-02 | AST de los mismos 45 métodos de test idéntico al snapshot inicial. Solo protocolos de sus dobles ampliados. |
| Sintaxis | compile() en memoria sobre app/ y tests/: correcto, sin bytecode generado. |
| Scope | Hashes: únicamente repository.py, game.py, test_backend.py y test_postgres_adapter.py cambian respecto al estado PG-02; se añade test_transactions.py y tres documentos PG-03. |
| Migración SQL | Sin cambios. SHA256 da743e629094da2b7d126f7889c5d1ca72e63a232844feadea3798254b19b0cb. |
| git diff --check | Correcto. Aviso previo de normalización LF/CRLF del lock PG-02, sin modificarlo en esta fase. |

## Cómo se bloquearon conexiones

Se ejecutó discovery equivalente a `python -m unittest discover -s backend/tests -v`, envuelto durante imports y tests con los bloqueos documentados en [PG-02-TEST-RESULTS](../pg-02/PG-02-TEST-RESULTS.md): socket.connect permite únicamente loopback para el socketpair interno Windows; connect_ex y getaddrinfo prohibidos; dotenv.load_dotenv prohibido; psycopg.AsyncConnection.connect prohibido. El último bloqueo impide el acceso nativo de libpq, que no depende de sockets Python.

No se proporcionan credenciales y no se leen .env. TestClient funciona dentro del proceso. La prueba heredada de importación en proceso nuevo conserva sus propios bloqueos. Se usa la .venv ya disponible, sin descargas ni acceso a servicios remotos.

## Diez pruebas añadidas: test_transactions.py

| Grupo / caso | Qué demuestra offline |
|---|---|
| TransactionAdapter / delegación | transaction() usa el contexto de la conexión psycopg. |
| TransactionAdapter / bloqueo partida | SQL parametrizado con UUID y FOR UPDATE; GET ordinario sigue sin bloquear. |
| TransactionAdapter / estadísticas | Se solicita INSERT ON CONFLICT DO NOTHING antes del SELECT FOR UPDATE, sin sobrescribir valores existentes. |
| TransactionAdapter / fila ausente tras inicializar | DataError aborta, sin un segundo INSERT a ciegas. |
| AttemptTransaction / fallos de escritura | Fallos tras insertar intento, antes de actualizar partida y al crear/actualizar stats salen del contexto; snapshot del doble vuelve al estado inicial. Ningún replay. |
| AttemptTransaction / cancelación | CancelledError atraviesa y abandona el contexto; el doble restaura su snapshot. |
| AttemptTransaction / frontera | Lectura bloqueada y todas las escrituras suceden entre begin y commit del contexto; resultado se devuelve después. |
| AttemptTransaction / defaults de stats | Fila inicializada a cero produce las mismas estadísticas de primera victoria/derrota sin crear otra fila. |
| AttemptTransaction / estado leído bajo bloqueo | Estados finalizados o activo al límite recibidos por get_game_for_update rechazan sin escribir. No se valida contra una lectura previa sin lock. |
| CommitFailure / HTTP | Excepción al salir del contexto transaccional no devuelve éxito: 500 genérico, una sola escritura del intento y devolución de conexión solicitada. |

Las 45 pruebas previas siguen cubriendo letras repetidas, victoria/derrota/sixth attempt, errores, propietario declarado, solución oculta, estadísticas, ranking, tipos, lifecycle y retorno al pool. No se eliminaron pruebas ni se redujeron aserciones.

## Límites explícitos

MemoryDB usa un snapshot de diccionarios de unas líneas para probar la frontera de rollback solicitada. No implementa SELECT, MVCC, locks, aislamiento o un coordinador de concurrencia. Su restauración no demuestra rollback de PostgreSQL. El doble de conexión/cursor registra el protocolo y SQL; no ejecuta ni valida SQL en el servidor. El contexto transaccional del doble no reproduce commit/rollback de libpq.

No se lanzaron dos peticiones reales simultáneas contra una DB ni se construyó un simulador para atribuir a mocks ausencia de números duplicados o integridad de estadísticas. Esas propiedades se derivan del diseño PostgreSQL propuesto y siguen pendientes de demostración en PG-04. Los tests presentes verifican las precondiciones controlables por el código: transacción, bloqueo antes de validar, orden de sentencias y ausencia de confirmación HTTP ante error.

Tampoco se verificó timeout/rollback/cancelación de una transacción real, recuperación de una conexión abortada, latencia de espera de lock o incertidumbre del COMMIT. El test de pool heredado utiliza el pool real con conexiones de protocolo simuladas; no prueba salud de una conexión libpq real.

Sin contenedores, Docker builds, migraciones, servicios externos, integración PostgreSQL, infraestructura, commits o push. FIN-01 continúa pendiente.
