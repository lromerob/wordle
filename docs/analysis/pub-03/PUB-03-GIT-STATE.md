# PUB-03 — Estado de Git y manifiesto

Fecha: 09/11/2026. Solo inspección, un fetch autorizado y estos tres informes nuevos. No se cambia de rama ni se modifica el índice/historial o archivo previo. No se ejecutan tests ni operaciones Docker/Kubernetes/Azure.

## Estado inicial verificado

- Rama activa: codex/devops-04a1-hardening.
- HEAD: a666b17680781a24889ea774778019995d3fca45.
- Último commit: ci: validate Terraform and document secure AKS access.
- Upstream: origin/codex/devops-04a1-hardening.
- 16 archivos versionados modificados y 65 nuevos sin seguimiento: **81 rutas**, exactamente las del manifiesto PUB-02. Índice vacío.
- 53 archivos ya versionados y 118 archivos no ignorados presentes antes de PUB-03; hashes registrados en memoria. No se ha abierto .env real, kubeconfig, backup o estado privado.

Origin fue verificado antes de conexión: HTTPS GitHub lromerob/wordle, URL de fetch/push esperada, sin usuario/password/query embebidos. Único remoto: origin. La configuración fetch corresponde a refs/heads/* → refs/remotes/origin/*; no se imprimieron valores privados ni se modificó autenticación/configuración global. safe.directory se limita a cada comando.

Ignorados relevantes por nombre: backend/.env, .venv/ (incluida kubeconfig local), __pycache__ del backend/tests, frontend/node_modules, frontend/dist e infra/terraform/.terraform. No se leen ni incluyen esos contenidos. PG-05/06 y sus recursos privados quedan fuera.

## Única sincronización realizada

`git fetch origin main` terminó con éxito. Prompts desactivados únicamente en el proceso (GIT_TERMINAL_PROMPT=0/GCM_INTERACTIVE=Never); sin cambiar helpers/credenciales ni buscar alternativas. No hubo solicitud interactiva ni error que requiriese intervención.

- origin/main antes: ed6b45bd7e827c9714f6d0978ac81b42e82af749.
- origin/main después: 86cbf8936dc04abc39b8bee26c37767328db13df.
- FETCH_HEAD: 86cbf8936dc04abc39b8bee26c37767328db13df.
- Ancestro común HEAD/main: a666b17680781a24889ea774778019995d3fca45.
- `rev-list --left-right --count HEAD...origin/main`: **0 / 1**.
- Commit exclusivo de main: 86cbf8936dc04abc39b8bee26c37767328db13df — Merge pull request #5 from lromerob/codex/devops-04a1-hardening.
- Commits exclusivos de HEAD: ninguno. HEAD es ancestro de main; no hay divergencia lateral.
- Padres del merge: ed6b45bd7e827c9714f6d0978ac81b42e82af749 a666b17680781a24889ea774778019995d3fca45.

Main sí avanzó respecto a la referencia antigua; incorporó el commit local de hardening mediante el merge PR#5. **Los árboles de HEAD y main son idénticos:** cf8c64542e1e1a79dd581415d41c22161141a89a. El diff de nombres/contenido HEAD..main está vacío. Avance de historial no equivale aquí a cambio de archivos.

El fetch actualiza origin/main/FETCH_HEAD y objetos Git como parte de la operación autorizada. Las ramas locales, etiquetas, HEAD e índice no se cambian; la referencia simbólica origin/HEAD resuelve ahora al main actualizado. No hubo pull, merge, rebase, reset o limpieza.

## Revisión exacta de las 81 rutas PUB-02

M=modificado respecto a HEAD; ?=sin seguimiento. Todas existen, son archivos de texto regulares (sin symlink) y no están ignoradas, comprobado también para las plantillas ya versionadas. Incluir es recomendación de una tarea futura, no preparación del índice.

| Ruta | Git | Existe / tipo | Ignorada | Dependencia o función | Inclusión y riesgo |
|---|---|---|---|---|---|
| `.github/workflows/ci.yml` | M | Sí / texto regular | No | CI backend/build/kind | Sí, propuesto; Literal público solo CI; GHCR deshabilitado |
| `.gitignore` | M | Sí / texto regular | No | Documentación/soporte; no ejecución CI directa | Sí, propuesto; Sin secreto detectado por patrones |
| `README.md` | M | Sí / texto regular | No | Documentación/soporte; no ejecución CI directa | Sí, propuesto; Sin secreto detectado por patrones |
| `backend/.env.example` | M | Sí / texto regular | No | CI backend/build/kind | Sí, propuesto; Sin secreto detectado por patrones |
| `backend/SECURITY-NOTES.md` | M | Sí / texto regular | No | CI backend/build/kind | Sí, propuesto; Sin secreto detectado por patrones |
| `backend/app/database.py` | M | Sí / texto regular | No | CI backend/build/kind | Sí, propuesto; Sin secreto detectado por patrones |
| `backend/app/main.py` | M | Sí / texto regular | No | CI backend/build/kind | Sí, propuesto; Sin secreto detectado por patrones |
| `backend/app/repository.py` | ? | Sí / texto regular | No | DB/repository; backend offline/real | Sí, propuesto; Sin secreto detectado por patrones |
| `backend/app/routers/game.py` | M | Sí / texto regular | No | CI backend/build/kind | Sí, propuesto; Sin secreto detectado por patrones |
| `backend/app/routers/stats.py` | M | Sí / texto regular | No | CI backend/build/kind | Sí, propuesto; Sin secreto detectado por patrones |
| `backend/docker/memory_server.py` | M | Sí / texto regular | No | CI backend/build/kind | Sí, propuesto; Sin secreto detectado por patrones |
| `backend/integration/run_pg04.py` | ? | Sí / texto regular | No | Bootstrap/suite/outage reutilizados por PG-07 | Sí, propuesto; Sin secreto detectado por patrones |
| `backend/integration/run_pg05_compose.py` | ? | Sí / texto regular | No | CI backend/build/kind | Sí, propuesto; Sin secreto detectado por patrones |
| `backend/integration/run_pg07_ci.py` | ? | Sí / texto regular | No | Workflow postgres-integration | Sí, propuesto; Sin secreto detectado por patrones |
| `backend/integration/test_postgres_integration.py` | ? | Sí / texto regular | No | Once casos reales PG-04/07 | Sí, propuesto; Sin secreto detectado por patrones |
| `backend/requirements.lock` | M | Sí / texto regular | No | CI backend/build/kind | Sí, propuesto; Sin secreto detectado por patrones |
| `backend/requirements.txt` | M | Sí / texto regular | No | CI backend/build/kind | Sí, propuesto; Sin secreto detectado por patrones |
| `backend/tests/test_backend.py` | M | Sí / texto regular | No | CI backend/build/kind | Sí, propuesto; Sin secreto detectado por patrones |
| `backend/tests/test_postgres_adapter.py` | ? | Sí / texto regular | No | Discovery offline; 55 casos | Sí, propuesto; Sin secreto detectado por patrones |
| `backend/tests/test_stabilization.py` | M | Sí / texto regular | No | CI backend/build/kind | Sí, propuesto; Sin secreto detectado por patrones |
| `backend/tests/test_transactions.py` | ? | Sí / texto regular | No | Discovery offline; atomicidad | Sí, propuesto; Sin secreto detectado por patrones |
| `compose.test.yaml` | M | Sí / texto regular | No | Compose/kind local | Sí, propuesto; Sin secreto detectado por patrones |
| `compose.yaml` | M | Sí / texto regular | No | Compose/kind local | Sí, propuesto; Sin secreto detectado por patrones |
| `docker/postgres/.env.example` | ? | Sí / texto regular | No | Compose/kind local | Sí, propuesto; Sin secreto detectado por patrones |
| `docker/postgres/.gitattributes` | ? | Sí / texto regular | No | Compose/kind local | Sí, propuesto; Sin secreto detectado por patrones |
| `docker/postgres/00-check-config.sh` | ? | Sí / texto regular | No | Compose/kind local | Sí, propuesto; Sin secreto detectado por patrones |
| `docker/postgres/20-demo-words.sql` | ? | Sí / texto regular | No | Seed CI/Compose/kind | Sí, propuesto; Sin secreto detectado por patrones |
| `docker/postgres/30-app-role.sh` | ? | Sí / texto regular | No | Compose/kind local | Sí, propuesto; Sin secreto detectado por patrones |
| `docker/postgres/demo-words.txt` | ? | Sí / texto regular | No | Compose/kind local | Sí, propuesto; Sin secreto detectado por patrones |
| `docs/analysis/fin-01a/FIN-01A-SCHEMA-ASSESSMENT.md` | ? | Sí / texto regular | No | Documentación/soporte; no ejecución CI directa | Sí, propuesto; Sin secreto detectado por patrones |
| `docs/analysis/fin-01b/FIN-01B-POSTGRES-VALIDATION.md` | ? | Sí / texto regular | No | Documentación/soporte; no ejecución CI directa | Sí, propuesto; Sin secreto detectado por patrones |
| `docs/analysis/fin-01b/FIN-01B-RECONSTRUCTION-REVIEW.md` | ? | Sí / texto regular | No | Documentación/soporte; no ejecución CI directa | Sí, propuesto; Sin secreto detectado por patrones |
| `docs/analysis/fin-01c/FIN-01C-ARCHITECTURE-IMPACT.md` | ? | Sí / texto regular | No | Documentación/soporte; no ejecución CI directa | Sí, propuesto; Sin secreto detectado por patrones |
| `docs/analysis/fin-01c/FIN-01C-DECISION-REPORT.md` | ? | Sí / texto regular | No | Documentación/soporte; no ejecución CI directa | Sí, propuesto; Sin secreto detectado por patrones |
| `docs/analysis/fin-01c/FIN-01C-DEPENDENCY-INVENTORY.md` | ? | Sí / texto regular | No | Documentación/soporte; no ejecución CI directa | Sí, propuesto; Sin secreto detectado por patrones |
| `docs/analysis/fin-01c/FIN-01C-MIGRATION-PLAN.md` | ? | Sí / texto regular | No | Documentación/soporte; no ejecución CI directa | Sí, propuesto; Sin secreto detectado por patrones |
| `docs/analysis/pg-01/PG-01-HTTP-CONTRACT.md` | ? | Sí / texto regular | No | Documentación/soporte; no ejecución CI directa | Sí, propuesto; Sin secreto detectado por patrones |
| `docs/analysis/pg-01/PG-01-PG02-ACCEPTANCE.md` | ? | Sí / texto regular | No | Documentación/soporte; no ejecución CI directa | Sí, propuesto; Sin secreto detectado por patrones |
| `docs/analysis/pg-01/PG-01-TRANSITION-DECISION.md` | ? | Sí / texto regular | No | Documentación/soporte; no ejecución CI directa | Sí, propuesto; Sin secreto detectado por patrones |
| `docs/analysis/pg-02/PG-02-IMPLEMENTATION-REPORT.md` | ? | Sí / texto regular | No | Documentación/soporte; no ejecución CI directa | Sí, propuesto; Sin secreto detectado por patrones |
| `docs/analysis/pg-02/PG-02-PG03-HANDOFF.md` | ? | Sí / texto regular | No | Documentación/soporte; no ejecución CI directa | Sí, propuesto; Sin secreto detectado por patrones |
| `docs/analysis/pg-02/PG-02-TEST-RESULTS.md` | ? | Sí / texto regular | No | Documentación/soporte; no ejecución CI directa | Sí, propuesto; Sin secreto detectado por patrones |
| `docs/analysis/pg-03/PG-03-IMPLEMENTATION-REPORT.md` | ? | Sí / texto regular | No | Documentación/soporte; no ejecución CI directa | Sí, propuesto; Sin secreto detectado por patrones |
| `docs/analysis/pg-03/PG-03-PG04-HANDOFF.md` | ? | Sí / texto regular | No | Documentación/soporte; no ejecución CI directa | Sí, propuesto; Sin secreto detectado por patrones |
| `docs/analysis/pg-03/PG-03-TEST-RESULTS.md` | ? | Sí / texto regular | No | Documentación/soporte; no ejecución CI directa | Sí, propuesto; Sin secreto detectado por patrones |
| `docs/analysis/pg-04/PG-04-INTEGRATION-REPORT.md` | ? | Sí / texto regular | No | Documentación/soporte; no ejecución CI directa | Sí, propuesto; Sin secreto detectado por patrones |
| `docs/analysis/pg-04/PG-04-PG05-HANDOFF.md` | ? | Sí / texto regular | No | Documentación/soporte; no ejecución CI directa | Sí, propuesto; Sin secreto detectado por patrones |
| `docs/analysis/pg-04/PG-04-TEST-RESULTS.md` | ? | Sí / texto regular | No | Documentación/soporte; no ejecución CI directa | Sí, propuesto; Sin secreto detectado por patrones |
| `docs/analysis/pg-05/PG-05-IMPLEMENTATION-REPORT.md` | ? | Sí / texto regular | No | Documentación/soporte; no ejecución CI directa | Sí, propuesto; Sin secreto detectado por patrones |
| `docs/analysis/pg-05/PG-05-PG06-HANDOFF.md` | ? | Sí / texto regular | No | Documentación/soporte; no ejecución CI directa | Sí, propuesto; Sin secreto detectado por patrones |
| `docs/analysis/pg-05/PG-05-TEST-RESULTS.md` | ? | Sí / texto regular | No | Documentación/soporte; no ejecución CI directa | Sí, propuesto; Sin secreto detectado por patrones |
| `docs/analysis/pg-06/PG-06-IMPLEMENTATION-REPORT.md` | ? | Sí / texto regular | No | Documentación/soporte; no ejecución CI directa | Sí, propuesto; Sin secreto detectado por patrones |
| `docs/analysis/pg-06/PG-06-PG07-HANDOFF.md` | ? | Sí / texto regular | No | Documentación/soporte; no ejecución CI directa | Sí, propuesto; Sin secreto detectado por patrones |
| `docs/analysis/pg-06/PG-06-TEST-RESULTS.md` | ? | Sí / texto regular | No | Documentación/soporte; no ejecución CI directa | Sí, propuesto; Sin secreto detectado por patrones |
| `docs/analysis/pg-07/PG-07-IMPLEMENTATION-REPORT.md` | ? | Sí / texto regular | No | Documentación/soporte; no ejecución CI directa | Sí, propuesto; Sin secreto detectado por patrones |
| `docs/analysis/pg-07/PG-07-NEXT-STEPS.md` | ? | Sí / texto regular | No | Documentación/soporte; no ejecución CI directa | Sí, propuesto; Sin secreto detectado por patrones |
| `docs/analysis/pg-07/PG-07-TEST-RESULTS.md` | ? | Sí / texto regular | No | Documentación/soporte; no ejecución CI directa | Sí, propuesto; Sin secreto detectado por patrones |
| `docs/analysis/pub-01/PUB-01-PUBLICATION-DECISION.md` | ? | Sí / texto regular | No | Documentación/soporte; no ejecución CI directa | Sí, propuesto; Sin secreto detectado por patrones |
| `docs/analysis/pub-01/PUB-01-PUBLICATION-MANIFEST.md` | ? | Sí / texto regular | No | Documentación/soporte; no ejecución CI directa | Sí, propuesto; Sin secreto detectado por patrones |
| `docs/analysis/pub-01/PUB-01-REPOSITORY-AUDIT.md` | ? | Sí / texto regular | No | Documentación/soporte; no ejecución CI directa | Sí, propuesto; Sin secreto detectado por patrones |
| `docs/analysis/pub-02/PUB-02-CORRECTION-REPORT.md` | ? | Sí / texto regular | No | Documentación/soporte; no ejecución CI directa | Sí, propuesto; Sin secreto detectado por patrones |
| `docs/analysis/pub-02/PUB-02-PUBLICATION-DECISION.md` | ? | Sí / texto regular | No | Documentación/soporte; no ejecución CI directa | Sí, propuesto; Sin secreto detectado por patrones |
| `docs/analysis/pub-02/PUB-02-PUBLICATION-MANIFEST.md` | ? | Sí / texto regular | No | Documentación/soporte; no ejecución CI directa | Sí, propuesto; Sin secreto detectado por patrones |
| `docs/analysis/tfg-plan-001/TFG-COMPLETION-PLAN.md` | ? | Sí / texto regular | No | Documentación/soporte; no ejecución CI directa | Sí, propuesto; Sin secreto detectado por patrones |
| `docs/analysis/tfg-plan-001/TFG-COMPLIANCE-MATRIX.md` | ? | Sí / texto regular | No | Documentación/soporte; no ejecución CI directa | Sí, propuesto; Sin secreto detectado por patrones |
| `docs/analysis/tfg-plan-001/TFG-DEFENSE-EVIDENCE.md` | ? | Sí / texto regular | No | Documentación/soporte; no ejecución CI directa | Sí, propuesto; Sin secreto detectado por patrones |
| `docs/analysis/tfg-plan-001/TFG-GAP-ANALYSIS.md` | ? | Sí / texto regular | No | Documentación/soporte; no ejecución CI directa | Sí, propuesto; Sin secreto detectado por patrones |
| `k8s/postgres/backend-patch.yaml` | ? | Sí / texto regular | No | Compose/kind local | Sí, propuesto; Sin secreto detectado por patrones |
| `k8s/postgres/kustomization.yaml` | ? | Sí / texto regular | No | Compose/kind local | Sí, propuesto; Sin secreto detectado por patrones |
| `k8s/postgres/postgres.yaml` | ? | Sí / texto regular | No | Compose/kind local | Sí, propuesto; Sin secreto detectado por patrones |
| `k8s/postgres/readiness.py` | ? | Sí / texto regular | No | Compose/kind local | Sí, propuesto; Sin secreto detectado por patrones |
| `k8s/postgres/run_pg06.py` | ? | Sí / texto regular | No | Compose/kind local | Sí, propuesto; Sin secreto detectado por patrones |
| `supabase/README.md` | ? | Sí / texto regular | No | Documentación/soporte; no ejecución CI directa | Sí, propuesto; Sin secreto detectado por patrones |
| `supabase/migrations/20261108000100_initial_wordle.sql` | ? | Sí / texto regular | No | Baseline CI/Compose/kind | Sí, propuesto; Sin secreto detectado por patrones |
| `supabase/prototype/allow_all.sql` | ? | Sí / texto regular | No | Documentación/soporte; no ejecución CI directa | Sí, propuesto; Histórico Supabase; nunca ejecutar como bootstrap vigente |
| `supabase/tests/backend_operations.sql` | ? | Sí / texto regular | No | Documentación/soporte; no ejecución CI directa | Sí, propuesto; Sin secreto detectado por patrones |
| `supabase/tests/local_backend_smoke.py` | ? | Sí / texto regular | No | Documentación/soporte; no ejecución CI directa | Sí, propuesto; Histórico Supabase; nunca ejecutar como bootstrap vigente |
| `supabase/tests/prototype_access.sql` | ? | Sí / texto regular | No | Documentación/soporte; no ejecución CI directa | Sí, propuesto; Histórico Supabase; nunca ejecutar como bootstrap vigente |
| `supabase/tests/schema_contracts.sql` | ? | Sí / texto regular | No | Catálogo CI/PG-04/06 | Sí, propuesto; Sin secreto detectado por patrones |
| `supabase/tests/test_dictionary_preparation.py` | ? | Sí / texto regular | No | Documentación/soporte; no ejecución CI directa | Sí, propuesto; Sin secreto detectado por patrones |
| `supabase/tools/prepare_dictionary.py` | ? | Sí / texto regular | No | Documentación/soporte; no ejecución CI directa | Sí, propuesto; Sin secreto detectado por patrones |

No faltan rutas del manifiesto y no había cambios adicionales fuera de sus 81 entradas antes de crear estos informes. Los nueve archivos CI señalados en PUB-01/02 existen y siguen sin seguimiento; no se han añadido solo para completar un recuento.

## Archivos adicionales creados por PUB-03

- docs/analysis/pub-03/PUB-03-GIT-STATE.md.
- docs/analysis/pub-03/PUB-03-CONFLICT-ASSESSMENT.md.
- docs/analysis/pub-03/PUB-03-PUBLICATION-STRATEGY.md.

Son entregables autorizados de esta auditoría, **no se agregan automáticamente al manifiesto PUB-02**. Aprobarlos expresamente elevaría la propuesta a84; mantener81 deja estos informes locales sin seguimiento. Ninguna variante se ha preparado en el índice. Después de los informes:16 modificados/68 nuevos, incluidos estos tres.

## Seguridad y comprobación de cierre

Scans acotados sobre81 candidatos: sin patrones de token/claves privadas/JWT/URI con credenciales reales detectados. Seis indicadores conocidos, solo rutas/líneas: workflow75/98 (valor público exclusivo CI), run_pg05_compose.py89 (generación aleatoria), compose.yaml8 (variable), 30-app-role.sh8 (variable psql) y postgres.yaml95 (probe con variables). No se muestran valores. No es auditoría de todos los blobs históricos/remotos ni certifica archivos privados que no se leyeron.

La validación final comprueba hashes de los118 archivos anteriores, rama/HEAD y representación del índice, y git diff --check. Los informes no añaden credenciales ni configuraciones de despliegue. No se repiten las55/11 pruebas: PUB-03 es revisión Git. FIN-01 sigue pendiente.
