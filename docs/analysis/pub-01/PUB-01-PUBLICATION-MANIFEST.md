# PUB-01 — Manifiesto propuesto de publicación

Fecha: 09/11/2026. Inventario de solo lectura; **no es un git add ni autorización de publicación**. Rutas relativas al repositorio. M=modificado respecto a HEAD; ?=nuevo sin seguimiento; =ya versionado sin cambios.

## Inventario explícito de candidatos y baseline

Se incluyen los 112 archivos no ignorados encontrados al iniciar: 53 ya versionados (13 modificados/40 sin cambios) y 59 nuevos. VERSIONAR en archivos = significa mantener su contenido existente, no crear un cambio artificial. REVISAR en un archivo ya versionado no lo retira de HEAD: requiere resolver su contenido/propósito antes de publicar; no se ha editado nada.

| Ruta | Git | Recomendación | Procedencia y justificación |
|---|---|---|---|
| `.github/workflows/.gitkeep` | = | VERSIONAR | Trabajo anterior ya en HEAD; conservar, no requiere añadir de nuevo |
| `.github/workflows/ci.yml` | M | VERSIONAR | PG-07; workflow previo DevOps conservado |
| `.gitignore` | M | VERSIONAR | PG-06; exclusiones locales |
| `README.md` | = | REVISAR | Ya versionado; instrucciones/plantilla obsoletas Supabase/get_supabase frente a PG directo |
| `backend/.dockerignore` | = | VERSIONAR | Trabajo anterior ya en HEAD; conservar, no requiere añadir de nuevo |
| `backend/.env.example` | = | REVISAR | Ya versionado; instrucciones/plantilla obsoletas Supabase/get_supabase frente a PG directo |
| `backend/Dockerfile` | = | VERSIONAR | Trabajo anterior ya en HEAD; conservar, no requiere añadir de nuevo |
| `backend/SECURITY-NOTES.md` | = | REVISAR | Ya versionado; instrucciones/plantilla obsoletas Supabase/get_supabase frente a PG directo |
| `backend/app/database.py` | M | VERSIONAR | PG-02; driver/pool async |
| `backend/app/main.py` | M | VERSIONAR | PG-02; lifespan |
| `backend/app/repository.py` | ? | VERSIONAR | PG-02/03; SQL parametrizado, protocolo transaccional y locks |
| `backend/app/routers/game.py` | M | VERSIONAR | PG-02/03; repositorio y transacción/locks |
| `backend/app/routers/stats.py` | M | VERSIONAR | PG-02; repositorio async |
| `backend/docker/memory_server.py` | M | VERSIONAR | PG-02/03; preservación memoria |
| `backend/integration/run_pg04.py` | ? | VERSIONAR | PG-04; bootstrap/suite/outage reutilizados por CI |
| `backend/integration/run_pg05_compose.py` | ? | VERSIONAR | PG-05; ejecución local persistente, Windows/LOCALAPPDATA |
| `backend/integration/run_pg07_ci.py` | ? | VERSIONAR | PG-07; adaptador del servicio CI real |
| `backend/integration/test_postgres_integration.py` | ? | VERSIONAR | PG-04; once tests reales |
| `backend/requirements.lock` | M | VERSIONAR | PG-02; dependencias Linux con hashes |
| `backend/requirements.txt` | M | VERSIONAR | PG-02; psycopg/pool |
| `backend/tests/test_backend.py` | M | VERSIONAR | PG-02/03; adaptación de dobles |
| `backend/tests/test_postgres_adapter.py` | ? | VERSIONAR | PG-02; contratos/adaptador |
| `backend/tests/test_stabilization.py` | M | VERSIONAR | PG-02; firma async |
| `backend/tests/test_transactions.py` | ? | VERSIONAR | PG-03; atomicidad/concurrencia |
| `compose.test.yaml` | M | VERSIONAR | PG-05; preservar perfil memoria |
| `compose.yaml` | M | VERSIONAR | PG-05; PostgreSQL persistente |
| `docker/postgres/.env.example` | ? | VERSIONAR | PG-05; inicialización única/fixture/plantilla vacía/LF según archivo |
| `docker/postgres/.gitattributes` | ? | VERSIONAR | PG-05; inicialización única/fixture/plantilla vacía/LF según archivo |
| `docker/postgres/00-check-config.sh` | ? | VERSIONAR | PG-05; inicialización única/fixture/plantilla vacía/LF según archivo |
| `docker/postgres/20-demo-words.sql` | ? | VERSIONAR | PG-05; inicialización única/fixture/plantilla vacía/LF según archivo |
| `docker/postgres/30-app-role.sh` | ? | VERSIONAR | PG-05; inicialización única/fixture/plantilla vacía/LF según archivo |
| `docker/postgres/demo-words.txt` | ? | VERSIONAR | PG-05; inicialización única/fixture/plantilla vacía/LF según archivo |
| `docs/analysis/fin-01a/FIN-01A-SCHEMA-ASSESSMENT.md` | ? | REVISAR | Anterior a PG-01: histórico/esquema/plan; decidir inclusión y marcar contexto sin actualizar backlog |
| `docs/analysis/fin-01b/FIN-01B-POSTGRES-VALIDATION.md` | ? | REVISAR | Anterior a PG-01: histórico/esquema/plan; decidir inclusión y marcar contexto sin actualizar backlog |
| `docs/analysis/fin-01b/FIN-01B-RECONSTRUCTION-REVIEW.md` | ? | REVISAR | Anterior a PG-01: histórico/esquema/plan; decidir inclusión y marcar contexto sin actualizar backlog |
| `docs/analysis/fin-01c/FIN-01C-ARCHITECTURE-IMPACT.md` | ? | REVISAR | Anterior a PG-01: histórico/esquema/plan; decidir inclusión y marcar contexto sin actualizar backlog |
| `docs/analysis/fin-01c/FIN-01C-DECISION-REPORT.md` | ? | REVISAR | Anterior a PG-01: histórico/esquema/plan; decidir inclusión y marcar contexto sin actualizar backlog |
| `docs/analysis/fin-01c/FIN-01C-DEPENDENCY-INVENTORY.md` | ? | REVISAR | Anterior a PG-01: histórico/esquema/plan; decidir inclusión y marcar contexto sin actualizar backlog |
| `docs/analysis/fin-01c/FIN-01C-MIGRATION-PLAN.md` | ? | REVISAR | Anterior a PG-01: histórico/esquema/plan; decidir inclusión y marcar contexto sin actualizar backlog |
| `docs/analysis/pg-01/PG-01-HTTP-CONTRACT.md` | ? | VERSIONAR | PG-01/07 según directorio; contrato/decisión/evidencia con alcance histórico explícito |
| `docs/analysis/pg-01/PG-01-PG02-ACCEPTANCE.md` | ? | VERSIONAR | PG-01/07 según directorio; contrato/decisión/evidencia con alcance histórico explícito |
| `docs/analysis/pg-01/PG-01-TRANSITION-DECISION.md` | ? | VERSIONAR | PG-01/07 según directorio; contrato/decisión/evidencia con alcance histórico explícito |
| `docs/analysis/pg-02/PG-02-IMPLEMENTATION-REPORT.md` | ? | VERSIONAR | PG-01/07 según directorio; contrato/decisión/evidencia con alcance histórico explícito |
| `docs/analysis/pg-02/PG-02-PG03-HANDOFF.md` | ? | VERSIONAR | PG-01/07 según directorio; contrato/decisión/evidencia con alcance histórico explícito |
| `docs/analysis/pg-02/PG-02-TEST-RESULTS.md` | ? | VERSIONAR | PG-01/07 según directorio; contrato/decisión/evidencia con alcance histórico explícito |
| `docs/analysis/pg-03/PG-03-IMPLEMENTATION-REPORT.md` | ? | VERSIONAR | PG-01/07 según directorio; contrato/decisión/evidencia con alcance histórico explícito |
| `docs/analysis/pg-03/PG-03-PG04-HANDOFF.md` | ? | VERSIONAR | PG-01/07 según directorio; contrato/decisión/evidencia con alcance histórico explícito |
| `docs/analysis/pg-03/PG-03-TEST-RESULTS.md` | ? | VERSIONAR | PG-01/07 según directorio; contrato/decisión/evidencia con alcance histórico explícito |
| `docs/analysis/pg-04/PG-04-INTEGRATION-REPORT.md` | ? | VERSIONAR | PG-01/07 según directorio; contrato/decisión/evidencia con alcance histórico explícito |
| `docs/analysis/pg-04/PG-04-PG05-HANDOFF.md` | ? | VERSIONAR | PG-01/07 según directorio; contrato/decisión/evidencia con alcance histórico explícito |
| `docs/analysis/pg-04/PG-04-TEST-RESULTS.md` | ? | VERSIONAR | PG-01/07 según directorio; contrato/decisión/evidencia con alcance histórico explícito |
| `docs/analysis/pg-05/PG-05-IMPLEMENTATION-REPORT.md` | ? | REVISAR | PG-05/06/07 necesario como evidencia/manual; sanear rutas personales y referencias de máquina antes de incluir |
| `docs/analysis/pg-05/PG-05-PG06-HANDOFF.md` | ? | REVISAR | PG-05/06/07 necesario como evidencia/manual; sanear rutas personales y referencias de máquina antes de incluir |
| `docs/analysis/pg-05/PG-05-TEST-RESULTS.md` | ? | REVISAR | PG-05/06/07 necesario como evidencia/manual; sanear rutas personales y referencias de máquina antes de incluir |
| `docs/analysis/pg-06/PG-06-IMPLEMENTATION-REPORT.md` | ? | REVISAR | PG-05/06/07 necesario como evidencia/manual; sanear rutas personales y referencias de máquina antes de incluir |
| `docs/analysis/pg-06/PG-06-PG07-HANDOFF.md` | ? | REVISAR | PG-05/06/07 necesario como evidencia/manual; sanear rutas personales y referencias de máquina antes de incluir |
| `docs/analysis/pg-06/PG-06-TEST-RESULTS.md` | ? | REVISAR | PG-05/06/07 necesario como evidencia/manual; sanear rutas personales y referencias de máquina antes de incluir |
| `docs/analysis/pg-07/PG-07-IMPLEMENTATION-REPORT.md` | ? | VERSIONAR | PG-01/07 según directorio; contrato/decisión/evidencia con alcance histórico explícito |
| `docs/analysis/pg-07/PG-07-NEXT-STEPS.md` | ? | REVISAR | PG-05/06/07 necesario como evidencia/manual; sanear rutas personales y referencias de máquina antes de incluir |
| `docs/analysis/pg-07/PG-07-TEST-RESULTS.md` | ? | VERSIONAR | PG-01/07 según directorio; contrato/decisión/evidencia con alcance histórico explícito |
| `docs/analysis/tfg-plan-001/TFG-COMPLETION-PLAN.md` | ? | REVISAR | Anterior a PG-01: histórico/esquema/plan; decidir inclusión y marcar contexto sin actualizar backlog |
| `docs/analysis/tfg-plan-001/TFG-COMPLIANCE-MATRIX.md` | ? | REVISAR | Anterior a PG-01: histórico/esquema/plan; decidir inclusión y marcar contexto sin actualizar backlog |
| `docs/analysis/tfg-plan-001/TFG-DEFENSE-EVIDENCE.md` | ? | REVISAR | Anterior a PG-01: histórico/esquema/plan; decidir inclusión y marcar contexto sin actualizar backlog |
| `docs/analysis/tfg-plan-001/TFG-GAP-ANALYSIS.md` | ? | REVISAR | Anterior a PG-01: histórico/esquema/plan; decidir inclusión y marcar contexto sin actualizar backlog |
| `frontend/.dockerignore` | = | VERSIONAR | Trabajo anterior ya en HEAD; conservar, no requiere añadir de nuevo |
| `frontend/.env.example` | = | VERSIONAR | Trabajo anterior ya en HEAD; conservar, no requiere añadir de nuevo |
| `frontend/Dockerfile` | = | VERSIONAR | Trabajo anterior ya en HEAD; conservar, no requiere añadir de nuevo |
| `frontend/index.html` | = | VERSIONAR | Trabajo anterior ya en HEAD; conservar, no requiere añadir de nuevo |
| `frontend/nginx.conf` | = | VERSIONAR | Trabajo anterior ya en HEAD; conservar, no requiere añadir de nuevo |
| `frontend/package-lock.json` | = | VERSIONAR | Trabajo anterior ya en HEAD; conservar, no requiere añadir de nuevo |
| `frontend/package.json` | = | VERSIONAR | Trabajo anterior ya en HEAD; conservar, no requiere añadir de nuevo |
| `frontend/src/App.jsx` | = | VERSIONAR | Trabajo anterior ya en HEAD; conservar, no requiere añadir de nuevo |
| `frontend/src/App.test.jsx` | = | VERSIONAR | Trabajo anterior ya en HEAD; conservar, no requiere añadir de nuevo |
| `frontend/src/api.js` | = | VERSIONAR | Trabajo anterior ya en HEAD; conservar, no requiere añadir de nuevo |
| `frontend/src/components/Board.jsx` | = | VERSIONAR | Trabajo anterior ya en HEAD; conservar, no requiere añadir de nuevo |
| `frontend/src/components/Keyboard.jsx` | = | VERSIONAR | Trabajo anterior ya en HEAD; conservar, no requiere añadir de nuevo |
| `frontend/src/main.jsx` | = | VERSIONAR | Trabajo anterior ya en HEAD; conservar, no requiere añadir de nuevo |
| `frontend/src/styles.css` | = | VERSIONAR | Trabajo anterior ya en HEAD; conservar, no requiere añadir de nuevo |
| `frontend/src/test-setup.js` | = | VERSIONAR | Trabajo anterior ya en HEAD; conservar, no requiere añadir de nuevo |
| `frontend/vite.config.js` | = | VERSIONAR | Trabajo anterior ya en HEAD; conservar, no requiere añadir de nuevo |
| `infra/terraform/.gitignore` | = | VERSIONAR | Trabajo anterior ya en HEAD; conservar, no requiere añadir de nuevo |
| `infra/terraform/.terraform.lock.hcl` | = | VERSIONAR | Trabajo anterior ya en HEAD; conservar, no requiere añadir de nuevo |
| `infra/terraform/README.md` | = | VERSIONAR | Trabajo anterior ya en HEAD; conservar, no requiere añadir de nuevo |
| `infra/terraform/backend.hcl.example` | = | VERSIONAR | Trabajo anterior ya en HEAD; conservar, no requiere añadir de nuevo |
| `infra/terraform/main.tf` | = | VERSIONAR | Trabajo anterior ya en HEAD; conservar, no requiere añadir de nuevo |
| `infra/terraform/outputs.tf` | = | VERSIONAR | Trabajo anterior ya en HEAD; conservar, no requiere añadir de nuevo |
| `infra/terraform/providers.tf` | = | VERSIONAR | Trabajo anterior ya en HEAD; conservar, no requiere añadir de nuevo |
| `infra/terraform/terraform.tfvars.example` | = | VERSIONAR | Trabajo anterior ya en HEAD; conservar, no requiere añadir de nuevo |
| `infra/terraform/variables.tf` | = | VERSIONAR | Trabajo anterior ya en HEAD; conservar, no requiere añadir de nuevo |
| `infra/terraform/versions.tf` | = | VERSIONAR | Trabajo anterior ya en HEAD; conservar, no requiere añadir de nuevo |
| `k8s/.gitkeep` | = | VERSIONAR | Trabajo anterior ya en HEAD; conservar, no requiere añadir de nuevo |
| `k8s/README.md` | = | VERSIONAR | Trabajo anterior ya en HEAD; conservar, no requiere añadir de nuevo |
| `k8s/local/backend.yaml` | = | VERSIONAR | Trabajo anterior ya en HEAD; conservar, no requiere añadir de nuevo |
| `k8s/local/frontend.yaml` | = | VERSIONAR | Trabajo anterior ya en HEAD; conservar, no requiere añadir de nuevo |
| `k8s/local/kind.yaml` | = | VERSIONAR | Trabajo anterior ya en HEAD; conservar, no requiere añadir de nuevo |
| `k8s/local/kustomization.yaml` | = | VERSIONAR | Trabajo anterior ya en HEAD; conservar, no requiere añadir de nuevo |
| `k8s/local/namespace.yaml` | = | VERSIONAR | Trabajo anterior ya en HEAD; conservar, no requiere añadir de nuevo |
| `k8s/local/nginx.conf` | = | VERSIONAR | Trabajo anterior ya en HEAD; conservar, no requiere añadir de nuevo |
| `k8s/postgres/backend-patch.yaml` | ? | VERSIONAR | PG-06; overlay/reutilización memoria, readiness y ejecutor local |
| `k8s/postgres/kustomization.yaml` | ? | VERSIONAR | PG-06; overlay/reutilización memoria, readiness y ejecutor local |
| `k8s/postgres/postgres.yaml` | ? | VERSIONAR | PG-06; overlay/reutilización memoria, readiness y ejecutor local |
| `k8s/postgres/readiness.py` | ? | VERSIONAR | PG-06; overlay/reutilización memoria, readiness y ejecutor local |
| `k8s/postgres/run_pg06.py` | ? | VERSIONAR | PG-06; overlay/reutilización memoria, readiness y ejecutor local |
| `supabase/README.md` | ? | REVISAR | Histórico FIN-01B; distingue Supabase de PostgreSQL actual, requiere aclaración |
| `supabase/migrations/20261108000100_initial_wordle.sql` | ? | VERSIONAR | FIN-01B previo a PG; baseline/checks/generador reutilizables, sin aplicar allow_all |
| `supabase/prototype/allow_all.sql` | ? | REVISAR | Prototipo RLS allow_all/grants inseguros; no necesario para runtime/CI |
| `supabase/tests/backend_operations.sql` | ? | VERSIONAR | FIN-01B previo a PG; baseline/checks/generador reutilizables, sin aplicar allow_all |
| `supabase/tests/local_backend_smoke.py` | ? | REVISAR | Smoke histórico Supabase local, no ejecutor de integración actual |
| `supabase/tests/prototype_access.sql` | ? | REVISAR | Prueba histórica de roles/políticas Supabase; no usada por CI PG-07 |
| `supabase/tests/schema_contracts.sql` | ? | VERSIONAR | FIN-01B previo a PG; baseline/checks/generador reutilizables, sin aplicar allow_all |
| `supabase/tests/test_dictionary_preparation.py` | ? | VERSIONAR | FIN-01B previo a PG; baseline/checks/generador reutilizables, sin aplicar allow_all |
| `supabase/tools/prepare_dictionary.py` | ? | VERSIONAR | FIN-01B previo a PG; baseline/checks/generador reutilizables, sin aplicar allow_all |

## Tres informes creados exclusivamente por PUB-01

| Ruta | Recomendación |
|---|---|
| docs/analysis/pub-01/PUB-01-REPOSITORY-AUDIT.md | VERSIONAR tras revisión de la auditoría |
| docs/analysis/pub-01/PUB-01-PUBLICATION-MANIFEST.md | VERSIONAR tras revisión; lista de selección explícita |
| docs/analysis/pub-01/PUB-01-PUBLICATION-DECISION.md | VERSIONAR tras aceptación de condiciones |

## Fuera del futuro commit

| Ruta o recurso | Categoría | Acción recomendada, no ejecutada |
|---|---|---|
| backend/.env | CONSERVAR LOCALMENTE | Privado, ignorado y no abierto; no certificar su contenido ni copiarlo a plantillas |
| .venv/wordle-kind.kubeconfig | CONSERVAR LOCALMENTE | Credencial de clúster local dentro de directorio ignorado; no abrir/publicar |
| .venv/ | IGNORAR | Entorno y paquetes locales; no sustituye requirements.lock |
| backend/app/__pycache__/ | IGNORAR | Bytecode generado |
| backend/app/routers/__pycache__/ | IGNORAR | Bytecode generado |
| backend/tests/__pycache__/ | IGNORAR | Bytecode generado |
| frontend/node_modules/ | IGNORAR | Instalación local; usar npm ci |
| frontend/dist/ | IGNORAR | Build generado, no fuente |
| infra/terraform/.terraform/ | IGNORAR | Providers/caché local, sin inspección de binarios |
| **/*.kubeconfig; k8s/postgres/.local/ | CONSERVAR LOCALMENTE | Reglas existentes, sin afirmar que exista cada patrón |
| .env y .env.* reales; credenciales/claves/certificados privados | CONSERVAR LOCALMENTE | Verificar exclusiones; jamás forzar incorporación |
| *.tfstate*, *.tfplan, *.tfvars privados, infra/terraform/backend.hcl | CONSERVAR LOCALMENTE | Reglas Terraform; no se afirma existencia ni se leen valores |
| %LOCALAPPDATA%/WordlePG05/<proyecto>/compose.env, state.json, pg05-demo.dump | CONSERVAR LOCALMENTE | Recursos documentados PG-05 fuera del repo; no abiertos ni verificados por Docker en PUB-01 |
| %LOCALAPPDATA%/WordlePG06/<cluster>/kind.kubeconfig y state.json | CONSERVAR LOCALMENTE | Acceso/estado privado del entorno retenido, no abiertos |
| Capturas PG-05/06 en carpeta privada de evidencias de Codex | CONSERVAR LOCALMENTE | Decidir exportación sanitizada futura; no copiar por defecto |
| Volumen wordle-pg05-7325afa8cc_postgres_data y backup/imágenes PG-05 | CONSERVAR LOCALMENTE | No son archivos de Git; no se operó sobre ellos |
| Clúster PG-06, namespace wordle-pg06, PVC data-postgres-0 e imágenes locales | CONSERVAR LOCALMENTE | No son dependencias de CI; no modificar/eliminar para publicar |

La plantilla docker/postgres/.env.example tiene contraseñas vacías y queda explícitamente incluida por .gitignore. backend/.env.example también es plantilla, pero necesita actualizar variables antes de presentarla como configuración vigente. infra/terraform/.terraform.lock.hcl está versionado y no debe ignorarse. No se encontraron dumps/estados/claves privadas entre los 112 candidatos por nombre o patrones analizados; los archivos privados ignorados no se abrieron.

## Dependencias obligatorias todavía sin versionar

Todas existen en disco; ninguna fue añadida al índice:

- backend/app/repository.py.
- backend/tests/test_postgres_adapter.py y backend/tests/test_transactions.py.
- backend/integration/run_pg07_ci.py, run_pg04.py y test_postgres_integration.py.
- supabase/migrations/20261108000100_initial_wordle.sql.
- supabase/tests/schema_contracts.sql.
- docker/postgres/20-demo-words.sql.

Además, Compose necesita los scripts 00-check-config.sh/30-app-role.sh y su .gitattributes/plantilla; el perfil kind PG necesita los cinco archivos k8s/postgres y su base k8s/local ya en HEAD. Los informes PG-05/06 contienen el manual, aunque antes deben revisarse sus rutas personales. No publicar solo ci.yml o solo los archivos modificados: la selección coherente debe incluir dependencias nuevas, código/lock/tests adaptados y documentación vigente.

## Selección pendiente y comprobaciones antes del push

1. Resolver README/plantilla/notas obsoletos y sanear los siete documentos operativos señalados; aprobar qué históricos FIN/plan se publican. No se editan en PUB-01.
2. Mantener fuera del incremento operativo los tres scripts históricos Supabase y su README hasta decidir si se archivan/documentan. No son necesarios para los builds ni PG-07; no borrarlos ni moverlos sin autorización. No incorporarlos por un add global.
3. Revisar la lista exacta de archivos del futuro índice, exclusiones de secretos y diff staged completo una vez se autorice prepararlo. No usar incorporación indiscriminada de todos los nuevos.
4. Antes de autorizar commit/push: contraste con main remoto actualizado y estrategia de rama que preserve este trabajo, análisis de secretos sobre índice final y comprobación de diferencias. No se consultó GitHub ni se modificó la rama durante PUB-01.
5. Tras autorización separada, ejecutar CI remoto sobre rama/PR; conservar evidencia de SHA/run. Este documento no autoriza commit, push, PR, merge, publicación GHCR o despliegue persistente/cloud.
