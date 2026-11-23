# FIN-AKS-QUOTA-REQUEST — 15/11/2026

## Resultado: PASS de cuota; AKS NO-GO

Una única solicitud de cuota familiar DSv5 a **límite absoluto 16 vCPU** fue aprobada. El estado de la solicitud es **Succeeded**; Compute Usage verifica **DSv5 16**, uso 0, y **regional 26**, uso 0. Se cumple DSv5 >=16 y regional >=16. No se presentan solicitudes adicionales ni se crean recursos facturables.

## Contexto y preflight

Suscripción `11306565…1bb5`, tenant `aff0390f…1eb9`, Enabled, coincidentes con el destino confirmado; región westeurope verificada en variables.tf. Microsoft.Quota Registered. Cuotas iniciales: DSv5 0 y regional 10, uso 0. GET quotaRequests devolvió cero solicitudes y sin nextLink, sin duplicados pendientes. Las acciones devueltas por permissions permiten Microsoft.Quota/quotas/write.

La primera lectura de isQuotaApplicable falló con MissingRegistrationForResourceProvider antes de cualquier envío. Tras 15 segundos se repitió únicamente la lectura y devolvió true para DSv5; provider seguía Registered. Se revalidaron contexto, ausencia de solicitudes, cuotas y acciones de permiso antes de la escritura. No se utiliza una solicitud como prueba de elegibilidad ni se reintenta una escritura fallida.

## Procedimiento utilizado y única escritura

API oficial [Quota Create Or Update](https://learn.microsoft.com/en-us/rest/api/quota/quota/create-or-update?view=rest-quota-2025-09-01), ejecutada con az rest, mediante PUT al recurso Microsoft.Compute/locations/westeurope/providers/Microsoft.Quota/quotas/standardDSv5Family (api-version=2025-09-01), bajo la suscripción confirmada. No es un endpoint de VM, AKS, reserva de capacidad o soporte.

Cuerpo sin credenciales:

```json
{"properties":{"name":{"value":"standardDSv5Family"},"limit":{"limitObjectType":"LimitValue","value":16}}}
```

Se utilizó archivo JSON temporal nuevo fuera del repositorio para preservar el cuerpo exacto en Windows y se eliminó en finally. No se modificaron archivos existentes. Una única ejecución PUT; sin POST/PATCH de cuota regional, tickets o registros de otros proveedores. La operación solo solicita un límite, no compra ni reserva capacidad.

## Solicitud y seguimiento

- Identificador: **59224f2e-fe6a-452d-9cac-f3072a2e1a90**.
- requestSubmitTime devuelto por Azure: **2026-11-15T17:35:04Z**.
- Respuesta inicial y GET de seguimiento: InProgress, límite solicitado 16, mensaje Request processing.
- Primer seguimiento tras 20 segundos: InProgress; cuotas aún DSv5 0 y regional 10.
- Seguimiento posterior tras otros 20 segundos: **Succeeded**, subsolicitud DSv5 Succeeded, mensaje Request completed.
- Verificación independiente posterior por `az vm list-usage -l westeurope --subscription <ID confirmado>`: límites efectivos de la tabla siguiente.

No se interpretó HTTP/exit 0 o InProgress como aprobación. Solo se declara PASS tras estado definitivo y límites efectivos comprobados.

| Cuota | Inicial | Final verificado | Uso final |
|---|---:|---:|---:|
| Standard DSv5 Family vCPUs | 0 | **16** | 0 |
| Total Regional vCPUs | 10 | **26** | 0 |

## Ajuste regional e incidencias

Azure incrementó automáticamente el regional **10→26**, es decir +16 al aprobar familia **0→16**. Es consistente con la [relación oficial entre cuota familiar y regional](https://learn.microsoft.com/en-us/azure/quotas/regional-quota-requests) y con la aceptación expresa del propietario de un regional superior a 16. No fue necesario ni se presentó una solicitud regional independiente.

Única incidencia: lectura intermitente previa al envío, resuelta mediante GET adicional. Sin rechazo o errores técnicos en la solicitud; no se abrieron tickets. Cuota aprobada no garantiza hardware/SKU/zona disponible, ni permisos/estado/presupuesto o funcionamiento AKS.

## Siguiente decisión y alcance

**AKS continúa NO-GO** por otros prerrequisitos: grupo Entra y pertenencia, CIDR de salida, backend remoto/permisos, versión AKS, presupuesto/duración y capacidad física aún por validar. No se inicia automáticamente plan, creación o despliegue; el propietario debe revisar y autorizar el siguiente incremento concreto.

Cambios efectivos: una solicitud familiar autorizada, aprobada, con ajuste regional automático permitido; este informe nuevo. Sin infraestructura, máquinas, reservas, discos o almacenamiento creados, sin nuevos recursos facturables por esta operación de cuota. No se inspecciona facturación ajena para inferir coste total de la suscripción. No modificación de .tf/.tfvars/configuración/secretos, no Terraform ejecutado, no cambio de contexto ni despliegue. Todos los archivos modificados/sin seguimiento previos se preservan por SHA-256. Sin staging, commits, pushes o alteración del historial Git. Lecturas Git limitadas a inventario para preservar archivos; sin auditoría de ramas.
