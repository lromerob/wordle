# FIN-17-PREPARATION-01 — 22/11/2026

## 1. Resumen ejecutivo

**PASS de preparación/auditoría; NO-GO para ejecutar CD/AKS ahora.**
Se identifican las fuentes necesarias y una propuesta selectiva de consolidación.
El checkout del HEAD actual no contiene el workflow CD, sus ejecutores ni aks-full:
su funcionamiento futuro no puede atribuirse a ese commit.

El sistema local integrado ya está acreditado; no se repitieron pruebas funcionales.
FIN-17 sigue PARTIAL: su criterio original exige primer despliegue autorizado con
servicios y señales verificados. Runner, environment, federación y permisos remotos:
**NO VERIFICADOS**, no declarados ausentes. No se activó ni publicó nada.

Hallazgos prioritarios: falta consolidar fuentes; falta ligar CD al CI satisfactorio
del release elegido; autenticación Terraform/backend con identidad federada no
acreditada; falta adaptador de captura AKS; procedimiento de emergencia y ejemplos
contienen identificadores de la instalación que requieren decisión antes de staging.
La infraestructura histórica fue creada y retirada, pero Wordle no se desplegó allí.

## 2. Alcance y fuentes

Lectura del encargo, Git local, plan FIN (§FIN-17/18/19), README, Dockerfiles/Compose,
Kustomize, Terraform y sus diffs; CI/CD y scripts asociados; documentación operativa;
informes LIVE-DEPLOYMENT-APPLY y LIVE-DESTROY-EXECUTION del 22/11; FIN-04,
FIN-16/19, FIN-EVIDENCE-READINESS-01 y FIN-EVIDENCE-CAPTURE-LOCAL-01.
Dossier definitivo: docs/evidence/local/20261122-capture-07/manifest.json.

Validaciones ejecutadas exclusivamente estáticas: ocho renders Kustomize en memoria,
AST Python, node --check del capturador, parser AST PowerShell y revisión textual de
workflows/referencias. No se importaron ejecutores cloud para invocar sus funciones.
PyYAML, yaml/js-yaml y actionlint no estaban disponibles en los runtimes consultados:
un intento de parser Python terminó ModuleNotFoundError, sin instalar nada.
**No se acredita validación automática especializada de expresiones GitHub Actions.**
La revisión manual de YAML no la sustituye.

Sin consultas remotas, ni siquiera autenticadas de lectura. Sin Azure CLI, Terraform,
Docker runtime, clústeres nuevos o pruebas funcionales en esta iteración.
kubectl solo se utilizó con kustomize, sin contacto con API Kubernetes.

## 3. Estado Git inicial

- Rama: codex/pg01-07-consolidation.
- HEAD: 4d56cf265cc5f0af8c72c64f2a93373660e8f122.
- Índice vacío. 181 archivos versionados, 276 sin seguimiento: 457 archivos visibles
  no ignorados; nueve versionados modificados y 285 pendientes en total.
- Se registraron hashes de los 457 archivos antes de crear este informe.
- No fetch: la sincronización remota actual es NO VERIFICADA.

Los nueve modificados:
```text
docs/analysis/fin-04/FIN-04-IMPLEMENTATION-REPORT.md
docs/analysis/tfg-plan-001/TFG-COMPLETION-PLAN.md
infra/terraform/README.md
infra/terraform/backend.hcl.example
infra/terraform/main.tf
infra/terraform/terraform.tfvars.example
infra/terraform/variables.tf
k8s/observability/run_observability.py
k8s/observability/validation.py
```

Los dos primeros son reconciliación documental; los cinco Terraform recogen Sweden,
configuración y hardening; los dos ejecutores conservan adaptación AKS/captura local.
Ningún cambio pendiente afecta al código de aplicación backend/frontend.

## 4. Clasificación completa de archivos

Inventario inicial, antes de este informe. Columna N/P = total / pendientes Git.
Los grupos son disjuntos y cubren los 457 archivos. A=release; B=documentación/evidencia
versionable tras revisión; C=archivo durable fuera de Git; D=local/sensible; E=decisión.

| Ruta/patrón exacto del grupo | N/P | Tamaño | Clase |
| --- | ---: | ---: | --- |
| `backend/**` | 24 / 0 | 228.7 KiB | A |
| `frontend/**` | 16 / 0 | 94.9 KiB | A |
| `compose.yaml, compose.test.yaml; docker/postgres/**` | 8 / 0 | 5.2 KiB | A |
| `infra/terraform/** excepto los dos ejemplos E` | 10 / 5 | 33.9 KiB | A |
| `infra/terraform/{terraform.tfvars.example,azure-variables.example.json}` | 2 / 2 | 1.8 KiB | E |
| `infra/scripts/*.ps1 (tres nombres en §5)` | 3 / 3 | 32.6 KiB | E |
| `k8s/**` | 56 / 5 | 181.3 KiB | A |
| `scripts/**` | 17 / 15 | 123.1 KiB | A |
| `.github/workflows/{ci.yml,azure-demo.yml,.gitkeep}` | 3 / 1 | 25.2 KiB | A |
| `supabase/migrations/**; supabase/tests/{backend_operations.sql,local_backend_smoke.py,schema_contracts.sql,test_dictionary_preparation.py}; supabase/tools/**` | 6 / 0 | 18.4 KiB | A |
| `supabase/{README.md,prototype/allow_all.sql,tests/prototype_access.sql}` | 3 / 0 | 15.8 KiB | B |
| `docs/operations/*.md (cuatro nombres en §5)` | 4 / 4 | 93.8 KiB | A |
| `docs/analysis/** (114 documentos iniciales)` | 114 / 61 | 1287.6 KiB | B |
| `docs/evidence/local/20261122-capture-0[1-7]/** — extensiones .json, .md, .sha256` | 93 / 93 | 1744.4 KiB | B |
| `docs/evidence/local/20261122-capture-07/screenshots/**/*.png` | 22 / 22 | 1779.4 KiB | B |
| `docs/evidence/local/20261122-capture-0[1-6]/**/*.png y capture-01/historical/*-original.jpg` | 74 / 74 | 5067.0 KiB | C |
| `.gitignore, README.md` | 2 / 0 | 18.6 KiB | A |

Totales: A=146 (30 pendientes), B=232 (176 pendientes), C=74 (74 pendientes),
E=5 (5 pendientes). D se inventaría por metadatos aparte, sin leer secretos.

| Grupo | Motivo y dependencias | Riesgo / acción propuesta |
| --- | --- | --- |
| A aplicación/Compose/SQL | FastAPI + psycopg async, React/Vite; baseline y scripts init/rol/diccionario | Conservar locks y fuentes; no usar memory-test como imagen AKS |
| A K8s/Terraform | aks-full hereda observability → blue-green → demo-kind → aks → postgres → local; Secret/init externos | Versionar toda la cadena ya presente y overlays nuevos; sin inputs operativos |
| A scripts/workflow/operación | Dispatch, planes, recuperación, promotion/validation y captura se referencian entre sí | Consolidar la lista cerrada §5; revisar brechas §6–11 antes de activar |
| B análisis | 55 documentos versionados y 59 nuevos, incluidos 12 históricos | No eliminar ni añadir automáticamente; curar por evidencia, sanitización y fecha |
| B dossier ligero | 93 JSON/Markdown/checksums, 1,70 MiB; incluyen ensayos fallidos | Versionables; conservar resultado real, procedencia y referencias cruzadas |
| B PNG final | 22 PNG, 1,74 MiB; tamaño moderado y valor académico | Propuesta de selección curada, no publicación autorizada |
| C otros binarios | 74 archivos, 4,95 MiB: diagnósticos, smoke, JPEG originales y derivados históricos | Mantener intactos en archivo durable privado; no borrarlos ni stagearlos por extensión |
| E ejemplos | terraform.tfvars.example y azure-variables.example.json contienen UUID reales de tenant/grupo/identidad | No son claves; decidir sanitización/aceptación explícita antes de incluir el cambio |
| E emergencia | Tres scripts PowerShell; el ejecutor fija suscripción, tenant y usuario humano | Herramienta personal de retirada, no runner OIDC genérico. Decidir plantilla parametrizada o custodia privada con hash |

Los 74 binarios C siguen físicamente bajo docs/evidence sin seguimiento. No se ha
verificado una copia externa de esos PNG/JPEG: su clasificación es una propuesta de
custodia, no evidencia de exportación realizada. Antes de publicar, acordar archivo
durable externo y comprobar hashes, sin mover ni borrar los originales por inferencia.

Los doce históricos excluidos de la propuesta de staging:
fin-01r/{FIN-01R-CLOSURE-DECISION.md,FIN-01R-REMAINING-GAPS.md};
fin-01s/FIN-01S-BASELINE-REVIEW.md; pub-04/PUB-04-COMMIT-REPORT.md;
pub-05/{PUB-05-CI-RESULTS.md,PUB-05-DECISION.md,PUB-05-PUSH-REPORT.md};
pub-05a/PUB-05A-CI-TRIGGER-REPORT.md;
pub-05b/{PUB-05B-CI-RESULTS.md,PUB-05B-DECISION.md,PUB-05B-PUSH-REPORT.md};
pub-05c/PUB-05C-IDENTITY-REPORT.md. Todos bajo docs/analysis/.

**D — ignorados presentes:** 8974 archivos, aproximadamente 418,4 MiB:
.venv/** (5455, incluye un kubeconfig local), frontend/node_modules/** y dist/**
(3505), backend/.env (1, 104 bytes), cachés Python backend (10), y
infra/terraform/.terraform/** (3, incluye metadatos locales de backend y proveedores).
Solo nombres/tamaños; no lectura de .env, kubeconfig o estado local.
.gitignore excluye .env/credenciales/claves/entornos/kubeconfig; infra/terraform/.gitignore
excluye planes/estados/variables/backend privado y permite .terraform.lock.hcl, ya versionado.
No se ha encontrado un dump/plan privado entre los candidatos no ignorados.
Los nombres genéricos variables.json, backend.json o un dump fuera de los directorios
previstos no están protegidos universalmente por ignore: mantenerlos fuera del repo,
como exige azure_supervised.external; no usar ignore como único control.

**C externo:** 25 JSON originales, aproximadamente 1,15 MiB, en
%LOCALAPPDATA%/WordleTFG/evidence/20261122-capture-0[1-7]/integrated/.
Conservar originales privados y copias sanitizadas diferenciadas; no importarlos
automáticamente. Planes, backups, sesiones e inputs operativos externos son D:
sus contenidos/existencia actual no se inspeccionaron fuera de lo necesario.

Análisis focalizado de 361 archivos de texto no ignorados: sin patrones detectados de
claves privadas, tokens GitHub, URLs PostgreSQL con contraseña literal o AccountKey.
No sustituye el análisis final del staging ni certifica ausencia universal de secretos.
Los UUID de los E son identificadores, no credenciales; no se reproducen sus valores.

## 5. Propuesta de staging selectivo — NO EJECUTADA

Primera lista cerrada A, 30 pendientes necesarios para reconstrucción:
```text
.github/workflows/azure-demo.yml
docs/operations/FIN-AKS-DEPLOYMENT-RUNBOOK.md
docs/operations/FIN-AKS-EMERGENCY-TEARDOWN.md
docs/operations/FIN-AKS-FRIDAY-DEPLOYMENT-CHECKLIST.md
docs/operations/azure-demo.md
infra/terraform/README.md
infra/terraform/azure-backend.example.json
infra/terraform/backend.hcl.example
infra/terraform/main.tf
infra/terraform/variables.tf
k8s/aks-full/images.lock.json
k8s/aks-full/kustomization.yaml
k8s/aks-restore/kustomization.yaml
k8s/observability/run_observability.py
k8s/observability/validation.py
scripts/aks_recovery.py
scripts/aks_run.py
scripts/azure_dispatch.py
scripts/azure_preflight.py
scripts/azure_release.py
scripts/azure_supervised.py
scripts/evidence/README.md
scripts/evidence/capture.cjs
scripts/evidence/finalize.py
scripts/evidence/hook.py
scripts/evidence/run_local.py
scripts/evidence/run_persistence.py
scripts/ghcr_check.py
scripts/test_aks_run.py
scripts/test_azure_readiness.py
```

Lista B documental inicialmente propuesta: los dos modificados FIN-04 y plan FIN;
los informes nuevos fin-16-19, fin-aks-live-deployment-apply,
fin-aks-live-destroy-execution, fin-evidence-readiness-01,
fin-evidence-capture-local-01 y este informe, con sus nombres existentes.
Añadir únicamente la lista revisada de 93 metadatos de los siete dossiers y las
22 PNG de capture-07/screenshots. No incluir el árbol docs/evidence completo:
contiene 74 binarios C. No ejecutar add con directorios indiscriminados.

E, D y C quedan fuera. Los demás informes B permanecen preservados, pendientes de
curación independiente. Antes de staging, resolver E y cualquier dato personal/ruta
innecesaria de documentos; no convertir su clasificación B en aprobación de publicación.
Los checksums/manifiestos históricos siguen nombrando binarios C: para verificar el dossier
completo desde checkout habrá que recuperar esos originales por hash desde su archivo.
No borrar referencias ni reescribir manifiestos antiguos para ocultar esa dependencia.

Se aconsejan dos commits futuros, sin crearlos aquí:
(1) fuentes operativas CD/AKS/recuperación y correcciones autorizadas;
(2) captura/documentación/evidencias curadas.
Así se separan controles de ejecución de material académico; los SHA finales se
registran sin reetiquetar las capturas históricas. Los dos necesitarán CI acorde al
commit final. Un push a esta rama puede publicar GHCR automáticamente: requerirá
autorización consciente de ese efecto, además de staging/commit/push.
Nunca add . o add -A. Aprobar rutas y hashes exactos, revisar diff cached, lista,
secretos e identidad personal; ningún E debe colarse por un patrón de directorio.

## 6. Reproducibilidad del release

**HEAD solo: insuficiente. Futuro commit con fuentes A revisadas: reconstrucción
plausible, aún no demostrada desde checkout limpio.** Dependencias concretas:

- Dockerfiles y locks backend/frontend están en Git; Compose usa una PG persistente
  y Nginx /api; producción va al target runtime. Las bases Docker usan tags móviles:
  rebuild no garantiza identidad binaria, aunque desplegar digest fijado sí evita
  seleccionar accidentalmente un tag distinto. No se exige rediseñar las imágenes.
- SQL vigente está bajo supabase/migrations por historia de nombres; no exige Supabase.
  docker/postgres/00-check-config.sh, baseline, 20-demo-words.sql y 30-app-role.sh
  alimentan el ConfigMap creado por configure_demo_secrets.py.
- Faltan en HEAD los tres archivos aks-full/aks-restore, los nueve scripts AKS/CD,
  seis de captura, azure-demo.yml, cuatro documentos operativos y ejemplos externos.
  Los siete cambios técnicos versionados pendientes son seis A y un ejemplo E: no perderlos.
- azure_release.py:11–35 incluye una lista NEW y SCOPES limitada. Es paquete de
  recuperación de infraestructura/configuración con imágenes, **no fuente completa
  de la aplicación**: omite frontend/src, backend/app, Dockerfiles, Compose y CI.
  Actualmente también omite scripts/evidence sin seguimiento y herramientas
  infra/scripts. No usar source.tar como único entregable reproducible.
- scripts/evidence requiere Edge/Playwright externos; .venv no viaja en Git.
  El README utiliza .venv/Scripts/python.exe y el runtime Codex de Windows; Linux
  necesita entorno explícito y WORDLE_PLAYWRIGHT_ROOT. No instalar nada por inferencia.
- Planes, variables, backend.json, backups y kubeconfig son externos por diseño.
  En múltiples runs, plans/<run>/ y source.json deben sobrevivir en el MISMO almacén
  privado; compartir etiquetas de runner no garantiza el mismo disco.
- El dossier capture-07 conserva HEAD base y advierte cambios sin commit. Sus hashes
  son de fuentes al finalizar, no sustituyen el futuro release. No modificarlo para
  atribuirle un SHA posterior.

Validación posterior propuesta, con permiso: exportar/checkout separado del commit
candidato, sin .venv/node_modules/estado/secretos; instalar solo dependencias aprobadas;
renderizar ocho perfiles, comprobar referencias y ejecutar las validaciones focalizadas
necesarias. Comprobar paquete de recuperación contra la lista de fuentes declarada.
No se realizó checkout, paquete ni instalación hoy.

## 7. Auditoría CI / GHCR / CD

| Workflow | Triggers/rama y permisos | Jobs/entorno/runner | Estado y bloqueo |
| --- | --- | --- | --- |
| ci.yml | PR, manual, push main y codex/**; contents:read global | Ubuntu 24.04 hospedado; sin environment Azure | IMPLEMENTADO; validado históricamente según informes, estado remoto actual NO VERIFICADO |
| publish-ghcr dentro de ci.yml | Solo push main o rama exacta de consolidación; contents:read y packages:write solo en ese job | Depende de siete gates; GITHUB_TOKEN, sin PAT | IMPLEMENTADO y evidencia GHCR histórica; consulta actual de imágenes NO VERIFICADA |
| azure-demo.yml:4–110 | Solo manual, repo/rama exactos y WORDLE_AZURE_ENABLED=true; contents/actions:read, id-token:write en supervised | self-hosted/linux/x64/wordle-azure; environment wordle-azure-demo; 60 min | IMPLEMENTADO local, sin seguimiento; activación/ejecución remotas NO VERIFICADAS |

CI: backend55 + CORS9 + telemetría4; integración PG16 once; frontend12 y build;
Docker runtime por ID; Kustomize; kind efímero; Terraform fmt/init backend=false/validate.
Los siete gates preceden a publicación. kind reconstruye imágenes en su daemon separado;
su backend es memoria, no acredita PostgreSQL en Kubernetes. No se repitieron tests.

Kustomize en CI renderiza seis perfiles; no incluye aún aks-full/aks-restore.
Se renderizaron estáticamente hoy los ocho (6/10/19/19/27/63/63/63 objetos).
Ambos overlays AKS tienen 14 contenedores declarados con imágenes fijadas y presentes
en el lock, 15 Services ClusterIP, ningún objeto Secret y PVC managed-csi. No prueba
admisión, CSI, permisos, salud ni disponibilidad de registro.

CD: gate de variable de repositorio antes de job, concurrency global sin cancelación,
checkout sin credenciales, environment obligatorio; comprueba reviewers antes de
azure/login y valida confirmación/inputs. azure_dispatch.py enlaza plan_run/hash con
source.json del SHA del workflow. execute exige CREATE/DESTROY exacto e inventario
para retirada. No hay activación por PR ni publicación de imágenes en CD.

**Brecha de gate:** el manual no consulta que los siete gates CI hayan concluido
success para github.sha, ni vincula la aprobación a un run CI seleccionado. actions:read
se usa para la comprobación de environment, no implica un gate de CI por sí solo.
La operación deploy tampoco exige una revisión CI del lock. Debe resolverse mediante
comprobación mínima autorizada del SHA/run/lock o procedimiento de aprobación
verificable explícito; no asumir que manual equivale a validado.

Evidencia histórica: FIN-04 enlaza run42840960356, commit782d37..., ocho jobs success y
digests cb070.../411839.... FIN-EVIDENCE-READINESS-01 distingue el run42841990340/HEAD4d56
comunicado por el propietario de una verificación remota nueva. Mantener ambos cortes;
ninguno acredita CD Azure. Advertencia Node.js20/24: mantenimiento histórico,
no vulnerabilidad confirmada ni warning observado hoy.

## 8. Runner / OIDC / environment

Todo lo siguiente es **esperado por código, configuración remota NO VERIFICADA**:

| Dependencia | Esperado / comprobación futura de solo lectura autorizada |
| --- | --- |
| Runner | Linux x64 exclusivo Wordle, etiquetas exactas, online/idle; no ejecutar PRs ajenos, almacén privado durable y herramientas preinstaladas |
| Herramientas | Python/dependencias lock, Terraform1.9.8/AzureRM4.50.0, az, kubectl compatible, kubelogin, Git, conectividad GHCR; Edge/Playwright si captura allí |
| Red | Salida estable aprobada al API TCP443 y al backend Storage, DNS y acceso privado del operador; NO 0.0.0.0/0 |
| Environment | wordle-azure-demo con required reviewers, restricciones de rama, prevención de autoaprobación/bypass según política acordada |
| Activación | WORDLE_AZURE_ENABLED de repositorio, no asumir variable de environment disponible antes del gate de job |
| Identidad | Federated credential con issuer/audience GitHub previstos y subject repo:lromerob/wordle:environment:wordle-azure-demo; sin client secret persistente |
| ARM | Roles efectivos mínimos por tarea, scopes dedicados y permisos para crear RG/AKS/red/MI/rol subnet; no asignar Owner global por comodidad |
| Estado | Data-plane Blob/lease en contenedor independiente y acceso de red; rol ARM no prueba acceso al blob |
| Kubernetes | Entra/Kubernetes RBAC (azure_rbac_enabled=false); SP del pipeline no hereda la pertenencia del humano al grupo administrador |

Nombres referenciados, sin valores: Secrets AZURE_CLIENT_ID, AZURE_TENANT_ID,
AZURE_SUBSCRIPTION_ID, WORDLE_AZURE_PRIVATE_DIR y tres WORDLE_DEMO_ADMIN_PASSWORD,
WORDLE_DEMO_APP_PASSWORD, WORDLE_GRAFANA_DEMO_PASSWORD.
En la carpeta externa: variables.json y backend.json aprobados; plans, backups,
evidence y kubeconfig privados. No copiar el almacén al checkout/artifacts públicos.

**OIDC incompleto como evidencia:** azure/login@v2 e id-token:write están presentes.
No aparecen ARM_USE_OIDC/ARM_CLIENT_ID ni configuración explícita equivalente de
autenticación federada para provider/backend Terraform. El helper invoca Terraform
tras comprobar sesión CLI; no se ha demostrado que ese recorrido acepte la identidad
no humana elegida. No se declara fallo inevitable ni OIDC Terraform configurado:
verificar soporte/configuración exacta sin client secret antes de plan/apply.

El GET de environment con GITHUB_TOKEN debe poder leer protection_rules; el script
rechaza error/permisos insuficientes. Solo comprueba reviewers no vacíos, no todos
los controles de bypass o rama. Disponibilidad de dispatch y reglas de rama por
defecto también requieren verificación autorizada; subirlo a una rama de trabajo
no se presupone suficiente para activarlo. No tocar main para resolverlo aquí.

RBAC K8s debe cubrir namespaces Wordle/observability, bootstrap de Secret/ConfigMap,
workloads/Services/Ingress/PVC, exec/port-forward, escalado/patch y recursos cluster-scope
de monitorización. Las reglas Prometheus leen nodes/proxy y nodes/metrics:
no basta ser Contributor ARM. La identidad del clúster/subnet es distinta de la de CI/CD.
Inspeccionar roles/asignaciones y grupo sin mostrar IDs/tokens completos ni modificarlos.

## 9. Trazabilidad commit / digest

- CI etiqueta con SHA completo, OCI revision/source, publica y vuelve a obtener por
  digest; compara ID construido y revisión, y prueba runtime aislado. No usa latest.
  Artifacts duran siete días: no son por sí solos archivo académico durable.
- aks-full/images.lock.json declara source_commit=4d56... y once referencias digest,
  incluidas las dos GHCR 936fcf13... y ebfe93fc...; render y lock coinciden hoy.
  aks_run.py:111–130 verifica Ready/imageID y revisión de GHCR contra source_commit,
  admitiendo raíz/plataforma/config OCI verificados por ghcr_check.py.
- k8s/aks mantiene digests históricos distintos cb070.../411839... del commit782d37....
  No son error por sí mismos: son otro perfil/corte. El despliegue integrado usa
  aks-full, no sustituir referencias mezclando releases.
- Existencia/pull actual de esos digests e igualdad de revisión remota: NO VERIFICADOS.
  No trasladar la evidencia de las imágenes antiguas a las del lock actual.
- Futura consolidación cambia SHA de manifiestos/scripts, aunque backend/frontend no
  tengan cambios. Registrar separadamente SHA de aplicación, SHA de configuración
  de despliegue, run CI/publicador, lock y runtime imageID. Si se opta por nuevas
  imágenes del release, obtener el lock desde la publicación real posterior; no
  inventar digests ni exigir circularmente que un lock versionado contenga su propio SHA.
- Ruptura pendiente: CI→selección del manual→configuración/lock no está cerrada por
  gate automático; la cadena completa hasta pods AKS aún no se ejecutó.

## 10. Preparación AKS: hechos y trabajo restante

Hechos históricos recuperados, no consultados de nuevo:
LIVE-DEPLOYMENT-APPLY acredita 22/11 Sweden Central, Terraform1.9.8/AzureRM4.50.0,
seis recursos, AKS Free1.35.9, dos D4s_v5 Ready, red azure/overlay/subnet,
Entra/grupo/Kubernetes RBAC, cuentas locales y Run Command deshabilitados.
LIVE-DESTROY-EXECUTION acredita CLEAN: seis retirados, ambos RG efímeros ausentes,
state list vacío, backend independiente accesible/lease libre; retirada ~6min25s.
No hubo Wordle, PostgreSQL ni observabilidad en AKS. Situación actual Azure NO VERIFICADA.

Distinción importante: main.tf:55 establece private_cluster_enabled=false y :87 una
sola IPv4 pública /32. Es **API público restringido**, no Private AKS. El entorno de
demo es privado/supervisado y usa Services ClusterIP + port-forward; no son conceptos
equivalentes. Runner y operador deben salir por la /32 aprobada o establecerse otra
decisión explícita compatible con ese control; no ampliar allowlist automáticamente.

Antes de crear: fuentes y E resueltos; release/run/lock revisados, runner/OIDC/RBAC/red,
MFA humano de retirada, Storage/lease/estado, cuotas/región/capacidad y presupuesto actuales.
Durante sesión: admisión/PSA, CSI/PVC8Gi, Secret externo, init SQL, Ingress, HTTP/SQL,
colores/rollback, exporters/Collector, dashboards/logs/trazas y notificaciones reales.
Retirada: preservar evidencia y política de datos sintéticos acordada, revisar inventario
y plan destroy, autorización exacta, comprobar remanentes y backend por lectura.

Riesgo AKS concreto: namespace observability permite privileged (resources.yaml:7);
Node Exporter monta hostPath (:775/:779) y Prometheus usa ClusterRole (:646).
Una policy gestionada puede impedirlo aunque el render sea correcto. Verificar admisión
con dry-run server autorizado; no debilitar políticas ni sustituir métricas sin decisión.
Los requests locales y dos nodos nominales no garantizan capacidad efectiva.

## 11. Adaptación futura del capturador — diseño, no implementación

Reutilizar capture.cjs y finalización, sin segundo sistema:
1. Adaptador explícito AKS que use la comprobación Cluster de aks_recovery.py:
   suscripción/grupo/nombre/tag/FQDN frente a kubeconfig externo; namespaces cerrados.
   Mantener hook.py de kind sin relajar su guard.
2. Recibir puertos loopback de forwards propios por stdin, acceso aprobado al API;
   localizador Wordle/queries/dashboards ya existentes y contraseña sintética solo
   por canal privado. Mantener allowlist de navegador y cierres finally.
3. Conectar hooks en Session.exercise: estable, candidata validada, postpromoción,
   rollback verificado y signals antes del fallo de alertas; no repetir acceptance
   con Green inicial ni cambiar selector solo para una foto.
4. capture.cjs:104 elimina el pod PG propio para probar persistencia local.
   **No reutilizar ciegamente esa fase contra AKS.** Separar captura de la mutación;
   reinicio remoto solo mediante autorización explícita, guard de objetivo y evidencia.
5. Parametrizar metadatos environment=AKS, run ID, release SHA, namespaces, imágenes,
   persistencia y archivo original. finalize.py supone LOCALAPPDATA y kind-local;
   admitir ubicación externa explícita para Linux sin cambiar evidencias previas.
6. Resolver Edge/Playwright y WORDLE_PLAYWRIGHT_ROOT en el host capturador; USERPROFILE
   no se presupone en Linux. Plazos acotados ajustados con observación, no sleeps amplios.
7. Exportar antes de destroy a archivo externo durable; firma/dimensiones/hash,
   JSON sanitizado, revisión de legibilidad y comprobación desde fuera del clúster.
   Marcar fallos/NOT RUN. Nunca limpieza automática de ARM/AKS desde el capturador.

Este adaptador es pendiente real; la capacidad local ya funciona y no se reimplementa.

## 12. Matriz de evidencias cloud

Identificadores y requisitos originales conservados. L=ya acreditado local/histórico;
P=pendiente AKS. No significa cierre académico global.

| EV / A | Prueba / entorno | Captura o artefacto | Automatización / condición PASS | Dependencia |
| --- | --- | --- | --- | --- |
| 01 A01/A50/A55 | L juego real; P juego AKS | UI desktop/móvil + SQL/HTTP | Capturador adaptado; inválida sin escribir, victoria, seis/derrota, reinicio; cubrir repetidas/séptimo según contrato | PG/Ingress/datos sintéticos |
| 02 A02–04/A34/A44 | L Docker; release Azure | Reusar builds y runtime/digest, sin screenshots de terminal | CI/publicador real asociado al release; no rebuild solo para foto | CI/GHCR |
| 03 A05–09/A45 | Infra 22/11 acreditada; pre/post nuevos si cambian | Resumen/hash de plan, nodos/seguridad, backend sin contenido | Helpers supervisados; parámetros efectivos coincidentes | Permiso CREATE/estado |
| 04 A10–15/A45 | P workloads AKS | Pods Ready, PVC, Services/Ingress, referencias Secret/config, HTTP | Session.wait/verify + campos permitidos; admisión/CSI reales | Bootstrap/RBAC |
| 05 A16–18/A31/A36/A46 | L CI/GHCR; P CD | Run CI→SHA/digest→run CD→images.json | CD protegido con gates verificados, mismo release seleccionado | Runner/environment/OIDC |
| 06 A20/A47 | L BG; P AKS | Selectores, candidata/activa, HTTP con release/tiempos | PromotionController y hooks; candidata validada antes del cambio | Ambos colores/PG compartido |
| 07 A21/A31 | L rollback; P AKS | Fallo503, eventos, petición estable y hash datos | Rechazo separado de rollback postpromoción; recuperar estable Green en fixture actual | Fallo reversible autorizado |
| 08 A22/A30/A48 | L OTel/Tempo; P AKS | Petición/span/TraceID y exportación | validate + Explore con traza real; no inventar Request ID distinto | Collector/Tempo |
| 09 A23/A26/A27 | L métricas; P AKS | Targets, consultas app/cAdvisor/nodo | Todos targets esperados UP; series reales del clúster Azure | RBAC kubelet/exporters |
| 10 A24/A30 | L dashboard; P AKS | Ocho paneles cargados y legibles | Captura tras datos reales, rango/unidades correctos | Datasources |
| 11 A25/A30 | L Loki; P AKS | Backend/frontend/deploy/error y correlación | LogQL real y resultado, no panel vacío | Agentes/Collector/Loki |
| 12 A28–30 | L alertas; P AKS | Firing, recibo receptor, resolved | validate; métricas y logs, entrega real de ambos estados | Faults/receptor autorizado |
| 13 A19/A49 | L perímetro; P comprobación cloud | Exposición/RBAC/CORS y logs sanitizados | Solo demo privada; sin afirmar aislamiento por jugador | Controles FIN-03/Secret |
| 14 A01/A50/A51 | L restore SQL/HTTP; P CSI/restore AKS | Hashes/dump privado/recibos SQL+HTTP | aks_run backup/restore; nuevo PG vacío, mismo dataset/secuencia | Backup y nueva instalación |
| 15 A05/A09/A51/A52 | L ciclo infra; P reconstrucción app | Cronología, inventario/destroy, remanentes, recreación | Dos autorizaciones; ausencia demostrada + backend retenido | Otra ventana si no cabe |
| 16 A32–54 | P memoria/release final | Fuentes, manual, PDF y enlaces | Revisión documental; checkout/archivo reproducible | Dossier aceptado |
| 17 A55–58 | P defensa/docente | Preguntas, vídeo≤15min, evidencia entrega | Acción real del propietario/docente; no prueba cloud inventada | FIN-20/21/22 |

El fixture recupera Green, no Blue como decía la propuesta histórica EV-07:
se registra la versión estable real sin renombrar los resultados ni alterar criterios.
No volver a crear infraestructura solo para reproducir una captura acreditada el 22/11.

## 13. Plan operativo Azure propuesto — NO AUTORIZACIÓN

A. Antes de T0, fuentes/gates corregidos y aceptados; runner/environment/OIDC configurados
y verificados por autorización separada. Release/digests listos. Preparar receptor,
capturador, almacenamiento y responsable humano de retirada; no abrir ventana facturable
mientras falten estos prerrequisitos.

B. Preflight de sesión: confirmar identidad/tenant/suscripción/MFA y permisos, región,
cuotas con surge, IP de salida exacta, backend/lease/estado esperado e inventario sin
residuales ajenos. Presupuesto aprobado, ventana y método de retirada operativo.
Plan guardado nuevo, revisión de seis recursos y hash; plan histórico consumido no se reutiliza.

C. Aprovisionamiento: autorización CREATE exacta del plan/fingerprint/presupuesto;
execute-infra supervisado, sin apply repetido por timeout. Comprobar AKS/nodos/red/acceso.
Conservar evidencia mínima de diferencias, no duplicar todos los informes históricos.

D. Aplicación: credentials aislado sin --admin; bootstrap fresco de namespaces/Secret,
deploy aks-full, dry-run server, PG/PVC/roles e imágenes verificados. CD y verify crean
datos de prueba: no tratarlos como lectura. Wordle por Ingress/forward loopback.

E. Blue-Green/fallo: acceptance con Blue inicial y autorización de fallos; promover Green,
fallo Blue postpromoción, recuperación automática, datos/PVC íntegros. Registrar muestras
y ventanas, no cero downtime. No tocar PG-05/PG-06.

F. Observabilidad/evidencia: validar señales/exporters/dashboards/logs/traza y entrega
firing/resolved, screenshots sincronizados; exportar JSON/PNG/checksums y revisarlos
desde almacenamiento externo antes de destruir. No subir planes/Secret/kubeconfig.
Backup de datos sintéticos si la política aprobada requiere conservarlos; restauración
independiente real en la ventana solo si hay tiempo explícitamente reservado.

G. Retirada: detener pruebas, inventario de IDs propio, nuevo plan -destroy en workspace
externo, hash de plan/inventario y autorización DESTROY independiente; serializar con
operaciones anteriores. Verificar state list vacío con exit0, RG/AKS/dependencias
ausentes por lectura, discos/PV/IP/LB/snapshots sin huérfanos y backend retenido/lease libre.
No borrar por prefijos, force-unlock, state rm o recursos ajenos. Si apply sigue en curso,
no lanzar destroy concurrente. Registrar costes diferidos cuando haya autorización de lectura.

## 14. Riesgos y GO/NO-GO

| Riesgo / hallazgo | Decisión requerida antes de GO |
| --- | --- |
| R1: fuentes CD/overlay no versionadas y E sin resolver | Commit candidato completo y revisado; checkout reproducible |
| R2: no gate CI→manual/lock | Verificar éxito para SHA elegido y aprobar selección inmutable |
| R3: runner/OIDC/roles/red externos NO VERIFICADOS | Lectura autorizada y recibo de checks, sin asignar permisos por inferencia |
| R4: autenticación Terraform federada no demostrada | Configuración explícita validada; no sustituir por client secret |
| R5: API público /32 y dos posibles salidas distintas | Operador/runner con salida aprobada compatible; no apertura masiva |
| R6: emergencia personal y estado privado entre runs | Procedimiento de retirada independiente, custodia y responsable probados |
| R7: PSA/hostPath/CSI/capacidad gestionada | Gates server-side tras CREATE; detener cargas ante denegación sin bajar seguridad |
| R8: capturas AKS ausentes/señales emptyDir | Adaptador aprobado y exportación antes de retirada |
| R9: timeout60min/job vs operación ARM | Estado real antes de reintentar; margen y alternativa humana autorizada |
| R10: GHCR históricamente disponible no garantiza pull hoy | Verificación autorizada de revisión/digest/permisos antes de CREATE |

Ni la auditoría PASS ni el plan de sesión autorizan activación, publicación o despliegue.
La garantía de retirada es un control operativo verificable, no promesa de duración Azure.

## 15. Estimación de tiempo y costes

Preparación previa estimada: **1–2 jornadas de trabajo condicionado** para resolver
brechas locales, revisión de staging y adaptación de captura. No es fecha de GO:
runner/Entra/RBAC/red y aprobaciones externas tienen plazo NO VERIFICADO.
No generar costes AKS mientras se preparan.

Ventana inicial propuesta de cuatro horas, con retirada alrededor de T+160:

| Minutos | Fase | GO/NO-GO |
| --- | --- | --- |
| 0–20 | A preflight/plan revisado | Sin identidad/estado/presupuesto/retirada: no CREATE |
| 20–70 | B aprovisionamiento | Si operación incierta, no repetir ni lanzar cargas |
| 70–100 | C admisión/PG/Ingress/Wordle | Si CSI/PSA/RBAC falla, conservar fallo y priorizar retirada |
| 100–125 | D promoción/rollback | Solo si la reserva de limpieza no queda comprometida |
| 125–145 | E señales/alertas | Timeouts de alertas aceptados antes de iniciar |
| 145–160 | F exportación/backup acordado | Cortar secundarios para asegurar evidencia |
| 160–220 | G retirada/verificación | Plan/hash/autorización; sin nuevas pruebas |
| 220–240 | Contingencia | Recursos pendientes → responsable y recuperación autorizada |

Si una fase termina antes, retirar antes. A T+120 evaluar margen; a T+160 parar nuevas
pruebas e iniciar retirada autorizada. No interrumpir a ciegas una operación ARM:
priorizar diagnóstico, avisar al propietario y usar solo recuperación autorizada.
Reconstrucción/restauración completas no se presuponen dentro de esta ventana.

Costes potenciales: dos nodos + surge, discos OS y PVC, LB/IP de salida, tráfico/IO,
estado/retención y backups. Free de AKS no significa recursos gratis.
USD5 era objetivo histórico, no presupuesto nuevo aprobado ni cap automático.
No se consultaron precios ni facturación; las cifras históricas no son factura.
Si proyección/alcance/tiempo cambian, posponer secundarios y pedir decisión antes de ampliar.

## 16. Acciones que requieren autorización adicional

Correcciones locales de gates/autenticación/adaptador/paquete/ejemplos o ignore;
staging selectivo, commits y push (con efecto GHCR explícito);
consultas autenticadas GitHub/Azure; configuración de environment/reviewers/runners/OIDC/RBAC;
disponibilidad de workflow manual en GitHub; nuevos planes/init y CREATE/DESTROY;
inyección de secretos, datos/fallos de aceptación y reconstrucción.
No se solicita entregar valores de secretos ni se presupone autorización heredada.

## 17. Siguiente incremento recomendado

**FIN-17 — preparación del release candidato y cierre de gates locales**:
autorizar únicamente correcciones mínimas de R1/R2/R4 y diseño acotado de R6/R8,
manteniendo despliegue deshabilitado; decidir tratamiento de los cinco E y aprobar
la lista final de staging. En paralelo, con autorización de solo lectura separada,
verificar runner/environment/OIDC/RBAC/red y disponibilidad de dispatch.
Después consolidación/publicación y CI; solo tras GO verificable, reservar ventana AKS.
No cambiar de roadmap FIN ni reimplementar componentes locales ya demostrados.

## 18. Integridad Git final

Verificación final 2026-11-22T15:40:30.576089+00:00: **457 archivos previos idénticos por SHA-256**; los 285 pendientes iniciales se preservan íntegros. Único archivo nuevo de esta iteración: este informe. Misma rama y HEAD; índice vacío; nueve versionados modificados y 277 sin seguimiento. git diff --check exit0; advertencias CRLF preexistentes, sin normalización. Los siete dossiers y doce informes históricos permanecen intactos.

No se modificaron dossiers, código, workflows, configuraciones, herramientas o recursos.
No staging, commit, push, cambio de rama, fetch, instalación ni operaciones remotas.
Este PASS acredita el inventario y la preparación documental; FIN-17 permanece PARTIAL.
