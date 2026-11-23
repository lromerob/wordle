# FIN-AKS-SWEDEN-BACKEND-PREFLIGHT — Wordle TFG

Fecha: **16/11/2026**. **PARTIAL diagnóstico; viabilidad del backend CONDITIONAL. Gate A y AKS NO-GO.**

## 1. Resumen ejecutivo

Sweden Central publica **StorageV2/Standard_LRS con restrictions=[]** y controles compatibles con la ficha de seguridad. Microsoft.Storage está Registered. El nombre **stwordletfgstate7c92d4 está disponible** y la cuenta anterior sigue ResourceNotFound. **rg-wordle-state existe en westeurope, Succeeded y vacío**.

No se detectó un deny para Sweden en los ámbitos legibles, pero listar asignaciones del management group heredado devuelve **AuthorizationFailed**. No puede garantizarse admisión de creación: catálogo, nombre disponible y permisos ARM no descartan una restricción superior comparable al rechazo previo. No se realiza prueba de creación ni se cambia Policy/RBAC.

Se recomienda **reutilizar rg-wordle-state**, con futura cuenta explícitamente en swedencentral, previa autorización. La ubicación del RG es metadato y no obliga a ubicar sus recursos en West Europe. Crear otro RG no demuestra que se elimine una restricción heredada y añade gestión sin necesidad acreditada.

Comprobación secundaria única de cuota: solicitud **a810bf18-9c0e-498d-8e11-9cc1b7f1c45a Succeeded**; familia DSv5 **16**, regional **26**, consumo0 en ambas. Ajuste automático confirmado10→26. No desbloquea por sí solo backend/AKS.

## 2. Contexto y alcance

Se consultaron los informes FIN-AKS-STORAGE-DENIAL-DIAGNOSIS, FIN-AKS-BACKEND-BOOTSTRAP, FIN-AKS-BACKEND-BOOTSTRAP-PREP, FIN-AKS-REGION-SELECTION y FIN-AKS-SWEDEN-QUOTA-REQUEST. Se conserva la cronología: el último informe de solicitud decía PENDING con observación15:22:49UTC; la lectura actual posterior acredita conclusión sin reescribirlo.

Evaluación de lectura de backend separado para AKS temporal Wordle. No creación de Storage/RG, bootstrap, Terraform, cambio de región configurada, cuotas, permisos/proveedores, soporte o scripts persistentes. No consulta de IP pública actual, secretos, claves, estado Terraform o recursos de otros proyectos. Único archivo nuevo: este informe.

## 3. Identidad y suscripción verificadas

Antes de las lecturas: suscripción **11306565…1bb5**, tenant **aff0390f…1eb9**, Enabled; operador Graph propio **b573130a…a831**, todos coincidentes con la referencia aprobada. No cambio de contexto/login ni difusión de IDs personales completos.

GET permissions de suscripción devuelve una entrada actions=* sin notActions, dataActions vacías. Las acciones devueltas cubren gestión Storage/RG/propiedades/contenedor/lifecycle y roleAssignments; no se ejercen. No equivalen a acceso de datos Blob ni garantizan éxito frente a Policy/deny. No se certifica un rol nominal o pertenencia administrativa nueva.

## 4. Restricciones regionales y Azure Policy

Lecturas actuales aproximadas15:26:47–15:26:48UTC:

| Comprobación | Resultado | Interpretación |
|---|---|---|
| Policy assignments suscripción, disable-scope-strict-match |0 entradas|Ausencia de restricciones visibles en esa respuesta; no prueba de inexistencia heredada|
| Policy assignments rg-wordle-state, mismo modo |0 entradas|Sin deny visible en ámbito legible, misma limitación|
| Listado assignments management group asociado al tenant, conocido por evento previo |AuthorizationFailed|Visibilidad superior incompleta; no elevar permisos|
| GET definición7509877f-d414-4d79-8d1f-d600ea78d087 |Éxito, BuiltIn1.0.0, modo Indexed|Regla confirmada: if location=westeurope then deny|
| Storage SKU Sweden |StorageV2/Standard_LRS restrictions=[]|No restricción de catálogo publicada para esa combinación; no admisión operativa|

La asignación heredada **sys.blockwesteurope** está confirmada causalmente en FIN-AKS-STORAGE-DENIAL-DIAGNOSIS por evento correlacionado al Storage write fallido, correlación2b97ec26-36cf-42c0-ad62-1a2411032364. La definición reconsultada hoy sigue negando location=westeurope, no location=swedencentral. **No se infiere que exista sys.blockswedencentral ni que no pueda haber otra restricción no visible.** No se inventan nombres de políticas ni se crean recursos para detectar denies.

No se recuperaron otras asignaciones/definiciones aplicables que impongan SKU, tipo o ubicación a Sweden; no es posible descartar de forma exhaustiva condiciones superiores/de plataforma/oferta. No se afirma que el permiso ARM o catálogo liberen a la suscripción de todas ellas. Esta limitación justifica PARTIAL/CONDITIONAL, no un NO-GO por bloqueo Sweden confirmado ni un GO garantizado.

## 5. Disponibilidad de StorageV2 y Standard_LRS

GET del proveedor Microsoft.Storage api-version2021-04-01: **Registered**; resourceTypes storageAccounts y storageAccounts/blobServices incluyen Sweden Central. GET de skus api-version2023-05-01: fila exacta name=Standard_LRS, kind=StorageV2, resourceType=storageAccounts, locations=[swedencentral], **restrictions=[]**, sin nextLink. Capacidades publicadas true: supportsnetworkacls, supportsBlobContainerRetention, supportsLcmVersionAndSnapshotActions, supportsmanagementpolicy, supportsIdentities. No se extrapola capacidad de otros países a Sweden.

Compatibilidad documentada de la ficha futura, no configuración efectiva aplicada:

| Parámetro | Objetivo / evaluación |
|---|---|
| Cuenta |StorageV2, Standard_LRS, Hot; soportado en catálogo Sweden|
| Ubicación |swedencentral explícita al crear; no heredar ubicación RG|
| Contenedor/key |tfstate privado / wordle/aks-demo.tfstate|
| Transporte |HTTPS obligatorio, minimumTlsVersion TLS1_2, compatible|
| Anónimo |allowBlobPublicAccess=false y contenedor publicAccess off|
| Autenticación |Entra para datos, SharedKey deshabilitada; sin claves/SAS|
| Red |Endpoint público Enabled con defaultAction Deny, bypass None e IP administrativa individual autorizada|
| Protección |Blob/container soft delete7d + versioning; sin HNS para preservar compatibilidad de versionado|

La existencia del catálogo no es aprobación de creación para nuevos clientes. Ninguna característica está activada porque la cuenta no existe. Prerrequisitos futuros: identidad/contexto aprobados, nombre disponible, región/RG aprobados, permisos ARM y datos, red y custodia/retención; los recursos deben verificarse tras creación autorizada.

Fuentes: [tipos Storage/LRS](https://learn.microsoft.com/en-us/azure/storage/common/storage-account-overview), [TLS mínimo](https://learn.microsoft.com/en-us/azure/storage/common/transport-layer-security-configure-minimum-version), [SharedKey y Entra](https://learn.microsoft.com/en-us/azure/storage/common/shared-key-authorization-prevent).

## 6. Disponibilidad del nombre

`az storage account check-name --name stwordletfgstate7c92d4`: **nameAvailable=true**, reason/message null; consulta iniciada **2026-11-16T15:26:45.873677Z**. Operación de comprobación no mutativa; no reserva nombre aunque el método HTTP interno de la API de disponibilidad pueda ser POST.

`storage account show -g rg-wordle-state -n stwordletfgstate7c92d4`: **ResourceNotFound**. No cuenta previa accesible en el destino; con nombre global disponible no hace falta buscar otras suscripciones o proponer alternativas. La disponibilidad puede cambiar; reconsultar justo antes de un futuro bootstrap. Si cambia, detener y pedir aprobación de otro nombre, no elegirlo automáticamente.

## 7. Evaluación del Resource Group

group show actual: **rg-wordle-state / westeurope / provisioningState Succeeded**. resource list del RG devuelve **0 recursos**. No se modifican tags, metadatos, locks, permisos o ubicación, ni se elimina.

| Alternativa | Ventajas | Inconvenientes / límites |
|---|---|---|
|A: reutilizar rg-wordle-state|Un RG de estado ya creado y exclusivo; menos objetos/pasos; mismos nombres/procedimiento y limpieza futura simple; permite Storage Sweden dentro de RG West|Ubicaciones distintas deben quedar explícitas; disponibilidad del metadato RG depende de su región; requiere autorización específica de reutilización y adaptar la guarda que antes exigía RG ausente|
|B: nuevo RG Sweden|Coherencia visual de ubicaciones y separación administrativa clara|Nueva creación/autorización/nombre; quedan dos RG, uno vacío que debe conservarse; no elimina Policy heredada ni demuestra elegibilidad; más pasos de custodia/limpieza|

**Recomendada A** para el TFG. La ubicación RG no determina la ubicación de cada recurso. La regla conocida compara ubicación del recurso; no se demuestra que una cuenta Sweden incumpla por estar dentro de RG West. Esto es interpretación de la regla recuperada, no simulación ni prueba de creación. Otra Policy podría imponer ubicación igual al RG, pero no se ha identificado una aplicable con la visibilidad disponible.

RG como contenedor administrativo no requiere capacidad de almacenamiento contratada ni genera cargo propio como VM; la cuenta y sus operaciones sí. B no ofrece ahorro material acreditado ni seguridad adicional frente a deny superior. Conservar el RG existente también si el propietario elige B; su eliminación requeriría autorización separada.

[Metadatos del RG y recursos en distintas regiones](https://learn.microsoft.com/en-us/azure/azure-resource-manager/management/manage-resource-groups-portal).

## 8. Red e identidad

El backend azurerm soporta Entra y Azure CLI; **Storage Blob Data Contributor solo sobre tfstate** es el ámbito recomendado para datos/lease. Crear el contenedor por ARM antes de asignar el rol evita conceder inicialmente permiso Blob a toda la cuenta. Reader sobre la cuenta solo si la configuración exige lookup_blob_endpoint; no claves ni fallback a listKeys/SharedKey para resolver errores.

Permisos ARM de gestionar cuenta/firewall/retención/roles son distintos de data-plane Blob. La respuesta actual de permissions tiene dataActions vacías; no prueba un acceso efectivo al contenedor futuro, que aún no existe. El rol al operador exacto y scope debe autorizarse antes de asignarlo; propagación RBAC, listado Entra y posterior escritura/lease permanecen sin probar. No se crean roles o identidades nuevas.

Desde el PC personal con IPv4 doméstica dinámica es viable el patrón de IP individual vigente, Entra y firewall Deny. No hace falta consultar ni publicar hoy la IP. Antes de crear, verificar salida real/ruta y obtener aprobación de la dirección. Storage utiliza IP individual sin /32 (CIDR/31 y/32 no admitidos); el /32 del APIAKS es otra configuración. Si cambia: detener acceso al estado, confirmar/autorizar nueva IP, añadirla por ARM, verificar datos Entra y retirar exclusivamente la IP propia anterior. No usar AllowAll ni ampliar rangos automáticamente.

Firewall Storage restringe data-plane, no control-plane ARM; eso permite reparar reglas propias mediante ARM con permisos y autorización, pero no garantiza acceso si hay otras restricciones. El patrón es para estación externa; reglas IP no deben extrapolarse a un futuro runner alojado en la misma región Azure. No añadir Private Endpoint/NAT/runner/VPN sin necesidad y aprobación.

Fuentes: [backend azurerm y roles](https://developer.hashicorp.com/terraform/language/backend/azurerm), [firewall, límites y planos](https://learn.microsoft.com/en-us/azure/storage/common/storage-network-security-limitations).

## 9. Protección y retención

Objetivo compatible: **blob soft delete7d**, **container soft delete7d**, **blob versioning** en StorageV2 sin HNS. Complementarios: versionado conserva cambios; container soft delete cubre borrado del contenedor; ninguno garantiza recuperar cuenta completa borrada. LRS no es backup independiente ni HA geográfica.

Política propuesta previamente: expirar **solo versiones anteriores mayores de7d** mediante actions.version.delete.daysAfterCreationGreaterThan=7 y prefijo tfstate/wordle/aks-demo.tfstate. Sin acción baseBlob/delete sobre estado actual; el prefijo puede incluir extensiones, por lo que debe reservarse a ese estado. Sin retención inmutable/WORM/legal hold que impida Terraform. La inmutabilidad intrínseca de una versión histórica no se confunde con una política WORM sobre el estado actual.

Lifecycle es asíncrono y soft delete puede prolongar almacenamiento tras la eliminación; no prometer purga exacta al séptimo día. La edad se basa en creación de versión, no tiempo desde que dejó de ser actual. Riesgo: versiones necesarias para reconstrucción pueden expirar antes de la defensa; custodiar checkpoints/segunda copia privada con fecha/responsable aprobados. Conservar estado actual hasta comprobar retirada de todos los recursos gestionados. No habilitar ni modificar nada hoy.

Fuentes: [versioning y soporte](https://learn.microsoft.com/en-us/azure/storage/blobs/versioning-overview), [blob soft delete](https://learn.microsoft.com/en-us/azure/storage/blobs/soft-delete-blob-overview), [container soft delete](https://learn.microsoft.com/en-us/azure/storage/blobs/soft-delete-container-overview), [lifecycle de versiones](https://learn.microsoft.com/en-us/azure/storage/blobs/lifecycle-management-policy-delete).

## 10. Coste estimado del backend

Retail Prices API oficial reconsultada16/11/2026: swedencentral, General Block Blob v2, Hot LRS, Consumption, USD, tierMinimumUnits0, sin descuentos/créditos/impuestos. Sin nextLink. Medidores y effectiveStartDate2021-06-08 en respuesta:

| Concepto | Tarifa |
|---|---:|
|Hot LRS Data Stored|0,0184USD/GB-mes|
|Hot LRS Write Operations|0,050USD/10K|
|LRS List and Create Container Operations|0,050USD/10K|
|Hot Read Operations / All Other Operations|0,004USD/10K|

Fórmula orientativa: GB medios efectivos (actual + versiones + borrados retenidos) ×0,0184×días/30 + write/list×0,050/10000 + read/other×0,004/10000 + otros medidores aplicables. Mes30d para ejemplos, no factura exacta.

- **100MiB efectivos durante30d**: capacidad0,001796875USD;1000writes/list +1000reads/other: operaciones0,0054USD; **subtotal0,007196875USD**.
- **1GB efectivo durante30d**: capacidad0,0184USD;10000writes/list +10000reads/other: operaciones0,054USD; **subtotal0,0724USD**.

Son hipótesis de tamaño total incluidas versiones, no tamaño medido ni techo de gasto. Retención larga, versiones numerosas, lifecycle/otros medidores, egreso o recuperación aumentan el total. Cada mes entre sesiones sigue facturándose capacidad retenida; no basta borrarAKS. No se añaden VM/LB/discos al coste específico de este backend ni se repite economía AKS.

Conservar temporalmente hasta defensa con custodio, revisión y fecha aprobados. Eliminación final de cuenta/versiones/estado requiere aprobación independiente y certeza de que no quedan recursos gestionados. No configurar presupuestos/alertas ni afirmar coste0 por ser académico.

[API oficial de precios](https://prices.azure.com/api/retail/prices). Filtro reproducible: armRegionName='swedencentral', priceType='Consumption', productName='General Block Blob v2', skuName='Hot LRS'; seleccionar los medidores y tier0 indicados.

## 11. Estado de la solicitud de cuota

**Una sola lectura del seguimiento**, iniciada **2026-11-16T15:26:49.133465Z** (sin polling ni reconsulta del ID): a810bf18-9c0e-498d-8e11-9cc1b7f1c45a → **Succeeded**, mensaje **Request completed.**, tanto general como subsolicitud; límite solicitado16, nombre devuelto STANDARDDSV5FAMILY. requestSubmitTime2026-11-16T15:20:19Z; la hora exacta de aprobación no se devuelve y no se inventa.

Compute Usage independiente, consulta iniciada **15:26:49.333105UTC**, confirma:

|Cuota|Límite previo documentado|Límite actual|Consumo|Disponible|
|---|---:|---:|---:|---:|
|DSv5|0|**16**|0|**16**|
|Regional cores|10|**26**|0|**26**|

**APPROVED** y suficiente aritméticamente para12vCPU en ambos límites. Ajuste automático regional **10→26** observado, sin petición regional independiente. No nueva solicitud ni modificación de la existente. No se modifica el informe histórico PENDING: esta evidencia posterior lo complementa.

La cuota AKS no es requisito técnico para crear Storage, ni su aprobación valida Storage/Policy/capacidad física. El objetivo principal de esta iteración sigue siendo backend.

## 12. Riesgos e incertidumbres

- **Confirmado:** bloqueo previo StorageWestEurope por Policy; no cuenta creada. La definición conocida sigue aplicando a location=westeurope.
- **Sin restricción visible Sweden:** SKU Storage sin restricciones y sin assignments devueltos en ámbitos legibles. No es ausencia exhaustiva de deny.
- **No verificable:** assignments superiores por AuthorizationFailed, elegibilidad efectiva de creación/oferta/capacidad, éxito con controles combinados.
- **Pendiente operativo:** acceso Blob Entra, firewall real, RBAC/propagación, protección aplicada y lease/escritura. ARM y catálogo no son esas pruebas.
- **Pendiente propietario:** región final del backend, reutilizaciónRG, identidad/scopeBlob, IP vigente, custodia/fecha/retención y presupuesto. No hay autorización implícita por cuota aprobada.
- Nombre disponible no reservado; revalidar antes de creación. Si falla creación futura, registrar error y detener, sin probar otra región/nombre o relajar seguridad.

No se demuestra inexistencia de restricciones por tipo/SKU/oferta superiores; no se diagnostica un bloqueo Sweden que Azure no haya devuelto. No se necesita ampliar roles por rutina para obtener una falsa certeza de lectura.

## 13. Recomendación de región y Resource Group

**Región: Sweden Central. RG recomendado: rg-wordle-state existente, sin cambiar su ubicación West Europe**, con location=swedencentral explícita para Storage. Mantiene separación del backend respecto a los RG efímeros AKS y reduce objetos. No se vuelve a ejecutar group create sobre el RG existente ni se usa la guarda histórica de ausencia sin adaptación autorizada.

No se propone recrear el RG como supuesto remedio de Policy. Si el propietario prefiere uniformidad regional, B es válida como diseño, pero requiere aprobar un nombre/RG nuevo y conservar el anterior; no elimina la incertidumbre heredada. No modificación de configuración local hoy.

## 14. Estado de viabilidad del backend

**CONDITIONAL**. Configuración y catálogo compatibles, nombre disponible y RG propio vacío; sin bloqueo Sweden confirmado. Persiste visibilidad incompleta de políticas y falta prueba operativa. Por ello **PARTIAL diagnóstico**, conforme al criterio de limitaciones de visibilidad con recomendación fundamentada.

No se declara GO operativo ni rechazo previsto. Un preflight de solo lectura no puede garantizar la aceptaciónAzure; tampoco se usa esa incertidumbre para autorizar prueba de creación por cuenta propia. La siguiente fase de creación debe aceptar explícitamente ese riesgo acotado, conservar medidas y detenerse si Azure deniega.

## 15. Próxima acción autorizable

Propietario puede **aprobar una ficha de bootstrap revisada**: cuenta stwordletfgstate7c92d4 en Sweden, reutilización del RG existente, StorageV2/LRS/Hot, tfstate/key indicada, TLS/HTTPS/Entra/SharedKeyfalse/anonfalse, firewallDeny/None con IP vigente, rol del operador al contenedor, versioning/softdelete7d/lifecycle solo anteriores y custodia/coste/retención. Si exige eliminar previamente la incertidumbre heredada, pedir aclaración al administrador/Microsoft mediante autorización específica, no elevar permisos ni enviar ticket ahora.

Secuencia mínima futura, **no ejecutada**:

1. Revalidar contexto/operador, RG propio vacío, ausenciacuenta/nombreavailable, provider/acciones y salidaIP aprobada. Aprobar expresamente reutilizaciónRG; no recrearlo.
2. Autorizar una creación de cuenta en swedencentral con seguridad restrictiva desde el inicio. Ante error, capturar código/correlación y parar; sin otra región o relajación automática.
3. Configurar protecciones y lifecycle; añadir exclusivamente IP administrativa autorizada. Crear contenedor privado por ARM; asignar Storage Blob Data Contributor al operador/scope precisos con autorización explícita.
4. Verificar por lectura cuenta/propiedades/red/retención/rol y acceso de listadoBlob Entra. Esperar propagación acotada ante403, sin nuevas asignaciones o SharedKeyfallback.
5. Pruebas de escritura/lease sobre blob de prueba, Terraform init/plan y AKS requieren autorizaciones posteriores separadas. No crear estado ficticio ni borrar estado para probar acceso. Limpieza de fallo parcial tampoco es automática.

El permiso solicitado para la siguiente fase debe detallar escrituras concretas, IP/operador/scope, retención y condiciones de parada. Aprobar cuota no autoriza esa fase. No se inicia automáticamente.

## 16. Estado de Gate A y AKS; preservación

**Gate A NO-GO: cuenta/backend no aprovisionados. AKS NO-GO:** cuota resuelta, resto de gates independientes sin cerrar. No Terraform ejecutado, configuración o región modificadas, recursosAzure creados/actualizados/borrados, cuotas/Policy/RBAC/proveedores alterados o tickets enviados.

Solo se crea este informe; pendientes previos comprobados porSHA-256 e índice/lista de cambios versionados conservados. Informes históricos, rg-wordle-state y estadoGit intactos. No staging/commits/push ni scripts auxiliares persistentes. LecturasGit limitadas a preservación, sin auditoría de otras ramas. Se detiene la iteración sin bootstrap.
