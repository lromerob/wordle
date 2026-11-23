# FIN-AKS-REGION-SELECTION — Wordle TFG

Fecha de consultas: 16/11/2026. **PARTIAL: comparación fundamentada y recomendación provisional; no hay región habilitada para desplegar con las cuotas actuales. Gate A y AKS NO-GO.**

## 1. Resumen ejecutivo

Se propone **Sweden Central como preferida provisional**, con dos Standard_D4s_v5, por ser la alternativa europea más barata comparada y disponer de comprobación satisfactoria del catálogo SKU sin restricciones devueltas. **East US es la alternativa y el mínimo económico calculado**, pero falta completar su consulta de restricciones de SKU. Si esa comprobación y el acceso regional fueran satisfactorios, East US pasaría a ser la preferida por coste; no se requiere residencia europea. No se afirma que Sweden Central sea la región globalmente más barata ni que alguna permita aprovisionar hoy.

**Bloqueo confirmado común a las cinco alternativas:** cuota DSv5 0, regional 10, consumo 0 en ambas; ninguna admite los 12 vCPU del escenario aprobado con surge. West Europe tiene 16/26 y consumo 0, pero el rechazo regional heredado impide recomendarla. Catálogo, versiones y cuotas no prueban capacidad física ni admisión de una creación.

Dos nodos en Sweden Central: subtotal estimado 0,88916 / 1,77833 / 5,33498 USD para 2 / 4 / 12 horas. East US: 0,83557 / 1,67115 / 5,01344 USD. **No son costes totales:** faltan Load Balancer, tráfico, operaciones de disco/estado, retención y otros consumos dependientes del uso. Diferencia del subtotal en tres sesiones de cuatro horas: 0,32153 USD. No justifica elegir una región menos comprobada solo por precio.

## 2. Objetivos y restricciones

Análisis regional para demo académica privada y temporal: PostgreSQL único, Blue-Green de aplicación, observabilidad autogestionada, reconstrucción y retirada supervisadas. Sin requisito de latencia o residencia geográfica. Se consultaron los seis informes solicitados (diagnóstico Storage, bootstrap, preparación, configuración, lifecycle y preflight), además de main.tf/variables.tf. Las secciones históricas se interpretan por fecha; no se reescriben.

Único entregable nuevo: este informe. No Terraform, despliegues, pruebas de creación, registro de proveedores, solicitudes de cuota, cambios RBAC/Policy, tickets, cambios de región/configuración, commits ni push. No se consultaron secretos, estados Terraform ni recursos de otros proyectos.

## 3. Estado del bloqueo West Europe

FIN-AKS-STORAGE-DENIAL-DIAGNOSIS acredita RequestDisallowedByAzure en Storage write, 16/11/2026 13:21:10Z, correlación 2b97ec26-36cf-42c0-ad62-1a2411032364. Mensaje: la región no acepta nuevos clientes. Evento Policy correlacionado identifica **sys.blockwesteurope**, efecto deny; definición 7509877f-d414-4d79-8d1f-d600ea78d087 con condición location=westeurope. GET de asignación en management group fue AuthorizationFailed; GET de definición sí permitió recuperar la regla.

El recurso cuyo rechazo está demostrado es la cuenta Storage; no se pretende haber intentado crear AKS. La restricción heredada constituye un bloqueo/riesgo regional efectivo, aunque el catálogo y las cuotas sean suficientes. No se sortea ni se solicita excepción. rg-wordle-state, creado previamente y documentado vacío, se conserva íntegro; no se vuelve a enumerar infraestructura ajena. La cuenta prevista no llegó a crearse. El informe de diagnóstico conserva la evidencia causal completa.

## 4. Regiones evaluadas

North Europe, France Central, Germany West Central, Sweden Central; se añade **East US** como contraste no europeo por tarifa D4s_v5 inferior, sin requisito de residencia/latencia que la excluya. West Europe solo referencia bloqueada. El análisis no pretende búsqueda exhaustiva de todas las regiones mundiales.

East US implica mayor latencia administrativa potencial desde España; no se midió. No afecta por principio a una demo supervisada, pero puede influir en tiempos de pulls, exportación y acceso operativo. La diferencia monetaria calculada es pequeña en ventanas cortas.

## 5. Políticas y restricciones

Contexto actual verificado sin cambiarlo: suscripción **11306565…1bb5**, tenant **aff0390f…1eb9**, Enabled; operador Graph propio **b573130a…a831**. GET subscription: quotaId PayAsYouGo_2014-09-01, locationPlacementId Public_2014-09-01, spendingLimit Off. No se clasifica como Students/Free Trial ni se presuponen créditos.

Los cuatro proveedores Microsoft.Storage, Microsoft.ContainerService, Microsoft.Compute y Microsoft.Network devuelven **Registered**. Sus metadatos incluyen las seis regiones para storageAccounts, managedClusters, virtualMachines, virtualNetworks, publicIPAddresses y loadBalancers. Esto confirma catálogo publicado para los recursos, no elegibilidad de creación.

Listado actual de Policy assignments en suscripción con disable-scope-strict-match: **cero entradas**. El deny heredado conocido y la imposibilidad previa de leer su asignación superior muestran que esa lista no es exhaustiva. Para las cinco alternativas: **sin otro deny detectado en las lecturas accesibles; restricciones superiores no verificables completamente**. No se afirma que Storage/Compute/AKS/Network estén permitidos efectivamente en ellas. Ninguna tiene aprovisionamiento validado.

GET permissions en suscripción devuelve una entrada actions=* sin notActions, con dataActions vacías. Acredita acciones ARM devueltas, no eliminación de deny/condiciones, permisos Graph, acceso Blob ni autorización de gasto. No se modificó ninguna identidad o permiso.

## 6. Disponibilidad de AKS

managedClusters figura en las seis regiones y `az aks get-versions` devuelve correctamente 1.35 con parches en todas. Es evidencia del catálogo consultado con la suscripción activa; no una prueba de creación ni una reserva de capacidad.

Free está publicado para regiones públicas donde AKS está soportado: gestión del clúster sin cargo de ese tier, pero recursos consumidos facturables y sin SLA financiero. Entra administrado + Kubernetes RBAC, Azure CNI Overlay y Standard Load Balancer están documentados para AKS; no se ha detectado en las fuentes consultadas una exclusión específica de estas regiones. Su combinación exacta con identidad, red, Ubuntu y AzureRM 4.50.0 sigue pendiente de plan y ejecución autorizados. No se confunde soporte publicado con validación por suscripción.

Terraform actual ya define sku_tier Free, RBAC, cuentas locales deshabilitadas, Entra con grupo obligatorio y azure_rbac_enabled=false, Overlay, Standard LB de salida y una IP gestionada. No ACR, NAT Gateway o monitorización premium. Grupo/membresía, IP administrativa aprobada y validación de solapamientos externos siguen pendientes según preflight.

Fuentes: [tiers y disponibilidad regional](https://learn.microsoft.com/en-us/azure/aks/free-standard-pricing-tiers), [Entra del control plane](https://learn.microsoft.com/en-us/azure/aks/entra-id-control-plane-authentication), [CNI Overlay](https://learn.microsoft.com/en-us/azure/aks/azure-cni-overlay), [Standard LB](https://learn.microsoft.com/en-us/azure/aks/load-balancer-standard).

## 7. Versiones Kubernetes

**Confirmado por consulta actual en las seis regiones:** rama 1.35 con parches 1.35.0 a **1.35.9**, incluido el candidato exacto. No se sustituye por la versión regional predeterminada. La minor 1.35 es GA según calendario Microsoft (marzo 2026), fin de soporte estándar marzo 2027; el catálogo no garantiza que el mismo parche siga ofertado en otra sesión.

Terraform conserva kubernetes_version=null; seleccionar 1.35.9 exige aprobación y cambio posterior separado. También sigue pendiente hacer explícito max_surge=1; el cálculo de 12 vCPU es el escenario solicitado, no configuración ya aplicada. Revalidar parche y soporte antes de un futuro plan. [Calendario oficial AKS](https://learn.microsoft.com/en-us/azure/aks/supported-kubernetes-versions).

## 8. Cuotas y capacidad

GET ARM `Microsoft.Compute/locations/<region>/usages?api-version=2024-03-01`, filtrando name.value cores y standardDSv5Family. Columnas límite/usado/disponible, en vCPU. No se interpreta una lista vacía como cero: aquí se recuperaron ambas filas en cada región.

| Región | DSv5 límite/usado/disponible | Regional límite/usado/disponible | ¿12 disponibles en ambas? | Acción necesaria |
|---|---|---|---|---|
| North Europe | 0 / 0 / 0 | 10 / 0 / 10 | No | Ampliación familiar y regional |
| France Central | 0 / 0 / 0 | 10 / 0 / 10 | No | Ampliación familiar y regional |
| Germany West Central | 0 / 0 / 0 | 10 / 0 / 10 | No | Ampliación familiar y regional |
| Sweden Central | 0 / 0 / 0 | 10 / 0 / 10 | No | Ampliación familiar y regional |
| East US | 0 / 0 / 0 | 10 / 0 / 10 | No | Ampliación familiar y regional |
| West Europe | 16 / 0 / 16 | 26 / 0 / 26 | Sí aritméticamente | Bloqueo Policy independiente |

Mínimo del escenario A: 12 disponibles en ambas; objetivo conservador anterior 16/16 solo puede proponerse de nuevo en la región elegida, no trasladarse de West Europe ni solicitarse bajo esta autorización. La elegibilidad/aprobación de futuras ampliaciones sigue pendiente.

**SKU:** Sweden Central devuelve Standard_D4s_v5 con restrictions=[] mediante `az vm list-skus --location swedencentral --size Standard_D4s_v5 --resource-type virtualMachines --all`. No prueba asignación física ni anula cuota 0. D4s_v5 está publicado con 4 vCPU/16 GiB y tiene tarifa regional en todas las regiones comparadas. Para North Europe, France Central, Germany West Central y East US, las consultas de restricciones SKU no produjeron resultado utilizable dentro de esta ejecución y se interrumpieron; no se presentan como restricciones vacías. Un intento ARM alternativo de catálogo East US terminó con MemoryError de Azure CLI y error de interpretación del argumento URL; no es una denegación Azure ni evidencia sobre la región. No se reintentó una creación. La restricción histórica por zonas 1 y 3 de West Europe no se revalidó y no se extrapola a otras regiones.

La primera consulta CLI de usage no completó a tiempo; se sustituyó por GET ARM acotado y se obtuvieron las cifras anteriores. Consultas iniciales con proyección JMESPath fallida no se usan como evidencia de ausencia; get-versions sin esa proyección sí tuvo éxito. Sin herramientas nuevas ni cambios de configuración para resolver las incidencias.

[Dsv5 oficial](https://learn.microsoft.com/en-us/azure/virtual-machines/sizes/general-purpose/dsv5-series). Cuota, restricción de catálogo y capacidad física son controles distintos; no se ha reservado capacidad ni validado una zona.

## 9. Comparación de topologías

| Escenario | Cómputo nominal / con surge | Utilidad y límites | Decisión |
|---|---|---|---|
| A: dos D4s_v5 | 8 / 12 vCPU | Distribución entre nodos, reprogramación y pruebas de escalabilidad; Blue-Green compartiendo PostgreSQL. Dos nodos no convierten PostgreSQL único/PVC en HA; sin zonas fijadas no se demuestra tolerancia zonal. Reservas AKS, CSI, DaemonSets y picos requieren runtime. | Recomendado inicial y para pruebas completas, sujeto a cuota/acceso |
| B: un D4s_v5 | 4 / 8 vCPU, cálculo hipotético | Reduce aproximadamente a la mitad VM y discos OS, sin redundancia entre nodos. No permite demostrar distribución/fallo entre nodos y puede limitar el stack completo. | No adoptable con configuración actual |
| C: uno → dos | Variable | Ahorro solo durante fase inicial de un nodo; agrega una operación de escalado, espera, evidencia y riesgo operativo. | No recomendado en esta iteración |

La documentación vigente de [System pools](https://learn.microsoft.com/en-us/azure/aks/use-system-pools) y [creación de pools](https://learn.microsoft.com/en-us/azure/aks/create-node-pools) establece al menos dos nodos System. Independientemente de posibles comportamientos históricos de la API para demos, variables.tf valida node_count entero >=2. Por tanto B/C requieren revisar tanto soporte del servicio como arquitectura y validación Terraform, con autorización; no basta cambiar una variable. No se presume una excepción académica.

Hipótesis puramente económica de C en Sweden: pasar las primeras dos horas de una sesión de cuatro con un nodo ahorraría unos 0,43876 USD de VM+OS frente a dos nodos toda la sesión; no incluye el tiempo/coste del escalado y no es una configuración compatible validada. Se prefiere reducir la duración de sesiones y reconstruir entre ellas, conservando las pruebas completas, antes que alterar el mínimo del pool.

## 10. Comparación económica

Consulta Azure Retail Prices API oficial el **16/11/2026**, USD, Consumption, Linux Dsv5, sin Windows/Spot/Low Priority/reservas/savings plans/descuentos/créditos. Tarifas retail orientativas sin impuestos ni conversión EUR; no cotización contractual. Para VM: armRegionName, armSkuName=Standard_D4s_v5, priceType=Consumption; seleccionar skuName exacto y producto Linux. Las respuestas tienen vigencias históricas del medidor, no fecha de creación de esta estimación.

| Región | VM USD/nodo-h | OS P6 LRS USD/mes | PG E2 LRS USD/mes | IPv4 Standard USD/h | Hot LRS USD/GB-mes | Blob write / read USD/10K |
|---|---:|---:|---:|---:|---:|---:|
| North Europe | 0,214 | 10,207 | 0,60 | 0,005 | 0,0220 | 0,050 / 0,0040 |
| France Central | 0,224 | 12,3499 | 0,66 | 0,005 | 0,0192 | 0,059 / 0,0047 |
| Germany West Central | 0,230 | 11,227 | 0,60 | 0,005 | 0,0196 | 0,054 / 0,0043 |
| Sweden Central | 0,204 | 11,2272 | 0,60 | 0,005 | 0,0184 | 0,050 / 0,0040 |
| East US | 0,192 | 10,207 | 0,60 | 0,005 | 0,0208 | 0,050 / 0,0040 |
| West Europe (bloqueada) | 0,230 | 11,2272 | 0,60 | 0,005 | 0,0196 | 0,054 / 0,0043 |

Discos: medidores exactos P6 LRS Disk y E2 LRS Disk, sin confundir Disk Mount. Hipótesis de estimación: un OS Premium SSD 64 GiB por nodo y un PostgreSQL Standard SSD 8 GiB. main.tf fija tamaño/tipo Managed, no verifica aquí tier OS efectivo; el disco real/facturación se comprobarán después. Prorrateo orientativo mes=730h; no garantía de factura. Una IP de salida, sin IP pública adicional para la app (port-forward). Ajustar si el inventario real difiere.

**Cómputo exclusivamente**, 2 / 4 / 12 horas; 12= tres sesiones de cuatro, no clúster persistente entre sesiones:

| Región | Un nodo (hipotético) USD | Dos nodos USD |
|---|---|---|
| North Europe | 0,428 / 0,856 / 2,568 | 0,856 / 1,712 / 5,136 |
| France Central | 0,448 / 0,896 / 2,688 | 0,896 / 1,792 / 5,376 |
| Germany West Central | 0,460 / 0,920 / 2,760 | 0,920 / 1,840 / 5,520 |
| Sweden Central | 0,408 / 0,816 / 2,448 | 0,816 / 1,632 / 4,896 |
| East US | 0,384 / 0,768 / 2,304 | 0,768 / 1,536 / 4,608 |
| West Europe | 0,460 / 0,920 / 2,760 | 0,920 / 1,840 / 5,520 |

**Subtotal conocido estimado** = h × (n×precio_VM + n×OS/730 + PG/730 + IPv4). Excluye expresamente conceptos posteriores:

| Región | Un nodo: 2h / 4h / 12h USD | Dos nodos: 2h / 4h / 12h USD |
|---|---|---|
| North Europe | 0,46761 / 0,93522 / 2,80565 | 0,92357 / 1,84715 / 5,54144 |
| France Central | 0,49364 / 0,98729 / 2,96186 | 0,97548 / 1,95096 / 5,85287 |
| Germany West Central | 0,50240 / 1,00481 / 3,01442 | 0,99316 / 1,98632 / 5,95897 |
| Sweden Central | 0,45040 / 0,90081 / 2,70242 | 0,88916 / 1,77833 / 5,33498 |
| East US | 0,42361 / 0,84722 / 2,54165 | 0,83557 / 1,67115 / 5,01344 |
| West Europe | 0,50240 / 1,00481 / 3,01442 | 0,99316 / 1,98633 / 5,95898 |

Complementos: para Sweden, dos nodos durante4h suman VM1,632 + OS0,12304 + PG0,00329 + IP0,020 =1,77833USD. Un surge durante1h añadiría unos0,21938USD de VM+OS, más conceptos de uso no cuantificados. Las duraciones deben incluir aprovisionamiento, esperas, pruebas y retirada mientras los recursos sigan facturándose, no solo tiempo de demo HTTP.

**No cuantificado, no cero:** Standard LB (reglas/salida y datos procesados), tráfico saliente real, operaciones Standard SSD, retenciones/snapshots si los hubiera, operaciones/capacidad real del estado y otros recursos que un futuro plan/inventario muestre. Las seis consultas retail serviceName='Load Balancer' devolvieron cero medidores; la página oficial mostró importes $- sin valor numérico. No se inventa una tarifa ni se presenta subtotal como total. [Precio oficial LB](https://azure.microsoft.com/en-us/pricing/details/load-balancer/).

Bandwidth retornó, para estas regiones, Standard Data Transfer Out con producto Rtn Preference: MGN: tier inicial0USD/GB, tier desde100GB0,087USD/GB; ruta Internet publicada0,08USD/GB desde100GB. Tráfico interregional publicado0,02USD/GB. La selección contractual/ruta, uso mensual compartido y volúmenes no se verificaron: no se presume egreso gratis ni se cambia routing preference. No sumar medidores alternativos como si todos facturaran a la vez.

Coste del ciclo = subtotales de sesiones + surge real + LB/datos/operaciones + periodos de aprovisionamiento/retirada + retención del backend/backups/remanentes. **Total y techo monetario pendientes**, no justificados por estos subtotales. Las alertas presupuestarias no son un límite automático de gasto. No se aprueba presupuesto con este diagnóstico.

Fuentes y reproducción: [API](https://prices.azure.com/api/retail/prices), [documentación de filtros/unidades](https://learn.microsoft.com/en-us/rest/api/cost-management/retail-prices/azure-retail-prices). Filtros adicionales: Storage/Premium SSD Managed Disks o Standard SSD Managed Disks; General Block Blob v2/Hot LRS/tierMinimumUnits0; Virtual Network/IP Addresses/Standard IPv4 Static Public IP; Bandwidth. Se recorrió paginación cuando estuvo presente en la consulta económica completa. No se conservaron respuestas como archivos adicionales.

## 11. Backend Terraform

Storage Accounts figura en todas las regiones comparadas; Standard general-purpose v2 soporta LRS y Blob, con Entra/RBAC, firewall, versioning y soft delete documentados. **Su creación no está validada para la suscripción en ninguna alternativa.** Mantener la ficha de seguridad: HTTPS/TLS1.2, anonimato/SharedKey deshabilitados, Deny/None, IP individual administrativa vigente, contenedor privado y rol Blob al ámbito del contenedor; sin claves/SAS ni red abierta.

Se recomienda inicialmente backend y AKS en **Sweden Central**, sujeto a aprobación y admisión regional. Una sola región simplifica fichas y evidencias; la administración del estado seguirá desde el PC, no requiere conectividad del Pod al backend. Alternativa: backend en Sweden y AKS en East US si solo esta última obtiene cuota; no hay necesidad técnica de colocarlos juntos. El ahorro por separar un estado pequeño no es relevante frente a la complejidad; no exige VNet/Private Endpoint/NAT adicionales.

rg-wordle-state existente permanece en West Europe. Ubicación de metadatos del RG y de un recurso pueden diferir; esto no autoriza crear nada dentro de ese RG ni garantiza que las políticas lo admitan. El propietario deberá aprobar explícitamente su reutilización y ubicación de la futura cuenta. No se elimina, traslada, modifica ni reserva nombre. Terraform conserva westeurope y backend no operativo.

Coste residual entre sesiones: capacidad efectiva media (estado actual + versiones + soft-deleted) × precio GB-mes × fracción del mes + writes/list/read/other + otros cargos aplicables. Ejemplo sintético Sweden30d:100MiB efectivos +1000writes +1000reads =0,001796875+0,005+0,0004 = **0,007196875USD**. East US mismo ejemplo≈0,00743125USD. Diferencia mensual≈0,000234375USD; no justifica separar regiones por precio. No es consumo medido ni límite; la retención de versiones puede aumentarlo. Lifecycle asíncrono y soft delete pueden prolongarlo.

Entre sesiones se pretende conservar solo backend/estado y artefactos/backups privados aprobados, con custodio, segunda copia y fecha de revisión. No basta detener AKS para eliminar costes de discos/IP/LB. La retirada de recursos y del backend final exige autorización y evidencia independiente; no se ejecuta ahora.

Fuentes: [StorageV2/LRS](https://learn.microsoft.com/en-us/azure/storage/common/storage-account-overview), [firewall y autorización](https://learn.microsoft.com/en-us/azure/storage/common/storage-network-security), [protección de datos](https://learn.microsoft.com/en-us/azure/storage/blobs/data-protection-overview), [backend azurerm](https://developer.hashicorp.com/terraform/language/backend/azurerm).

## 12. Matriz de decisión

Leyenda: **C** confirmado por consulta actual o evidencia histórica identificada; **E** estimado; **NV** no verificable con resultados disponibles; **PO** pendiente de validación operativa. Soporte publicado no equivale a autorización de creación.

| Criterio | North Europe | France Central | Germany West Central | Sweden Central | East US | West Europe |
|---|---|---|---|---|---|---|
| Policy | NV heredadas; sin otro deny detectado | Igual | Igual | Igual | Igual | C deny Storage observado |
| AKS catálogo / Free publicado | C / C; PO creación | Igual | Igual | Igual | Igual | Igual; bloqueo regional |
| Kubernetes1.35.9 listado | C | C | C | C | C | C |
| D4s_v5 tarifa publicada | C | C | C | C | C | C |
| Restricción SKU por suscripción | NV consulta incompleta | NV | NV | C restrictions=[]; PO capacidad | NV consulta fallida | Histórico zonas1/3; no revalidado |
| DSv5 disponible | C0 | C0 | C0 | C0 | C0 | C16 |
| Regional disponible | C10 | C10 | C10 | C10 | C10 | C26 |
| Storage catálogo / creación permitida | C / NV-PO | Igual | Igual | Igual | Igual | C / rechazo C |
| Subtotal2nodos2h USD (E) | 0,92357 | 0,97548 | 0,99316 | 0,88916 | 0,83557 | 0,99316 |
| Subtotal2nodos4h USD (E) | 1,84715 | 1,95096 | 1,98632 | 1,77833 | 1,67115 | 1,98633 |
| Subtotal2nodos12h USD (E) | 5,54144 | 5,85287 | 5,95897 | 5,33498 | 5,01344 | 5,95898 |
| Riesgo principal | Cuota + visibilidad/capacidad | Igual; mayor coste | Igual; mayor coste | Cuota + Policy/operación no probadas | Cuota + SKU/Policy pendientes | Denegación heredada |
| Viabilidad actual | No, cuota | No, cuota | No, cuota | No, cuota; preferida condicional | No, cuota; alternativa económica | No, bloqueo Policy |

No se asignan puntuaciones arbitrarias. Orden de decisión: admisión regional y cuota/SKU → coste comparable → reproducción y sencillez. Ninguna está validada operativamente.

## 13. Región recomendada

**Sweden Central, provisional y condicionada**, no cambio aprobado. Es la opción europea de menor subtotal entre las comparadas; el catálogo objetivo se comprobó sin restricciones y falta solucionar cuota. Dos D4s_v5 desde el inicio y durante pruebas completas. Backend en misma región por sencillez si se autoriza y admite. Costes parciales detallados arriba, sin presentar0,89/1,78/5,33USD como presupuesto total.

Elegir una región con DSv5=0 no es recomendar desplegar incumpliendo un bloqueo: es priorizar la candidata para la siguiente decisión de elegibilidad/cuota. **No hay región inmediatamente desplegable acreditada.** Si el propietario exige una región utilizable sin ampliaciones ni aclaraciones de acceso, el resultado operativo es BLOCKED.

## 14. Alternativa

**East US**, por menor cómputo y menor subtotal conocido (0,84/1,67/5,01USD para dos nodos2/4/12h). Pendiente consulta utilizable de restricciones SKU y habilitación de cuotas/acceso. Si obtiene evidencia equivalente a Sweden, pasa a ser primera por coste; si Sweden tiene acceso y East US no, mantener Sweden. La latencia no se usa como veto sin medición. North Europe queda tercera opción económica entre las europeas, sin ventajas de cuota verificadas; no se selecciona automáticamente.

## 15. Riesgos y validaciones pendientes

- Políticas superiores no completamente legibles; el catálogo Storage/AKS no acredita admisión. No se declara ninguna alternativa libre de deny.
- Cuotas DSv5/regional insuficientes en todas las alternativas; ampliación no solicitada. No garantía de que pueda aprobarse16/16.
- Restricciones SKU incompletas en cuatro alternativas, capacidad real/zonal no verificable sin asignación; no se provisiona para comprobarla.
- CNI/Entra/Ubuntu/CSI/observabilidad/Blue-Green y rendimiento deben probarse en AKS; kind no sustituye esa evidencia.
- Falta presupuesto completo LB/uso/retención, ventana y procedimiento de cierre aprobados; no generar expectativa de coste máximo.
- Grupo Entra/membresía, IP vigente para API y Storage, CIDR externos y custodia/retención siguen pendientes según preflight.
- Parche1.35.9, surge1 y cambio de región requieren aprobación posterior; archivos actuales no se modificaron.

## 16. Próxima acción operativa propuesta

El propietario debe **ratificar la región candidata** (Sweden provisional, o East US condicionada a completar catálogo) y autorizar un incremento acotado para verificar elegibilidad de ampliación regional/DSv5 a16/16 y aclarar acceso regional Storage/AKS si es necesario. No autoriza por extensión presentar solicitudes, abrir soporte o cambiar configuración. Completar la consulta SKU con una lectura más acotada si se elige East US; no nuevas pruebas de creación ni instalación de herramientas.

Solo con nuevas autorizaciones: solicitud de cuota, ficha de backend revisada con región/RG/seguridad/retención, recuperación del bootstrap, cambios de variables, posterior plan y aprovisionamiento supervisado. Preservar rg-wordle-state; no repetir el bootstrap original ni retirar recursos. No iniciar ninguno de esos incrementos automáticamente.

## 17. Estado de los gates y preservación

**PARTIAL diagnóstico**: regiones, cuotas, versiones, proveedores, documentación y estimación comparadas; recomendación condicional útil. Quedan incompletas restricciones SKU de cuatro alternativas, visibilidad de políticas heredadas y cotización numérica LB. No se presenta como selección definitivamente habilitada ni coste total aprobado.

**Gate A NO-GO; AKS NO-GO.** Solo se crea este informe. Se verifican por SHA-256 los archivos pendientes previos y el índice se conserva; no se alteran informes históricos, configuraciones Terraform ni historial Git. Sin escrituras Azure, reserva de nombres, solicitudes de cuota, registros, RBAC/Policy, soporte o despliegues. Las lecturas Git se limitaron a la preservación de archivos pendientes, sin auditoría de otras ramas.
