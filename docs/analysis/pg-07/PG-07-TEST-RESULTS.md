# PG-07 — Pruebas ejecutadas y límites

Fecha: 09/11/2026. Evidencia local; ninguna ejecución remota de GitHub Actions.

| Comprobación ejecutada | Resultado |
|---|---|
| YAML | Parse correcto con PyYAML ya instalado; estructura de ocho jobs y dependencias existentes verificadas. Se corrigió durante edición un run con :all: para usar bloque YAML. |
| Scripts | Todos los run pasan bash -n con imagen Node existente, --network none; Python embebido y nuevo adaptador pasan sintaxis. No se ejecutaron scripts de despliegue/publicación/Terraform. |
| Guardas del workflow | Triggers y concurrency iguales; contents:read, sin packages:write ni pull_request_target; publicador if:false. job.services.postgres.id solo en env de paso. Revisión estática, no validador completo de expresiones. |
| Preservación jobs | Comparación estructural contra versión previa confirma frontend-build, kubernetes-validation, kind-smoke-test y terraform-validation idénticos. Docker solo añade dependencia; offline añade guardia nativa y recuento55. |
| Offline Windows | **55 aprobadas, cero omitidas, 2.697s**. Se ejecutó el Python extraído del paso real del workflow, con sockets/DNS/dotenv/libpq bloqueados. |
| Offline Linux | **55 aprobadas, cero omitidas, 1.414s**. Mismo wrapper dentro del runtime Linux construido, --network none, raíz read-only y solo app/tests montados de lectura. No son 110 casos diferentes. |
| Servicio PG-07 local | postgres:16.15, healthy; creado con opciones Docker obtenidas del YAML, tmpfs/sin volumen, loopback dinámico, nombre wordle-pg07-d4c4a50137, credencial aleatoria de prueba solo en memoria. |
| Bootstrap real | Catálogo FIN-01B aprobado, cuatro tablas sobre DB inicialmente vacía; grants/rol separado y seed existente de cinco palabras aplicados. Sin cambios SQL. |
| Suite real | **11 aprobadas, cero omitidas, 1.863s**, test_postgres_integration.py intacto. Psycopg async/HTTP/persistencia/tipos/errores/rollback/locks concurrentes/stats/ranking. Cliente de pruebas Windows, servidor PostgreSQL Linux. No se ejecutaron los once mediante un runner hospedado Linux de Actions. |
| Caída real | Solo servicio de esta prueba detenido al final: HTTP500 genérico, /health200, pool cerrado; cuatro tablas vacías y deadlocks cero antes de detenerlo. Tres division-by-zero esperados de los casos rollback; logs crudos no mostrados. |
| Limpieza | Únicamente ID del contenedor y red creados por esta ejecución eliminados; ausencia verificada. No volumen PG-07 persistente. Sin operaciones sobre clúster/PVC PG-06 o volumen PG-05. |
| Build backend | PASS, wordle-backend:v1-pg07-ci, linux/amd64, USER10001:10001. ID sha256:5c05d58dc08b1b58057190ac1de0fdc44cec97de8ba0fcd7d4cbcd5ad635e8e1. Ocho pasos cacheados. |
| Build frontend | PASS, wordle-frontend:v1-pg07-ci, linux/amd64, USERnginx. ID sha256:8c1a00a7a7a328c9c4ad6984ed93d9a702e7c263ab0d3c33a7b38bccd76d57aa. Nueve pasos cacheados; no se afirma npm ci/build nuevos fuera de caché. |
| Git/archivos | Hashes previos: únicamente .github/workflows/ci.yml cambia respecto al inicio PG-07. git diff --check correcto; avisos CRLF informativos. Índice vacío y sin commit/push. Sintaxis/whitespace y patrones acotados de secretos revisados sobre candidatos. |

## No ejecutado y no demostrado

- GitHub Actions remoto, arranque de services por el runner de Actions, condiciones reales PR/main, instalación del lock en ubuntu-24.04 y resultado/checks de ese run.
- actionlint: ausente, no instalado. YAML válido no certifica todas las reglas de contexto/expresiones de GitHub.
- kind smoke en esta fase ni validación nueva Terraform/Kubernetes: se conservaron sus jobs, no se repitieron despliegues ni se tocó PG-06.
- Publicación de imágenes: deshabilitada; no hubo login, push o nuevos tokens. Las imágenes locales no equivalen a imágenes GHCR.
- npm ci/build independientes fuera de las capas cacheadas; el job existente sigue configurándolos.
- Protección de main/branch rules, aprobación de workflows de forks o garantía de aislamiento frente a un PR malicioso. Los jobs no reciben secretos productivos.

La prueba local del servicio usa credenciales aleatorias y las mismas opciones que el YAML; el YAML contiene únicamente una credencial pública desechable de CI autorizada. Nunca se reutiliza una credencial real. Persisten riesgos de identidad usuario_id, diccionario mínimo y restauración independiente, fuera de PG-07. FIN-01 sigue pendiente.
