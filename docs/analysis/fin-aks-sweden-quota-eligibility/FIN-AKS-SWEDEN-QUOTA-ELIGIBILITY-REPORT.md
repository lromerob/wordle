# FIN-AKS-SWEDEN-QUOTA-ELIGIBILITY — Wordle TFG

Fecha: **16/11/2026**. Consultas de lectura realizadas en esta sesión; referencia horaria de consulta 15:00 UTC (16:00 Europe/Madrid), no hora exacta de cada GET.

## 1. Resumen ejecutivo

**PASS diagnóstico.** La suscripción autorizada tiene en Sweden Central **DSv5: límite0, consumo0, disponible0 vCPU; regional: límite10, consumo0, disponible10 vCPU**. Ambos recursos Microsoft.Quota devolvieron **isQuotaApplicable=true**. Es técnicamente admisible preparar una solicitud; no hay preaprobación del valor16 ni garantía de aceptación/capacidad.

Recomendación: una futura solicitud familiar **standardDSv5Family a límite absoluto16**, con regional disponible **al menos16**, comprobando primero su ajuste automático. No solicitar regional por separado por defecto. No presentar solicitudes todavía. SKU Standard_D4s_v5 confirmado en catálogo, sin restricciones devueltas, 4vCPU/16GiB/x64 y zonas1/2/3 publicadas. No existe prueba de asignación física ni de aprovisionamiento permitido frente a todas las políticas heredadas.

**Gate A NO-GO y AKS NO-GO.** Solo se crea este informe; ningún recurso, cuota, proveedor, rol, configuración o historial Git se modifica.

## 2. Contexto y alcance

Se leyó FIN-AKS-REGION-SELECTION y la evidencia previa de elegibilidad/provider/request de West Europe para reutilizar el procedimiento, sin extrapolar cuotas ni aprobaciones a Sweden. Se revisó la validación node_count de variables.tf y el pool actual de main.tf. Los informes previos de Policy/preflight se conservan: West Europe tuvo deny real sys.blockwesteurope; backend remoto sigue pendiente. No se repiten precios ni análisis arquitectónicos generales.

Región investigada exclusivamente **swedencentral**. Dos D4s_v5, 8vCPU nominales, candidato surge1 y máximo simultáneo12vCPU. Ciclo temporal DEPLOY → VALIDATE → EVIDENCE → DESTROY → REDEPLOY → DESTROY. Cuota no constituye autorización para ninguna fase operativa. No se investigó East US de nuevo.

## 3. Identidad y suscripción verificadas

Antes de consultas específicas: account show coincide con suscripción **11306565…1bb5**, tenant **aff0390f…1eb9**, Enabled. Graph signed-in-user, solo proyección id, confirma operador **b573130a…a831**. No se cambió contexto ni se realizó login. GET subscription devuelve PayAsYouGo_2014-09-01, Public_2014-09-01, spendingLimit Off. No se presume una oferta Students/Free Trial, crédito, límite monetario o capacidad reservada.

Sweden Central es accesible para consultas: GET Compute Usage y Quota regional/familiar con datos utilizables; get-versions AKS confirma candidato1.35.9; catálogo SKU devuelve la región. Esto no certifica permiso para crear Storage/AKS.

Microsoft.Quota **Registered**, sin ejecutar register. GET Microsoft.Authorization/permissions en suscripción devuelve una entrada actions=* sin notActions y dataActions vacías: incluye lectura de cuotas/solicitudes y la acción Microsoft.Quota/quotas/write para futura presentación, sin ejercerla. No se detecta acción ARM faltante en esa respuesta; no se certifican roles nominales, condiciones/deny superiores o éxito de escritura. Acceso de lectura quedó probado por los GET, no por deducción del rol.

Para una futura operación se necesitan acciones de lectura/seguimiento y quotas/write al ámbito correspondiente. Microsoft documenta Quota Request Operator para la API y Contributor o acceso equivalente para Portal; no hay necesidad justificada de asignar roles adicionales ahora. No se modificó RBAC ni se leyó ningún token o secreto en las salidas.

## 4. Cuota DSv5

Familia exacta confirmada por catálogo SKU: **standardDSv5Family**, nombre localizado Standard DSv5 Family vCPUs; no confundir con DSv4, Dv5 sin s, Spot o cuota regional.

Identificador sanitizado:

`/subscriptions/<suscripción-aprobada>/providers/Microsoft.Compute/locations/swedencentral/providers/Microsoft.Quota/quotas/standardDSv5Family`

GET Quota api-version2025-09-01: name.value=standardDSv5Family, unit=Count, limit.limitObjectType=LimitValue, limit.limitType=Independent, limit.value=0, **isQuotaApplicable=true**. Properties adicionales vacío; no hay máximo de solicitud/preaprobación16 en la respuesta. Compute Usage api-version2024-03-01 confirma límite0/currentValue0: disponible=0−0=0vCPU, no inferido solo de disponibilidad anterior.

Incidencia: primera lectura familiar devolvió MissingRegistrationForResourceProvider pese a Microsoft.Quota Registered. Una segunda lectura acotada, tras las demás comprobaciones de solo lectura, devolvió los datos anteriores. No se volvió a registrar nada. Compatible con transitoriedad de servicio, sin atribuir causa exacta a propagación ni interpretar ese primer error como inampliable. La lectura posterior exitosa es la evidencia de ajustabilidad utilizada.

[API GET y significado de isQuotaApplicable](https://learn.microsoft.com/en-us/rest/api/quota/quota/get?view=rest-quota-2025-09-01).

## 5. Cuota regional

Recurso **cores**, Total Regional vCPUs, mismo ámbito regional y proveedor Quota:

`/subscriptions/<suscripción-aprobada>/providers/Microsoft.Compute/locations/swedencentral/providers/Microsoft.Quota/quotas/cores`

GET Quota2025-09-01: límite10, unit Count, limitType Independent, **isQuotaApplicable=true**. Compute Usage2024-03-01: límite10, consumo0, disponible10vCPU. Se acredita solicitud técnicamente admitida de ese recurso, no aprobación futura de un límite concreto.

| Escenario | vCPU requeridas | Déficit familiar disponible actual | Déficit regional disponible actual |
|---|---:|---:|---:|
| Un D4s_v5, referencia aritmética | 4 | 4 | 0 |
| Dos nodos | 8 | 8 | 0 |
| Dos más un surge | 12 | 12 | 2 |
| Margen propuesto | 16 | 16 | 6 |

Ambos límites deben cumplirse simultáneamente, descontando todo consumo de la región/familia. Los escenarios no autorizan cambiar topología ni usar un nodo. La cuota de West Europe no se comparte con Sweden.

## 6. Disponibilidad y restricciones del SKU

Consulta actual ejecutada:

`az vm list-skus --location swedencentral --size Standard_D4s_v5 --resource-type virtualMachines --all`

Salida proyectada sobre el SKU exacto, sin aprovisionar:

- name Standard_D4s_v5; family standardDSv5Family.
- locations y locationInfo.location: SwedenCentral.
- restrictions: **[]**.
- locationInfo.zones: **2,1,3**; conjunto publicado1/2/3, sin orden de preferencia.
- capabilities: vCPUs4, MemoryGB16, CpuArchitectureType x64.
- zoneDetails publica UltraSSDAvailable=True para1/2/3; no se necesita ni se propone UltraSSD.

No se detecta restricción NotAvailableForSubscription en este resultado. Las zonas son catálogo, no capacidad física reservada; Terraform no fija zonas y no se modifican. El comando tardó varios minutos, pero concluyó correctamente; no se instala extensión ni se despliega un recurso para acelerar/verificarlo.

Policy assignments a suscripción con disable-scope-strict-match: cero entradas. El informe previo demuestra un deny heredado West Europe aunque esa lista fuera vacía y la asignación superior no fuera legible. Por ello, **no hay un bloqueo Sweden comparable detectado, pero no se acredita ausencia de toda restricción heredada**. La regla West Europe conocida no demuestra bloqueo Sweden; tampoco autoriza concluir que la región esté habilitada para cualquier recurso.

El catálogo AKS consultado sigue ofreciendo1.35.9. No se demuestra admisión de un nuevo clúster ni compatibilidad runtime de todo el stack; no hay Storage Account de prueba ni despliegue. Restricciones comerciales/regionales no visibles y capacidad efectiva siguen pendientes.

## 7. Elegibilidad para ampliación

| Nivel | Resultado |
|---|---|
| Recurso admite solicitar cuota | **Confirmado** para DSv5 y regional por isQuotaApplicable=true |
| Oferta/operador potencialmente elegibles | **Confirmado como vía ordinaria disponible**: PayAsYouGo Enabled, provider Registered y acciones ARM devueltas; aprobación concreta condicionada |
| Valor16 aprobado en Sweden | **No**: ninguna solicitud presentada en este incremento ni aprobación aportada |
| Capacidad física de tres D4s_v5 | **No verificable** sin asignación; no se prueba creando |

GET regional quotaRequests2025-09-01: **cero entradas y sin nextLink**. No solicitudes observadas en ese endpoint/ámbito; no equivale a inexistencia de tickets externos o restricciones de acceso. No se consultan solicitudes ajenas a esta región.

Portal Azure Quotas/Compute y API Microsoft.Quota son vías documentadas. El GET no muestra máximo permitido ni si la revisión de16 será automática o manual. Puede requerir revisión de Microsoft, rechazo por oferta/capacidad o derivación a soporte. No hay evidencia que obligue ahora a abrir ticket; solo se propondrá con autorización si la solicitud autorizada es rechazada, no ajustable o la interfaz lo exige.

Según [prerrequisitos Portal](https://learn.microsoft.com/en-us/azure/quotas/quickstart-increase-quota-portal), las solicitudes corresponden a suscripciones de pago; la oferta observada cumple esa condición general, sin garantizar una cantidad/región. [API y permisos](https://learn.microsoft.com/en-us/rest/api/quota/).

## 8. Dependencias de AKS

Separación de requisitos:

| Origen | Evidencia / interpretación |
|---|---|
| Servicio Azure, publicado actualmente | Restricciones System pools: Linux, al menos30pods, al menos dos nodos y SKU>=4vCPU/4GB; no B-series. Es documentación del servicio, no una prueba de enforcement de la API ejecutada hoy. |
| Terraform del proyecto | variables.tf exige node_count entero>=2; default2 y Standard_D4s_v5. Se verifica por lectura, sin Terraform ejecutado. |
| Disponibilidad recomendada | Microsoft recomienda tres nodos para mayor tolerancia en producción; no se convierte esa recomendación en nuevo requisito de este TFG. |
| Arquitectura académica | Dos nodos para distribución/operación; PostgreSQL único compartido no HA; no aumentar a tres nodos permanentes ni añadir otro pool. |
| Surge candidato | 2×4 +1×4=12vCPU simultáneas. main.tf no fija max_surge explícito; formalizar1 requiere autorización posterior. |

Se conserva la topología aprobada. La referencia de un nodo solo calcula cuota; no es una propuesta compatible con el proyecto. Para surge se necesitan también IP de subred, capacidad VMSS/Load Balancer, discos y capacidad física. No se verifican esos recursos mediante creación ni se promete que cuota CPU por sí sola baste. No se asigna arbitrariamente una IP pública por nodo: depende de la configuración; aquí se prevé una IP de salida gestionada.

Fuentes: [System pools, restricciones y recomendaciones](https://learn.microsoft.com/en-us/azure/aks/use-system-pools), [capacidad y costes de surge](https://learn.microsoft.com/en-us/azure/aks/upgrade-capacity-cost-planning).

## 9. Cuota objetivo recomendada

| Alternativa | Límite DSv5 propuesto | Incremento familiar | Regional disponible objetivo | Incremento regional mínimo si fuera independiente | Ventajas / riesgos |
|---|---:|---:|---:|---:|---|
| A: estricto | 12 | +12 desde0 | >=12 | +2 desde10 | Cubre dos nodos+surge sin margen familiar; otro consumo puede agotar capacidad autorizada. |
| B: margen | 16 | +16 desde0 | >=16 | +6 desde10 | Margen4vCPU sobre pico12, evita nueva gestión por un pequeño consumo adicional; no autoriza cuatro nodos ni garantiza aprobación. |

**Recomendada B:** límite familiar absoluto16 y regional disponible>=16, con consumo actual0. Es un margen de un D4s_v5 sobre el pico de tres nodos, limitado y coherente con la decisión candidata del propietario. No se propone más de16 para la familia. A sigue siendo suficiente para el pico exacto si se rechaza16; aceptar una cantidad distinta requeriría decisión posterior, no una solicitud alternativa automática.

**No pedir dos aumentos independientes de entrada.** Microsoft documenta que una ampliación familiar aprobada aumenta el regional por la misma cantidad. Con valores actuales, familia0→16 podría llevar regional10→26; alternativaA podría llevarlo10→22. Son resultados esperables según regla publicada, no valores aprobados ni garantizados de antemano. Ese regional superior no implica solicitar familia26 ni ampliar el despliegue. Verificar ambos límites después y solicitar regional por separado solo si queda insuficiente y existe autorización nueva. La evidencia previa de West Europe0→16/10→26 es un precedente fechado, no aprobación para Sweden.

Corrección interpretativa del informe de selección: «ampliación familiar y regional» identifica dos límites actualmente insuficientes; **no exige dos solicitudes**. El informe anterior no se modifica.

Pedir o mantener cuota no tiene cargo directo ni reserva capacidad. La facturación deriva de recursos usados; mayor cuota permite potencialmente mayor consumo, no constituye tope monetario. Un aumento no crea nodos/AKS ni autoriza gasto. [Cuotas y coste](https://learn.microsoft.com/en-us/azure/quotas/quotas-overview), [ajuste regional automático](https://learn.microsoft.com/en-us/azure/quotas/regional-quota-requests).

## 10. Procedimiento futuro de solicitud — NO EJECUTADO

1. Obtener autorización expresa para **una solicitud familiar Sweden Central a límite absoluto16**, aceptando regional al menos16 y posible ajuste automático superior (esperable26 con valores actuales). Excluir AKS/Storage/Terraform/RBAC/soporte.
2. Revalidar suscripción/tenant/operador exactos, Enabled, providerRegistered, límites/usos, isQuotaApplicable y solicitudes pendientes. Si hay discrepancia o solicitud en curso, detener; no duplicar.
3. Vía Portal: Azure Portal → Quotas → Compute → My quotas; filtrar suscripción aprobada y **Sweden Central**; elegir **Standard DSv5 Family vCPUs**, comprobar límite0/usado0/Adjustable; New Quota Request → Enter a new limit → **16**. El valor es límite absoluto, no incremento adicional a16.
4. Justificación: Wordle TFG privado temporal; dos System nodes D4s_v5 de4vCPU, ocho nominales y doce durante upgrade con surge1; margen acotado cuatrovCPU. Sin producción ni infraestructura permanente. No afirmar reserva o gasto aprobado.
5. **Submit solo después de autorización de presentación.** Microsoft revisa; no prometer plazo o aprobación automática. Conservar ID/fecha/estado y no repetir envío mientras esté pendiente.
6. Alternativa API, sin instalar extensión: endpoint oficial PUT `https://management.azure.com/subscriptions/<aprobada>/providers/Microsoft.Compute/locations/swedencentral/providers/Microsoft.Quota/quotas/standardDSv5Family?api-version=2025-09-01`, cuerpo `{"properties":{"name":{"value":"standardDSv5Family"},"limit":{"limitObjectType":"LimitValue","value":16}}}`. **Solo documentación; no invocado.** Requiere quotas/write y lecturas/seguimiento. Supervisar mediante GET de la URI Location/ID recibida, no reenviar PUT como consulta.
7. Al terminar, comprobar conclusión de la solicitud y valores independientes Compute Usage/Quota: familia>=16, regional disponible>=16, descontando consumo actual. Accepted/InProgress no es Succeeded. Si aprobación parcial o regional insuficiente, informar; no presentar otra solicitud automáticamente.
8. Si aparece no ajustable/rechazo/ContactSupport/restricción de oferta, registrar código y solicitar autorización separada para soporte o intervención del administrador. No abrir ticket, cambiar oferta ni asignar rol para resolverlo por cuenta propia. Antes de esa vía comprobar requisitos del canal de soporte disponible.

Fuentes: [procedimiento familiar Portal](https://learn.microsoft.com/en-us/azure/quotas/per-vm-quota-requests), [API CreateOrUpdate y seguimiento](https://learn.microsoft.com/en-us/rest/api/quota/quota/create-or-update?view=rest-quota-2025-09-01). No se ejecutó PUT, PATCH o POST de cuota ni se abrió formulario de envío.

## 11. Riesgos y limitaciones

- isQuotaApplicable=true acredita que puede solicitarse; no máximo numérico, aceptación de16 ni capacidad física.
- QuotaRequests vacío solo cubre ese listado/ámbito, no tickets por otras vías.
- No se detectan restricciones SKU actuales; no prueba admisión de Storage/AKS frente a Policy heredada. No afirmar que Sweden acepte nuevos clientes para todos los servicios.
- Visibilidad superior de Policy limitada según diagnóstico previo; lista actual vacía no demuestra ausencia.
- Cuotas pueden cambiar con consumo concurrente o revisión Microsoft; revalidar antes de solicitud y despliegue autorizados.
- No se prometen HA de PostgreSQL, compatibilidad completa AKS ni presupuesto total por obtener cuota. Backend, Entra/grupo, CIDR, versión/surge y presupuesto conservan gates independientes.
- Ninguna cuota actual de otra región se transfiere. No hay motivo probado para descartar Sweden ni iniciar East US mientras la vía de solicitud familiar sea admisible.

## 12. Matriz de decisión

| Criterio | Resultado | Evidencia | Estado |
|---|---|---|---|
| DSv5: límite actual | 0vCPU | Compute Usage + GET Quota | Confirmado |
| DSv5: consumo | 0vCPU | Compute Usage | Confirmado |
| DSv5: disponible | 0vCPU | Límite menos consumo | Confirmado |
| Regional: límite | 10vCPU | Compute Usage + GET Quota | Confirmado |
| Regional: consumo | 0vCPU | Compute Usage | Confirmado |
| Regional: disponible | 10vCPU | Límite menos consumo | Confirmado |
| SKU D4s_v5 | 4vCPU/16GiB/x64, zonas1/2/3, restrictions=[] | list-skus actual | Confirmado catálogo; capacidad pendiente de validación operativa |
| Ajustabilidad DSv5 | isQuotaApplicable=true | Segundo GET2025-09-01 correcto | Confirmado |
| Ajustabilidad regional | isQuotaApplicable=true | GET2025-09-01 correcto | Confirmado |
| Restricciones de suscripción | PayAsYouGo Enabled, accionesARM amplias | GET subscription/permissions | Confirmado; condiciones superiores no verificables por completo |
| Restricciones regionales | Ningún deny Sweden detectado; no prueba de ausencia | Policy visible vacío, SKU y AKS accesibles; precedente West | No verificable de forma exhaustiva |
| Elegibilidad de solicitud | Vía técnica y condición general de oferta satisfechas | Ajustabilidad de ambos recursos, proveedorRegistered, permisos | Confirmado para solicitar; valor16 pendiente de aprobación |
| Solicitudes observadas | Cero, sin paginación | GET quotaRequests Sweden | Confirmado dentro del endpoint |
| Capacidad efectiva de despliegue | No disponible por cuota familiar0; hardware no probado | Límites actuales y ausencia de aprovisionamiento | Pendiente de aprobación y validación operativa |

Evidencias obtenidas únicamente con account show, Graph ID propio, GET subscription/provider/permissions/ComputeUsage/Quota/QuotaRequests, listado Policy visible, list-skus y get-versions Sweden. APIversions utilizadas: Quota2025-09-01, ComputeUsage2024-03-01, subscription2022-12-01, provider2021-04-01, permissions2022-04-01. Solo GET/consultas de listado; sin modificaciones administrativas.

## 13. Recomendación

Mantener Sweden Central como candidata y **proponer una solicitud familiar16**, verificando regional>=16 tras el ajuste automático. No se necesita de entrada solicitud regional independiente; su cuota actual10 sí es insuficiente para el pico12, pero la aprobación familiar puede resolver ambos límites. Se confirma la elegibilidad de la vía, no el resultado futuro.

PASS del diagnóstico no cierra Gate A, FIN-05 o la validación AKS. No se reconsidera región sin evidencia de rechazo/restricción o decisión del propietario. La alternativa East US se conserva para un incremento posterior si Sweden no resulta admisible, sin investigarla hoy.

## 14. Próxima acción

El propietario debe decidir si **autoriza FIN-AKS-SWEDEN-QUOTA-REQUEST: un único envío familiar DSv5 a16vCPU en Sweden Central, con aceptación de ajuste regional automático superior a16, seguimiento y verificación posterior, sin solicitud regional independiente automática**. No implica aprovisionamiento, soporte, permisos nuevos ni gasto de infraestructura.

Si no autoriza todavía el envío, no hay otra operación necesaria en esta iteración. No se inicia una nueva fase ni se presenta formulario/ticket.

## 15. Estado de Gate A y AKS; preservación

**PASS diagnóstico; Gate A NO-GO y AKS NO-GO.** Cuota no aprobada, backend no operativo y otros gates previos siguen pendientes. Solo se crea este informe. Archivos pendientes preexistentes comprobados por SHA-256; índice y lista de cambios versionados preservados. No se modifican informes históricos, Terraform/configuración, recursosAzure, permisos, proveedores o historialGit; sin staging, commits o push. rg-wordle-state intacto. Sin secretos, otras bases/proyectos o despliegues de prueba.
