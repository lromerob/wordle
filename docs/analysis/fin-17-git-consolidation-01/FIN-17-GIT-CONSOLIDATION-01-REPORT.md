# FIN-17-GIT-CONSOLIDATION-01 — 23/11/2026

## 1. Estado inicial
Repo C:/WordleTFG/repo; rama codex/pg01-07-consolidation.
HEAD 4d56cf265cc5f0af8c72c64f2a93373660e8f122.
9 modificados, 318 sin seguimiento, índice vacío.
Inventario Git con --no-optional-locks y safe.directory por comando; sin fetch.

## 2. Nueve modificados
| Ruta | Finalidad/cambio y relación | Riesgo | Clase/acción |
|---|---|---|---|
| docs/analysis/fin-04/FIN-04-IMPLEMENTATION-REPORT.md | Ratificación GHCR/cierre técnico FIN-04, anterior a FIN-17 | Bajo, documental | B, commit documental |
| docs/analysis/tfg-plan-001/TFG-COMPLETION-PLAN.md | Reconciliación FIN-04 y preparación FIN-16/19 | Bajo, enlaces/estados históricos | B, commit documental |
| infra/terraform/README.md | Sweden Central, capacidad, Entra/backend | Bajo, IDs operativos no secretos | A, con Terraform |
| infra/terraform/backend.hcl.example | Coordenadas reales del backend externo y Entra | Medio, selección de estado | A, revisar alcance público de coordenadas |
| infra/terraform/main.tf | Run Command deshabilitado, max_surge=1 | Medio, capacidad/coste AKS | A, previo a FIN-17 |
| infra/terraform/terraform.tfvars.example | Placeholders, región/versión fija, aprobación API falsa | Bajo/medio, no es input real | A, con variables.tf |
| infra/terraform/variables.tf | Un /32 público y aprobación obligatoria, defaults Sweden/version | Medio, cambia contrato de inputs | A, con ejemplos/scripts |
| k8s/observability/run_observability.py | Hook opcional captura, reutilización ship_event | Medio, subprocess/contexto privado por stdin | A, con scripts/evidence |
| k8s/observability/validation.py | Callbacks capture/disk_reader y ship_event | Medio, aceptación AKS/observabilidad | A, mismo commit |
Son cambios acumulados de varias iteraciones, no sólo del registro del runner.
No se revirtieron ni reescribieron. Preservar estados fechados como historial.

## 3. Clasificación de los 318
**A=54, B=121, C=0, D=143**, todos asignados.
C=0 sólo para los candidatos visibles. Hay 8.974 archivos ya ignorados que
deben permanecer fuera de publicación; no usar add -f.

Reglas exactas: A todos los nuevos de .github/workflows, docker/runner,
docs/operations, infra/scripts, infra/terraform, k8s/aks-full, k8s/aks-restore
y scripts. B todos los informes docs/analysis salvo las excepciones D listadas,
más capture-01 y capture-07 completos. D los doce históricos, cinco informes
con rutas personales y capture-02/03/04/05/06 completos.

| Grupo | Archivos | KiB aprox. | Clase |
|---|---:|---:|:---:|
| .github/workflows | 1 | 4.9 | A |
| docker/runner | 15 | 66.8 | A |
| docs/analysis contexto personal | 5 | 33.7 | D |
| docs/analysis históricos | 12 | 62.3 | D |
| docs/analysis restantes | 58 | 803.6 | B |
| docs/evidence/local/20261122-capture-01 | 20 | 801.8 | B |
| docs/evidence/local/20261122-capture-02 | 13 | 164.2 | D |
| docs/evidence/local/20261122-capture-03 | 19 | 431.9 | D |
| docs/evidence/local/20261122-capture-04 | 27 | 944.9 | D |
| docs/evidence/local/20261122-capture-05 | 36 | 2095.8 | D |
| docs/evidence/local/20261122-capture-06 | 31 | 1971.9 | D |
| docs/evidence/local/20261122-capture-07 | 43 | 2180.4 | B |
| docs/operations | 6 | 118.7 | A |
| infra/scripts | 3 | 37.8 | A |
| infra/terraform | 3 | 1.4 | A |
| k8s/aks-full | 2 | 3.0 | A |
| k8s/aks-restore | 1 | 0.2 | A |
| scripts (incluye evidence) | 23 | 169.9 | A |

A: fuente, configuración reproducible, pruebas y guía operativa; incorporar.
B: trazabilidad académica; incorporar tras revisión documental.
D: preservar localmente y decidir publicación, no borrar ni ignorar silenciosamente.
Tipos encontrados: Python/PowerShell/JS, YAML, Dockerfile, plantillas, Markdown,
JSON de resultados/proveniencia, SHA-256 y PNG/JPG; total aproximado 9,7 MiB.
No hay binarios grandes de dependencias entre los candidatos.

Excepciones D, doce históricos previamente excluidos:
- docs/analysis/fin-01r/FIN-01R-CLOSURE-DECISION.md
- docs/analysis/fin-01r/FIN-01R-REMAINING-GAPS.md
- docs/analysis/fin-01s/FIN-01S-BASELINE-REVIEW.md
- docs/analysis/pub-04/PUB-04-COMMIT-REPORT.md
- docs/analysis/pub-05/PUB-05-CI-RESULTS.md
- docs/analysis/pub-05/PUB-05-DECISION.md
- docs/analysis/pub-05/PUB-05-PUSH-REPORT.md
- docs/analysis/pub-05a/PUB-05A-CI-TRIGGER-REPORT.md
- docs/analysis/pub-05b/PUB-05B-CI-RESULTS.md
- docs/analysis/pub-05b/PUB-05B-DECISION.md
- docs/analysis/pub-05b/PUB-05B-PUSH-REPORT.md
- docs/analysis/pub-05c/PUB-05C-IDENTITY-REPORT.md

Excepciones D, cinco informes con rutas personales innecesarias para publicar:
- docs/analysis/fin-17-aks-recovery-01/FIN-17-AKS-RECOVERY-01-REPORT.md
- docs/analysis/fin-17-aks-recovery-03/FIN-17-AKS-RECOVERY-03-REPORT.md
- docs/analysis/fin-17-aks-recovery-04/FIN-17-AKS-RECOVERY-04-REPORT.md
- docs/analysis/fin-17-private-store-03/FIN-17-PRIVATE-STORE-03-REPORT.md
- docs/analysis/fin-17-workspace-migration-01/FIN-17-WORKSPACE-MIGRATION-01-REPORT.md

Los 126 archivos D de capture-02..06 son ensayos intermedios/solapados con fallos
registrados: decisión de selección académica, no declaración de corrupción.
B incluye capture-01 (20) y capture-07 (43): el segundo referencia explícitamente
provenance/restore/smoke del primero. Sus checksums se verificaron sin diferencias.
No publicar sólo capture-07 rompiendo esas referencias.
capture-07 dispone de revisión visual histórica de 22 capturas; no se hizo nueva
revisión visual. Los hashes no certifican ausencia de secretos en píxeles.

## 4. Riesgos y límites
Análisis textual focalizado en candidatos: sin coincidencias de claves privadas,
tokens GitHub, JWT, URI PostgreSQL con contraseña o asignaciones literales
de credencial según patrones aplicados. No certifica ausencia universal ni historial.
Cinco informes incluyen rutas personales; PUB-05C incluye email (ya clasificado D).
Registrar sólo rutas/tipos, no duplicar valores. UUID Entra/nombres de backend
son contexto operativo, no credenciales; revisar conveniencia pública.
Por nombres, sin abrir valores, se identificaron archivos ignorados sensibles:
backend/.env, infra/terraform/.terraform/terraform.tfstate,
.venv/wordle-kind.kubeconfig. No incorporarlos.
No se encontraron .env reales, estados, dumps, backups o tokens como candidatos
visibles. Los directorios privados reales permanecen fuera del repo.
Los enlaces a informes D pueden quedar rotos: resolver versión publicable antes
del commit documental; no ocultar la dependencia ni publicar por conveniencia.

## 5. .gitignore: propuesta NO aplicada
check-ignore confirma .env excluido, plantillas y lock incluibles.
Faltan cobertura .terraform/ y *.tfplan fuera de infra/terraform, copias privadas
accidentales y respaldos. Añadir en futura iteración autorizada:
~~~
.terraform/
*.tfplan
/private/
/recovery/
/backups/
/.wordle-private-store.json
/target.json
/variables.json
/backend.json
*.7z
*.7z.[0-9]*
*.dump
*.backup
~~~
No ignorar *.sql, docs/evidence/, docs/analysis/, scripts/, *.json ni
.terraform.lock.hcl indiscriminadamente. Excepciones .env.example redundantes
pero funcionales. No se detectó fuente necesaria afectada por *.key/*.pem.

## 6. Dependencias CI/CD
Conservar los versionados que usa CI: backend/app/tests/cors_tests/integration,
requirements.lock, migraciones SQL; frontend/src/package.json/package-lock.json;
Dockerfiles/contextos backend/frontend; scripts/verify_ci_images.py;
k8s/{local,postgres,aks,demo-kind,blue-green,observability} y sus bases/recursos;
Terraform .tf/lock. No se auditó código ajeno al análisis de dependencias.

El nuevo azure-demo.yml usa release_gate.py/azure_dispatch.py y sus módulos,
overlays y contrato operativo. REQUIRED enumera 52 rutas hoy sin versionar,
todas existentes. El HEAD actual no las suministra a un checkout limpio.
Conjunto funcional suficiente propuesto: los 54 A nuevos y los siete modificados A,
manteniendo las dependencias ya versionadas. No se requieren las capturas para CI.

## 7. Faltantes críticos exactos
Las 52 rutas del contrato operativo:
- .github/workflows/azure-demo.yml
- scripts/azure_release.py
- scripts/azure_dispatch.py
- scripts/azure_supervised.py
- scripts/azure_preflight.py
- scripts/ghcr_check.py
- scripts/aks_run.py
- scripts/aks_recovery.py
- scripts/release_gate.py
- scripts/private_store.py
- scripts/operational_contract.py
- scripts/evidence/aks_capture.py
- scripts/evidence/capture.cjs
- scripts/evidence/capture_policy.cjs
- scripts/evidence/test_capture_policy.cjs
- scripts/evidence/hook.py
- scripts/evidence/finalize.py
- scripts/evidence/README.md
- scripts/evidence/run_local.py
- scripts/evidence/run_persistence.py
- infra/scripts/Invoke-AksEmergencyTeardown.ps1
- infra/scripts/Test-AksEmergencyTeardown.ps1
- infra/scripts/Test-AksEmergencyAzureResolution.ps1
- infra/terraform/emergency-target.example.json
- infra/terraform/azure-variables.example.json
- infra/terraform/azure-backend.example.json
- k8s/aks-full/kustomization.yaml
- k8s/aks-full/images.lock.json
- k8s/aks-restore/kustomization.yaml
- docs/operations/FIN-AKS-DEPLOYMENT-RUNBOOK.md
- docs/operations/FIN-AKS-EMERGENCY-TEARDOWN.md
- docs/operations/FIN-AKS-FRIDAY-DEPLOYMENT-CHECKLIST.md
- docs/operations/azure-demo.md
- docs/operations/release-gates.md
- docker/runner/Dockerfile
- docker/runner/.dockerignore
- docker/runner/compose.yaml
- docker/runner/install_tools.py
- docker/runner/entrypoint.py
- docker/runner/runner.env.example
- docker/runner/Invoke-WordleRunner.ps1
- docker/runner/Test-WordlePrivateStore.ps1
- docker/runner/Test-WordleSupervisedStore.ps1
- docker/runner/test_runner.py
- docker/runner/test_private_store.py
- docker/runner/test_windows_store.py
- docker/runner/validate_persistence.py
- docs/operations/wordle-docker-runner.md
- scripts/test_release_gate.py
- scripts/test_aks_capture.py
- scripts/test_aks_run.py
- scripts/test_azure_readiness.py

Los dos A adicionales son docker/runner/.gitignore y validate_local.py.
El segundo es diagnóstico legado, no sustituye al launcher supervisado.
Externos/generados, NO versionar: registro runner, environment/reviewers/OIDC,
roles y secrets/vars GitHub; UUID/marker, variables.json/backend.json privados,
kubeconfig, planes/recibos/selecciones/backups; .terraform, node_modules, .venv,
imágenes y RUNNER_TEMP.
El CD espera sus inputs dentro de su almacén montado. Los inputs humanos de
C:/WordleTFG/recovery NO se trasladan automáticamente allí ni existen por aprobar
durabilidad. No se activaron estos prerrequisitos ni se ejecutó checkout limpio.

## 8. Tres commits propuestos, NO ejecutados
| Commit | Contenido exacto por reglas anteriores | Exclusiones/dependencias |
|---|---|---|
| feat(devops): consolidate supervised AKS runner and recovery tooling | 54 nuevos A + siete modificados A = 61 archivos | Mantener workflow/helpers juntos; cero B/C/D; sin activación externa |
| docs(tfg): consolidate operational progress and acceptance evidence | 58 informes B nuevos + dos modificados B; este informe tras revisión | Excluir doce históricos y cinco personales D; resolver enlaces/aceptación antes |
| docs(tfg): preserve referenced local acceptance evidence | capture-01 y capture-07 completos = 63 nuevos B | Preservar referencias; excluir capture-02..06 hasta decisión |

En la ejecución futura, generar LISTAS EXPLÍCITAS con estas reglas/excepciones.
No add ., -A, -f ni globs generales de docs/analysis.
Revisar nombres/diff preparados y secretos; diff --cached --check.
Validaciones futuras mínimas: sintaxis de scripts y casos focalizados release/
runner/recuperación, renders y fmt/validate según archivos cambiados.
No repetir demos completas por defecto. Publicación exige autorización separada.

## 9. Decisiones pendientes
- Mantener privados o autorizar versiones sanitizadas de los cinco informes;
  no alterar evidencias originales en esta iteración.
- Confirmar exclusión de los doce históricos y selección capture-01/07 frente
  a los ensayos intermedios, preservando todos los archivos locales.
- Confirmar alcance público del contexto operativo y aceptación documental FIN-04.
Decisiones explícitas: no hay exclusiones silenciosas.

## 10. Git final
Misma rama/HEAD; índice vacío; nueve modificados y 319 sin seguimiento
(este informe es el único nuevo). .gitignore y todos los archivos anteriores
conservados. Sin staging, commits, push, limpieza, stash ni cambio de rama.

## 11. OneDrive
Intacto; almacén privado, recuperación y respaldos no modificados.

## 12. Resultado
PARTIAL: inventario fiable y 318/318 clasificados; plan funcional concreto.
La publicación documental depende de decisiones D y enlaces pendientes.
Sin pruebas de aplicación/infraestructura, Azure, Terraform, workflows o instalaciones.

## 13. Próximo paso mínimo
Aprobar selección/exclusiones y tratamiento del contexto personal; después
autorizar saneamiento mínimo y staging por listas explícitas.
No ejecutar consolidación, registro del runner ni CD automáticamente.
