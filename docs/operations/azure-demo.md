# Wordle: ejecución Azure supervisada y reconstrucción

**Preparación, no autorización de ejecución.** No se ha creado AKS. Solo demo privada/supervisada, datos sintéticos y acceso loopback por port-forward. No autenticación por jugador. No usar PG-05/PG-06 como origen/destino. FIN-18 conserva su redacción histórica Supabase, pero la decisión aprobada PG-01 y el baseline vigente son PostgreSQL 16 directo; no se recupera la dependencia de Supabase ni se modifica el criterio para declarar cierre.

## 1. Gates previos: detenerse si falta cualquiera

- Revisar `python -B scripts/azure_preflight.py`. No registra providers ni inicia sesión. No imprime tokens/IDs.
- Aprobar suscripción/tenant, región/versión, cuota/capacidad y grupo Entra con pertenencia comprobada. La sesión CLI no prueba pertenencia ni acceso a Kubernetes. Terraform mantiene local_account_disabled: no usar credenciales admin locales.
- Confirmar permisos efectivos en el ámbito correcto: creación de RG/AKS/red/identidad y asignación de roles; Storage Blob Data Contributor limitado al contenedor de estado, más acceso de administración que proceda. Las comprobaciones generales de actions no prueban data-plane ni exclusiones/denegaciones.
- Registrar Microsoft.ContainerService/Network/Compute **solo con autorización adicional**, si siguen NotRegistered. No se registra nada en esta fase.
- Aprobar presupuesto/duración y revisión de remanentes. Dos D4s_v5 representan 8 vCPU nominales; reservar cuota/capacidad adicional para surge. No se acredita disponibilidad ni coste regional por estar el SKU en Terraform.
- Storage externo existente y separado de ambos RG desechables: Entra, ACL/RBAC y red restringidos, versionado/retención revisados. Comprobar acceso y lease/bloqueo con dos procesos solo cuando se autoricen escrituras de estado. No borrar el contenedor al destruir AKS.
- Acceso API desde IP/CIDR explícitos. No añadir 0.0.0.0/0 ni los rangos masivos de runners hospedados. En esta primera ejecución usar estación supervisada con salida aprobada. OIDC y runner con salida fija/privada, environments con reviewers y permisos federados quedan pendientes de configuración/verificación por el propietario; no hay CD cloud activado.
- Terraform nativo compatible (CI fija 1.9.8), Azure CLI, kubectl, kubelogin y Python. No se instalan automáticamente. AzureRM 4.50.0 fijado; no se registran providers automáticamente.

Referencias: [API AKS](https://learn.microsoft.com/en-us/azure/aks/api-server-authorized-ip-ranges), [backend Entra/bloqueo](https://developer.hashicorp.com/terraform/language/backend/azurerm), [costes](https://azure.microsoft.com/en-us/pricing/calculator/).

## 2. Infraestructura: plan privado y confirmaciones separadas

Copiar los dos `infra/terraform/azure-*.example.json` a un directorio privado **fuera del repositorio**. Sustituir placeholders en editor seguro: no introducir claves, contraseñas, SAS o tokens. El backend ya debe existir; su RG debe ser independiente. Variables y planes contienen identificadores: no publicarlos como artifacts de un repo público.

Comandos FUTUROS desde la raíz (Python del venv en Windows). `$Private` y `$Work` son rutas privadas externas elegidas por el operador; no usar rutas del repo:

```powershell
python -B scripts/azure_supervised.py prepare --workdir "$Work" --variables "$Private/variables.json" --backend "$Private/backend.json"
# CHECKPOINT: autorizar lectura/plan remoto y bloqueo del estado; no crear recursos.
python -B scripts/azure_supervised.py plan --workdir "$Work" --confirm "PLAN rg-wordle-academic/aks-wordle-academic"
# Revisar privadamente review.txt, review.json, costes y cambios; no difundir plan binario.
# CHECKPOINT CREACIÓN: autorización expresa del propietario y presupuesto aprobado.
python -B scripts/azure_supervised.py execute --workdir "$Work" --confirm "EXECUTE rg-wordle-academic/aks-wordle-academic" --approve-intent "CREATE rg-wordle-academic/aks-wordle-academic" --budget-approved --plan-sha256 "<HASH_REVISADO>"
```

El helper rechaza configuración alterada, suscripción/tenant equivocados, recursos inesperados, borrados/replacements en plan de creación y almacenamiento de estado dentro del RG desechable. No cambia la suscripción activa. Trabaja en workspace default/backend explícito. Los planes se ejecutan una sola vez; para otro plan preparar otro directorio vacío con el mismo backend. Un presupuesto reconocido no es un límite automático de facturación. No modificar el estado ni importar recursos ajenos para forzar éxito.

## 3. Clúster y secretos externos

Solo después del aprovisionamiento autorizado:

```powershell
# Variables privadas $Subscription, $Kubeconfig, $Context: elegidas/revisadas por el operador.
az aks get-credentials --subscription "$Subscription" --resource-group rg-wordle-academic --name aks-wordle-academic --file "$Kubeconfig" --context "$Context"
kubelogin convert-kubeconfig -l azurecli --kubeconfig "$Kubeconfig"
kubectl --kubeconfig "$Kubeconfig" --context "$Context" auth can-i create deployments -n wordle-demo
```

No usar `--admin`, el kubeconfig por defecto ni logins interactivos automáticos. Verificar pertenencia al grupo Entra y conectividad desde la salida autorizada. Inyectar fuera del historial tres contraseñas **sintéticas**, distintas, >=32 caracteres: WORDLE_DEMO_ADMIN_PASSWORD, WORDLE_DEMO_APP_PASSWORD y WORDLE_GRAFANA_DEMO_PASSWORD. Custodiarlas externamente para reconstrucción; no leerlas desde el Secret para copiarlas.

```powershell
python -B scripts/aks_recovery.py bootstrap --kubeconfig "$Kubeconfig" --context "$Context" --subscription "$Subscription" --resource-group rg-wordle-academic --cluster aks-wordle-academic --confirm "BOOTSTRAP rg-wordle-academic/aks-wordle-academic"
kubectl --kubeconfig "$Kubeconfig" --context "$Context" apply --dry-run=server -k k8s/aks-full
# CHECKPOINT: revisar render, RBAC/hostPath y coste del PVC antes de aplicar.
kubectl --kubeconfig "$Kubeconfig" --context "$Context" apply -k k8s/aks-full
```

El bootstrap verifica FQDN de AKS frente al kubeconfig y tag project=wordle; rechaza contextos kind/PG-05/PG-06 y namespaces existentes, sin sobrescribir secretos. No crea recursos ARM. Es un bootstrap de una instalación nueva: no usarlo para actualizar una instalación existente. Un fallo parcial exige inspección y recuperación autorizadas, no borrado automático. `aks-full` reutiliza observabilidad/Blue-Green, fija las once imágenes por digest, usa managed-csi/8Gi y una única base compartida. No hay Service público ni LoadBalancer de aplicación. La salida del AKS sí crea recursos facturables.

## 4. Aceptación y evidencia real (pendiente de Azure)

- Esperar StatefulSet/postgres, Deployments backend-blue/frontend-blue/ingress y siete Deployments de observabilidad; esperar DaemonSet/node-exporter. Green empieza en cero réplicas y solo se espera tras prepararlo. Verificar PVC Bound, managed-csi disponible, nodos Ready y ausencia de OOM. Node Exporter hostPath y permisos kubelet-cAdvisor requieren admission/RBAC reales de AKS.
- Comprobar que los Services son ClusterIP y no publican backend/PG. Usar `kubectl --kubeconfig ... --context ... -n wordle-demo port-forward --address 127.0.0.1 service/ingress 18080:8080`; HTTP con Host: wordle.test. Frontend / y /api/health deben ser 200; crear partida sintética, intento inválido 400 sin escritura, intento válido y partida persistidos. Comprobar SQL con `supabase/tests/schema_contracts.sql`, ocultación de solución activa y estadísticas.
- Preparar Green a una réplica, esperar nueva revisión y probar sus Services. Reutilizar `k8s/blue-green/promotion.py:PromotionController`: callbacks Kubernetes con kubeconfig/contexto explícitos y callbacks HTTP que devuelvan (status, X-Wordle-Release, body). Conmutación mediante test/replace del selector frontend; conservar ambos colores. No basta parchear el selector y suponer éxito.
- Tras promoción sana, provocar mediante la configuración `wordle-nginx-blue-fault-*` el 503 de la candidata Blue ya promocionada; el controlador debe restaurar Green automáticamente y probar lectura funcional. Registrar conmutaciones, motivo, muestras HTTP, tiempos y hash de datos/secuencia. La integración del runner kind no se ejecuta contra AKS: depende de creación/borrado de kind y de inspección Docker del nodo; la adaptación automatizada AKS queda pendiente y no se finge disponible.
- Comprobar Collector/Prometheus targets UP, nodo/cAdvisor, contador HTTP/duración; Loki logs frontend/backend/despliegue, trace_id consultable en Tempo y dashboard Grafana provisionado con datos. Forward de cada Service únicamente en loopback. Repetir entrega firing/resolved de alertas al webhook de demo con fallo reversible **solo tras autorización**; no basta consultar las reglas. Configs/consultas están en `k8s/observability/validation.py`, pero su ejecutor completo usa Docker local y no es portable a AKS sin adaptación.
- Guardar cronología, commit/digests, resultados SQL/HTTP y consultas sanitizadas fuera de Git. No guardar Secret, kubeconfig, DSN, filas reales o logs crudos con datos sensibles. Las señales actuales usan emptyDir: exportarlas antes de retirar; no prometer recuperación histórica de métricas/logs/trazas. Un receptor dentro del clúster no acredita notificación a personas/servicios externos.

**FIN-17/18 no cierran con un render o con estos comandos**: faltan ejecución autorizada, workflows manuales protegidos/OIDC y prueba de rollback/observabilidad sobre AKS.

## 5. Backup, retirada y reconstrucción

Crear y verificar paquete offline, sin acceso Azure:

```powershell
python -B scripts/azure_release.py create --directory "$Private/release"
python -B scripts/azure_release.py verify --directory "$Private/release"
```

Incluye infraestructura/config/scripts por hash y once referencias inmutables; excluye credenciales, estado, dumps e informes. Contiene cambios locales preparados: el HEAD publicado por sí solo no reconstruye este incremento. Custodiar manifiesto/archivo en almacenamiento privado y conservar también fuentes externas de secretos, variables/backend y el estado remoto.

Antes de backup real: registrar selector activo y réplicas deseadas; escalar los cuatro Deployments de aplicación a cero y esperar que desaparezcan sus Pods. La parada de escrituras supone indisponibilidad planificada. No interrumpir PG ni borrar PVC. El helper rechaza cualquier Deployment aún con réplicas:

```powershell
python -B scripts/aks_recovery.py backup --kubeconfig "$Kubeconfig" --context "$Context" --subscription "$Subscription" --resource-group rg-wordle-academic --cluster aks-wordle-academic --directory "$Private/backup" --confirm "BACKUP rg-wordle-academic/aks-wordle-academic"
```

Comando de parada de escrituras (solo tras la autorización del entorno correcto):

```powershell
kubectl --kubeconfig "$Kubeconfig" --context "$Context" -n wordle-demo scale deployment/backend-blue deployment/frontend-blue deployment/backend-green deployment/frontend-green --replicas=0
kubectl --kubeconfig "$Kubeconfig" --context "$Context" -n wordle-demo wait --for=delete pod -l 'app in (wordle-backend,wordle-frontend)' --timeout=180s
```

Ejecutar esa parada **antes** del comando backup anterior, y de restore. Conservar fuera de Git el selector/réplicas originales para reanudarlos; el helper no los infiere ni modifica.

El dump binario custom usa pg_dump 16, sin owner/ACL; hash de datos de cuatro tablas + secuencia antes/después, SHA-256 y metadata privada. No se vuelcan roles/contraseñas. No usar redirección de binarios en Windows PowerShell. El backup **no se marca restaurable** hasta completar restauración SQL y HTTP. Reanudar las réplicas registradas y comprobar servicio si se aplaza la retirada; no dejarlas en cero por olvido.

**CHECKPOINT RETIRADA:** autorización expresa, backup ya restaurado/comprobado, evidencia exportada y revisión de recursos ajenos/remanentes. Preparar OTRO workspace vacío con las mismas variables/backend:

```powershell
python -B scripts/azure_supervised.py plan-destroy --workdir "$DestroyWork" --confirm "PLAN-DESTROY rg-wordle-academic/aks-wordle-academic"
# Revisar privadamente plan y inventory.json de ambos RG; detenerse ante cualquier recurso ajeno.
python -B scripts/azure_supervised.py execute --workdir "$DestroyWork" --confirm "EXECUTE rg-wordle-academic/aks-wordle-academic" --approve-intent "DESTROY rg-wordle-academic/aks-wordle-academic" --plan-sha256 "<HASH_PLAN_REVISADO>" --inventory-sha256 "<HASH_INVENTARIO_REVISADO>"
```

Usar `prepare` para crear DestroyWork antes de plan-destroy. El helper compara inventario antes de ejecutar, pero el propietario debe identificar recursos ajenos: no se deduce exclusividad solo por el nombre del RG. No ejecutar `az group delete`, borrar estado, PVC o RG administrado de nodos por separado. Comprobar después, en lectura, RG/nodos, discos, snapshots, IP/LB y facturación diferida. Storage del estado/retención/backups permanece y puede seguir cobrando.

Para recrear: verificar paquete, extraerlo en carpeta privada vacía, revisar configuración/fechas/versiones/cuotas y repetir plan/aprobación. Custodiar el estado existente; no copiar solo .tf y perder el backend. No promover un plan antiguo tras reconstrucción/drift. Se crea infraestructura nueva desde Terraform, no se garantiza identidad de IP/UID.

En la nueva instalación usar `bootstrap --empty-restore` **antes** de aplicar aks-full: omite schema/semillas, crea roles desde las nuevas credenciales externas y deja PostgreSQL listo para pg_restore. Tras apply, mantener cuatro Deployments de aplicación en cero; esperar solo pg_isready (readiness SQL fallará justificadamente hasta restaurar). No esperar rollout Ready del StatefulSet vacío antes de restaurar:

```powershell
python -B scripts/aks_recovery.py restore --kubeconfig "$Kubeconfig" --context "$Context" --subscription "$Subscription" --resource-group rg-wordle-academic --cluster aks-wordle-academic --directory "$Private/backup" --confirm "RESTORE rg-wordle-academic/aks-wordle-academic"
```

Rechaza tablas públicas existentes y SHA/versiones discordantes; no hace DROP/clean/TRUNCATE. pg_restore single-transaction, regrants mínimos al rol app, contratos SQL y hash completo de datos/secuencia. Un fallo exige diagnóstico; no vaciar una base para forzar el reintento. Reanudar réplicas/selector guardados (verificar ambos colores antes de restituir tráfico), probar salud, partidas/estadísticas restauradas e intento/escritura HTTP reales. Guardar tiempos, restauración SQL/HTTP y costes remanentes; solo entonces valorar FIN-19.

Ensayo local independiente ya disponible, que no usa AKS/PG-05/PG-06:

```powershell
python -B backend/integration/run_fin02b.py --run-disposable-postgres
```

Este ensayo prueba dump/restore/HTTP en dos contenedores PostgreSQL nuevos; **no prueba** CSI, estado Azure, identidad, retirada/recreación AKS ni recuperación de señales históricas. Mantener FIN-16 a FIN-19 parciales hasta sus criterios originales completos.

## Actualización final: ejecutor integrado, sin ejecución cloud

Esta sección completa la preparación anterior: ya no queda pendiente escribir el adaptador AKS ni el workflow. **Siguen pendientes su activación externa y prueba real**. No ejecutar run_observability.py contra AKS: aks_run.py reutiliza PromotionController, validate y ship_event con un lector de disco PVC, sin Docker en el nodo Azure. El runner kind conserva el comportamiento anterior mediante el parámetro opcional por defecto.

Preflight de lectura reproducible (sin login/registro):

```powershell
python -B scripts/azure_preflight.py --check-ghcr
# Opcional, solo ficheros explícitos privados sin credenciales:
python -B scripts/azure_preflight.py --variables "$Private/variables.json" --backend "$Private/backend.json" --check-ghcr
# Sin acceso a Azure, pero verificando GHCR: añadir --offline.
```

El modo offline marca autenticación como no comprobada; no afirma que no exista sesión. GHCR se consulta con acceso pull anónimo, sin PAT ni credenciales personales; se verifican hashes de manifests/config, Linux/amd64 y revisión. No se muestran ni persisten los tokens de transporte. La ausencia de acceso no inicia logins alternativos. La comprobación runtime acepta el digest raíz/plataforma/config verificado, porque el imageID de containerd puede diferir del digest del índice OCI.

Tras aprobar y ejecutar el plan Terraform por el procedimiento anterior, usar comandos futuros con confirmación exacta de cada acción:

```powershell
$aksArgs = @('--variables', "$Private/variables.json", '--kubeconfig', "$Private/aks.kubeconfig", '--context', 'wordle-azure-supervised')
python -B scripts/aks_run.py credentials @aksArgs --evidence "$Private/evidence/credentials" --confirm "CREDENTIALS rg-wordle-academic/aks-wordle-academic"
# CHECKPOINT de coste/creación: namespaces/Secret/PVC/Deployments nuevos.
python -B scripts/aks_run.py deploy @aksArgs --evidence "$Private/evidence/deploy" --confirm "DEPLOY rg-wordle-academic/aks-wordle-academic" --ack-costs
python -B scripts/aks_run.py verify @aksArgs --evidence "$Private/evidence/verify" --confirm "VERIFY rg-wordle-academic/aks-wordle-academic"
# CHECKPOINT de fallo controlado, solo instalación sintética Blue inicialmente activa:
python -B scripts/aks_run.py acceptance @aksArgs --evidence "$Private/evidence/acceptance" --confirm "ACCEPTANCE rg-wordle-academic/aks-wordle-academic"
```

Verificación incluye Ingress/HTML/salud, cabecera del color activo, imágenes solicitadas y imageID real contra GHCR, contratos SQL, partida persistida, intento inválido sin escritura y victoria con intento persistido. Usa exclusivamente datos sintéticos. verify escribe una partida de prueba: no es una operación de solo lectura. No se captura la solución ni las credenciales.

acceptance promueve Green sano, promociona Blue y provoca 503 funcional **después** del cambio; el controlador existente debe revertir automáticamente a Green. Comprueba datos/UID del PVC y repara la configuración Blue inactiva. Reutiliza comprobaciones reales de métricas/trazas/logs/dashboard y firing/resolved del webhook mediante REVOKE/GRANT reversible sobre la base sintética. Requiere las credenciales externas del bootstrap; se comprueban antes de modificar tráfico. No garantiza cero interrupciones ni notificación a personas. Su diagnóstico de disco mide el PVC PostgreSQL; no afirma medir el disco OS del nodo.

El ejecutor termina forwards propios, conserva result.json/events.json/images.json/observability.json privados y **no borra** clúster ni cargas ante error. Un fallo deja evidencia FAIL, no autoriza aplicar/destroy/reintentar a ciegas. No se reescalan instalaciones ajenas ni se modifica el selector si el color inicial no admite la fixture.

Para recuperación usar el nuevo backup, que conserva réplicas/selector y lock de imágenes; no mezclar con metadata antigua del helper SQL básico:

```powershell
python -B scripts/aks_run.py backup @aksArgs --evidence "$Private/evidence/backup" --directory "$Private/backups/run1" --confirm "BACKUP rg-wordle-academic/aks-wordle-academic"
# Retirada solo tras plan/inventario/aprobación DESTROY anteriores; preservar estado/backup/evidencia.
# Tras reconstrucción Terraform autorizada, obtener kubeconfig NUEVO y secretos externos.
python -B scripts/aks_run.py restore-deploy @aksArgs --evidence "$Private/evidence/restore-deploy" --confirm "RESTORE-DEPLOY rg-wordle-academic/aks-wordle-academic" --ack-costs
python -B scripts/aks_run.py restore @aksArgs --evidence "$Private/evidence/restore" --directory "$Private/backups/run1" --confirm "RESTORE rg-wordle-academic/aks-wordle-academic"
```

backup detiene aplicaciones y las reanuda en finally; registra estado deseado y digest lock. restore-deploy aplica el overlay aks-restore con cuatro réplicas de aplicación a cero y bootstrap sin schema/semillas. restore espera el proceso PG, verifica metadata/versión/checksum/destino vacío, restaura SQL y replica/selector guardados, compara el dataset y realiza lecturas/escrituras HTTP. El recibo restored-http.json solo se genera tras éxito SQL/HTTP. La observabilidad se reprovisiona; sus datos históricos emptyDir no se recuperan. No se repite automáticamente una avería durante restore; acceptance separado exige autorización nueva y Blue inicial.

### Workflow manual preparado

`.github/workflows/azure-demo.yml`: workflow_dispatch, repositorio/rama exactos, cancel-in-progress=false y environment wordle-azure-demo. **Deshabilitado por defecto** salvo WORDLE_AZURE_ENABLED=true. Comprueba mediante API que hay reviewers configurados antes de azure/login; valida los inputs antes de autenticar. OIDC sin secretos Azure personales; permisos contents/actions read e id-token write solo en el job. No publica GHCR. Planes/variables/kubeconfig/dumps permanecen fuera del checkout, sin artifacts públicos.

Activación posterior por el propietario: registrar workflow según las reglas de la rama por defecto de GitHub (hoy es local, sin commit/push ni cambios main); configurar reviewers y política de rama; runner Linux x64 dedicado con etiqueta wordle-azure, salida API autorizada y herramientas preinstaladas; OIDC federado para repo:lromerob/wordle:environment:wordle-azure-demo con ámbitos mínimos. No se crean environment, runner, identidad ni permisos en esta fase.

Metadatos externos: WORDLE_AZURE_PRIVATE_DIR y AZURE_CLIENT_ID/TENANT_ID/SUBSCRIPTION_ID se guardan como Secrets del environment, sin valores en Git, para que GitHub los enmascare incluso antes de ejecutar el primer paso. Los identificadores no son una contraseña Azure; la autenticación sigue siendo OIDC sin client secret. Secretos externos de demo: las tres contraseñas sintéticas existentes. En el directorio privado: variables.json/backend.json aprobados. Los identificadores se enmascaran antes del login; el runner debe ser exclusivo y custodiar su carpeta. No usar un runner público o compartido. Los planes guardan el commit del workflow y solo se ejecutan con ese mismo commit, hash e inventario revisados; suscripciones/tenant/entorno incorrectos se rechazan.

El despacho permite preflight, plan/plan-destroy, execute-infra y acciones AKS. Para ejecutar un plan, indicar run original, SHA-256 de plan/inventario y CREATE/DESTROY; CREATE exige presupuesto aprobado. Cada llamada requiere confirmación específica. El workflow no se ha validado remotamente ni se afirma que OIDC/reviewers/runner estén disponibles. [API de environments y permiso Actions read](https://docs.github.com/en/rest/deployments/environments#get-an-environment).

WORDLE_AZURE_ENABLED debe ser una variable **de repositorio**, porque se evalúa antes de iniciar el job; mantenerla ausente/false hasta autorizar la activación. El resto de metadatos sensibles/contraseñas se configura como Secrets en el entorno protegido, con enmascarado desde el inicio del job. No se han registrado ni alterado estos valores remotos.

Para reconstruir, reasignar aksArgs a un kubeconfig externo nuevo (por ejemplo, aks-rebuilt.kubeconfig) y ejecutar de nuevo credentials antes de restore-deploy; se rechaza sobrescribir el fichero anterior. La aceptación integrada requiere Blue activo al inicio; tras restore se comprueba el selector guardado sin forzarlo a Blue. No repetir acceptance sobre una instalación Green activa sin un nuevo plan de ensayo aprobado.

## FIN-AKS-TOOLS — instalación local verificada, 15/11/2026

Terraform **1.9.8 windows_amd64** y kubelogin **v0.2.22 windows/amd64** instalados en directorios nuevos del usuario, mediante ZIP oficiales y sin permisos administrativos ni modificación del PATH (usuario/sistema). Este registro supera únicamente los pendientes históricos de instalación; no implica acceso Azure, backend o AKS preparados.

- Terraform: `%LOCALAPPDATA%/WordleTFG/tools/terraform-1.9.8/terraform.exe`.
- kubelogin: `%LOCALAPPDATA%/WordleTFG/tools/kubelogin-0.2.22/bin/windows_amd64/kubelogin.exe`.
- ZIP y checksums oficiales conservados en cada carpeta. SHA-256 de Terraform ZIP: `2667de56106bc6707968286357e29c20f8dbbb2f429ef57099b04994f82d9684`; kubelogin ZIP: `62839abfdaddc35dc460bfe1d40f2c569c168b7aa090e2c831776e84f95402b9`. Ambos coinciden con valores publicados oficialmente, verificados antes de extraer. No se ejecutó verificación adicional de firma; no se presenta el checksum como una firma.
- Origen Terraform: [ZIP 1.9.8](https://releases.hashicorp.com/terraform/1.9.8/terraform_1.9.8_windows_amd64.zip) y [SHA256SUMS](https://releases.hashicorp.com/terraform/1.9.8/terraform_1.9.8_SHA256SUMS).
- Origen kubelogin: [ZIP v0.2.22](https://github.com/Azure/kubelogin/releases/download/v0.2.22/kubelogin-win-amd64.zip) y [SHA-256](https://github.com/Azure/kubelogin/releases/download/v0.2.22/kubelogin-win-amd64.zip.sha256).
- Comandos ejecutados: exclusivamente `terraform.exe version` (v1.9.8) y `kubelogin.exe --version` (git hash v0.2.22/f341e3167eb2c077fd95f73b3c454236262299ce). Checkpoint Terraform deshabilitado en el proceso de verificación. Sin bloqueos encontrados.

Uso desde una nueva sesión PowerShell, sin cambios persistentes:

```powershell
$WordleTerraform = Join-Path $env:LOCALAPPDATA 'WordleTFG/tools/terraform-1.9.8/terraform.exe'
$WordleKubelogin = Join-Path $env:LOCALAPPDATA 'WordleTFG/tools/kubelogin-0.2.22/bin/windows_amd64/kubelogin.exe'
$env:CHECKPOINT_DISABLE = '1' # Solo esta sesión; evita comprobación remota de actualización.
& $WordleTerraform version
& $WordleKubelogin --version
# Si los helpers necesitan descubrir herramientas, opcional y solo en esta sesión:
$env:PATH = "$(Split-Path $WordleTerraform);$(Split-Path $WordleKubelogin);$env:PATH"
```

No se ejecuta init/plan/apply/destroy, no se registran providers ni se realizan llamadas/operaciones Azure. Los comandos operativos anteriores siguen sujetos a sus autorizaciones; instalar no autoriza desplegar ni acceder al estado remoto. No se modifican aplicaciones, infraestructura o secretos, ni se realizan commits/push. Se preservan los informes previos; no se inicia la siguiente fase.

## FIN-AKS-DEPLOYMENT-DECISIONS — ciclo temporal aprobado (16/11/2026)

Esta sección actualiza los prerrequisitos operativos anteriores; **no autoriza
ninguna ejecución cloud ni Terraform**. Gate A GO por bootstrap/lease previos;
Gate B y AKS NO-GO. Ver el informe fin-aks-deployment-decisions para la observación
fechada de IP y redes. No copiar su IP como valor permanente ni publicarla.

Configuración aprobada: Sweden Central, AKS Free 1.35.9, dos Standard_D4s_v5,
surge un nodo, Entra/Kubernetes RBAC y cuentas locales deshabilitadas.
Los helpers leen región/SKU/nodos de las variables Terraform; no presuponen West Europe.
Backend persistente: rg-wordle-state (RG en West Europe), Storage
stwordletfgstate7c92d4 en Sweden Central, tfstate/wordle/aks-demo.tfstate,
Entra y Shared Key deshabilitada. No modificarlo para desplegar o retirar AKS.

### DEPLOY — checkpoints futuros, sin ejecutar en esta iteración

1. Obtener autorización separada para validación/init/plan; después, para apply y
   retirada supervisada. No despachar azure-demo.yml ni activar variables remotas.
2. En el ordenador personal/conexión doméstica, sin VPN corporativa, revisar Azure
   CLI en lectura: account show, tenant/suscripción Enabled y coincidencia exacta
   con los IDs privados aprobados. No account set, login automático ni cambios RBAC.
3. Revalidar región, versión, SKU y cuotas en swedencentral mediante consultas de
   lectura autorizadas. Dos nodos necesitan 8 vCPU; con un surge, 12, además del
   consumo de otros recursos. Los límites históricos 16 DSv5/26 regionales no son
   garantía de capacidad actual ni reserva de hardware.
4. Comprobar en lectura acceso Entra/red al backend existente sin claves, cambios de
   firewall ni lease de prueba implícito. Gate A histórico no sustituye esta revisión.
5. Repetir consulta de IPv4 y revisión de rutas justo antes de plan/aplicar y de
   administrar AKS. Si cambia la IP, se activa VPN o hay discrepancia: parar y revisar
   los inputs/plan. No parchear Azure ni Storage automáticamente.

Ejemplo FUTURO en PowerShell, solo tras autorizar la preparación de los inputs
privados. No crea ni modifica recursos; no se ha ejecutado aquí:

```powershell
# $Private es un directorio privado externo elegido por el propietario.
# Partir de los ejemplos actuales; completar la suscripción ya autorizada.
$WordleObserved = foreach ($WordleSource in @('https://api4.ipify.org', 'https://checkip.amazonaws.com')) {
    $WordleReply = & curl.exe -4 --noproxy '*' --fail --silent --show-error --max-time 20 $WordleSource
    if ($LASTEXITCODE -ne 0) { throw 'No se pudo verificar la IPv4; detener.' }
    ($WordleReply -join '').Trim()
}
if ($WordleObserved.Count -ne 2 -or $WordleObserved[0] -ne $WordleObserved[1]) {
    throw 'Fuentes de IPv4 discrepantes; detener.'
}
$WordleAddress = [System.Net.IPAddress]::Parse($WordleObserved[0])
if ($WordleAddress.AddressFamily -ne [System.Net.Sockets.AddressFamily]::InterNetwork) {
    throw 'Se requiere IPv4.'
}
$WordleApiCidr = $WordleAddress.ToString() + '/32'
# Confirmar que esta es la salida doméstica autorizada, no la de otra red/proxy/VPN.
$WordleValues = Get-Content -Raw -LiteralPath "$Private/variables.json" | ConvertFrom-Json
$WordleValues.api_authorized_cidrs = @($WordleApiCidr)
$WordleValues.api_access_approved = $true
# Revisar privadamente y guardar solo tras confirmación del propietario:
# Usar UTF-8 sin BOM, compatible con el helper y Windows PowerShell 5.1:
# [IO.File]::WriteAllText("$Private/variables.json", ($WordleValues | ConvertTo-Json -Depth 6), [Text.UTF8Encoding]::new($false))
```

El helper exige exactamente un /32 IPv4 público y api_access_approved=true;
rechaza rangos amplios, privados/reservados, placeholders o confirmación ausente.
Los ejemplos genéricos siguen []/false; no se ha generado configuración operativa.
No hay detección automática durante despliegue: el dato debe revisarse y pasarse
explícitamente. La pertenencia Entra y RBAC siguen siendo controles independientes.
AKS puede autorizar IP internas/de salida propias por comportamiento del servicio;
la lista administrativa que configura este proyecto solo contiene el /32 elegido.

6. Revisar presupuesto completo, tiempo de creación/validación/evidencias/retirada
   y margen de limpieza. **4 horas totales y objetivo 5 USD**; no es un límite
   automático de Azure. Detener antes de apply si partidas desconocidas impiden
   aceptar el coste o exceden el objetivo. No activar Log Analytics/servicios nuevos.
7. Solo con autorización posterior: preparar workspace externo mediante prepare;
   ejecutar fmt/validate/init/plan según autorizaciones independientes y comandos de
   la sección 2. Revisar los seis recursos previstos, región, versión, surge,
   CIDR exacto, RBAC, disco/Load Balancer/IP y ausencia de cambios al backend.
8. **CHECKPOINT APPLY:** propietario revisa el plan privado, SHA-256 y presupuesto;
   autorización expresa de CREATE. Un plan aprobado no es reutilizable tras cambio
   de IP/configuración/drift. Usar execute con hash y confirmaciones ya documentadas;
   nunca aplicar automáticamente ni habilitar el workflow por extensión.

### VALIDATE — previsto, no ejecutado

Tras apply autorizado: comprobar clúster/régimen Free/versión, dos nodos Ready y
surge configurado; obtener kubeconfig externo nuevo sin --admin, convertir mediante
kubelogin y verificar pertenencia/RBAC y acceso por API desde el /32 aprobado.
Revisar networking, discos, Services ClusterIP y ausencia de exposición backend/PG.
Solo después de autorización de cargas: usar credentials/deploy/verify de aks_run.py
según la sección de ejecutor integrado. Wordle por Ingress con port-forward loopback,
frontend y /api/health HTTP 200, SQL/partida/intentos persistidos y datos sintéticos.
Blue-Green/rollback/observabilidad se ejecutan únicamente con su autorización de
fallo controlado; no alargar la ventana automáticamente para completar pruebas.

### EVIDENCE — antes de la retirada

Guardar fuera de Git, sanitizado: cronología UTC, configuración/hash/commit/digests,
versiones Terraform/AzureRM/AKS, resumen del plan, nodos/Pods/PVC/Services, resultados
SQL/HTTP, capturas, incidencias, tiempos y costes disponibles. No exportar secretos,
tokens, kubeconfig ni planes/DSN/logs crudos como evidencia pública. Backup/restore
sintético según el procedimiento existente si corresponde a los criterios del
ensayo; confirmar su duración antes de CREATE. Señales emptyDir se pierden al retirar.

### DESTROY — autorización separada y preservación del backend

Destruir AKS al terminar la validación, aunque quede ventana. Nunca ejecutar retirada
sin autorización expresa; obtenerla y reservar tiempo antes de crear recursos.
Usar OTRO workspace externo vacío con el mismo backend/variables, prepare y
plan-destroy. Revisar plan, inventario y hashes antes del execute DESTROY ya descrito
(sección 5); no ejecutar ninguno de esos comandos en este incremento.

El alcance debe limitarse al módulo/estado AKS y recursos propios: RG de aplicación,
AKS, VNet/subnet/identidad/rol propios y grupo administrado de nodos con sus recursos.
**Excluir rg-wordle-state, stwordletfgstate7c92d4, contenedor tfstate, blobs/estado y
versiones.** No usar az group delete, borrar RG de nodos por separado, borrar estado,
recursos PG-05/PG-06, ni purgar cuentas/discos ajenos. No usar -auto-approve en un plan
nuevo; el helper ejecuta únicamente el plan guardado y autorizado.

Después, consultar en lectura remanentes: RG/clúster/nodos, discos/PVC/PV/snapshots,
LB/IP y recursos separados facturables. Verificar que el backend y sus protecciones
permanecen; no modificarlo ni eliminar remanentes automáticamente. Cost Management
puede tener retraso: ausencia inmediata de cargo no significa coste cero.

### Presupuesto y condiciones de parada

Subtotal histórico 16/11/2026 para 4 h: 1,77833 USD (dos nodos, dos OS de 64 GiB,
PG SSD de 8 GiB y una IP de salida, con supuestos del informe Gate B). No es precio
actual cotizado ni total garantizado. Un surge de una hora añadía aproximadamente
0,21938 USD de VM+OS; no asumir que no habrá surge durante el ensayo.

Sin cuantificar: LB/reglas/datos, egreso, operaciones de discos/Storage, estado y
versiones/retención, backups, tiempos adicionales, remanentes. Observabilidad local
consume nodos y almacenamiento/red; sin servicio premium añadido, pero no es coste
cero. Azure Free solo elimina cargo de gestión, no recursos consumidos.

Parar y pedir nueva decisión si el total estimado supera 5 USD, aparecen recursos
imprevistos, cambia SKU/servicios/seguridad/cuota/capacidad o se necesita ampliar 4 h.
Si ya existen recursos, conservar evidencia y ejecutar solo la retirada previamente
autorizada; no abandonar recursos facturables ni improvisar cambios. Fallo de retirada:
informar inmediatamente del riesgo de coste y solicitar resolución acotada.


### Release gates (FIN-17-RELEASE-GATES-01, 22/11/2026)

La preparación vigente exige `ci_run` del SHA exacto y siete jobs exitosos antes
del login, selección privada inmutable y OIDC explícito para Terraform. Las
instrucciones anteriores son contexto histórico; para nuevas ejecuciones prevalece
[el contrato de release, custodia durable, emergencia y captura AKS](release-gates.md).
La etiqueta del runner no garantiza persistencia entre runs: el mount externo,
marker y store ID deben estar aprobados antes de habilitar CD. No se han realizado
operaciones remotas ni se ha validado la federación real en esta iteración.
