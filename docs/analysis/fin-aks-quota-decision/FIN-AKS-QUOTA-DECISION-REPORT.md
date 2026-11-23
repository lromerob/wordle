# FIN-AKS-QUOTA-DECISION — Wordle — 15/11/2026

## Resumen y resultado

**PASS del análisis; preparación del despliegue: NO-GO.** El propietario ha aclarado expresamente que Nexo es otro proyecto y que el ámbito es exclusivamente Wordle. No se usan recursos/credenciales de Nexo.

Recomendación: **opción A, mantener DSv5 y proponer límites de 16 vCPU regionales y 16 DSv5 en westeurope**, sujetos a autorización y aprobación Azure. Mínimo para dos nodos más un surge: **12 en ambos límites**, con uso ajeno igual a cero. No se solicita nada hoy. Si Azure no admite la ampliación/oferta, evaluar B; mientras los gates sigan abiertos, mantener C (sin desplegar).

Referencias internas: FIN-AKS-READINESS-REPORT.md (cuotas reales CLI/REST), FIN-AKS-PREREQ-REPORT.md (providers y destino confirmado), infra/terraform/main.tf y variables.tf. No se repiten auditorías, pruebas ni consultas SKU que agotaron tiempo en READINESS: esas limitaciones se conservan explícitas.

## Configuración actual verificada

- westeurope; suscripción aprobada `11306565…1bb5`, tenant `aff0390f…1eb9` conforme a confirmación del propietario. No cambio de contexto ni nueva consulta Azure en esta iteración.
- Pool System de dos `Standard_D4s_v5`: 4 vCPU/16 GiB por nodo; 8 vCPU y 32 GiB nominales totales, menos reservas reales de sistema.
- Sin autoscaling configurado, sin zonas explícitas y **sin bloque upgrade_settings/max_surge**. No se afirma que Terraform fije un surge: el servidor/proveedor resolverá su valor efectivo, a revisar en futuro plan/estado. Para el cálculo solicitado se usa un nodo surge; la documentación AKS describe ese escenario y las necesidades adicionales. No se cambia max_surge.
- OS Ubuntu, discos Managed 64 GB y max_pods=30; base PostgreSQL compartida en PVC 8 GiB. Blue/Green añade Pods, no duplica automáticamente nodos/DB. Requests locales no prueban capacidad AKS.
- Evidencia de cuotas de READINESS: regional 0 usado/10 límite; DSv5 0/0; DSv4 0/10. Son medidas documentadas de la iteración previa, no reconsultadas hoy.

## Dimensionamiento

La disponibilidad de cuota se calcula como límite menos consumo actual en **toda la suscripción/región**, no solo Wordle. El uso previo era cero; revalidarlo antes de solicitar/desplegar.

| Escenario | Nodos simultáneos | Necesidad Wordle | Objetivo mínimo de límite regional y DSv5, sin otros consumos |
|---|---:|---:|---:|
| Operación estable | 2 | 8 vCPU | 8 |
| Actualización con un surge | 3 | 12 vCPU | 12 |
| Recomendación con margen de un nodo | 4 | 16 vCPU | 16 |

Ampliación mínima completa para operación + surge: regional **10→12** (+2) y DSv5 **0→12** (+12). Solo para arrancar, DSv5 0→8 bastaría aritméticamente con la cuota regional actual, pero dejaría sin capacidad de actualización con surge y **no es la recomendación operativa**.

Propuesta recomendada: regional **10→16** (+6) y DSv5 **0→16** (+16). Son límites absolutos solicitados, no incrementos de 16 ni compromiso de crear cuatro nodos. El margen permite un nodo adicional sobre el escenario de tres para contingencia; no se exige por norma académica. No es necesario pedir 20/32 por defecto.

Cuota de familia y regional son puertas independientes. Cuota aprobada no asegura SKU, zona, capacidad física o permiso/política de aprovisionamiento. No se utiliza fallback de actualización in-place ni maxUnavailable para eludir cuota sin una decisión explícita. Otros límites (discos, IP, VMSS) y permisos siguen pendientes del preflight operativo.

Reconstrucción: cuatro nodos simultáneos de dos clústeres consumirían 16; con surge podrían necesitar más. Los 16 recomendados **no autorizan dos clústeres ni garantizan reconstrucción con solapamiento**. La demo mantiene retirada/recreación supervisadas, backup y coste revisados; no se amplía arquitectura.

## Solicitud DSv5: procedimiento preparado, NO ejecutado

Ámbito: suscripción confirmada, Microsoft.Compute, región westeurope, recursos de cuota `standardDSv5Family` y total regional `cores`. Revisar sus nombres exactos devueltos por el proveedor antes de automatizar. Registrar objetivos absolutos y motivo: demo académica temporal, dos D4s_v5 más surge y margen.

Portal: abrir Quotas/My quotas, seleccionar Compute, suscripción y West Europe; localizar Standard DSv5 Family vCPUs y Total Regional vCPUs; Request increase → nuevo límite. Proponer 16 para cada uno, revisar ambos y enviar **solo tras autorización posterior**. Si no está disponible el autoservicio o se rechaza, revisar oferta/limitación y vía de soporte, sin cambiar suscripción automáticamente. Conservar resultado y comprobar límites aprobados antes de planificar.

Permisos: el procedimiento de Portal exige Contributor o equivalente; para API se requiere acceso de cuota al ámbito correspondiente (por ejemplo Quota Request Operator, sujeto a sus acciones y políticas). No asignar roles automáticamente ni asumir que permisos ARM generales prueban elegibilidad. Verificar capacidad de registrar Microsoft.Quota si la vía API lo requiere; su registro NO está autorizado aquí.

Existe CLI mediante extensión `quota`, con `az quota update --resource-name standardDSv5Family --scope /subscriptions/<SUB_APROBADA>/providers/Microsoft.Compute/locations/westeurope --limit-object value=16 --resource-type dedicated`. Es **ejemplo futuro de escritura**, no ejecutado ni verificado en la extensión local. La API de Azure Quota también soporta actualización por ámbito/recurso; consultar versión/esquema oficial antes de usarla. La API Quota falló en READINESS: no se inventa su causa, no se instala extensión ni se registra provider para solventarla. Para este caso se prefiere Portal supervisado. La cuota regional se solicita/revisa por separado; no asumir que la aprobación de familia la aumenta.

Solicitar aumento no tiene coste de solicitud; crear recursos sí. Aprobación, cantidades y plazo están sujetos a Azure y a la oferta. Free Trial y algunas ofertas restringidas no permiten aumentos: el tipo comercial/elegibilidad de esta suscripción **no está verificado**; no se convierte a Pay-as-you-go ni se promete aceptación. La cuota no reserva hardware, no es presupuesto ni límite monetario automático.

Fuentes oficiales: [familia/Portal](https://learn.microsoft.com/en-us/azure/quotas/per-vm-quota-requests), [CLI](https://learn.microsoft.com/en-us/cli/azure/quota), [API actualización](https://learn.microsoft.com/en-us/rest/api/quota/quota/update?view=rest-quota-2025-09-01), [permisos](https://learn.microsoft.com/en-us/rest/api/quota/), [condiciones/coste de solicitud](https://learn.microsoft.com/en-us/azure/quotas/quotas-overview), [restricciones de ofertas](https://learn.microsoft.com/en-us/azure/azure-resource-manager/management/azure-subscription-service-limits).

## DSv4 como alternativa

Standard_D4s_v4 también ofrece 4 vCPU/16 GiB, x64 y discos remotos sin almacenamiento temporal local, al igual que D4s_v5. Es compatible en características nominales con System pool (>=4 vCPU/4 GB) y el modelo de discos Managed del módulo. La generación/procesador, rendimiento de E/S/red y límites no son idénticos: no se supone igualdad de rendimiento ni se infiere que una generación anterior vaya mejor. Elegibilidad regional para AKS e imagen Ubuntu concreta siguen pendientes.

Cuota DSv4 10 y regional 10 permitirían aritméticamente dos nodos (8), pero no tres (12). Pasarse a v4 **no resuelve todo el requisito operativo de surge**: necesita límites >=12 o una estrategia diferente autorizada. El listado SKU D4s_v4 agotó tiempo en READINESS; no se sabe si tiene restricciones de suscripción/zona. La disponibilidad real continúa BLOCKED. Puede reintentarse la consulta o revisarse Portal tras decisión del propietario, sin desplegar para probar.

Precio documentado en READINESS (Retail API, Linux, westeurope, Consumption): v5 0.23 USD/nodo/h, v4 0.31. Dos nodos/4 h: **1.84 frente a 2.48 USD solo cómputo**, diferencia 0.64 USD; no incluye discos, LB/IP, tráfico, estado o surge. Una hora adicional de un surge: 0.23 o 0.31 USD orientativos. No se reconsulta precio ni se presenta como oferta contractual actual. DSv4 no es alternativa de ahorro según esa evidencia.

Fuentes: [Dsv4](https://learn.microsoft.com/en-us/azure/virtual-machines/sizes/general-purpose/dsv4-series), [Dsv5](https://learn.microsoft.com/en-us/azure/virtual-machines/sizes/general-purpose/dsv5-series), [System pools](https://learn.microsoft.com/en-us/azure/aks/use-system-pools), [capacidad de upgrades](https://learn.microsoft.com/en-us/azure/aks/upgrade-capacity-cost-planning).

## Matriz de decisión

| Opción | Viabilidad acreditada | Riesgo/dependencias | Coste y autorización |
|---|---|---|---|
| A — ampliar DSv5 y conservar diseño | Preferente técnicamente; hoy bloqueada por familia 0 | Aprobación de familia y regional, oferta elegible, SKU/capacidad/zona y gates identidad/red/estado | Solicitar 16/16 tras autorización; no crea nodos. Mejor tarifa documentada; creación posterior separada. |
| B — evaluar y autorizar DSv4 | Cuota inicial 8 cabe; SKU/región no verificados y surge no cabe | Verificación AKS/SKU; aumentar familia/regional o aprobar otra estrategia; cambio Terraform explícito | Más caro en evidencia disponible; requiere autorización de cambio, no aplicado. |
| C — mantener bloqueo | Ejecutable inmediatamente sin cambiar nada | Retrasa evidencia AKS FIN-18; no resuelve cuotas ni identidad | Sin nuevos recursos/costes de despliegue. Es el estado operativo vigente hasta cerrar gates. |

## Decisión y autorizaciones pendientes

Elegir A como camino objetivo y C como condición operativa actual. Próxima decisión concreta: **autorizar o rechazar la solicitud de límites absolutos de 16 regionales y 16 DSv5 en West Europe**, después de confirmar elegibilidad de la oferta; si se prefiere mínimo estricto, 12/12 cubre dos nodos + un surge sin margen. No equivale a autorizar plan, CREATE, despliegue o gasto.

Persisten selección de parche AKS compatible, grupo Entra/pertenencia, CIDR, backend externo/permisos y presupuesto/duración. Aprobación de cuota no los cierra. No se ejecuta siguiente iteración automáticamente ni se modifica el plan general.

## Preservación y alcance

Solo se crea este informe. No consultas Azure nuevas ni acciones de escritura, solicitudes de cuota, registros, Terraform ejecutado o modificado, cambios de contexto, despliegues, commits/push ni alteración de otros documentos. Lecturas Git limitadas al inventario de archivos para comprobar preservación por hash; sin auditoría de ramas. Todos los archivos pendientes previos permanecen byte a byte intactos. Análisis de Wordle exclusivamente, sin interacción con Nexo.
