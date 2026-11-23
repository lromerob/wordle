# FIN-AKS-BACKEND-BOOTSTRAP-PREP — Wordle — 16/11/2026

**PASS documental; Gate A NO-GO operativo y AKS NO-GO.** Procedimiento preparado para aprobación, no ejecutado. Contexto aportado por el propietario: suscripción personal y PC personal, IP doméstica dinámica, backend temporal hasta defensa. No se vuelve a exigir IP fija como si fuera obligatoria: se exige origen vigente autorizado y recuperación por ARM.

## 1. Ficha definitiva propuesta para aprobación

| Parámetro | Valor propuesto, no aplicado |
|---|---|
| Suscripción/tenant | Destino confirmado `11306565…1bb5` / `aff0390f…1eb9`, Enabled |
| RG/ubicación | rg-wordle-state / westeurope, independiente de AKS y RG nodos |
| Cuenta | **stwordletfgstate7c92d4**, sin datos personales |
| Tipo/replicación/tier | StorageV2 / Standard_LRS / Hot |
| Contenedor/key | tfstate privado / wordle/aks-demo.tfstate |
| Auth | Entra ID, Azure RBAC data-plane, sin claves ni SAS habituales |
| Seguridad | HTTPS, TLS1.2 mínimo, anonimato y Shared Key deshabilitados |
| Red | Endpoint público Enabled, defaultAction Deny, bypass None, solo IPv4 administrativa autorizada |
| Protección | Versioning; blob/container soft delete7d; lifecycle solo versiones previas >7d de la key |
| Custodia | Propietario, carpeta privada externa y segunda copia; fecha de defensa/expiración aún por aprobar |

No Private Endpoint, NAT, cuenta premium, HNS/Data Lake, immutability o cambio a otra arquitectura. Estado actual no se elimina por lifecycle. El bootstrap no crea AKS, grupo Entra o configuración Terraform.

## 2. Nombre y disponibilidad

Nombre de22caracteres, minúsculas/números, dentro del límite3–24. `az storage account check-name --name stwordletfgstate7c92d4 --subscription <destino>` devuelve **nameAvailable=true**, sin razón/error, el16/11/2026. Es una consulta de disponibilidad sin reserva/creación; puede quedar ocupado antes del bootstrap. Repetir inmediatamente antes de crear y detener si no disponible, sin escoger otro nombre o tomar cuenta existente automáticamente.

El RG previsto no existe (group exists=false). No se buscan/reutilizan cuentas ajenas. Si se encuentra RG/cuenta preexistente en la fase futura, detener y revisar inventario/autorización antes de continuar.

## 3. Identidad y permisos

Sesión CLI actual coincide con suscripción/tenant aprobados, Enabled, principal user. Graph signed-in-user consultado solo con proyección id identifica operador `b573130a…a831`; no se publica nombre/email/ID completo. Ese operador es candidato para acceso al estado, **pendiente de aprobación expresa**, no administrador definitivo AKS automático.

La lectura ARM de permissions permite en sus acciones: resourceGroups/write, storageAccounts/write, storageAccounts/blobServices/write, storageAccounts/blobServices/containers/write y roleAssignments/write. Esto acredita acciones devueltas, no ausencia de deny/condiciones/Policy o éxito de creación. dataActions devueltas vacías: **no hay acceso Blob acreditado al contenedor futuro**. No se asigna ningún rol hoy.

Bootstrap necesita gestión del RG/cuenta, propiedades Blob/lifecycle/firewall/contenedor y asignación del rol, con lecturas correspondientes. Para lifecycle se requiere storageAccounts/managementPolicies/write; la entrada ARM amplia previa permite razonar que figura incluida, pero no se comprueba mediante escritura. No exigir Owner si un rol/ámbito delegado autorizado basta. El operador futuro puede requerir administrador para asignar roles si aparece una denegación; no elevar privilegios automáticamente.

Acceso habitual mínimo: **Storage Blob Data Contributor sobre el contenedor tfstate**, no toda la suscripción. Contenedor se crea por ARM antes de asignar rol scoped, evitando dar permiso de datos sobre toda la cuenta solo para crearlo. El rol cubre operaciones de blob/lease de Terraform; Reader adicional en cuenta solo si backend usa lookup_blob_endpoint. No habilitar Shared Key para resolver un403. No necesita grupo adminAKS para bootstrap; Entra autentica usuario y ARM gestiona seguridad, Kubernetes RBAC es otra fase.

## 4. IP doméstica dinámica: procedimiento y recuperación

1. Desde el PC y ruta exacta que usará Azure CLI/Terraform, comprobar IPv4 pública con servicio sin credenciales (por ejemplo api4.ipify.org); validar IPv4 global y contrastar ruta/VPN/proxy con propietario. No se consulta de nuevo hoy una IP que seguiría sin aprobación.
2. Propietario autoriza esa dirección individual para Storage; queda vigente solo mientras sea su salida real. No garantía de estabilidad por observarla dos veces.
3. Azure Storage usa **IP individual sin /32** para un solo host: reglas CIDR /31 y /32 no se admiten. AKS usa authorized_ip_ranges con el CIDR /32. No reutilizar literalmente el comando de uno en el otro.
4. Crear cuenta con Deny, luego añadir IP; validar metadatos/reglas y lectura Entra antes de operar estado. No fase temporal Allow a todoInternet. PublicNetworkAccess Enabled es necesario para el endpoint con firewall; no equivale a AllNetworks autorizado.
5. Si cambia la IP, detener Terraform/estado; confirmar nueva salida y autorización. Con permisos ARM, añadir IP nueva usando network-rule add, probar data-plane Entra y retirar exclusivamente la IP anterior propia con network-rule remove. Mantener ambas solo durante recuperación acotada aprobada; no acumular accesos obsoletos.
6. Firewall Storage restringe data-plane, no management.azure.com: ARM permite reparar la regla desde la nueva IP si autenticación/rol/red de gestión siguen funcionando. Si hay deny/política/NSP o accesoARM falla, detener y pedir intervención del administrador autorizado. No llamar account keys/SAS ni cambiar defaultAction Allow.

Esta recuperación debe incluirse en autorización futura de reglas propias/IP dinámica; hoy no se modifica ninguna. Antes de cada ventana: cuenta/tenant, ruta/IP, firewall, Entra/RBAC y endpoint correctos; actualizar autorizaciones primero. El APIAKS tiene su lista independiente y no se cambia por reparar Storage.

Fuentes: [límites firewall e IPindividual](https://learn.microsoft.com/en-us/azure/storage/common/storage-network-security-limitations), [planos de control/datos](https://learn.microsoft.com/en-us/azure/azure-resource-manager/management/control-plane-and-data-plane).

## 5. Seguridad y retención

Soft delete de blobs y contenedores7d permite recuperación acotada de borrados; versioning protege sobrescrituras. Política concreta propuesta: **borrar solo versiones previas mayores de7d** para prefijo tfstate/wordle/aks-demo.tfstate. No acción baseBlob/delete, no snapshots genéricos, no expiry de la versión actual. El prefijo selecciona ese nombre y posibles extensiones; reservarlo exclusivamente para esta key, sin blobs ajenos. Lifecycle es asíncrono; soft delete puede prolongar almacenamiento tras la acción, así que no prometer purgaexacta en7d o14d. La edad es de creación de la versión, no necesariamente tiempo desde que dejó de ser actual.

Fragmento de policyJSON para futura creación en carpeta privada (no se crea hoy):

```json
{"rules":[{"enabled":true,"name":"wordle-state-old-versions","type":"Lifecycle","definition":{"filters":{"blobTypes":["blockBlob"],"prefixMatch":["tfstate/wordle/aks-demo.tfstate"]},"actions":{"version":{"delete":{"daysAfterCreationGreaterThan":7}}}}}]}
```

Conservar estado actual mientras haya recursos gestionados y hasta comprobar retirada/defensa. Copia privada de checkpoints importantes y hashes antes de cambios: no depender de que versions>7d sobrevivan hasta la defensa. Sin WORM/retenciones bloqueadas, archive tier ni legal hold que impidan operaciones del estado. No se activa PITR/changefeed innecesario.

Lease nativo azurerm evita escrituras concurrentes; propagación RBAC y lease no probados. No force-unlock por rutina: verificar proceso/propietario del lock y pedir autorización especial si es huérfano. No crear o borrar el stateblob para probar acceso en este incremento.

Fuentes: [backendEntra/lease](https://developer.hashicorp.com/terraform/language/backend/azurerm), [lifecycle](https://learn.microsoft.com/en-us/azure/storage/blobs/lifecycle-management-policy-delete), [protecciónBlob](https://learn.microsoft.com/en-us/azure/storage/blobs/data-protection-overview).

## 6. Coste residual

Retail API oficial reconsultada16/11/2026: westeurope, General Block Blob v2, Hot LRS, USD Consumption primer tier: **0.0196 USD/GB-mes**. Write/list/createcontainer **0.054 USD/10K**; read/other **0.0043 USD/10K**. Versiones y soft-deleted siguen sumando capacidad; operaciones lifecycle también pueden generar costes. No base fija de cuenta/RG declarada como VM o LB.

Fórmula: capacidad media efectiva GB (estado+versiones+borradosretenidos) ×0.0196×días/30 +0.054×write/list/10000 +0.0043×read/other/10000 + otros medidores aplicables. El ejemplo usa30d, no factura exacta de cualquier mes. Egreso/recuperación y medidores concretos no estimados no se consideran cero.

Ejemplos sintéticos de30d, no tamaño medido:

-100MiB efectivos incluyendo versiones +1000writes/list +1000reads/other: capacidad0.001914+ops0.00583 ≈**0.00774 USD**.
-1GB efectivo +10000writes/list +10000reads/other:0.0196+0.054+0.0043 =**0.0779 USD**.

No son cota ni presupuesto definitivo; versiones numerosas, sesiones adicionales y retenciones aumentan consumo. No incluyen AKS/discos/LB porque se estima solo backend. Aprobar duración máxima hasta defensa y revisión mensual; fecha exacta aún no indicada. Tras defensa, confirmarAKS/destrucción/remanentes, exportar copia privada aprobada y aprobar eliminación definitiva de cuenta/contenedor/versiones/roles propios. **Nunca eliminar estado antes de verificar eliminación de sus recursos gestionados**. Softdelete y facturación tienen latencia; verificar inventario/cargos y retención real, no garantizar coste0 inmediato.

Fuentes: [RetailAPI](https://prices.azure.com/api/retail/prices), [preciosBlob](https://azure.microsoft.com/en-us/pricing/details/storage/blobs/).

## 7. Secuencia futura de bootstrap — NO EJECUTADA

Aprobar antes la ficha, operador porID, IP, coste/retención y cambios de rol/red. Variables ApprovedSubscription/ApprovedTenant/ApprovedOperatorId se aportan externamente sin credenciales; no incluir sus valores completos en el informe. PublicIPv4 es dirección observada y aprobada en esa sesión; PolicyFile es JSON anterior en carpeta privada. Cada fase requiere comprobar salida/estado y parar al fallar, sin reintentar escrituras ciegamente.

ComandosPowerShell futuros, solo documentación:

```powershell
function Invoke-WordleAz { & az @args; if ($LASTEXITCODE -ne 0) { throw 'Azure falló; detener y revisar' } }
$Rg='rg-wordle-state'; $Account='stwordletfgstate7c92d4'
$Context = Invoke-WordleAz account show --output json | ConvertFrom-Json
if ($Context.id -ne $ApprovedSubscription -or $Context.tenantId -ne $ApprovedTenant -or $Context.state -ne 'Enabled') { throw 'Destino incorrecto' }
$Who = Invoke-WordleAz ad signed-in-user show --query id --output tsv
if ($Who -ne $ApprovedOperatorId) { throw 'Operador no aprobado' }
$ObservedIPv4 = (Invoke-RestMethod 'https://api4.ipify.org').ToString().Trim()
# Validar IPv4global y ruta, obtener aprobación; no asignar PublicIPv4 sin ese gate.
if ($PublicIPv4 -ne $ObservedIPv4) { throw 'Salida distinta de aprobada' }
$Available=Invoke-WordleAz storage account check-name --name $Account --subscription $ApprovedSubscription --output json | ConvertFrom-Json
if (-not $Available.nameAvailable) { throw 'Nombre no disponible' }
$Exists=Invoke-WordleAz group exists --name $Rg --subscription $ApprovedSubscription --output tsv
if ($Exists -eq 'true') { throw 'RG existente: inspeccionar, no sobrescribir' }
# GATE CREACIÓN: autorizaciónbackend concreta, noAKS/Terraform.
Invoke-WordleAz group create --name $Rg --location westeurope --subscription $ApprovedSubscription --tags project=wordle lifecycle=temporary-state --output none
Invoke-WordleAz storage account create --name $Account --resource-group $Rg --location westeurope --subscription $ApprovedSubscription --kind StorageV2 --sku Standard_LRS --access-tier Hot --https-only true --min-tls-version TLS1_2 --allow-blob-public-access false --allow-shared-key-access false --public-network-access Enabled --default-action Deny --bypass None --tags project=wordle lifecycle=temporary-state --output none
# Seguridad de control-plane antes de acceder a datos.
Invoke-WordleAz storage account blob-service-properties update --account-name $Account --resource-group $Rg --subscription $ApprovedSubscription --enable-versioning true --enable-delete-retention true --delete-retention-days 7 --enable-container-delete-retention true --container-delete-retention-days 7 --output none
Invoke-WordleAz storage account network-rule add --account-name $Account --resource-group $Rg --subscription $ApprovedSubscription --ip-address $PublicIPv4 --output none
Invoke-WordleAz storage account management-policy create --account-name $Account --resource-group $Rg --subscription $ApprovedSubscription --policy "@$PolicyFile" --output none
# ARM crea contenedor antes de RBACacotado; no necesita permisosBlob globales.
Invoke-WordleAz storage container-rm create --storage-account $Account --resource-group $Rg --subscription $ApprovedSubscription --name tfstate --public-access off --output none
$ContainerScope="/subscriptions/$ApprovedSubscription/resourceGroups/$Rg/providers/Microsoft.Storage/storageAccounts/$Account/blobServices/default/containers/tfstate"
# GATE RBAC: identidad/ámbito exactos autorizados, no grupoAKS ni rol en suscripción.
Invoke-WordleAz role assignment create --assignee-object-id $ApprovedOperatorId --assignee-principal-type User --role 'Storage Blob Data Contributor' --scope $ContainerScope --subscription $ApprovedSubscription --output none
# Esperar propagación y comprobar metadatos, no crear otra asignación ante403.
Invoke-WordleAz storage blob list --account-name $Account --container-name tfstate --auth-mode login --num-results 1 --query 'length(@)' --output tsv
```

Estos fragmentos no se ejecutan hoy ni crean script adicional. Comprobar sintaxis compatible con CLI instalada antes de la futura fase si hay cambios de versión. Para validación final usar account show, blob-service-properties show, network-rule list, container-rm show, management-policy show y role assignment list en el scope preciso, capturando solo metadatos sin claves. Se espera Deny/None, IP propia, TLS/HTTPS, SharedKey/anonfalse, softdelete7d/versioning/policy y contenedor privado. Listado Entra prueba lectura, **no escritura/lease**; su ensayo controlado sobre blob de prueba no state requiere autorización específica posterior, igual que terraforminit. No llamar init para terminar este bootstrap.

RBAC suele tardar minutos; si acceso falla, esperar y releer dentro de plazo acordado (p.ej. hasta30min propuestos, no SLA), sin repetir creación/assignment. El firewall y el RBAC son puertas distintas; ni crearcontainerporARM prueba data-plane ni tener rol elimina requisitoIP.

## 8. Validaciones, recuperación y rollback propuestos

| Punto | Validación futura | Si falla |
|---|---|---|
| Preflight/nombre | DestinoID,IP,ruta,ausenciaRG,nombreavailable | No crear nada; volver a aprobación si cambia nombre |
| RG/cuenta | IDs/ubicación/tags ySKU/propiedades esperadas | Registrar qué se creó; no tomar otroRG ni borrar automáticamente |
| Firewall/TLS | Deny/None, IP individual autorizada, HTTPS/TLS | Reparar solo regla propia porARM con permiso; nuncaAllowAll/SharedKey |
| Contenedor/RBAC | Private yscope individual, identidad exacta |403: distinguir ARM/Graph/data-plane/red ypropagación; no elevarrol |
| ListadoBlob | Login Entra correcto ysin exponer contenido | Validar endpoint/red/contexto del token, parar tras el plazo; no SAS |
| Lease/escritura | No probados enesta fase | Gateposterior autorizado yblob de prueba, nunca estado falso |
| Bootstrap parcial | Inventario propio guardado ysin estado gestionado previo | No repetir creación global; continuar/revertir solo acciones autorizadas |

Ante cambioIP: validar/autorizar nueva; añadir regla, comprobar Blob con Entra, removerregla antigua propia. La recuperación por ARM no depende del firewall Blob, pero sí conectividad ARM/roles/tenant. No modificarlas IP autorizadas de AKS indirectamente.

Rollback no automático: si falló bootstrap antes de estado y los recursos son exclusivamente nuevos de esta ejecución, se pueden **proponer** retirar roleAssignment, policy/container/account/RG propios mediante autorización posterior y orden inverso. Nunca eliminar RG si contiene algo ajeno oestado con recursos gestionados. Conservar evidencia/IDs privados de cada creación. Una vez usado el backend, destrucción deAKS/state debe seguir lifecycle documentado, no rollback del bootstrap.

Confirmar costes residuales con lecturas ARM propias, estado de cuenta/discos/red según alcance y Cost Management con latencia; retirar rol no elimina Storage/coste. No borrar cuentas por nombre coincidente yno crear alertas/locks destructivos nuevos sin permiso.

## 9. Decisiones pendientes

Aprobar ficha exacta y nombre; ID del operador y rol al contenedor; IPv4 vigente, ruta y autorización de cambio; responsable de custodia y fecha de defensa; softdelete7d/versioning/lifecycle7d y coste/retención; forma de documentación externa de IDs/receipts. Ausencia de permisos efectivos data-plane todavía por resolver con rol futuro autorizado. Las accionesARM observadas no autorizan usarlas ahora.

No son gates de bootstrap: grupoAKS, parche Kubernetes o CIDR pods. Sí son gates posteriores AKS y no se dan por cerrados. El grupo admin AKS sigue pendiente; backend no confiere administración del clúster.

## 10. Checklist de autorización futura

- [ ] Nombre/contexto/límites de almacenamiento y oferta sin conflicto revalidados.
- [ ] Aprobar RG/cuenta/contenedor/propiedades/lifecycle exactos y salidaIPv4individual.
- [ ] Aprobar operador y Storage Blob Data Contributor solo en contenedor; capacidad de asignar roles comprobada.
- [ ] Aprobar retención/fecha/coste, custodia privada y procedimiento de IP dinámica.
- [ ] Autorizar únicamente bootstrap, sin AKS/grupo Entra/Terraform ni lectura de estado existente.
- [ ] Acordar plazo/criterios de parada, recuperación IP y tratamiento de fallo parcial.
- [ ] Cualquier prueba de escritura/lease/init o eliminación queda fuera y requiere aprobación posterior.

## 11. Próxima operación recomendada

Con la ficha aceptada, autorizar bootstrap acotado de rg-wordle-state/stwordletfgstate7c92d4/tfstate, seguridad/red/retención y asignación al operador exacto, después de reconfirmar IPv4. **Hoy no se solicita aprobación de apply ni GO para AKS.** Detenerse y esperar autorización.

Fuentes de comandos: [cuentaCLI](https://learn.microsoft.com/en-us/cli/azure/storage/account), [container-rm](https://learn.microsoft.com/en-us/cli/azure/storage/container-rm), [propiedadesBlob](https://learn.microsoft.com/en-us/cli/azure/storage/account/blob-service-properties), [RBACestado](https://developer.hashicorp.com/terraform/language/backend/azurerm).

Alcance efectivo: consultas de contexto, nombre/Graph del ID propio/permisos ARM/RG y tarifas públicas; check-name es consulta, no reserva. Solo se crea este informe, sin scripts/configuración adicionales. Archivos previos preservados por SHA-256. Sin recursosAzure,firewall/RBAC,Terraform,commits/push o staging. AKS NO-GO.
