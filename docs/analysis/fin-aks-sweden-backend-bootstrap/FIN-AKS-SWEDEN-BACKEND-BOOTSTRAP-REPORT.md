# FIN-AKS-SWEDEN-BACKEND-BOOTSTRAP — Wordle TFG

Fecha: **16/11/2026**. **PASS operativo. Gate A GO para el bootstrap configurado y el acceso de listado Entra verificado; AKS NO-GO.**

## 1. Resumen ejecutivo

Se creó **stwordletfgstate7c92d4 en swedencentral**, StorageV2/Standard_LRS/Hot, reutilizando **rg-wordle-state en westeurope** sin modificarlo. Configuración verificada: HTTPS/TLS1.2, anonimato y SharedKey deshabilitados, firewallDeny/None con una única IPv4 administrativa vigente, tfstate privado, rol Storage Blob Data Contributor exclusivamente al operador autorizado sobre ese contenedor, soft delete de blobs/contenedores7d, versioning y lifecycle limitado a versiones anteriores7d del prefijo de estado.

**Lectura/listado real por Entra ID satisfactorio**, contenedor vacío incluso incluyendo versiones/snapshots/borrados. No se escribieron blobs, no se creó estado y no se ejecutó Terraform. No AKS, redes, VM, otro RG/cuenta o roles adicionales. No discrepancia de seguridad pendiente. Gate A GO no autoriza init/lease/plan ni despliegue; esas operaciones no se han probado ni ejecutado.

## 2. Autorización y alcance

Adjunto FIN-AKS-SWEDEN-BACKEND-BOOTSTRAP: autorización expresa para esta cuenta, regiónSweden, RG existenteWest, controles, IP doméstica vigente, operador aprobado y rol al contenedor. Se aceptó conscientemente la incertidumbre de Policy heredada de la fase previa sin autorizar cambios de Policy/exenciones/permisos superiores. No se reintentó creación en West Europe ni se cambió la ficha.

Consultados los informes SwedishBackendPreflight, BackendBootstrap anterior, BootstrapPrep, StorageDenialDiagnosis y EphemeralLifecycle. Se conserva su contenido histórico. La cuotaSweden16/regional26 ya aprobada no se volvió a consultar: no es requisito intrínseco del backend. Único entregable persistente local nuevo: este informe.

## 3. Identidad y suscripción verificadas

Azure CLI mantiene suscripción **11306565…1bb5**, tenant **aff0390f…1eb9**, Enabled. Graph signed-in-user, solo proyección id, verifica operador **b573130a…a831**. Se revalidó inmediatamente antes de la creación y antes del RBAC. No cambio de identidad/suscripción, login, exposición de tokens, claves/SAS o lectura del estado.

La identidad destinataria RBAC es el operador aprobado por los informes y el propietario, no un nombre descriptivo inferido. Se usó --assignee-object-id y principal-type User, sin crear identidades ni grupos.

## 4. Preflight

| Control | Resultado |
|---|---|
| RG destino |rg-wordle-state pertenece a suscripción aprobada, westeurope, Succeeded|
| Recursos previos del RG |0; no objeto inesperado|
| Cuenta previa |ResourceNotFound|
| Nombre global |nameAvailable=true, revalidado antes de crear|
| Provider Storage |Registered; catálogo storageAccounts incluye Sweden|
| SKU |StorageV2/Standard_LRS en swedencentral, restrictions=[]|
| Policy visible RG con herencia solicitada |0 entradas; limitación de visibilidad superior conocida del preflight previo|
| Permisos ARM |GET permissions: entrada actions=* sin notActions; gestión cuenta/red/BlobProperties/lifecycle/contenedor y roleAssignments incluidas|
| Rol de datos |No se confundió actions ARM con dataActions: rolBlob exacto asignado después al contenedor|
| Identidad destinataria |ObjectID coincide con operador autorizado|
| Salida administrativa |IPv4 global confirmada por dos fuentes; señales proxy/VPN sin discrepancias|

No se identificó restricción confirmada Sweden que exigiera parar. La ausencia de Policy visible no se interpretó como garantía; la creación autorizada posterior es la evidencia operativa para esta cuenta concreta. No prueba ausencia de restricciones sobre otros recursos/AKS.

## 5. IPv4 administrativa validada

Dos consultas independientes a api4.ipify.org y checkip.amazonaws.com coincidieron en IPv4 pública global válida, no privada/loopback. Se reconsultó salida antes de añadir regla y volvió a comprobarse contra la regla efectiva en la verificación final, sin publicar dirección.

Variables HTTP_PROXY/HTTPS_PROXY/ALL_PROXY y equivalentes minúsculas ausentes; WinInet ProxyEnable=false, sin AutoConfigURL; cero VPNWindows conectadas según Get-VpnConnection de usuario/allusers. Con contexto doméstico declarado y autorizado por el propietario, no se detectó ruta/proxy/VPN inesperada. Estas señales no son una certificación exhaustiva de todo software de red, pero no hubo discrepancia que impidiera continuar.

Se utilizó IP individual **sin /32** en Storage, no dirección histórica ni rango corporativo. No se modificaron VPN/proxy/rutas/Windows o la red del sistema. Si cambia la salida, puede perderse acceso Blob hasta una actualización de regla expresamente autorizada; no se habilita AllNetworks para recuperarlo.

## 6. Creación de Storage Account

Única creación de cuenta, iniciada **2026-11-16T16:43:02.866137Z**; Azure CLI exit0 y provisioningState **Succeeded**. No creación alternativa/reintento. Comando ejecutado, con suscripción enmascarada:

```text
az storage account create --name stwordletfgstate7c92d4 --resource-group rg-wordle-state --location swedencentral --subscription <aprobada> --kind StorageV2 --sku Standard_LRS --access-tier Hot --https-only true --min-tls-version TLS1_2 --allow-blob-public-access false --allow-shared-key-access false --public-network-access Enabled --default-action Deny --bypass None --tags project=wordle purpose=terraform-state environment=tfg lifecycle=temporary --only-show-errors -o json
```

Se capturó la respuesta y solo se emitieron propiedades no sensibles. La cuenta nació con Deny/None y ceroIPRules: no hubo intervalo de acceso público irrestricto. Se añadió después la única IP administrativa y se verificó antes de las siguientes operaciones. No Private Endpoint ni red auxiliar.

## 7. Región, tipo y SKU

| Propiedad | Verificado |
|---|---|
| Cuenta |stwordletfgstate7c92d4|
| RG |rg-wordle-state, ubicación de metadatos westeurope, reutilizado|
| Ubicación de cuenta |**swedencentral**|
| Tipo/SKU |**StorageV2 / Standard_LRS**, tier Standard|
| Access tier |Hot, solicitado explícitamente|
| Estado |Succeeded|

La cuenta puede estar en distinta región del RG, sin traslado/recreación. No se cambió location de Terraform o del RG. La aceptación de esta creación no generaliza la elegibilidad regional deAKS ni altera sys.blockwesteurope.

## 8. Configuración de seguridad

GET account posterior a creación y final confirma enableHttpsTrafficOnly=true, minimumTlsVersion=TLS1_2, allowBlobPublicAccess=false y allowSharedKeyAccess=false. publicNetworkAccess=Enabled se combina con firewallDeny, **no significa AllNetworks**. Cuenta no utilizada mediante claves ni SAS; nunca se invocó listKeys ni fallback de autenticación.

No legal hold ni política de inmutabilidad en el contenedor; hasImmutabilityPolicy=false y hasLegalHold=false. No se habilitó HNS; API account devolvió isHnsEnabled=null, no se presenta ese null como medición de false. Versioning efectivo true y la creación no solicitó HNS.

## 9. Firewall

Una operación `storage account network-rule add` con la IPv4 vigente validada. Verificación directa account.networkRuleSet:

- defaultAction **Deny**, bypass **None**.
- **Una** ipRule, coincide con IPv4 pública vigente en lectura final.
- Cero reglasIPv6, VNet y resourceAccessRules.
- Sin0.0.0.0/0, rangos corporativos, otraIP o excepciónAzureServices.

No se demuestra un ensayo desde una segunda IP no autorizada; se verifican configuración efectiva y acceso permitido desde la propia. ARM y Blob son planos distintos: las operaciones de gestión se autenticaron por Entra sobreARM, sin depender de abrir firewall de datos.

## 10. Contenedor privado

Creado una sola vez mediante **Azure Resource Manager autenticado con Entra de Azure CLI**:

`az storage container-rm create --storage-account stwordletfgstate7c92d4 --resource-group rg-wordle-state --name tfstate --public-access off --fail-on-exist --subscription <aprobada>`

Es el mecanismo ARM preparado previamente: evita necesitar un rolBlob amplio para crear el contenedor. No usa claves ni SharedKey como autenticación alternativa. GET container-rm show confirma nombretfstate, publicAccess=None, sinWORM/legalhold. Sin blobs iniciales de estado ni datos ajenos. State key **wordle/aks-demo.tfstate** es futura; aún no existe.

## 11. RBAC

Se leyó la definición exacta **Storage Blob Data Contributor**, ID builtin **ba92f5b4-2d11-453d-a403-e96b0029c9fe**. Se comprobó lista de asignaciones del contenedor antes de crear: vacía. Se creó una única asignación:

- Nombre/ID local de asignación: **b1ddae31-38db-4a9f-bc03-cb9c428cbb2f**.
- Principal User: **b573130a…a831**, verificado.
- Rol: Storage Blob Data Contributor.
- Scope exacto sanitizado: `/subscriptions/<aprobada>/resourceGroups/rg-wordle-state/providers/Microsoft.Storage/storageAccounts/stwordletfgstate7c92d4/blobServices/default/containers/tfstate`.
- condition=null; no roles adicionales.

Se verificó respuesta de create y listado posterior: única asignación devuelta, principal/roleDefinition/scope coincidentes. No asignación nueva en cuenta/RG/suscripción, no modificación de asignaciones anteriores. El listado real de datos por login acredita propagación suficiente para lectura; no se prueba mediante escritura ni lease.

## 12. Retención y versionado

Una actualización de BlobServiceProperties, comprobada por GET:

| Propiedad | Resultado |
|---|---|
|isVersioningEnabled|true|
|deleteRetentionPolicy.enabled / days|true /7|
|containerDeleteRetentionPolicy.enabled / days|true /7|
|allowPermanentDelete de blobs|false|

No políticas adicionales de backup/PITR, inmutabilidad, archive o retención bloqueada. Versioning protege cambios; container soft delete complementa el borrado del contenedor. No protege por sí solo una cuenta completa borrada ni sustituye copia privada independiente. Retención y versiones tienen coste potencial.

## 13. Lifecycle management

Una policy `wordle-state-old-versions`, Enabled, Lifecycle, con filtros blockBlob y prefijo **tfstate/wordle/aks-demo.tfstate**. Acción única efectiva: **version.delete.daysAfterCreationGreaterThan=7**. Sin baseBlob, snapshot o acciones de tiering. No borrado de versión actual/contenedor ni inmutabilidad.

Se creó mediante JSON temporal nuevo externo al repositorio, eliminado en finally. GET posterior normaliza campos opcionales a null y7 a7.0; validación semántica confirma exactamente el alcance aprobado, sin repetir ni cambiar la política. La comparación inicial de objetos JSON completos falló por esa normalización, no por regla distinta.

Lifecycle es asíncrono; soft delete puede prolongar retención/coste. El prefijo también puede seleccionar nombres con esa extensión/prefijo: reservado para este estado, no datos de otros proyectos. No se garantiza purga exacta al séptimo día ni conservación de checkpoints históricos hasta defensa sin copia externa. Estado actual no expira por esta política.

## 14. Verificación del plano de datos

Listado real ejecutado con:

`az storage blob list --account-name stwordletfgstate7c92d4 --container-name tfstate --auth-mode login --num-results 1 --only-show-errors -o json`

**Exit0, lista vacía**. Segunda verificación con `--include dsv` (borrados, snapshots y versiones): **exit0, lista vacía**. La enumeración de un máximo de1 que devuelve0 acredita ausencia de objetos enumerables de esos estados; no se escribió ningún blob para probarlo.

Al comprobar las propiedades de cuenta/red en paralelo, finalizó GET a **2026-11-16T16:46:45.866476Z** con controles correctos y coincidencia deIP actual. Los dos listados satisfactorios y la lectura final de lifecycle se realizaron después, durante esta misma sesión. No se inventan timestamps individuales no capturados.

Acceso Entra efectivo confirmado desde salida administrativa autorizada; contenedor privado, SharedKeyfalse y firewallDeny/None permanecen. No ejecución Terraform init ni creación de statefile/blob de prueba/lease. La ausencia de prueba de escritura/lease es deliberada por alcance, no un PASS de esas operaciones futuras.

## 15. Recursos creados

Inventario ARM de rg-wordle-state final: **una cuenta Microsoft.Storage/storageAccounts**, nombre aprobado, ubicaciónSweden. RG previo conservado. Subrecursos/configuraciones autorizados: BlobServiceProperties, management policydefault, contenedortfstate y única asignaciónRBAC al scope del contenedor; reglaIP individual.

No AKS, VM, VNet, nuevoRG, otroStorage, privateendpoint, reservas, alertas o recursos de monitorización. El listado ARM genérico no siempre enumera todos los subrecursos: los anteriores se verificaron separadamente y no se ocultan bajo el conteo de una cuenta. No recursos eliminados automáticamente.

## 16. Costes residuales

Cuenta Standard_LRS/Hot con versioning/softdelete/lifecycle activos, actualmente sin blobs. No se genera coste de nodos/AKS por este incremento; no se afirma que toda la suscripción tenga coste0 ni se consultó facturación ajena.

Referencia oficial Sweden del preflight16/11/2026: **0,0184USD/GB-mes**, write/list **0,050USD/10K**, read/other **0,004USD/10K**. Gestión/listados, operaciones futuras/lifecycle, datos retenidos/versiones y egreso pueden facturar según medidor. No se repitió innecesariamente la cotización ni se supone crédito.

Ejemplo heredado **100MiB efectivos30d +1000writes/list+1000reads/other≈0,007196875USD** es ilustrativo y no máximo. Hoy no hay estado ni ese volumen observado. Antes de operar Terraform: custodiar estado/checkpoints/segunda copia y fecha de defensa/revisión; eliminación de backend requiere autorización independiente y retirada comprobada de sus recursos gestionados. No presupuestos/alertas configurados.

## 17. Incidencias

- Una consulta local de ayuda CLI sin elevación falló al abrir su logfile en el sandbox; no llegó a invocar Azure ni ninguna escritura. Las operaciones autorizadas posteriores usaron el mecanismo de permisos del entorno, sin modificar permisosWindows/configuraciónAzure.
- Tras añadir la IP, el helper esperaba defaultAction en nivel superior de network-rule list y produjo KeyError. Se detuvieron pasos dependientes; GET account directo confirmó Deny/None/IPexacta. No se repitió ni alteró la regla.
- Tras crear lifecycle, comparación JSON exacta falló por camposnull de Azure. Se detuvo antes de contenedor; lectura recuperó regla correcta y validación semántica permitió continuar sin reescribir política.
- Primera enumeración Blob con argumentos separados `--include d s v` no produjo resultado utilizable (READ_FAILED, sin código específico capturado). Listado mínimo correcto y sintaxis combinada `--include dsv` terminaron satisfactoriamente. No se atribuye a faltaRBAC/propagación ni se reconfiguró permiso/firewall para resolverlo.

No rechazo regional, Policy o seguridad en la creaciónSweden. No discrepancia de seguridad real observada. Todas las incidencias locales se resolvieron con lecturas/corrección de interpretación o sintaxis, sin escrituras duplicadas ni cambios de la ficha. No necesidad de recuperación/desmontaje parcial; no se elimina nada.

## 18. Estado de Gate A

**GO para el bootstrap autorizado:** cuenta completa/configurada, redprivada por firewall, contenedorprivado, RBACexacto, protecciones y listado real Entra confirmados. Esto cierra los criterios operativos de esta iteración, no certifica operaciones de escritura/lease/concurrencia Terraform que estaban prohibidas.

**AKS NO-GO.** Continúan otros prerrequisitos (grupoEntra/miembros, API/IP/CIDR externos, versión/surge, presupuesto y autorizacionesplan/despliegue). Cuota aprobada y backendconfigurado no son autorización de gasto/despliegue ni una validación realAKS.

Todos los documentos y archivos pendientes anteriores permanecen intactos por comprobaciónSHA-256; índice y lista de archivos versionados modificados conservados. Solo se crea este informe persistente. Sin staging/commits/push, cambiosTerraform/código/regiónconfigurada, accesoSupabase o actuaciones enNexo. Los JSON temporales fueron eliminados; no scripts auxiliarespersistentes.

## 19. Próxima acción recomendada

Revisar el resultado y autorizar separadamente, si se desea, **validación controlada de escritura/lease del backend** sobre blob de prueba exclusivo y posterior configuración/init, con condiciones de limpieza del blob expresamente aprobadas, sin tocar el estado real. Nada de ello se ejecuta hoy ni se crea estado ficticio. En paralelo, resolver los restantes datos/aprobaciones de GateB sin iniciarAKS automáticamente.

Conservar RG/cuenta/contenedor/rol/protecciones y documentar cualquier cambio posterior deIP bajo autorización; no ampliar red para solventar futuras pérdidas de acceso. Desmontaje o retirada de roles/Storage requieren permiso específico, no quedan autorizados por estePASS. Se detiene la iteración.

Fuentes técnicas consultadas16/11/2026: [creacióncuentaAzureCLI](https://learn.microsoft.com/en-us/cli/azure/storage/account), [container-rm víaARM](https://learn.microsoft.com/en-us/cli/azure/storage/container-rm). Ficha/seguridad, lifecycle y tarifas oficiales detalladas en FIN-AKS-SWEDEN-BACKEND-PREFLIGHT y FIN-AKS-BACKEND-BOOTSTRAP-PREP, conservados. Evidencia primaria son salidas AzureCLI y GET sanitizados documentados arriba.
