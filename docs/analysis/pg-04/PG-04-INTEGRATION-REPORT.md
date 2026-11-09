# PG-04 — Integración real con PostgreSQL 16

Fecha: 09/11/2026. Preparado para revisión. Rama existente codex/devops-04a1-hardening, HEAD a666b17680781a24889ea774778019995d3fca45; todos los cambios locales PG-02/03 y documentos/SQL previos preservados. Sin commits/push, cambios de esquema ni inicio de PG-05. FIN-01 permanece pendiente.

## Resultado

Se ejecutaron correctamente **11 pruebas de integración con PostgreSQL real, cero omitidas**, más una comprobación real de caída del servidor. Se conservaron y ejecutaron aparte **55 pruebas unitarias/HTTP simuladas, cero omitidas**. El build Docker del backend terminó correctamente instalando el lock Linux con wheels/hashes. No se detectó un defecto del runtime que exigiera cambiar backend, Dockerfile o baseline.

La evidencia real corresponde a FastAPI/HTTPX ASGI dentro del proceso Windows y psycopg async contra PostgreSQL Linux en Docker. No se ejecutó el backend como contenedor conectado a PG, ni frontend/Nginx, Compose, Kubernetes o Azure. Construir la imagen no se presenta como prueba de despliegue.

## Lecturas y archivos

Se inspeccionaron los tres informes PG-03, contratos/aceptación PG-01, migración FIN-01B, implementación y pruebas actuales, comprobaciones de catálogo y Dockerfile.

Nuevos archivos backend, separados de backend/tests/:

- `backend/integration/run_pg04.py`: ejecutor opt-in que crea y elimina su propio contenedor/red; no admite DSN ni una base existente; genera credenciales solo en memoria, inicializa/valida esquema y lanza integración/caída real.
- `backend/integration/test_postgres_integration.py`: once tests async reales; fixtures, limpieza, contratos/tipos, SQL fallido y coordinación observable de dos conexiones.

Documentación: este informe, [resultados](PG-04-TEST-RESULTS.md) y [traspaso PG-05](PG-04-PG05-HANDOFF.md). Ningún archivo previo de aplicación, pruebas offline, dependencias, Dockerfile, SQL, frontend, infraestructura, CI/CD o documentación histórica fue modificado. La comparación final de hashes controla el estado local de entrada, no solo HEAD.

## Entorno e aislamiento

- Docker Engine 29.9.2, Docker Desktop Linux.
- Imagen oficial local `postgres:16`, misma imagen de FIN-01B: ID sha256:f9a7b9ebf6f56201f949db745e47bc423c0f0f8294bafe991cc10bf74b029657. No se necesitó descargar otra imagen PG.
- Versión ejecutada: **PostgreSQL 16.15 (Debian 16.15-1.pgdg13+2), x86_64, GCC 14.2.0**.
- Contenedor y red bridge con nombre aleatorio `wordle-pg04-<id>`, etiqueta exclusiva y pertenencia comprobada de un solo contenedor. No se utilizó host networking, una red de otro entorno ni una DB existente.
- Puerto Docker dinámico publicado únicamente en 127.0.0.1; inspección de bindings antes de conectar. Ejecución final: contenedor/red wordle-pg04-af2a886a8325, puerto local 59703. Ejecución real anterior: wordle-pg04-3ebf52d53445, puerto 53798. Ambos ya eliminados.
- PGDATA en tmpfs de 256 MiB y socket en tmpfs de 16 MiB; sin bind mounts ni volúmenes Docker persistentes/anónimos. Memoria del contenedor 512 MiB y una CPU.
- La red bridge es exclusiva, no internal:true ni una política de denegación de egress. No se configuraron clientes remotos en PG. En el ejecutor, DNS y conexiones Python externas están bloqueados; la entrada nativa de psycopg permite únicamente el host/puerto/base/roles creados en ese run. No se conectó a Supabase, Azure ni otros DB.
- Admin temporal pg04_owner y rol de aplicación wordle_pg04_app con contraseñas distintas y aleatorias por ejecución. No se imprimen, versionan o guardan archivos de contraseña/.env. Docker recibe la contraseña temporal por entorno, sin valor literal en los argumentos. Nunca se inspecciona .Config.Env.
- El rol de app no es superusuario: se verificó current_user/rolsuper. Solo USAGE de esquema/secuencia y SELECT/INSERT/UPDATE de tablas; admin separado para baseline, fixtures y TRUNCATE de este destino temporal.
- Aislamiento verificado **read committed**. Python 3.12.14, psycopg 3.3.8 y psycopg_pool 3.3.3. El ejecutor usa WindowsSelectorEventLoopPolicy únicamente en su propio proceso Windows; sin configuración global del sistema ni cambio de main.py.

## Inicialización

El ejecutor obtiene el ID del contenedor creado por él y su puerto, comprueba cero tablas public, y aplica una sola vez por DB nueva:

`supabase/migrations/20261108000100_initial_wordle.sql`

SHA256 inalterado: da743e629094da2b7d126f7889c5d1ca72e63a232844feadea3798254b19b0cb.

Se ejecutó también `supabase/tests/schema_contracts.sql`: PASS para cuatro tablas, 23 columnas, tipos, defaults, PK/FK/UNIQUE e índices esperados, sin añadir CHECK/triggers. No se aplicó prototype/allow_all.sql ni otra migración. Las únicas fixtures de vocabulario son CASAS, PERRO, SACAS, AAAAA y NIÑOS. No representan un diccionario final ni datos históricos Supabase.

## Evidencias de funcionamiento

Todos los endpoints solicitados se ejecutaron con las dependencias de producción, sin MemoryDB ni override del repositorio. La elección de CASAS se fija únicamente desde tests; no hay endpoint de secreto ni cambio de reglas. Se verificaron UUID/JSONB/numeric/timestamp nativos contra sus formas JSON y filas consultadas por una conexión administrativa independiente.

En cada test, lifespan abre el pool vacío; las consultas prestan/devuelven conexiones y su cierre se comprueba al finalizar. /health no consulta PG y conserva 200 incluso después de detener realmente el servidor temporal. En la caída, la operación de datos devuelve 500 sanitizado sin detalles del driver y el pool se cierra.

La atomicidad se verificó inyectando `SELECT 1 / 0` únicamente en hooks de tests, tras INSERT de intento, tras inicialización de stats y tras UPDATE de stats existentes. PostgreSQL revirtió las filas/counters/estado correspondientes; no persistió una fila nueva de ceros. Una petición válida posterior demostró recuperación del acceso.

La concurrencia usa dos requests HTTP solapados y dos conexiones PG con PID distinto. El primer request se pausa después de tomar su bloqueo real; se observa el segundo en pg_stat_activity con wait_event_type=Lock antes de liberar el primero. Se comprueban números 1/2, última oportunidad sin séptima escritura, finalización ganadora única y dos finales de partidas distintas creando/actualizando stats del mismo usuario. No se implementa un simulador de bloqueos ni una prueba de carga. Tiempos acotados evitan esperas indefinidas; deadlocks registrados: cero.

## Build y limpieza

Build real ejecutado:

```text
docker build --progress=plain --target runtime --tag wordle-pg04-backend:validation-20261109 --file backend/Dockerfile backend
```

Python base oficial 3.12-slim-bookworm resuelta a sha256:935c3c5b12357a7e10caa9c1e6ca5692344d97cf229832ef584be2cec9fc03df; frontend oficial de BuildKit docker/dockerfile:1 resuelto a sha256:4edf897a3ffa55b89f906fc8cc78afdb3f1834cc9c7083565e611a8a7d5fe99e. Descargas permitidas de Docker Hub y dependencias PyPI. pip instaló las 40 distribuciones Linux de requirements.lock con --only-binary/--require-hashes. No se modificó el Dockerfile.

ID local construido sha256:fff669915d0a588897e1277e706fe2493bd3285c3b5590bae07fab452ad2e830; linux/amd64, usuario 10001:10001. La etiqueta temporal fue retirada con docker image rm, sin force ni publicación. Las capas/bases de build pueden permanecer en caché; no se purgaron imágenes o recursos compartidos/preexistentes.

El finally del ejecutor elimina por ID solo su contenedor y su red, incluso ante fallo, y comprueba su ausencia. La última ejecución verificó antes de la caída que las cuatro tablas estaban vacías por la limpieza de tests. Tras terminar, búsquedas por etiqueta wordle.pg04.run no devolvieron contenedores ni redes. El primer intento fallido y las dos ejecuciones completas limpiaron sus propios recursos.

## Criterios de aceptación y límites

Los diez criterios de la solicitud tienen evidencia: PG16 aislado, baseline correcta, driver/API reales, contratos relevantes, rollback, concurrencia básica, datos persistidos coherentes, 55 tests previos verdes, build correcto y recursos temporales retirados. La matriz C01–C22 y las incidencias están en resultados.

No se valida durabilidad tras reinicio, volumen/PVC, backups, HTTP por TCP/Nginx, despliegue de imagen Linux, multiproceso/Blue-Green, carga/saturación, cancelación real durante una transacción o pérdida de conexión exactamente en COMMIT. Estos límites no se ocultan con resultados mock. usuario_id sigue sin autenticación y GET mantiene su consistencia previa entre lecturas independientes. No se declara FIN-01 completo.

Recomendación: tras revisar/aceptar PG-04, se puede autorizar PG-05 para Compose persistente de tres servicios con migración/seed controlados. No se inició automáticamente.
