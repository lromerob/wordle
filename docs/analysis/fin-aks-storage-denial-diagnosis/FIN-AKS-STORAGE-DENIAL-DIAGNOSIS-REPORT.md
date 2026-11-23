# FIN-AKS-STORAGE-DENIAL-DIAGNOSIS — Wordle — 16/11/2026

## 1. Resumen ejecutivo: PASS diagnóstico, bloqueo sin resolver

**Causa confirmada del intento Storage:** denegación regional heredada `sys.blockwesteurope`, efecto deny, correlacionada con el fallo. La respuesta Azure indica: **“The selected region is currently not accepting new customers”**. La definición identificada bloquea location=westeurope. No es una hipótesis deducida de una lista vacía o de un código genérico: se recuperó el evento Policy concreto con la misma correlación, y se leyó la definición.

**Gate A NO-GO y AKS NO-GO.** No reintentar creación ni cambiar parámetros/región/permisos. La operación siguiente recomendada es que el propietario decida autorizar preparación/presentación de un caso de acceso regional a Microsoft con esta evidencia, o una evaluación separada de cambio regional. No se abre ticket ni se modifica nada hoy.

## 2. Contexto y operación fallida

Contexto actual coincide: suscripción `11306565…1bb5`, tenant `aff0390f…1eb9`, Enabled, operador `b573130a…a831` confirmado por lectura de ID propio. Sin cambio de contexto. Región aprobada westeurope. RG rg-wordle-state existe, ubicación correcta, provisioningState Succeeded; Storage Account stwordletfgstate7c92d4 sigue ResourceNotFound. No inspección de recursos ajenos o Nexo.

Informe operativo original FIN-AKS-BACKEND-BOOTSTRAP conservaba código pero no hora exacta/correlationId/mensaje completo. No se inventaron ni se asumieron esos datos. Se recuperan ahora del Activity Log de esa cuenta/RG. La creación del RG tuvo éxito el16/11/2026 13:21:06.6533341Z; el rechazo Storage ocurrió unos segundos después.

## 3. Error original y correlación recuperados

- Operación: Microsoft.Storage/storageAccounts/write, Create/Update Storage Account.
- Recurso: stwordletfgstate7c92d4 en rg-wordle-state, suscripción confirmada.
- eventTimestamp del fallo: **2026-11-16T13:21:10.5758564Z**.
- Estado: **Failed**; subestado **Forbidden**.
- error.code: **RequestDisallowedByAzure**.
- error.message recuperado: `Resource 'stwordletfgstate7c92d4' was disallowed by Azure: The selected region is currently not accepting new customers: https://aka.ms/locationineligible.`
- error.target: stwordletfgstate7c92d4.
- correlationId y operationId: **2b97ec26-36cf-42c0-ad62-1a2411032364**.
- eventDataId del fallo: c5117cf0-d808-409f-9b43-9c636df23599.
- submissionTimestamp: **2026-11-16T13:23:36Z**.

No se recuperó un requestId separado ni innererror/error.details con otro código; no se inventa un código interno RequestDisallowedByPolicy. El código principal sigue RequestDisallowedByAzure y la causalidad Policy se acredita por otro evento. El código no es una prueba de cuota o IAM insuficientes.

## 4. Azure Activity Log

Ventana consultada: **2026-11-15T23:00:00Z a 2026-11-16T14:20:54Z**, elegida dentro de la fecha16/11 en Europe/Madrid, porque el informe original no tenía hora exacta. Consultas con max-events200, sin filtro status para no perder Started ni eventosPolicy:

1. `az monitor activity-log list --resource-id <cuenta prevista> --start-time ... --end-time ... --max-events 200 --subscription <confirmada>`: **3 eventos**.
2. Misma ventana, `--resource-group rg-wordle-state`: **5 eventos**; permite correlacionar RG propio creado y Storagefallido, sin consulta global.

Secuencia del recurso:

| UTC | Evento | Resultado |
|---|---|---|
|13:21:10.4821098 | Storage write Started | Body coincide con parámetros aprobados |
|13:21:10.5602317 | Microsoft.Authorization/policies/deny/action | Failed; categoría Policy; identifica asignación/definición |
|13:21:10.5758564 | Storage write Failed | Forbidden, RequestDisallowedByAzure y mensaje regional |

Los tres comparten correlationId/operationId anteriores. El evento Policy contiene resourceLocation=westeurope, isComplianceCheck=False, policyDefinitionEffect=deny, enforcementMode=Default y sin exenciones en su metadata. No es mera evaluación de cumplimiento posterior: está asociado a la operación bloqueada.

El registro fue enviado a las13:23:36Z, aproximadamente2m25s después del intento, por lo que la ausencia en las lecturas inmediatas del bootstrap es compatible con latencia. No se afirma que esta fuera la única razón de la lista previa vacía; filtros y alcance influyen. Ninguna ausencia de eventos se usa para descartar AzurePolicy.

## 5. Azure Policy: causa confirmada y visibilidad limitada

Evento Policy recuperado:

- policyDefinitionId: `/providers/Microsoft.Authorization/policyDefinitions/7509877f-d414-4d79-8d1f-d600ea78d087`.
- Nombre: **Resources should not be created in West Europe**; versión del evento1.0.0.
- policyAssignmentName: **sys.blockwesteurope**.
- policyAssignmentId: `/providers/Microsoft.Management/managementGroups/<TENANT>/providers/Microsoft.Authorization/policyAssignments/sys.blockwesteurope`.
- Display: Microsoft Azure region access restriction blocking West Europe region.
- Ámbito heredado: management group asociado al tenant, enmascarado; no asignación creada por Wordle.

GET directo de la definición (api-version2023-04-01) tuvo éxito: policyType BuiltIn, descripción bloquea creación/actualización en West Europe. Regla:

```json
{"if":{"equals":"westeurope","field":"location"},"then":{"effect":"deny"}}
```

Consultas de asignaciones al ámbito de suscripción y RG, con disable-scope-strict-match, devuelven cero. GET de la asignación exacta en management group (api-version2022-06-01) devuelve **AuthorizationFailed**. Por tanto la lista vacía **no confirma ausencia**; existe evidencia del deny aunque el operador no pueda leer el objeto asignación directamente. No se amplían permisos para verlo. La definición no contiene excepción específica de TLS, firewall oSKU; la condición recuperada es location.

Se distinguen: (a) política potencial por documentación general, no suficiente; (b) asignación aplicable observada por evento; (c) política confirmada causal por correlación y regla. Aquí se alcanza(c), con límites de lectura administrativa sobre la asignación.

## 6. Suscripción y proveedor

GET subscription actual: PayAsYouGo_2014-09-01, Enabled, spendingLimit Off, locationPlacementId Public_2014-09-01. No atribuir a Free Trial/Azure for Students basándose en ejemplos de internet. La restricción regional existe en esta suscripción a pesar de ese tipo de oferta.

Microsoft.Storage: **Registered**. Metadatos storageAccounts incluyen West Europe. Ese catálogo declara soporte general del servicio, **no elegibilidad específica de esta suscripción**. No se registra provider ni se consulta/modifica cuotaAKS para resolverlo.

Permissions de suscripción devuelve actions=* sin notActions en una entrada; no garantiza ausencia de controles heredados ni capacidad de cambiar una asignación de management group. La operación concreta fue rechazada por deny, no por un error AuthorizationFailed de Storage. El AuthorizationFailed actual corresponde solo al GET de la asignación superior. No confundir ambos errores.

## 7. Validación de parámetros usados

El requestbody del evento Started confirma StorageV2, Standard_LRS, westeurope, Hot, supportsHttpsTrafficOnly=true, minimumTlsVersion=TLS1_2, allowBlobPublicAccess=false, allowSharedKeyAccess=false, publicNetworkAccess=Enabled, networkAcls.defaultAction=Deny y bypass=None. Tags del request se muestran redactados porAzure; los del RG sí están verificados por el informe operativo.

Coincide con la ficha aprobada y el comando registrado. No se identifica incompatibilidad causal de SKU/TLS/Entra/firewall. La incompatibilidad efectiva es **solicitar location=westeurope bajo la denegación regional aplicada**, aunque esa región estuviera aprobada por el propietario. Aprobar una configuración local no anula controles Azure.

El RG pudo crearse con esa ubicación; no se infiere que la regla afecte igual a todos los tipos de recurso solo por el display. El intento de cuenta es el recurso bloqueado demostrado. No se creó todavía regla IP, contenedor, roleAssignment, versioning o lifecycle; no son candidatos causales de esta creación.

## 8. Diagnóstico diferencial

| Hipótesis | A favor | En contra/límite | Estado | Confianza |
|---|---|---|---|---|
| AzurePolicy heredada | Evento deny, misma correlación, definición location=west | GETassignment denegado no oculta evidencia del evento | **Confirmada** | Alta |
| Restricción regional de acceso | Mensaje no acepta nuevos clientes y reglaWestEurope | No se conoce fecha de liberación/regiones alternativas autorizadas | **Confirmada para este intento** | Alta |
| Restricción de suscripción/oferta | Asignación en ámbito heredado aplica a este destino | No es ofertaFreeTrial; motivo comercial exacto no consta | Posible como origen administrativo; acceso regional confirmado | Media para origen, alta para bloqueo |
| Proveedor no registrado | Hipótesis inicial genérica | Microsoft.Storage Registered | Descartada con evidencia actual | Alta |
| Permisos Storage insuficientes | IAM puede limitar operaciones | Errorcausal denyregional; acciones permitidas | No sustentada como causa del intento | Alta sobre error observado; no garantíaIAMfuturo |
| Parámetro incompatible de seguridad/SKU | Se deben respetar restricciones efectivas | Request coincide y regla niega solo location | No sustentada como causa | Alta sobre el rechazo recuperado |
| Restricción propia del servicio/capacidad | Mensaje regional de acceso; región catalogada no basta | No demuestra agotamiento físico concreto de Storage | Acceso regional confirmado; capacidad física no verificable | Alta/media |
| CuotaAKS/DSv5 | Ninguna evidencia relacionada | Operación Storage noVM y políticaexplicita | Descartada como explicación del rechazo registrado | Alta |
| Otras causas independientes | Podrían aparecer tras resolver esta | No evidenciadas por intentoactual | No verificables | Baja |

## 9. Causa raíz y límites

**Causa raíz operativa confirmada:** la solicitud Storage en westeurope incumplió la denegación regional heredada sys.blockwesteurope; Azure no admite esa creación en ese contexto de acceso regional. No se demuestra el motivo interno por el que Microsoft aplica esa restricción, ni cuándo cambiará o si otro servicio será admitido. No se debe considerar AKSWestEurope viable por tenercuota: la misma condición de ubicación representa un riesgo real para despliegues futuros, que deberán evaluarse antes de autorizarlos, no probarse creando.

No se necesita una prueba de creación diagnóstica mínima: ya existe evidencia causal suficiente. No se propone debilitar medidas de seguridad ni ensayar otra región a ciegas.

## 10. Resolución mínima recomendada

Prioridad: **solicitar intervención del propietario/Microsoft para aclarar o habilitar acceso a West Europe**, manteniendo ficha de seguridad. Preparar, tras autorización adicional de soporte, un caso con: suscripción completa en canal privado, nombrecuenta/RG, operación Storagewrite, hora13:21:10Z, correlación2b97ec26-36cf-42c0-ad62-1a2411032364, código/mensaje, policyDefinitionID yassignmentheredado, ofertaPayAsYouGo y Registered. Pedir explicación de restricción/ámbito y opciones de habilitación; no crear exención manual ni solicitar un rol superior para eludirla.

La mera preparación de este informe no autoriza enviar ticket. Coste/plazo/condiciones de soporte no verificados, no prometer resolución inmediata o acceso garantizado. Seguridad no necesita relajarse; reintento futuro requiere confirmación de restricción resuelta y autorización de creación específica sobre el RG yaexistente.

Alternativa solo si el propietario la elige y Azure aporta evidencia: evaluar otra región permitida para backend y consecuencias sobreAKS, disponibilidad, red, cuotas, precio y residencia de datos. Cambiar solo Storage no resuelve necesariamente futuros deniesAKS. No seleccionar región/SKU automáticamente ni actualizarTerraform. El RGvacío no se elimina hoy; su futura reutilización/retirada exige aprobación explícita.

Verificación futura de corrección: evidencia de acceso regional habilitado o ficha alternativa aprobada; nuevo preflight de lectura acotado; **una nueva creación solo autorizada posteriormente**, seguida de seguridad/RBAC/Bloblectura. No basta borrar el error del informe.

## 11. Autorizaciones necesarias

- Enviar caso de soporte o pedir intervención administrativa de ámbito superior: autorización separada, con datos en canal privado.
- Cualquier habilitación/cambioregional/excepción de plataforma corresponde al responsable autorizado; no se propone deshabilitar Policy o crear exenciones por el agente.
- Aprobar expresamente reutilizar RGWordle existente en reanudación o eliminarlo vacío si se abandona, sin modificación actual.
- Reintentarbootstrap solo tras decisión y autorización nueva. Sin ampliación automática de privilegios/red ni cambio de cuenta.

## 12. Estado final Gate A

**NO-GO:** RG propio creado anteriormente se conserva; cuenta inexistente, backend no operativo. AKS NO-GO. Este PASS es diagnóstico, no resolución del bloqueo ni aprobación de creación.

## 13. Próxima acción y preservación

Propietario decide autorizar un caso de acceso regional a Microsoft con evidencias anteriores, sin reintentos. No iniciar otraiteración automáticamente. No se modifican informes anteriores: este informe complementa la causa que no pudo recuperarse durantebootstrap.

Fuentes: [diagnóstico oficial de denegacionesPolicy](https://learn.microsoft.com/en-us/azure/azure-resource-manager/troubleshooting/error-policy-requestdisallowedbypolicy) para método de correlación/definición; no se sustituye el códigoAzureobservado por el de esa guía. El enlaceaka.ms/locationineligible figura en el error original, pero no pudo abrirse desde la herramientadeconsultaweb; no se inventa su contenido. Prueba primaria son losGETAzure ylos eventos recuperados.

Solo se crea este informe. Archivosprevios modificados/sinseguimiento preservados porSHA-256. Sin escriturasAzure, cambiosPolicy/RBAC/Storage/región/identidad, Terraform, solicitudescuota, tickets, recursos de prueba, commits/push ni staging. LecturasGit limitadas a preservar archivos, sin auditoría de ramas. No consultas a recursos deNexo ni a estados/secretos.
