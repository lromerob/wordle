# FIN-AKS-SWEDEN-QUOTA-REQUEST — Wordle TFG

Fecha: **16/11/2026**. **PASS operativo; solicitud PENDING. Gate A NO-GO y AKS NO-GO.**

## 1. Resumen ejecutivo

Se presentó **una única solicitud familiar DSv5** con límite absoluto **16vCPU** en **swedencentral**, suscripción personal autorizada. Azure aceptó la operación y creó seguimiento **a810bf18-9c0e-498d-8e11-9cc1b7f1c45a**. Al último GET, **15:22:49UTC**, mantiene provisioningState **InProgress**, mensaje **Request processing.** No se declara aprobada.

Límites efectivos posteriores aún **DSv5 0/regional10**, consumo0 en ambos. No se observó ajuste regional todavía ni disponibilidad simultánea de12vCPU. No se reenvía la solicitud ni se presenta otra cantidad/familia/región/cuota regional. El PASS corresponde a ejecución controlada y registro del resultado, no a aprobación Microsoft.

## 2. Autorización y alcance

Adjunto FIN-AKS-SWEDEN-QUOTA-REQUEST del propietario: una solicitud DSv5 a16 totales en Sweden Central, aceptando aumento regional automático incluso por encima de16. No autoriza solicitud regional independiente, recursos, registros de proveedores, permisos, soporte, Terraform o despliegue.

Se leyó FIN-AKS-SWEDEN-QUOTA-ELIGIBILITY-REPORT.md y se reutilizó su identificación exacta de familia/SKU y procedimiento. Sin cambios de región/topología ni modificación de informes anteriores. Dos D4s_v5 implican8vCPU nominales y12 con un surge;16 aporta margen moderado para la demo temporal, no compra ni reserva capacidad.

## 3. Identidad y suscripción verificadas

account show: suscripción **11306565…1bb5**, tenant **aff0390f…1eb9**, Enabled, coincidentes con la referencia autorizada. Graph signed-in-user con proyección soloid: operador **b573130a…a831**. Se repitieron estas comprobaciones inmediatamente antes del envío satisfactorio. Sin cambio de cuenta, tenant, suscripción o login, sin publicar IDs personales completos ni tokens.

## 4. Preflight

| Control | Resultado previo a solicitud |
|---|---|
| Identidad/tenant/suscripción | Coinciden y Enabled |
| Región del recurso de cuota | swedencentral, URL explícita |
| Familia | standardDSv5Family, Standard DSv5 Family vCPUs; correspondencia D4s_v5 acreditada por el catálogo del informe anterior |
| Cuota DSv5 | Límite0; consumo0; disponible0 |
| Cuota regional | Límite10; consumo0; disponible10 |
| Ajustabilidad | isQuotaApplicable=true para ambos GET |
| Solicitudes previas | quotaRequests devuelve cero entradas, sin nextLink; se confirma de nuevo antes del único PUT |
| Proveedor | Microsoft.Quota Registered, no se registra |
| Permisos | GET permissions devuelve actions=* sin notActions en una entrada; incluye quotas/write y lecturas/seguimiento; no se modifican roles |
| Límite autorizado |0<16; no reducción, exceso o solicitud redundante |

Las acciones ARM devueltas no son garantía universal frente a Policy/deny; la aceptación real acredita que esta operación concreta se pudo presentar. No se repitió el catálogo SKU de varios minutos porque la correspondencia exacta se había verificado en la iteración anterior y la cuota actual la confirma por nombre. No se realizó auditoría general de Git ni de otros proyectos.

## 5. Cuotas anteriores

Consulta independiente Compute Usage api-version2024-03-01, filas name.value cores y standardDSv5Family, unit Count. GET Quota2025-09-01 concordante con límites:

| Cuota | Límite | Consumo | Disponible |
|---|---:|---:|---:|
| standardDSv5Family |0|0|0|
| cores — total regional |10|0|10|

No se extrapoló cuota desde West Europe ni se confundió límite con disponible.

## 6. Solicitud presentada

**Un único PUT ejecutado**, iniciado **2026-11-16T15:20:17.227453Z**. Azure CLI exit0. Endpoint oficial, sanitizado:

`PUT https://management.azure.com/subscriptions/<aprobada>/providers/Microsoft.Compute/locations/swedencentral/providers/Microsoft.Quota/quotas/standardDSv5Family?api-version=2025-09-01`

Cuerpo exacto sin credenciales:

```json
{"properties":{"name":{"value":"standardDSv5Family"},"limit":{"limitObjectType":"LimitValue","value":16}}}
```

Se utilizó `az rest --method put --url <endpoint> --body @<JSON-temporal> --headers Content-Type=application/json -o json`. JSON temporal nuevo fuera del repositorio eliminado mediante finally, con confirmación TEMPORARY_BODY_REMOVED. No script ni configuración persistente adicional. No PUT regional, POST/PATCH, soporte, cuotas de otras familias/regiones o capacidad reservada.

Justificación técnica de la autorización: AKS académico temporal Wordle, dos nodos4vCPU con un surge; pico12 y margen4. El esquema de solicitud utilizado no contiene campo libre de justificación, por lo que **no se afirma haber enviado ese texto a Azure**: se envió exclusivamente el cuerpo mostrado.

## 7. Identificador de seguimiento

**a810bf18-9c0e-498d-8e11-9cc1b7f1c45a**.

URI de seguimiento sanitizada:

`GET https://management.azure.com/subscriptions/<aprobada>/providers/Microsoft.Compute/locations/swedencentral/providers/Microsoft.Quota/quotaRequests/a810bf18-9c0e-498d-8e11-9cc1b7f1c45a?api-version=2025-09-01`

requestSubmitTime devuelto: **2026-11-16T15:20:19Z**. El subRequestId coincide con el ID anterior. No se interpreta el ID de seguimiento como recurso AKS/Compute aprovisionado.

## 8. Respuesta de Azure

Respuesta inicial parseada: recurso quotaRequests con ID anterior; properties.isQuotaApplicable=true, limit.value16, name.value=STANDARDDSV5FAMILY y provisioningState=InProgress. La normalización a mayúsculas en la respuesta es de Azure; petición/endpoint usaron el identificador técnico verificado standardDSv5Family.

GET posteriores devuelven message **Request processing.**, estado general y subsolicitud **InProgress**, cantidad16. No se capturó un código HTTP separado porque no se activaron logs verbose/debug para extraer cabeceras; exit0 y seguimiento legible acreditan aceptación, no aprobación. No se inventa HTTP202 o200 específico.

## 9. Estado de la solicitud

**PENDING**. Seguimiento inicial y tres consultas adicionales, con esperas acotadas de20segundos entre consultas (más tiempo de herramientas/procesamiento), conservaron InProgress. Última observación: **2026-11-16T15:22:49.066340Z**, aproximadamente2m30s tras requestSubmitTime.

No existe respuesta de rechazo ni conclusión Succeeded/Failed observada. No se garantiza plazo. Microsoft puede aprobar, rechazar o requerir revisión adicional. La iteración permite PASS operativo coexistiendo con PENDING; no es una incertidumbre sobre si se envió: existe solicitud identificada y legible. No se mantuvo supervisión indefinida ni se configuró monitor automático.

## 10. Cuota DSv5 posterior

Último GET Compute Usage: **límite0, consumo0, disponible0vCPU**. El valor16 del cuerpo de solicitud no se presenta como límite concedido. Continúa pendiente aprobación; no se crea máquina para verificarla.

## 11. Cuota regional posterior

Último GET Compute Usage: **límite10, consumo0, disponible10vCPU**. No solicitud independiente regional; no se intentó forzar el ajuste. El límite regional no cambió dentro de la ventana observada.

## 12. Ajuste automático observado

**Ninguno hasta el cierre**, mientras la solicitud está InProgress. La autorización permite el aumento regional automático por la aprobación familiar, incluso si supera16; eso no permite una petición regional separada.

Microsoft documenta el ajuste regional al aprobar familia. El resultado esperado con datos0→16/10 inicial sería regional26 según esa regla, pero **no se declara aplicado ni garantizado**. Tras resolución deberá consultarse el valor real; si es insuficiente, documentar bloqueo y detener, no remediar mediante otra solicitud.

[Relación oficial entre cuota familiar y regional](https://learn.microsoft.com/en-us/azure/quotas/regional-quota-requests).

## 13. Disponibilidad para12vCPU

| Cuota | Antes: límite/usado/disponible | Después observado: límite/usado/disponible | ¿Disponible>=12? |
|---|---|---|---|
| DSv5 |0/0/0|0/0/0|No|
| Regional |10/0/10|10/0/10|No|

**Escenario dos nodos+surge todavía bloqueado por cuota.** Los dos límites deben cumplirse simultáneamente. Incluso una aprobación futura de16 no garantiza SKU/capacidad física, disponibilidad zonal ni admisión de AKS/Storage frente a restricciones regionales/políticas. Catálogo sin restricciones no sustituye esa evidencia.

## 14. Incidencias y restricciones

Una revalidación familiar previa a cualquier envío falló en lectura (PREFLIGHT_READ_FAILED), sin alcanzar SINGLE_PUT_STARTED ni crear archivo temporal/ejecutar PUT. La comprobación diagnóstica siguiente recuperó isQuotaApplicable=true/límite0 y requests vacío. Se repitió preflight de identidad/familia/ausencia de solicitud y entonces se ejecutó **el único PUT**. No se registra un código Azure concreto para ese fallo inicial, porque ese helper no lo capturó; no se inventa MissingRegistration ni se atribuye causa. No se modificó provider/RBAC para resolverlo.

No errores observados en el envío o seguimiento. InProgress es una revisión pendiente, no fallo técnico ni rechazo. No hubo reintento de escritura por incertidumbre ni duplicado. Si la resolución requiere soporte/roles/registro/cambio de cuota, detener y pedir autorización específica. No se envía otra cantidad ni región como alternativa automática.

## 15. Costes o recursos creados

Única modificación Azure: **solicitud administrativa de cuota familiar autorizada**, todavía pendiente. Sin máquinas, AKS, Storage Accounts, discos/redes/reservas, presupuestos, alertas o servicios adicionales. rg-wordle-state no se modifica ni elimina.

Solicitar cuota no aprovisiona recursos facturables ni reserva capacidad. La facturación futura depende del consumo, no del límite administrativo; no es una auditoría de costes totales ajenos de la suscripción. No se ejecutó Terraform, no se cambió región/topología/Policy/roles ni se registraron proveedores.

Fuente: [cuotas, coste y ausencia de garantía de capacidad](https://learn.microsoft.com/en-us/azure/quotas/quotas-overview).

## 16. Estado de Gate A y AKS

**Gate A NO-GO; AKS NO-GO.** No hay aprobación familiar efectiva y no existe backend remoto operativo. El resultado de cuota no resuelve automáticamente Entra/grupo, IP/CIDR, versión/surge, presupuesto, bootstrap o validación real AKS.

Se crea exclusivamente este informe. Todos los archivos pendientes anteriores se comprueban por SHA-256 al crear el entregable; se conservan índice y lista de cambios versionados, informes históricos y configuraciones. Sin staging, commits, pushes o alteración del historial Git. No se crean otros archivos persistentes; JSON temporal eliminado. No se leen secretos ni se opera en Nexo u otros proyectos.

## 17. Próxima acción recomendada

**Consultar posteriormente por GET el mismo ID**, con nueva instrucción del propietario, hasta conocer su conclusión; no reenviar la solicitud. Verificar de nuevo Compute Usage y disponibilidad familiar/regional; APPROVED requiere límite familiar16 y estado completado/aprobado. Si regional sigue insuficiente, informar y detener sin petición adicional.

Si permanece pendiente, conservar ID; si se rechaza, registrar código/motivo y esperar decisión, sin soporte automático. Una aprobación de cuota solo permitiría retomar las decisiones de backend/región y demás prerrequisitos mediante autorizaciones separadas; no es permiso de desplegar. Se detiene la iteración aquí.

Fuentes oficiales del procedimiento, consultadas16/11/2026: [solicitudes familiares](https://learn.microsoft.com/en-us/azure/quotas/per-vm-quota-requests), [API CreateOrUpdate y seguimiento](https://learn.microsoft.com/en-us/rest/api/quota/quota/create-or-update?view=rest-quota-2025-09-01). Evidencia primaria del resultado: respuesta del único PUT, GET quotaRequests por ID y GET ComputeUsage regionales; todos sanitizados en este informe.
