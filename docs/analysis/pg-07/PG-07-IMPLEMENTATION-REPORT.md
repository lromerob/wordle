# PG-07 — Integración continua con PostgreSQL real

Fecha: 09/11/2026. Implementado para revisión local; no ejecutado en GitHub Actions. FIN-01 sigue pendiente. Sin commits/push ni tareas posteriores.

## Inventario y cambios mínimos

Se inspeccionaron los tres informes PG-06, resultados PG-04/05, workflow, suite offline/real, requisitos/lock, Dockerfiles y ejecutores existentes. Había un workflow ci.yml con siete jobs: backend-tests, frontend-build, docker-build, kubernetes-validation, kind-smoke-test, publish-ghcr y terraform-validation.

Archivos PG-07:

- Modificado .github/workflows/ci.yml.
- Nuevo backend/integration/run_pg07_ci.py, adaptador del servicio CI para la suite PG-04.
- Tres informes nuevos de esta carpeta.

No se modifican aplicación, contratos, SQL, dependencias/lock, Dockerfiles, Compose, Terraform, Kubernetes, tests existentes o documentos anteriores. Los cambios locales PG-01/06 se preservan. No se instala software ni actionlint.

## Flujo resultante

Triggers pull_request, workflow_dispatch y push a main, junto a concurrency, intactos.

1. backend-tests: instala lock con hashes/wheels, ejecuta discovery y exige 55 casos/cero omitidos/éxito. Se añade bloqueo psycopg.AsyncConnection.connect al bloqueo Python sockets/DNS/dotenv; libpq no depende de los sockets Python.
2. **postgres-integration nuevo**: Python3.12 sobre ubuntu-24.04, servicio oficial postgres:16.15 temporal; inicialización y once casos reales con caída aislada al final.
3. frontend-build sin cambios: npm ci y npm run build.
4. docker-build conserva sus dos construcciones runtime sin push; ahora depende también de postgres-integration, además de offline/frontend. Un fallo real bloquea builds y el smoke dependiente.
5. kubernetes-validation sin cambios: comprueba archivos versionados y renderiza k8s/local; no valida por sí mismo el overlay PostgreSQL ni demuestra despliegue.
6. kind-smoke-test sin cambios: despliegue/mínimo funcional efímero **en memoria**, no PostgreSQL. Sigue necesitando sus cuatro jobs anteriores; Docker depende transitivamente de integración real. No se ejecutó localmente ni se alteró el clúster PG-06.
7. terraform-validation sin cambios: fmt/init sin backend/validate, sin Azure.
8. publish-ghcr conserva definición pero **if: false** y se elimina packages:write. No se ejecutará en PR, push o manual. Esto se acordó expresamente con el propietario al resolver la incompatibilidad entre conservar controles y no publicar/desplegar. Se autorizó conservar el kind efímero de CI, no despliegues persistentes/cloud. No restaurar publicación ni permisos sin revisión posterior.

Permisos globales y nuevo job contents:read; checkout persist-credentials:false; sin pull_request_target, nuevos tokens, credenciales Azure o secretos de producción. La referencia GITHUB_TOKEN del publicador histórico permanece en su definición deshabilitada, no se incorpora un token nuevo ni se ejecuta login/push.

## Servicio PostgreSQL

Base pg07_ci, administrador pg04_owner (nombre mantenido por reutilización PG-04). Credencial pública declarada **exclusivamente de CI desechable** en servicio/paso; nunca usarla fuera del runner. Rol de aplicación wordle_pg04_app con password aleatorio en memoria separado de admin.

Docker options: etiqueta wordle.pg07=ci, publicación dinámica **127.0.0.1::5432**, PGDATA tmpfs256MiB y socket tmpfs16MiB, máximo512MiB/1CPU. Sin volúmenes/bind persistentes. pg_isready TCP con health interval5s/timeout3s/retries12. Cada job hospedado tiene su propio runner/daemon; el puerto dinámico evita colisiones y no se publica en todas las interfaces.

El adaptador recibe el ID de job.services.postgres.id como variable de entorno (no interpolado en código shell). Inspecciona solo ID/etiqueta/imagen/montajes/tmpfs/puerto, nunca Config.Env. Rechaza otro tipo de contenedor, persistencia, imagen distinta o binding no loopback. No admite DSN/host/base arbitrarios. Las conexiones psycopg nativas se restringen al puerto de ese contenedor/base/roles; sockets externos/DNS/dotenv bloqueados durante inicialización/suite. Es aislamiento del ejecutor de prueba, no una sandbox frente a código malicioso de PR.

## Inicialización y fixtures

Reutiliza prepare() de run_pg04.py: espera conexión al servicio, exige **cero tablas public antes de DDL**, aplica sin modificar supabase/migrations/20261108000100_initial_wordle.sql, valida supabase/tests/schema_contracts.sql y crea rol app no superusuario con grants originales. Una DB ya inicializada provoca fallo antes de los TRUNCATE de las pruebas; no hay reset automático.

Se aplica docker/postgres/20-demo-words.sql y se verifica cinco palabras. Después, cada caso PG-04 instala su fixture propia de cinco palabras (incluye AAAAA para letras repetidas); esta difiere deliberadamente de la muestra PG-05 que contiene GATOS. No es un esquema alternativo ni diccionario definitivo. La suite se reutiliza **sin cambios** y mantiene sus TRUNCATE únicamente después del bootstrap validado en la DB temporal.

Tras once tests: cuatro tablas vacías y deadlocks cero; outage() existente detiene solo el ID del servicio validado, comprueba 500 sanitizado, /health200 y cierre del pool. Se esperan tres errores SQL division-by-zero de rollback, sin deadlock; no se publican logs crudos ni contraseñas. La caída es una comprobación adicional, no un duodécimo unittest. Actions gestiona la retirada final del servicio; no interfiere con los demás jobs.

Comandos del workflow:

```text
python -m pip install --only-binary=:all: --require-hashes -r backend/requirements.lock
python -B backend/integration/run_pg07_ci.py --service-container "$PG07_SERVICE_CONTAINER"
docker build --target runtime --tag wordle-backend:ci backend
docker build --tag wordle-frontend:ci frontend
```

El runner no sirve para apuntar a una DB existente. Para repetir localmente, crear un servicio NUEVO postgres:16.15 con las opciones exactas del YAML, POSTGRES_DB/USER de CI y contraseña efímera suministrada por entorno, esperar healthy, establecer PG07_CI_ADMIN_PASSWORD en el proceso y pasar exclusivamente su ID. Eliminar únicamente ese contenedor y su red al terminar. No usar DB/PVC/volumen PG-05/06 ni ejecutar el adaptador sobre otros destinos.

## Estado y límites

Validación local: 55 offline Windows y Linux, once reales contra servicio temporal y outage; builds Linux y validación estática disponibles correctos (resultados separados). No se ejecutó el servicio mediante el orquestador de Actions ni el pipeline remoto. actionlint no está instalado: YAML/Bash/Python y controles explícitos no equivalen a validar todas las expresiones con GitHub.

Varias entradas necesarias siguen locales/sin versionar: app/repository.py, integration/run_pg04.py, test_postgres_integration.py, nuevo adaptador, tests adicionales, baseline/catalog tests, fixture y cambios PG anteriores. No basta publicar solo ci.yml: revisar el conjunto coherente antes de autorizar publicación. No se preparó ningún archivo en el índice.

Recursos locales PG-07: servicio wordle-pg07-d4c4a50137 y red exclusivos retirados, sin volumen. Imágenes wordle-backend:v1-pg07-ci y wordle-frontend:v1-pg07-ci conservadas; builds usaron caché válida (8/9 pasos), no se afirma instalación nueva de paquetes. PG-05 volumen/imágenes/backup intactos; PG-06 no recibió operaciones Kubernetes ni cambios de archivos. Sin servicios Supabase/Azure, despliegues nuevos o publicación.
