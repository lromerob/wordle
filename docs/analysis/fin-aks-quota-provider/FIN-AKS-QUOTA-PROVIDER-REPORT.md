# FIN-AKS-QUOTA-PROVIDER — 15/11/2026

## Resumen ejecutivo: PASS del incremento; elegibilidad 16/16 condicionada

Microsoft.Quota quedó **Registered** tras una única solicitud autorizada. La consulta específica DSv5 devuelve **isQuotaApplicable=true**, lo que permite establecer que la cuota familiar puede solicitarse. La API no devuelve un máximo admisible ni aprobación de 16; el GET regional sigue fallando. Se documenta esa limitación sin declarar la ampliación aprobada. **AKS NO-GO** y ninguna solicitud de cuota/ticket realizada.

La conclusión es suficiente para recomendar preparar una solicitud familiar primero, sujeta a nueva autorización y revisión de condiciones; no para afirmar que ambas cuotas específicas a 16 estén confirmadas por API. El PASS corresponde al registro y a las consultas/diagnóstico exigidos, no al despliegue ni a la aprobación de cuota.

## Contexto y registro

Suscripción `11306565…1bb5` y tenant `aff0390f…1eb9` coincidentes con el destino confirmado por el propietario; suscripción Enabled, sin cambio de contexto/login. Se releyó el informe de elegibilidad y se comprobaron las acciones de permiso antes de registrar.

| Proveedor autorizado | Inicial | Acción | Intermedio | Final |
|---|---|---|---|---|
| Microsoft.Quota | NotRegistered | Una solicitud register, exit 0 | Registering | Registered |

Comando de escritura único: `az provider register --namespace Microsoft.Quota --subscription <ID confirmado> --only-show-errors -o none`. Supervisión mediante provider show exclusivamente; sin repetir registro en Registering. El registro completó dentro de la espera acotada, aproximadamente un minuto; sin errores de registro observados. No se registran otros proveedores.

## Cuotas, ajustabilidad y restricciones

| Comprobación | Estado | Resultado observado |
|---|---|---|
| Provider Quota | PASS | Registered, confirmado antes y después de las consultas. |
| Cuota regional actual | PASS | vm list-usage westeurope: cores uso 0, límite 10. |
| Cuota DSv5 actual | PASS | vm list-usage: uso 0, límite 0; GET específico coincide en límite 0. |
| Ajustabilidad DSv5 | PASS | GET api-version=2025-09-01: isQuotaApplicable=true, unit Count, limitType Independent. |
| Límite familiar absoluto 16 | Condicionada | Recurso admite solicitud, pero no hay máximo ni preaprobación de 16 en respuesta. Revisión Azure/capacidad/oferta siguen aplicando. |
| Ajustabilidad regional por API | BLOCKED | GET quotas/cores conserva MissingRegistrationForResourceProvider tras Registered y reintento. No se interpreta como no ajustable ni se registra otro provider. |
| Listado API versión anterior | BLOCKED | GET quotas?api-version=2023-02-01 devuelve el mismo error. No se atribuye automáticamente a versión o permisos. |
| Solicitudes pendientes | PASS limitado | GET quotaRequests devuelve cero entradas y sin nextLink; no se observan solicitudes en ese endpoint/ámbito. No prueba ausencia de tickets por otra vía. |
| Capacidad física y restricciones SKU | NOT RUN | No se aprovisiona ni se repite catálogo; cuota no reserva hardware. |

Los primeros GET de ambas cuotas devolvieron MissingRegistrationForResourceProvider aun con el provider Registered. Después de una pausa de 20 segundos, DSv5 pasó a devolver datos, pero regional no. La evolución es compatible con propagación; **no prueba la causa exacta del error regional restante** ni justifica volver a registrar. No se repite indefinidamente ni se realiza escritura de prueba.

Payload DSv5 sanitizado: isQuotaApplicable true; limitObjectType LimitValue; limitType Independent; value 0; name standardDSv5Family; unit Count; properties vacío. Según la documentación, isQuotaApplicable indica si puede solicitarse cuota, no que el objetivo 16 vaya a aprobarse. No hay campo de máximo numérico que permita confirmar automáticamente 16. La política PayAsYouGo/Enabled se conserva como evidencia de FIN-AKS-QUOTA-ELIGIBILITY; no se modifica oferta/spendingLimit ni se interpreta como presupuesto aprobado.

## Dependencia familiar y regional

Microsoft documenta que una ampliación aprobada de cuota por serie incrementa automáticamente el regional; la guía regional describe el incremento por la misma cantidad. Por ello, el procedimiento recomendado es **solicitar primero DSv5 con límite absoluto 16**, únicamente después de nueva autorización, y consultar después DSv5 y regional mediante API/Compute Usage.

No enviar dos solicitudes por defecto. Regional debe ser **al menos 16** para el objetivo operativo; no se promete que el ajuste automático lo deje exactamente en 16. Si el propietario exige exactamente 16 y no al menos 16, aclararlo antes de solicitar porque el regional podría acabar superior y las reducciones no se presuponen soportadas. Solo si el regional final sigue por debajo se prepara una solicitud separada, con nueva autorización y verificación de la vía admitida.

El error del GET regional no impide conocer su límite actual por Compute Usage, pero no confirma su ajustabilidad independiente. Antes de necesitar una solicitud regional separada, revisar Azure Quotas en Portal o reintentar lectura tras propagación; soporte solo con autorización expresa si el error persiste y exige intervención. No se crea ticket hoy.

## Siguiente decisión y procedimiento

El propietario debe decidir si autoriza FIN-AKS-QUOTA-REQUEST para **una solicitud familiar DSv5 a 16 en westeurope**, con comprobación posterior del regional y sin solicitud regional automática. Vía preferida: Azure Quotas/Compute en Portal supervisado; API también es posible cuando se revisen esquema/permisos y se dé autorización. No se instala extensión ni se utiliza PUT/PATCH/POST para probar elegibilidad.

Condiciones: confirmar interpretación regional >=16, que la solicitud queda sujeta a aprobación y que no autoriza CREATE/plan/deploy ni gasto. Permisos de cuota previamente observados no garantizan aprobación comercial/capacidad ni ausencia de políticas. Siguen pendientes Entra/pertenencia, CIDR, backend/estado, versión AKS y presupuesto. Mantener AKS NO-GO y no iniciar otra iteración.

## Evidencias y fuentes

Operaciones de lectura ejecutadas: account show; provider show Microsoft.Quota; GET Microsoft.Authorization/permissions para register/action; vm list-usage; GET quotas/cores y quotas/standardDSv5Family (2025-09-01); GET quotaRequests; reintento regional/familia y listado quotas (2023-02-01). Salidas capturadas y sanitizadas sin IDs completos o secretos.

- [API GET y significado de isQuotaApplicable](https://learn.microsoft.com/en-us/rest/api/quota/quota/get?view=rest-quota-2025-09-01).
- [Solicitud por familia, ajustes y límites](https://learn.microsoft.com/en-us/azure/quotas/per-vm-quota-requests).
- [Ajuste automático regional al aumentar familia](https://learn.microsoft.com/en-us/azure/quotas/regional-quota-requests).

## Alcance efectivo y preservación

Única modificación Azure: registro Microsoft.Quota autorizado. Único archivo creado: este informe. Se preservan por SHA-256 todos los cambios y archivos sin seguimiento previos; no se modifica documentación histórica/configuración/estado. Sin solicitudes de cuota, tickets, recursos/RBAC, cambio de contexto, Terraform, despliegues, commits ni pushes. No se accede a secretos ni se interactúa con Nexo. Esperar autorización expresa.
