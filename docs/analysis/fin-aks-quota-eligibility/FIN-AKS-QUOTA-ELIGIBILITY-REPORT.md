# FIN-AKS-QUOTA-ELIGIBILITY — 15/11/2026

## Resumen ejecutivo: BLOCKED; AKS NO-GO

Objetivo aprobado por el propietario: 16 vCPU regionales y 16 DSv5, westeurope, dos Standard_D4s_v5 con margen de surge. Esta aprobación **no autoriza solicitudes**.

La oferta declarada es PayAsYouGo, no Free Trial, y las acciones de permiso para cuota están disponibles. No obstante, la elegibilidad específica/ajustabilidad y el máximo admisible para 16 no pueden acreditarse: los GET de Microsoft.Quota fallan por falta de registro del proveedor. No se infiere elegibilidad por tener permisos o por ser PayAsYouGo. No se registra el proveedor ni se envían solicitudes/tickets.

## Contexto, cuota y resultados

Suscripción `11306565…1bb5`, tenant `aff0390f…1eb9`, confirmados previamente por el propietario y coincidentes con el contexto actual; estado Enabled, principal tipo user. Región verificada en Terraform: westeurope. No cambio de contexto, login ni acceso a secretos.

| Comprobación | Estado | Evidencia observada |
|---|---|---|
| Contexto autorizado y estado | PASS | account show, IDs coincidentes y Enabled. |
| Política de suscripción | PASS | GET subscription api-version=2022-12-01: quotaId PayAsYouGo_2014-09-01, locationPlacementId Public_2014-09-01, spendingLimit Off. Esto no significa presupuesto aprobado ni coste limitado. |
| Cuota regional | PASS | vm list-usage: cores, uso 0/límite 10. Para llegar al objetivo absoluto 16 faltan 6 de límite, sujeto al ajuste automático de familia. |
| Cuota DSv5 | PASS | standardDSv5Family, uso 0/límite 0. Objetivo absoluto 16, no incremento adicional sobre 16. |
| Ajustabilidad DSv5 y regional | BLOCKED | GET de ambos recursos de Quota api-version=2025-09-01 devuelve MissingRegistrationForResourceProvider. isQuotaApplicable y límite máximo de solicitud no disponibles. |
| Proveedor Quota | PASS de diagnóstico | provider show confirma Microsoft.Quota NotRegistered. No se registra. |
| Solicitudes existentes | PASS limitado | GET quotaRequests devuelve cero registros y sin nextLink. No se observan pendientes en ese ámbito/endpoint; no prueba ausencia de tickets por otras vías o restricciones. |
| Acciones de permiso de cuota | PASS limitado | permissions GET devuelve permitidas quotas/read, quotas/write y quotaRequests/read. No prueba ausencia de deny assignments/condiciones ni éxito de una operación no ejecutada. |
| Acción de soporte | PASS limitado | Microsoft.Support/supportTickets/write permitida por las acciones devueltas; no se abre ticket ni se comprueba elegibilidad de un plan de soporte. |
| Elegibilidad específica para 16/16 | BLOCKED | Falta lectura de ajustabilidad y condiciones concretas del proveedor/Portal. No existe simulación de solicitud ejecutada. |

## Permisos disponibles y faltantes

La operación API de solicitud requiere Microsoft.Quota/quotas/write al ámbito de suscripción/proveedor/región, con permisos de lectura para consultar cuotas y seguimiento. Se observan esas acciones en permissions; no se detecta una acción faltante en esa respuesta. Rol nominal asignado, condiciones/deny y acceso efectivo final no se certifican. La documentación presenta Quota Request Operator para gestión de cuotas y Contributor o equivalente para el procedimiento Portal; no se necesitan cambios RBAC por defecto solo para sustituir roles por nombres.

El prerrequisito ausente confirmado es el registro Microsoft.Quota para la vía API. Registrarlo exige autorización separada y permiso Microsoft.Quota/register/action; **no se ejecuta ni se da aquí por verificado ese permiso específico**. Registrar no es solicitar cuota ni autoriza crear AKS. No modificar roles/identidades para solventarlo automáticamente.

## Elegibilidad de la oferta y condiciones

PayAsYouGo permite considerar la vía ordinaria de solicitud; no se confirma aprobación de cantidad/región por ese dato. Las restricciones generales de Free Trial no corresponden al quotaId observado. Restricciones comerciales adicionales, revisiones de capacidad o políticas pueden existir: no hay respuesta afirmativa de isQuotaApplicable. spendingLimit Off implica que no hay límite de gasto de ese tipo; la cuota técnica no es límite monetario.

Microsoft revisa las solicitudes; aprobación y plazo no garantizados. Una cuota concedida no reserva capacidad física ni elimina restricciones del SKU o zona. Sigue siendo necesario confirmar capacidad y demás gates de Entra/CIDR/backend/presupuesto antes de planificar/desplegar.

## Ajuste de cuota regional: precisión respecto al informe anterior

La documentación oficial de cuotas por familia indica que aprobar un aumento de familia incrementa automáticamente la cuota regional; la de cuota regional describe un aumento por la misma cantidad. Por tanto, **no asumir dos solicitudes independientes obligatorias ni que el regional final quedará exactamente en 16**. Solicitar familia de 0 a 16 podría dejar un regional superior al objetivo mínimo, según el comportamiento aplicado; no se promete un valor exacto por adelantado.

Objetivo operativo interpretado: DSv5 16 y regional al menos 16. El propietario debe confirmar si exige límite regional exactamente 16 antes de una solicitud, dado el ajuste automático y las limitaciones de reducción. Tras una eventual aprobación, consultar ambos valores; pedir regional por separado solo si aún es insuficiente y existe autorización. Esta precisión se registra exclusivamente aquí, sin reescribir informes anteriores.

## Procedimiento recomendado y decisión requerida

1. **Primera autorización propuesta:** registrar únicamente Microsoft.Quota en la suscripción confirmada y volver a consultar por GET isQuotaApplicable para cores/standardDSv5Family, estado y solicitudes. No incluye solicitar cuota, soporte, desplegar o cambiar RBAC. No se ejecuta ahora.
2. Como alternativa sin registrar desde el agente, el propietario puede revisar Azure Portal → Quotas/My quotas → Compute → suscripción aprobada → West Europe; comprobar ajustabilidad, límite que ofrece el formulario y la elegibilidad de DSv5. Solo inspeccionar, sin enviar formulario ni aceptar registros/modificaciones implícitos sin autorización. No se automatiza navegador en esta iteración.
3. Si es ajustable, preparar solicitud familiar con límite absoluto 16, considerando el ajuste regional. La presentación pertenece a FIN-AKS-QUOTA-REQUEST y exige autorización explícita nueva; verificar límites efectivos tras respuesta. CLI/API son vías soportadas, pero la API necesita su prerrequisito y no se instala extensión.
4. Si aparece no ajustable, QuotaNotAvailableForResource o derivación a soporte, documentar la causa y solicitar autorización separada para ticket de cuotas. No concluir hoy que un ticket sea obligatorio. Si se detecta carencia efectiva de permisos, intervención del administrador en vez de asignación automática de roles.

No ejecutar un PUT/PATCH/POST de cuota para probar elegibilidad. Una lectura BLOCKED no se elude enviando una solicitud. Mantener AKS NO-GO y no iniciar FIN-AKS-QUOTA-REQUEST.

## Evidencias técnicas y referencias

Se ejecutaron únicamente lecturas, con salida capturada/sanitizada y sin IDs completos: account show; GET subscription; vm list-usage en westeurope; GET Microsoft.Authorization/permissions; provider show Microsoft.Quota; GET de quotas/cores y quotas/standardDSv5Family; GET quotaRequests. No errores de autenticación observados. Errores de cuota identificados como MissingRegistrationForResourceProvider; cero solicitudes es solo el resultado de lista, no una comprobación de ajustabilidad.

Fuentes oficiales consultadas el 15/11/2026:

- [API GET Quota: isQuotaApplicable indica si se puede solicitar](https://learn.microsoft.com/en-us/rest/api/quota/quota/get?view=rest-quota-2025-09-01).
- [API y prerrequisito de registro Microsoft.Quota](https://learn.microsoft.com/en-us/rest/api/quota/).
- [Solicitud por familia y aumento regional automático](https://learn.microsoft.com/en-us/azure/quotas/per-vm-quota-requests).
- [Relación entre cuota regional y familia](https://learn.microsoft.com/en-us/azure/quotas/regional-quota-requests).
- [Restricciones generales de suscripción](https://learn.microsoft.com/en-us/azure/azure-resource-manager/management/azure-subscription-service-limits).
- [Permisos Microsoft.Quota](https://learn.microsoft.com/en-us/azure/role-based-access-control/permissions/general).

## Preservación

Solo se crea este informe. Archivos modificados y sin seguimiento anteriores preservados por SHA-256, sin alteración de Terraform/configuración ni documentación ajena. Lecturas Git limitadas a identificar archivos para comprobar integridad; sin auditoría de ramas, staging, commits o pushes. Sin cambios Azure, solicitudes/tickets, registros de providers, despliegues ni comandos Terraform. Resultado BLOCKED por elegibilidad específica no determinable; no se presenta como fallo definitivo de la oferta PayAsYouGo.
