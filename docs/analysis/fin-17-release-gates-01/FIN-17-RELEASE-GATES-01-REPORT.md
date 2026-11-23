# FIN-17-RELEASE-GATES-01 — 22/11/2026

## 1. Resumen ejecutivo

**PASS de implementación local; AKS/CD permanece NO-GO.** Se cierran las brechas
locales R1/R2/R4/R6/R8 con controles y pruebas offline. No se acredita configuración
real de GitHub/Azure, federación, permisos ni capturas AKS. FIN-17 no se cierra.
No se ha modificado el plan ni código funcional de Wordle.

Referencia principal: [auditoría previa](../fin-17-preparation-01/FIN-17-PREPARATION-01-REPORT.md).
Se conservan las capacidades locales ya demostradas y la evidencia del primer
ciclo AKS de infraestructura; no se han repetido las demostraciones funcionales.

## 2. Estado inicial

Rama codex/pg01-07-consolidation; HEAD
4d56cf265cc5f0af8c72c64f2a93373660e8f122. Índice vacío, nueve versionados
modificados y 277 sin seguimiento. Se registraron SHA-256 de los 458 archivos
versionados/no ignorados presentes antes de escribir. Doce informes históricos,
siete dossiers y todos los pendientes anteriores se preservan.

Consultados el informe de preparación, evidencia readiness/capture local, manifest
capture-07, evidencia histórica de apply/destroy y scripts/runbooks pertinentes.
El dossier capture-07 acredita kind local, no una aplicación desplegada en AKS.

## 3. Archivos modificados

Preexistentes modificados en esta iteración (17; varios ya estaban sin seguimiento):

- `.github/workflows/azure-demo.yml`
- `docs/operations/FIN-AKS-EMERGENCY-TEARDOWN.md`
- `docs/operations/azure-demo.md`
- `infra/scripts/Invoke-AksEmergencyTeardown.ps1`
- `infra/scripts/Test-AksEmergencyAzureResolution.ps1`
- `infra/scripts/Test-AksEmergencyTeardown.ps1`
- `infra/terraform/azure-variables.example.json`
- `scripts/aks_recovery.py`
- `scripts/aks_run.py`
- `scripts/azure_dispatch.py`
- `scripts/azure_release.py`
- `scripts/azure_supervised.py`
- `scripts/evidence/README.md`
- `scripts/evidence/capture.cjs`
- `scripts/test_aks_run.py`
- `scripts/test_azure_readiness.py`
- `infra/terraform/terraform.tfvars.example`

Nuevos (10 más este informe):

- `docs/operations/release-gates.md`
- `infra/terraform/emergency-target.example.json`
- `scripts/evidence/aks_capture.py`
- `scripts/evidence/capture_policy.cjs`
- `scripts/evidence/test_capture_policy.cjs`
- `scripts/operational_contract.py`
- `scripts/private_store.py`
- `scripts/release_gate.py`
- `scripts/test_aks_capture.py`
- `scripts/test_release_gate.py`
- `docs/analysis/fin-17-release-gates-01/FIN-17-RELEASE-GATES-01-REPORT.md`

## 4. R1 — Contrato y referencias del release

azure_release.py produce un **kit de recuperación operativa**, no fuentes completas
de aplicación ni un paquete académico. El contrato se registra también en
release.json; las fuentes completas siguen siendo el checkout Git del SHA de
release, y el source_commit del lock identifica las imágenes de aplicación.
No se ha convertido el kit en un archivo monolítico del repositorio.

operational_contract.REQUIRED declara entradas operativas nuevas; verify_references
comprueba presencia, ausencia de enlaces, imports Python locales, dependencias
JavaScript relativas, rutas operativas literales y recursos/generadores Kustomize.
azure_release.sources la invoca antes de archivar. Se incorporan los nuevos gates,
adaptador/política de captura, scripts humanos y runbooks necesarios. No se incluyen
credenciales, herramientas, estado, planes ni originales privados.

Validación local: 122 archivos operativos; creación/verificación del tar en un
TemporaryDirectory y rechazo tras corrupción. Un kit construido hoy incluye
pendientes y lo declara: **HEAD solo todavía no reconstruye el release**. Falta
consolidación autorizada y comprobación posterior desde checkout limpio.

## 5. R2 — Gate CI → CD

release_gate.ci_evidence exige repositorio lromerob/wordle, rama exacta autorizada,
SHA completo del checkout, workflow ci.yml, evento push/manual y run completado con
success. Consulta los jobs del intento explícito del run; exige los siete nombres
actuales, únicos, completed/success. Rechaza omisiones, cancelaciones, fallos,
paginación incompleta/duplicada, ambigüedad, 403 y cambios de intento. No presupone
un campo run_attempt en cada job: el endpoint por intento proporciona esa asociación.

El workflow manual pide ci_run; el gate precede a azure/login. Conserva reviewers,
environment protegido, enable externo, serialización y permisos contents/actions
read más id-token write en el job. No PAT ni packages write. Ci.yml no se modifica.
Las consultas futuras son GET a la API oficial, sin redirecciones del token.

selected_images comprueba que los contextos completos backend/frontend tienen el
mismo árbol Git que el source_commit de las imágenes. Así permite reutilizar las
imágenes verificadas sin exigir circularmente que images.lock contenga su propio
SHA. Compara las once imágenes del render aks-full con el lock y verifica mediante
el helper GHCR existente los dos digests, revisión OCI y plataforma. Todos esos
accesos de registro/API fueron **simulados** en las pruebas; solo el render real
fue local. No se ha vuelto a consultar GHCR.

select guarda SHA de release/configuración, SHA de aplicación, run/intento CI,
identidades de imagen y hashes operativos en selections/run-attempt.json, con
creación exclusiva. verify_selection comprueba hash del recibo, checkout y fuentes
antes del dispatch y de cada comando. source.json vincula el plan con release_id,
commit y store_id; ejecutar exige exactamente la misma selección revisada.
La aprobación humana no se sustituye por un estado global de CI.

Referencia oficial:
[API de jobs por intento](https://docs.github.com/en/rest/actions/workflow-jobs#list-jobs-for-a-workflow-run-attempt).

## 6. R4 — OIDC Terraform explícito

azure-demo.yml transmite ARM_USE_OIDC=true, ARM_USE_AZUREAD=true, ARM_USE_CLI=false,
client/tenant/subscription y cliente aprobado. validate_oidc comprueba flags,
coincidencia con los inputs privados, cliente y disponibilidad del canal efímero
ACTIONS_ID_TOKEN_REQUEST_URL/TOKEN; rechaza secretos de cliente, claves/SAS,
certificados, tokens OIDC persistidos y fuentes alternativas. Se invoca antes del
login desde check-inputs y antes de operar Terraform en GitHub Actions.

El backend existente mantiene use_azuread_auth=true. No se escriben tokens en HCL,
recibos o archivos. El recorrido humano CLI sigue separado. azure/login prepara
las operaciones CLI, pero **no demuestra autenticación del provider/backend**.
ARM_USE_CLI corresponde al provider; no se presupone que Terraform 1.9.8 tenga el
mismo interruptor de fallback en el backend. La configuración OIDC y su canal son
obligatorios localmente; verificar el mecanismo efectivo real sigue pendiente.

Compatibilidad revisada en fuentes oficiales fijadas:
[backend Terraform 1.9.8](https://github.com/hashicorp/terraform/blob/v1.9.8/internal/backend/remote-state/azure/backend.go) y
[AzureRM 4.50.0](https://github.com/hashicorp/terraform-provider-azurerm/blob/v4.50.0/internal/provider/provider.go).
La lectura de documentación pública no fue una consulta autenticada a recursos.

**PENDIENTE DE VERIFICACIÓN EXTERNA:** federación issuer/audience/subject del
environment, identidad real, roles ARM, permisos de asignación de la identidad del
clúster, Blob data-plane separado y red/firewall. No se ha ejecutado init remoto,
plan, apply ni autenticación. OIDC queda preparado localmente, no probado en Azure.

## 7. R6 — Retirada humana y custodia privada

Invoke-AksEmergencyTeardown.ps1 exige -TargetFile y -WorkDirectory externos,
explícitos y existentes. El objetivo contiene UUID de suscripción/tenant/operador
humano y nombres/coordenadas de instalación. Set-EmergencyTarget valida estructura,
separación del backend, ámbito Wordle y rutas. No selecciona automáticamente una
identidad ni sustituye al humano por el principal del pipeline.

Se conservan sesión humana exacta, CREATE/DESTROY separados, confirmaciones PLAN
WORDLE AKS y DESTRUIR WORDLE AKS, seis direcciones Terraform permitidas, ámbito/IDs
exactos, hash del plan, fingerprint (ahora incluye target), inventario/ETag/lease,
exclusión del backend, rechazo de concurrencia y estados parciales. No auto-login,
force-unlock ni borrado de RG como fallback. No se han ejecutado comandos reales.
El plan temporal de emergencia propio se elimina como antes; el audit sanitizado
se conserva. Los planes de pipeline permanecen en el almacén durable.

private_store.require_store exige mount externo ya existente, marker con store UUID
aprobado y durable_acknowledged=true, subdirectorios plans/selections/evidence/backups
sin enlaces y permisos privados en POSIX. El dispatcher no presupone que dos
runners con la misma etiqueta comparten disco. Falta de mount, aprobación o ID
provoca rechazo antes del login. No se crea almacenamiento cloud ni se publican
planes. source.json, fingerprints e inventarios permanecen privados entre runs.

El marker es **declaración del operador**, no prueba física de durabilidad. ACL de
Windows, cifrado, backup, continuidad del mount, acceso exclusivo y restauración
deben verificarse externamente antes de activar CD. Ver runbook release-gates.md.

## 8. R8 — Captura AKS con el motor existente

scripts/evidence/aks_capture.py reutiliza capture.cjs; no es otro motor de captura.
Exige modo/acción capture y confirmación exacta, selección de release vigente,
mount durable, destino privado aprobado y contexto wordle-azure-supervised.
Cluster verifica ID ARM/suscripción/RG/nombre/tag y FQDN de kubeconfig antes de
interactuar con workloads. Solo wordle-demo y wordle-observability.

Abre únicamente sus propios forwards loopback y los cierra en finally. La política
Node valida metadatos/puertos y navegación; no permite hosts externos ni puertos
ajenos. En modo AKS no se ejecuta el flujo estable local que escribe SQL y elimina
el pod PG. No se hace patch/scale/delete/restore desde captura. El navegador
rechaza escrituras de juego; solo admite GET/HEAD y POST específicos de login y
consultas de datasource Grafana. SQL/HTTP funcional, persistencia, promoción,
faults, alertas y restore quedan en ejecutores previamente autorizados.

El hook.py kind permanece idéntico por hash y con su guard estricto. El motor admite
rutas de herramientas y browser executable/channel explícitos sin dependencia de
USERPROFILE en Linux ni instalación automática.

El flag opcional --capture en aks_run acceptance y el input capture del workflow
conectan snapshots estable Blue, promoción Green, rollback Green y señales. Sin
flag no cambia el recorrido anterior. El callback no autoriza acceptance: esta
operación mantiene su confirmación separada. La prueba con el controlador real y
dobles comprueba el orden de fases y la recuperación Green sin operaciones remotas.

Se registran environment=azure-aks, SHA/release_id, identidades runtime observadas,
hashes/dimensiones PNG y fingerprint del destino sin credenciales. El exportador
crea archivo privado fuera del clúster, verifica inventario/hashes y falla si existe
o falla la exportación. No sobrescribe dossiers ni pone PASS funcional por una
captura visual. La revisión humana de imágenes y su sanitización siguen siendo
necesarias antes de publicar derivados. **Captura real AKS: NOT RUN.**

## 9. Tratamiento de los cinco E

Los dos ejemplos Terraform/Azure ahora tienen placeholders explícitos para
suscripción, tenant y grupo; mantienen estructura y tipos, /32 vacío y aprobación
false. No son inputs ejecutables hasta completar copias privadas. Se añade un
emergency-target.example.json genérico, sin copiar UUID reales.

El ejecutor PowerShell deja de fijar la instalación y el operador. Los dos scripts
de regresión usan fixtures sintéticos; el tercero ya no contenía IDs operativos,
y se amplía con pruebas de parámetros. No se ha abierto ni sobrescrito ninguna
configuración privada ni se han eliminado originales históricos.

## 10. Pruebas ejecutadas

| Comprobación | Resultado y alcance |
| --- | --- |
| Unitarias scripts Python con socket connect/connect_ex y DNS bloqueados | 68 pruebas, 0 errores/fallos/omitidas; gate, store, OIDC, referencias, captura y regresiones AKS |
| Node node:test capture_policy | 9/9, 0 omitidas; sin lanzar navegador |
| PowerShell Test-AksEmergencyTeardown | 28/28; Native completamente sustituido |
| PowerShell Test-AksEmergencyAzureResolution | 14/14; solo az.cmd temporal inerte para resolución, nunca Azure CLI real |
| Sintaxis Python | AST de 21 archivos operativos Python; sin pycache |
| Sintaxis JavaScript | node --check de capture.cjs y capture_policy.cjs |
| Parseo PowerShell | 3 archivos, sin errores |
| YAML del workflow | Parseo estructural mediante parser local Kustomize sobre copia temporal con GVK; correcto |
| Coherencia Actions local | 10 inputs únicos (límite conservado), script Python embebido compilable, gates anteriores a login, sin runner en contexto job-env ni permisos packages |
| Kustomize local | aks-full 2189 líneas; aks-restore 2189; demo-kind 616; sin contacto con clúster |
| Render ↔ lock | 11 referencias inmutables coincidentes |
| Kit operativo | 122 fuentes verificadas; tar/checksums y detección de corrupción |
| Terraform 1.9.8 fmt -check | PASS, sin escritura |
| Terraform validate | PASS con inicialización/proveedor local preexistentes; sin init o backend remoto |
| Dossiers históricos | Los siete checksums/inventarios/JSON/PNG verificados; 189 archivos intactos |
| Revisión focalizada de datos sensibles | Patrones y revisión de los candidatos; sin credenciales reales nuevas detectadas; no certificación universal |
| git diff --check | PASS; avisos CRLF previos, sin normalización |

Las regresiones detectaron y permitieron corregir conflictos de ámbito en fixtures
PowerShell y la omisión de '- image:' al leer render YAML. Se añadieron regresiones.
No se han repetido las suites funcionales de aplicación ni creado clústeres.

## 11. Resultados PASS/FAIL/BLOCKED

- R1/R2/R4/R6/R8: PASS de implementación y pruebas locales, con límites externos explícitos.
- Casos focalizados: 119 satisfactorios (68 Python + 9 Node + 42 PowerShell), cero omitidos.
- FAIL pendiente: ninguno en comprobaciones locales ejecutadas.
- Validador Actions específico: NOT RUN; actionlint no disponible, no instalado.
- Azure/OIDC/runner/RBAC/red/GHCR actual/capturas AKS: NOT RUN por restricciones.
- GO de despliegue: bloqueado por dependencias externas, no por el resultado unitario.

## 12. Limitaciones

El parser YAML no valida expresiones/contextos Actions ni sustituye una ejecución
remota. No hay un release nuevo publicado o comprobado desde checkout limpio.
Las pruebas usan dobles para APIs, registro, Kubernetes y comandos destructivos;
no demuestran permisos, admisión, capacidad ni funcionamiento AKS. La seguridad de
un mount y runner comprometidos no se obtiene con un hash o marker.
No se declara que los digests históricos sigan recuperables hoy.

## 13. Dependencias externas pendientes

R3: runner dedicado, environment/reviewers/reglas de rama, dispatch disponible,
federación y permisos efectivos. R5: salida IPv4 /32 aprobada compatible con API y
Storage. R7: admisión PSA, hostPath/exporters, CSI y capacidad gestionada.
R9: ventana, timeout de job y operaciones ARM incompletas; retirada humana verificada.
R10: disponibilidad/permisos de pull GHCR actuales. Además: mount durable aprobado,
responsable de custodia y host de captura/herramientas existentes.
Toda verificación autenticada exige autorización independiente. Ninguna se ha hecho aquí.

## 14. Propuesta de staging selectivo — NO EJECUTADA

Lista operativa cerrada propuesta (45 pendientes, incluidos cinco E tratados y diez
archivos nuevos). Revisar diff/hashes e identidad antes de autorizar cualquier add:

- `.github/workflows/azure-demo.yml`
- `docs/operations/FIN-AKS-DEPLOYMENT-RUNBOOK.md`
- `docs/operations/FIN-AKS-EMERGENCY-TEARDOWN.md`
- `docs/operations/FIN-AKS-FRIDAY-DEPLOYMENT-CHECKLIST.md`
- `docs/operations/azure-demo.md`
- `docs/operations/release-gates.md`
- `infra/scripts/Invoke-AksEmergencyTeardown.ps1`
- `infra/scripts/Test-AksEmergencyAzureResolution.ps1`
- `infra/scripts/Test-AksEmergencyTeardown.ps1`
- `infra/terraform/README.md`
- `infra/terraform/azure-backend.example.json`
- `infra/terraform/azure-variables.example.json`
- `infra/terraform/backend.hcl.example`
- `infra/terraform/emergency-target.example.json`
- `infra/terraform/main.tf`
- `infra/terraform/terraform.tfvars.example`
- `infra/terraform/variables.tf`
- `k8s/aks-full/images.lock.json`
- `k8s/aks-full/kustomization.yaml`
- `k8s/aks-restore/kustomization.yaml`
- `k8s/observability/run_observability.py`
- `k8s/observability/validation.py`
- `scripts/aks_recovery.py`
- `scripts/aks_run.py`
- `scripts/azure_dispatch.py`
- `scripts/azure_preflight.py`
- `scripts/azure_release.py`
- `scripts/azure_supervised.py`
- `scripts/evidence/README.md`
- `scripts/evidence/aks_capture.py`
- `scripts/evidence/capture.cjs`
- `scripts/evidence/capture_policy.cjs`
- `scripts/evidence/finalize.py`
- `scripts/evidence/hook.py`
- `scripts/evidence/run_local.py`
- `scripts/evidence/run_persistence.py`
- `scripts/evidence/test_capture_policy.cjs`
- `scripts/ghcr_check.py`
- `scripts/operational_contract.py`
- `scripts/private_store.py`
- `scripts/release_gate.py`
- `scripts/test_aks_capture.py`
- `scripts/test_aks_run.py`
- `scripts/test_azure_readiness.py`
- `scripts/test_release_gate.py`

Documentación de evidencia propuesta, solo tras revisión humana: los dos modificados
FIN-04 y plan FIN; informes existentes de fin-16-19, fin-aks-live-deployment-apply,
fin-aks-live-destroy-execution, fin-evidence-readiness-01,
fin-evidence-capture-local-01, fin-17-preparation-01 y este informe. No se reetiquetan
los resultados históricos con el nuevo SHA.

Evidencia ligera seleccionada: únicamente los 93 archivos .json/.md/.sha256 ya
inventariados en los siete dossiers 20261122-capture-01 a 07. Capturas definitivas:
únicamente las 22 PNG en capture-07/screenshots. No añadir un directorio completo.
Antes de consolidar, resolver custodia verificable de los 74 binarios excluidos:
los manifiestos históricos los referencian y un checkout parcial no verifica por
sí solo esos dossiers completos. No borrar referencias ni alterar sus checksums.

Exclusiones explícitas: los doce informes históricos enumerados en §18; 74 binarios
de diagnóstico/históricos; otros informes sin selección; originales privados;
.env, variables/backend operativos, kubeconfig, state/planes/cache, dumps, entornos,
node_modules/dist y artefactos temporales. Los ejemplos genéricos no habilitan
la incorporación de copias privadas. No se ha ejecutado staging.

Revisión humana pendiente: retirada parametrizada y datos de su copia privada,
custodia/retención real, workflow protegido y selección del release, documentos
históricos con rutas/identificadores y legibilidad/sanitización de imágenes. La
propuesta no es autorización de publicación; un push futuro a la rama puede activar
GHCR por su política existente y exige autorización consciente de ese efecto.

## 15. Riesgos residuales

Demo privada sin autenticación ni aislamiento por jugador, como ya fue aceptado.
CORS no evita llamadas directas. Ningún cambio en ese contrato. API AKS público
restringido /32 no equivale a Private AKS. Estado y datos/evidencias tienen ciclos
de custodia separados. Los capturadores no recuperan señales emptyDir después de
destruirlas: exportar antes. El responsable debe tener recuperación humana
independiente y revisar estados ARM incompletos antes de reintentar.

## 16. Criterios GO/NO-GO

GO local: controles implementados, pruebas satisfactorias, referencias coherentes,
ejemplos genéricos e integridad de evidencia preservada.
NO-GO AKS/CD: falta revisión/consolidación autorizada y checkout limpio, CI del SHA
final, verificación externa R3/R5/R7/R9/R10, custodia/host efectivos y autorización
de ventana/presupuesto. PASS local no cambia las autorizaciones de Azure.

## 17. Próximo incremento recomendado

Aceptar/revisar el staging selectivo y el contrato humano de retirada/custodia;
posteriormente autorizar una verificación externa acotada de runner/environment,
federación, RBAC y red antes de cualquier CREATE. No volver a implementar el stack
local ya demostrado. No se inicia esa verificación ni consolidación aquí.

## 18. Estado Git final

Misma rama y HEAD. Índice vacío. Nueve versionados modificados, 288 sin seguimiento.
De 458 archivos previos, 441 idénticos por SHA-256 y 17 modificados únicamente dentro
del alcance. Se añaden 11 archivos incluido este informe; ninguno eliminado.
Los ocho versionados ya modificados distintos del ejemplo Terraform conservan
exactamente su hash inicial. Los siete dossiers (189 archivos), los doce históricos
y hook.py permanecen idénticos. Los hashes históricos de fuentes en los manifiestos
siguen describiendo la captura anterior, no el código nuevo de esta iteración.

Históricos preservados/excluidos, bajo docs/analysis:
fin-01r/{FIN-01R-CLOSURE-DECISION.md,FIN-01R-REMAINING-GAPS.md};
fin-01s/FIN-01S-BASELINE-REVIEW.md; pub-04/PUB-04-COMMIT-REPORT.md;
pub-05/{PUB-05-CI-RESULTS.md,PUB-05-DECISION.md,PUB-05-PUSH-REPORT.md};
pub-05a/PUB-05A-CI-TRIGGER-REPORT.md;
pub-05b/{PUB-05B-CI-RESULTS.md,PUB-05B-DECISION.md,PUB-05B-PUSH-REPORT.md};
pub-05c/PUB-05C-IDENTITY-REPORT.md.

No add/commit/push/fetch/cambio de rama ni modificación de Git. No consultas remotas
autenticadas, publicación GHCR, recursos Azure/AKS o backend remoto Terraform.
Solo se consultó documentación pública oficial. Ninguna instalación global,
credencial real, recurso PG-05/PG-06 o evidencia histórica se modificó.
