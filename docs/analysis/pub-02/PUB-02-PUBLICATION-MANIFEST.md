# PUB-02 — Manifiesto exacto propuesto

Fecha: 09/11/2026. Propuesta para revisión; **ningún archivo añadido al índice**. Sustituye la selección pendiente de PUB-01 sin alterar aquel registro. No autoriza commit/push, ejecución de históricos ni despliegue.

## Incluir en el futuro commit coherente

81 rutas: 16 archivos ya versionados modificados y 65 nuevos sin seguimiento, incluidos los tres informes PUB-02. Los demás archivos ya en HEAD se conservan sin cambio; no necesitan añadirse otra vez. Las rutas son relativas al repositorio.

El material Supabase/FIN/plan aporta trazabilidad y se propone explícitamente como histórico con notas de alcance; no entra en los comandos de inicialización. No se han trasladado, eliminado ni editado sus scripts. Los siete informes operativos señalados por PUB-01 ya están saneados. Toda selección futura debe revisarse contra esta lista, no mediante un add indiscriminado.

| Ruta exacta | Estado real/propuesto | Razón de inclusión |
|---|---|---|
| `.github/workflows/ci.yml` | Modificado, ya versionado | Operativo: código, prueba, configuración pública o fixture necesaria del conjunto |
| `.gitignore` | Modificado, ya versionado | Operativo: código, prueba, configuración pública o fixture necesaria del conjunto |
| `README.md` | Modificado, ya versionado | Operativo: código, prueba, configuración pública o fixture necesaria del conjunto |
| `backend/.env.example` | Modificado, ya versionado | Operativo: código, prueba, configuración pública o fixture necesaria del conjunto |
| `backend/SECURITY-NOTES.md` | Modificado, ya versionado | Operativo: código, prueba, configuración pública o fixture necesaria del conjunto |
| `backend/app/database.py` | Modificado, ya versionado | Operativo: código, prueba, configuración pública o fixture necesaria del conjunto |
| `backend/app/main.py` | Modificado, ya versionado | Operativo: código, prueba, configuración pública o fixture necesaria del conjunto |
| `backend/app/repository.py` | Nuevo, sin seguimiento | Operativo: código, prueba, configuración pública o fixture necesaria del conjunto |
| `backend/app/routers/game.py` | Modificado, ya versionado | Operativo: código, prueba, configuración pública o fixture necesaria del conjunto |
| `backend/app/routers/stats.py` | Modificado, ya versionado | Operativo: código, prueba, configuración pública o fixture necesaria del conjunto |
| `backend/docker/memory_server.py` | Modificado, ya versionado | Operativo: código, prueba, configuración pública o fixture necesaria del conjunto |
| `backend/integration/run_pg04.py` | Nuevo, sin seguimiento | Operativo: código, prueba, configuración pública o fixture necesaria del conjunto |
| `backend/integration/run_pg05_compose.py` | Nuevo, sin seguimiento | Operativo: código, prueba, configuración pública o fixture necesaria del conjunto |
| `backend/integration/run_pg07_ci.py` | Nuevo, sin seguimiento | Operativo: código, prueba, configuración pública o fixture necesaria del conjunto |
| `backend/integration/test_postgres_integration.py` | Nuevo, sin seguimiento | Operativo: código, prueba, configuración pública o fixture necesaria del conjunto |
| `backend/requirements.lock` | Modificado, ya versionado | Operativo: código, prueba, configuración pública o fixture necesaria del conjunto |
| `backend/requirements.txt` | Modificado, ya versionado | Operativo: código, prueba, configuración pública o fixture necesaria del conjunto |
| `backend/tests/test_backend.py` | Modificado, ya versionado | Operativo: código, prueba, configuración pública o fixture necesaria del conjunto |
| `backend/tests/test_postgres_adapter.py` | Nuevo, sin seguimiento | Operativo: código, prueba, configuración pública o fixture necesaria del conjunto |
| `backend/tests/test_stabilization.py` | Modificado, ya versionado | Operativo: código, prueba, configuración pública o fixture necesaria del conjunto |
| `backend/tests/test_transactions.py` | Nuevo, sin seguimiento | Operativo: código, prueba, configuración pública o fixture necesaria del conjunto |
| `compose.test.yaml` | Modificado, ya versionado | Operativo: código, prueba, configuración pública o fixture necesaria del conjunto |
| `compose.yaml` | Modificado, ya versionado | Operativo: código, prueba, configuración pública o fixture necesaria del conjunto |
| `docker/postgres/.env.example` | Nuevo, sin seguimiento | Operativo: código, prueba, configuración pública o fixture necesaria del conjunto |
| `docker/postgres/.gitattributes` | Nuevo, sin seguimiento | Operativo: código, prueba, configuración pública o fixture necesaria del conjunto |
| `docker/postgres/00-check-config.sh` | Nuevo, sin seguimiento | Operativo: código, prueba, configuración pública o fixture necesaria del conjunto |
| `docker/postgres/20-demo-words.sql` | Nuevo, sin seguimiento | Operativo: código, prueba, configuración pública o fixture necesaria del conjunto |
| `docker/postgres/30-app-role.sh` | Nuevo, sin seguimiento | Operativo: código, prueba, configuración pública o fixture necesaria del conjunto |
| `docker/postgres/demo-words.txt` | Nuevo, sin seguimiento | Operativo: código, prueba, configuración pública o fixture necesaria del conjunto |
| `docs/analysis/fin-01a/FIN-01A-SCHEMA-ASSESSMENT.md` | Nuevo, sin seguimiento | HISTÓRICO: trazabilidad de esquema/decisión/plan; no instrucciones operativas actuales |
| `docs/analysis/fin-01b/FIN-01B-POSTGRES-VALIDATION.md` | Nuevo, sin seguimiento | HISTÓRICO: trazabilidad de esquema/decisión/plan; no instrucciones operativas actuales |
| `docs/analysis/fin-01b/FIN-01B-RECONSTRUCTION-REVIEW.md` | Nuevo, sin seguimiento | HISTÓRICO: trazabilidad de esquema/decisión/plan; no instrucciones operativas actuales |
| `docs/analysis/fin-01c/FIN-01C-ARCHITECTURE-IMPACT.md` | Nuevo, sin seguimiento | HISTÓRICO: trazabilidad de esquema/decisión/plan; no instrucciones operativas actuales |
| `docs/analysis/fin-01c/FIN-01C-DECISION-REPORT.md` | Nuevo, sin seguimiento | HISTÓRICO: trazabilidad de esquema/decisión/plan; no instrucciones operativas actuales |
| `docs/analysis/fin-01c/FIN-01C-DEPENDENCY-INVENTORY.md` | Nuevo, sin seguimiento | HISTÓRICO: trazabilidad de esquema/decisión/plan; no instrucciones operativas actuales |
| `docs/analysis/fin-01c/FIN-01C-MIGRATION-PLAN.md` | Nuevo, sin seguimiento | HISTÓRICO: trazabilidad de esquema/decisión/plan; no instrucciones operativas actuales |
| `docs/analysis/pg-01/PG-01-HTTP-CONTRACT.md` | Nuevo, sin seguimiento | Documentación/evidencia por incremento; revisada, sin secretos; distinguir fecha histórica |
| `docs/analysis/pg-01/PG-01-PG02-ACCEPTANCE.md` | Nuevo, sin seguimiento | Documentación/evidencia por incremento; revisada, sin secretos; distinguir fecha histórica |
| `docs/analysis/pg-01/PG-01-TRANSITION-DECISION.md` | Nuevo, sin seguimiento | Documentación/evidencia por incremento; revisada, sin secretos; distinguir fecha histórica |
| `docs/analysis/pg-02/PG-02-IMPLEMENTATION-REPORT.md` | Nuevo, sin seguimiento | Documentación/evidencia por incremento; revisada, sin secretos; distinguir fecha histórica |
| `docs/analysis/pg-02/PG-02-PG03-HANDOFF.md` | Nuevo, sin seguimiento | Documentación/evidencia por incremento; revisada, sin secretos; distinguir fecha histórica |
| `docs/analysis/pg-02/PG-02-TEST-RESULTS.md` | Nuevo, sin seguimiento | Documentación/evidencia por incremento; revisada, sin secretos; distinguir fecha histórica |
| `docs/analysis/pg-03/PG-03-IMPLEMENTATION-REPORT.md` | Nuevo, sin seguimiento | Documentación/evidencia por incremento; revisada, sin secretos; distinguir fecha histórica |
| `docs/analysis/pg-03/PG-03-PG04-HANDOFF.md` | Nuevo, sin seguimiento | Documentación/evidencia por incremento; revisada, sin secretos; distinguir fecha histórica |
| `docs/analysis/pg-03/PG-03-TEST-RESULTS.md` | Nuevo, sin seguimiento | Documentación/evidencia por incremento; revisada, sin secretos; distinguir fecha histórica |
| `docs/analysis/pg-04/PG-04-INTEGRATION-REPORT.md` | Nuevo, sin seguimiento | Documentación/evidencia por incremento; revisada, sin secretos; distinguir fecha histórica |
| `docs/analysis/pg-04/PG-04-PG05-HANDOFF.md` | Nuevo, sin seguimiento | Documentación/evidencia por incremento; revisada, sin secretos; distinguir fecha histórica |
| `docs/analysis/pg-04/PG-04-TEST-RESULTS.md` | Nuevo, sin seguimiento | Documentación/evidencia por incremento; revisada, sin secretos; distinguir fecha histórica |
| `docs/analysis/pg-05/PG-05-IMPLEMENTATION-REPORT.md` | Nuevo, sin seguimiento | Documentación/evidencia por incremento; revisada, sin secretos; distinguir fecha histórica |
| `docs/analysis/pg-05/PG-05-PG06-HANDOFF.md` | Nuevo, sin seguimiento | Documentación/evidencia por incremento; revisada, sin secretos; distinguir fecha histórica |
| `docs/analysis/pg-05/PG-05-TEST-RESULTS.md` | Nuevo, sin seguimiento | Documentación/evidencia por incremento; revisada, sin secretos; distinguir fecha histórica |
| `docs/analysis/pg-06/PG-06-IMPLEMENTATION-REPORT.md` | Nuevo, sin seguimiento | Documentación/evidencia por incremento; revisada, sin secretos; distinguir fecha histórica |
| `docs/analysis/pg-06/PG-06-PG07-HANDOFF.md` | Nuevo, sin seguimiento | Documentación/evidencia por incremento; revisada, sin secretos; distinguir fecha histórica |
| `docs/analysis/pg-06/PG-06-TEST-RESULTS.md` | Nuevo, sin seguimiento | Documentación/evidencia por incremento; revisada, sin secretos; distinguir fecha histórica |
| `docs/analysis/pg-07/PG-07-IMPLEMENTATION-REPORT.md` | Nuevo, sin seguimiento | Documentación/evidencia por incremento; revisada, sin secretos; distinguir fecha histórica |
| `docs/analysis/pg-07/PG-07-NEXT-STEPS.md` | Nuevo, sin seguimiento | Documentación/evidencia por incremento; revisada, sin secretos; distinguir fecha histórica |
| `docs/analysis/pg-07/PG-07-TEST-RESULTS.md` | Nuevo, sin seguimiento | Documentación/evidencia por incremento; revisada, sin secretos; distinguir fecha histórica |
| `docs/analysis/pub-01/PUB-01-PUBLICATION-DECISION.md` | Nuevo, sin seguimiento | HISTÓRICO: auditoría previa, superada por PUB-02; conservar snapshot |
| `docs/analysis/pub-01/PUB-01-PUBLICATION-MANIFEST.md` | Nuevo, sin seguimiento | HISTÓRICO: auditoría previa, superada por PUB-02; conservar snapshot |
| `docs/analysis/pub-01/PUB-01-REPOSITORY-AUDIT.md` | Nuevo, sin seguimiento | HISTÓRICO: auditoría previa, superada por PUB-02; conservar snapshot |
| `docs/analysis/pub-02/PUB-02-CORRECTION-REPORT.md` | Nuevo, sin seguimiento | Documentación/evidencia por incremento; revisada, sin secretos; distinguir fecha histórica |
| `docs/analysis/pub-02/PUB-02-PUBLICATION-DECISION.md` | Nuevo, sin seguimiento | Documentación/evidencia por incremento; revisada, sin secretos; distinguir fecha histórica |
| `docs/analysis/pub-02/PUB-02-PUBLICATION-MANIFEST.md` | Nuevo, sin seguimiento | Documentación/evidencia por incremento; revisada, sin secretos; distinguir fecha histórica |
| `docs/analysis/tfg-plan-001/TFG-COMPLETION-PLAN.md` | Nuevo, sin seguimiento | HISTÓRICO: trazabilidad de esquema/decisión/plan; no instrucciones operativas actuales |
| `docs/analysis/tfg-plan-001/TFG-COMPLIANCE-MATRIX.md` | Nuevo, sin seguimiento | HISTÓRICO: trazabilidad de esquema/decisión/plan; no instrucciones operativas actuales |
| `docs/analysis/tfg-plan-001/TFG-DEFENSE-EVIDENCE.md` | Nuevo, sin seguimiento | HISTÓRICO: trazabilidad de esquema/decisión/plan; no instrucciones operativas actuales |
| `docs/analysis/tfg-plan-001/TFG-GAP-ANALYSIS.md` | Nuevo, sin seguimiento | HISTÓRICO: trazabilidad de esquema/decisión/plan; no instrucciones operativas actuales |
| `k8s/postgres/backend-patch.yaml` | Nuevo, sin seguimiento | Operativo: código, prueba, configuración pública o fixture necesaria del conjunto |
| `k8s/postgres/kustomization.yaml` | Nuevo, sin seguimiento | Operativo: código, prueba, configuración pública o fixture necesaria del conjunto |
| `k8s/postgres/postgres.yaml` | Nuevo, sin seguimiento | Operativo: código, prueba, configuración pública o fixture necesaria del conjunto |
| `k8s/postgres/readiness.py` | Nuevo, sin seguimiento | Operativo: código, prueba, configuración pública o fixture necesaria del conjunto |
| `k8s/postgres/run_pg06.py` | Nuevo, sin seguimiento | Operativo: código, prueba, configuración pública o fixture necesaria del conjunto |
| `supabase/README.md` | Nuevo, sin seguimiento | Nota vigente de alcance + sección histórica FIN-01B preservada |
| `supabase/migrations/20261108000100_initial_wordle.sql` | Nuevo, sin seguimiento | Operativo: código, prueba, configuración pública o fixture necesaria del conjunto |
| `supabase/prototype/allow_all.sql` | Nuevo, sin seguimiento | HISTÓRICO: incluir con nota supabase/README; nunca init/CI vigente |
| `supabase/tests/backend_operations.sql` | Nuevo, sin seguimiento | Operativo: código, prueba, configuración pública o fixture necesaria del conjunto |
| `supabase/tests/local_backend_smoke.py` | Nuevo, sin seguimiento | HISTÓRICO: incluir con nota supabase/README; nunca init/CI vigente |
| `supabase/tests/prototype_access.sql` | Nuevo, sin seguimiento | HISTÓRICO: incluir con nota supabase/README; nunca init/CI vigente |
| `supabase/tests/schema_contracts.sql` | Nuevo, sin seguimiento | Operativo: código, prueba, configuración pública o fixture necesaria del conjunto |
| `supabase/tests/test_dictionary_preparation.py` | Nuevo, sin seguimiento | Operativo: código, prueba, configuración pública o fixture necesaria del conjunto |
| `supabase/tools/prepare_dictionary.py` | Nuevo, sin seguimiento | Operativo: código, prueba, configuración pública o fixture necesaria del conjunto |

## Mantener fuera del commit

| Ruta/recurso | Tratamiento |
|---|---|
| backend/.env | Privado, ignorado y no abierto; jamás copiar sus valores a las plantillas |
| .venv/ y .venv/wordle-kind.kubeconfig | Entorno local y credencial de clúster; no abrir/publicar |
| backend/app/__pycache__/, backend/app/routers/__pycache__/, backend/tests/__pycache__/ y demás __pycache__/ | Cachés generadas; ignorar |
| frontend/node_modules/ | Dependencias instaladas, reproducir con npm ci |
| frontend/dist/ | Assets generados, reproducir con build |
| infra/terraform/.terraform/ | Caché/providers, no fuente |
| .env.* reales, secretos, claves/certificados privados, *.kubeconfig | Conservar privados, sin forzar incorporación |
| *.tfstate*, *.tfplan, variables privadas y backend.hcl local | Conservar fuera, reglas Terraform; no se certifica contenido ni existencia de todos los patrones |
| k8s/postgres/.local/ | Estado/credenciales privados si se generan allí, excluidos |
| %LOCALAPPDATA%/WordlePG05/<proyecto>/compose.env, state.json, pg05-demo.dump | Recursos privados externos conservados; no abiertos ni copiados |
| %LOCALAPPDATA%/WordlePG06/<cluster>/kind.kubeconfig y state.json | Estado privado del clúster retenido, no publicar |
| <evidencias-privadas>/pg05-ui-win.png, pg05-ui-loss.png, pg06-ui-win.png | Capturas externas; marcadores documentales, no archivos inexistentes que se deban generar o incorporar |
| Volumen PG-05, clúster/PVC PG-06, imágenes Docker locales | Recursos fuera de Git, no operados por esta tarea; no eliminarlos para publicar |

Las dos plantillas `.env.example` y `.terraform.lock.hcl` sí pertenecen a la fuente; no confundirlas con archivos privados. No hay exclusiones nuevas que escondan código necesario. Los tres scripts históricos Supabase se proponen en la tabla de inclusión únicamente como historia claramente rotulada, no como configuración activa ni requisito de PostgreSQL.

## Dependencias y completitud

Las nueve dependencias exactas PUB-01 se verificaron una a una en el informe de correcciones: necesarias, presentes, no ignoradas, sin rutas privadas/credenciales reales detectadas y todavía **sin seguimiento**. Figuran todas en esta tabla. Compose/kind también requieren scripts/fixture/baseline y todo el overlay, incluidos aquí; k8s/local y Dockerfiles están ya versionados e intactos.

No se detecta archivo necesario ausente en disco. Un checkout de HEAD todavía carece del conjunto PG: el manifiesto preparado no equivale a haberlo versionado. Workflow/app/lock/tests/SQL deben acompañarse en el futuro commit. El README documenta intervención manual legítima: instalar herramientas, generar credenciales nuevas o destino LOCALAPPDATA explícito y usar el state devuelto por cada ejecución, sin adoptar los recursos del autor.

## Antes de preparar índice/commit/push, en tarea autorizada

- Actualizar referencias de origin/main y acordar rama de publicación, preservando los cambios acumulados. La comparación local 0/1 no demuestra actualidad remota.
- Contrastar los archivos seleccionados con estas rutas; revisar diff staged, scan acotado de secretos y whitespace sobre el índice real una vez se autorice crearlo. Actualmente vacío.
- Mantener GHCR if:false; no introducir permisos/tokens ni convertir scripts históricos en bootstrap.
- Tras publicación autorizada, obtener evidencia de Actions real (55 offline/once reales/cero omitidas, builds y controles existentes). No confundir comprobaciones locales con run GitHub.

FIN-01 sigue pendiente. No se prepara Git ni se publica desde PUB-02.
