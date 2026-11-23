# FIN-AKS-DEPLOYMENT-BLOCKERS — 17/11/2026

## 1. Resumen ejecutivo

**PARTIAL de diagnóstico; recomendación CONDITIONAL GO para revisión humana.**
SKU Standard_D4s_v5: SUPPORTED, publicado en Sweden Central sin restricciones
detectadas. Cuotas suficientes. La consulta atScope recupera tres políticas heredadas,
incluidas exigencias MFA para escritura y borrado; no se confirma la condición MFA
de la sesión sin consultar tokens. Costes ampliados con fuentes actuales, bajo
supuestos verificables: unos 2,06 USD/4 h y 4,36 USD/8 h con la demo/observabilidad.
No son límite ni factura garantizada. Run Command no es necesario para los scripts
actuales; se recomienda deshabilitarlo en otra iteración autorizada.
Quedan condiciones de sesión, seguridad, consumos y capacidad runtime sin demostrar;
no se fuerza PASS ni se autoriza apply. Gate A GO; Gate B y AKS NO-GO.

## 2. Alcance autorizado

Solo lecturas locales, Azure ARM/Graph y fuentes públicas oficiales. No Terraform
ejecutado, nuevo plan, acceso al backend/estado, cambios cloud/Entra/RBAC/firewall,
solicitud de cuota o compromiso de gasto. Sin herramientas instaladas.
Solo este informe nuevo; configuración e históricos preservados.
Sin datos de Nexo, secretos, tokens o IP doméstica consultados/conservados.

## 3. Estado inicial

Plan anterior exit 0: seis altas, cero cambios/borrados/reemplazos. No infraestructura
desplegada por esa ejecución. Terraform 1.9.8 / AzureRM 4.50.0; backend ya inicializado.
66 archivos pendientes previos e índice vacío capturados por hashes.
Arquitectura aprobada: Sweden Central, AKS Free 1.35.9, dos D4s_v5, surge 1,
CNI Overlay y CIDR vigentes; Entra/Kubernetes RBAC, cuentas locales off, API /32.

## 4. Referencias revisadas

TF PLAN, REMOTE-BACKEND-INITIALIZATION, PROVIDER-SCHEMA-VALIDATION,
DEPLOYMENT-DECISIONS y GATE-B-READINESS. main.tf, variables/versions,
plan sanitizado, k8s/aks-full y recursos/configuración observabilidad.
Históricos STORAGE-DENIAL-DIAGNOSIS/REGION-SELECTION usados para localizar
sys.blockwesteurope, no para asumir que sea la única política.

## 5. Identidad y contexto Azure

account show / signed-in-user show: identidad aprobada b573130a…a831,
tenant aff0390f-c390-4edc-919f-77da2a811eb9 y suscripción Enabled
11306565…1bb5. Sin login/context switch/permisos alterados.
Se utilizó el Azure CLI ya instalado; para REST se invocó su mismo intérprete
oficial -IBm azure.cli, evitando el wrapper cmd y preservando URLs con filtros.
Sin configuración del entorno modificada ni autenticaciones alternativas.

## 6. Disponibilidad del SKU

**SUPPORTED según la definición de esta iteración.**
GET Microsoft.Compute/skus, API 2021-07-01, filtro servidor
location eq 'swedencentral'; selección exacta Standard_D4s_v5/virtualMachines.
Resultado: un SKU, restrictions=[], sin nextLink. Consulta exit 0, 3,05 segundos;
UTC 2026-11-17T07:59:32.308234+00:00. Ubicación SwedenCentral, zonas publicadas 1/2/3.
Capacidades: 4 vCPU, 16 GiB, x64, PremiumIO true, VMSS/AKS previstos compatibles
nominalmente con requisitos System (no B-series). EphemeralOSDiskSupported=false:
el diseño usa Managed OS, por lo que no exige ese soporte.
Sin garantía de capacidad física, colocación o admisión AKS en el momento de apply.
La publicación Compute y compatibilidad nominal no sustituyen creación real.
No zonas nuevas ni VM de prueba.

Antecedente: CLI anterior timeout 60 s. Primera REST mediante wrapper devolvió error
tras 35,88 s; alternativa más directa y filtrada resolvió la consulta, sin bucle
indefinido ni enumeración global. No se interpretó timeout/error como indisponibilidad.
[Compute SKU API](https://learn.microsoft.com/en-us/rest/api/compute/resource-skus/list?view=rest-compute-2021-07-01),
[AKS System pools](https://learn.microsoft.com/en-us/azure/aks/use-system-pools).

## 7. Cuotas regionales

Consulta vm list-usage Sweden Central: DSv5 usado 0/límite 16 vCPU;
total regional usado 0/límite 26. Dos nodos necesitan 8; con un surge, 12.
**PASS de cuota al consultar**, no reserva de hardware ni garantía futura.
No solicitud de ampliación, cambio de SKU ni consulta de recursos ajenos.

## 8. Azure Policy

GET assignments de suscripción con $filter=atScope(), API 2023-04-01:
tres asignaciones heredadas de tenant-root management group, sin paginación pendiente.
Definiciones directas, no iniciativas en el resultado.
GET exemptions atScope API 2022-07-01-preview: cero exenciones devueltas.
Enforcement Default; sin notScopes/exclusiones en las tres asignaciones recuperadas.

| Asignación | Efecto efectivo / condición | Aplicabilidad | Clasificación |
| --- | --- | --- | --- |
| sys.blockwesteurope | override deny; location=westeurope; modo Indexed | Heredada, condición regional no coincide con Sweden Central | Compatible con región aprobada |
| sys.mfa-write | parámetro Deny; usuario sin mfa y sin acrs p1 | Escrituras futuras RG/VNet/MI/rol/AKS; no comprobación de sesión MFA hoy | Potencialmente conflictiva, condicional |
| sys.mfa-delete | parámetro DenyAction, actionNames delete; mismas condiciones MFA | Retirada futura dentro de ventana | Potencialmente conflictiva, condicional |

Definiciones consultadas: 7509877f…d087 (West Europe),
54f51f64…4d21 (write) y f69cd8b8…7944 (delete); reglas y parámetros leídos.
MFA mode All exige idtyp=user, ausencia de mfa en authnmethodsreferences y ausencia
de p1 en acrs para negar. No se consultan esos claims/token de la sesión.
El default Audit/AuditAction de las definiciones **no** es el efecto aplicado:
las asignaciones fijan Deny/DenyAction.
No Modify/DeployIfNotExists/Audit activos identificados en las tres recuperadas.
No restricciones adicionales SKU/network/tags/MI/Run Command en este resultado.
No significa inexistencia universal de otras restricciones plataforma/futuras.

## 9. Visibilidad y limitaciones

GET directo de assignments en management group y del assignment West Europe:
AuthorizationFailed; no elevación solicitada.
La vía de suscripción atScope sí devuelve los heredados aplicables, superando la
lista de suscripción previa que había mostrado cero. Se clasifica cobertura por
respuesta efectiva, no ausencia deducida de una lista vacía.
Definiciones BuiltIn y exenciones aplicables accesibles; no se inspeccionaron
management groups ajenos ni recursos de otros proyectos.
RG futuro aún no existe: no hay evaluación real de recursos del plan ni de
cambios de políticas posteriores. Sesión con MFA vigente no verificada;
históricos de escritura exitosa no demuestran su condición en un apply futuro.
No se prueba el borrado creando recursos, porque no está autorizado.
[Semántica atScope](https://learn.microsoft.com/en-us/rest/api/policy-authorization/policy-assignments/list),
[Exenciones](https://learn.microsoft.com/en-us/rest/api/policy-authorization/policy-exemptions/list?view=rest-policy-authorization-2023-04-01).

## 10. Estimación económica

Precios minoristas oficiales consultados 2026-11-17T08:00:19.217112+00:00; USD Consumption, Linux,
sin Spot/reserva/descuentos/créditos o ventajas gratuitas supuestas.
Región Sweden Central salvo medidores LB publicados como Global.
Global en el catálogo **no** implica usar SKU Global/cross-region: se selecciona Standard.
No cotización contractual ni acceso a facturación privada.

| Concepto / medidor | Tarifa consultada | Supuesto |
| --- | ---: | --- |
| VM D4s v5 / Virtual Machines Dsv5 Series | 0,204 USD/nodo-h | 2 nodos |
| Premium SSD Managed Disks P6 LRS Disk | 11,2272 USD/mes | 2 OS 64 GiB; SKU real por confirmar |
| Standard SSD Managed Disks E2 LRS Disk | 0,60 USD/mes | PG PVC 8 GiB, perfil aks-full |
| E4 LRS Disk Operations | 0,002 USD/10K IO | Medidor transacciones Standard SSD, no nuevo disco E4 |
| AKS Free | 0 gestión | Recursos subyacentes facturan |
| Standard Included LB Rules and Outbound Rules | 0,025 USD/h | Tramo primeras 5 reglas, incluido outbound |
| Standard Data Processed | 0,005 USD/GB | Ingreso+egreso procesado por LB |
| Standard IPv4 Static Public IP | 0,005 USD/h | 1 IP salida |
| Bandwidth MGN Standard Data Transfer Out | 0,087 USD/GB en tramo desde 100 GB | No se presupone saldo gratuito disponible |
| General Block Blob v2 Hot LRS Data Stored | 0,0184 USD/GB-mes | Backend/versiones; volumen hipotético |
| Hot LRS Write / Hot Read Operations | 0,05 / 0,004 USD por 10K | Operaciones backend |

Consulta LB regional devolvió cero; catálogo serviceName Load Balancer identificó
armRegionName Global y ahí los medidores Standard. No se inventó tarifa 0,025.
Filas -Free/beneficios excluidas de la estimación.
Operaciones de disco cobradas según tamaño IO y topes horarios del servicio;
no se añadió Mount como cargo normal: el medidor se refiere a uso compartido,
no al montaje ordinario del PVC de una VM. Sin nuevo recurso de disco temporal:
este SKU no publica disco local de recursos; emptyDir usa almacenamiento del nodo.
Discos mensuales se aproximan con mes 730 h para estimación, no contrato de prorrateo.
LB factura hora parcial como completa; retirada/aprovisionamiento pueden redondear.
[LB facturación](https://azure.microsoft.com/en-us/pricing/details/load-balancer/),
[Discos y transacciones](https://learn.microsoft.com/en-us/azure/virtual-machines/disks-understand-billing).

## 11. Escenarios de 4 y 8 horas

Supuestos explícitos, **no previsión medida ni total garantizado**:
A = dos nodos, dos OS P6, LB Standard con outbound y una IP.
B = A + PostgreSQL PVC 8 GiB y observabilidad sobre los mismos nodos.
B agrupa demo completa; el pequeño incremento PG no es un coste exclusivo de observar.
4 h: 10 GB procesados LB, 1 GB egreso cobrado y 100K IO PG.
8 h: 20 GB LB, 5 GB egreso y 200K IO PG.
Ambos incluyen como hipótesis conservadora 1 GB-mes de backend/versiones retenido,
1000 escrituras y 1000 lecturas: 0,0238 USD. No es volumen real consultado.
Sin franquicia gratis, sin nuevo pool, snapshot o servicio premium.
Ingresos de imágenes no tienen coste de egress pero sí pueden contar como datos LB;
los GB propuestos no son un límite medido o impuesto.

| Escenario | Base fija VM/OS/LB/IP | Modelo con tráfico y backend | Con 1 h de surge VM+OS |
| --- | ---: | ---: | ---: |
| A mínimo, 4 h | 1,87504 | 2,03584 USD | 2,25522 USD |
| B demo+observabilidad, 4 h | misma base | 2,05913 USD | 2,27851 USD |
| C prolongación A, 8 h | 3,75008 | 4,30888 USD | 4,52826 USD |
| C prolongación B, 8 h | misma base | 4,35545 USD | 4,57483 USD |

Fórmula A = (2*0,204 + 2*11,2272/730 + 0,005 + 0,025)*horas
+ 0,005*GB_LB + 0,087*GB_egreso + 0,0238.
B añade 0,60*horas/730 + 0,002*IO/10000.
Surge añade 0,204 + 11,2272/730 por hora de nodo extra; tráfico/otros incrementos aparte.

Conclusión: **5 USD parece alcanzable en 4 h bajo estos supuestos**;
8 h reduce sensiblemente el margen y no está autorizado como extensión de ventana.
Pendientes: cantidades reales, discos efectivos, backups/custodia externa, tráfico
por zona/región si ocurre, retención fuera de 1 GB-mes y recursos residuales.
Costes de terceros/contrato/impuestos/cambio y redondeos no garantizados.
No se presentan esos pendientes como cero ni se cambia el presupuesto.

## 12. Costes de observabilidad

k8s/aks-full importa ../observability. Collector, Prometheus, Grafana, Loki,
Tempo, Alertmanager y receptor notifications son Deployments en nodos existentes;
Node Exporter es DaemonSet. cAdvisor se obtiene por kubelet /metrics/cadvisor,
no un servicio Azure cAdvisor facturable.
No recursos Azure Monitor/Log Analytics/Managed Prometheus/ACR añadidos por el plan;
coste directo de servicio no previsto, no una declaración de coste operativo cero.
Alertas/webhook internos no implican SMS/email/SaaS externo contratado.

Lectura de stack/resources.yaml, un ejemplar por Deployment y dos Node Exporter:
requests agregados 900m CPU / 672 MiB; limits 4500m / 2016 MiB.
No incluye aplicación, PostgreSQL, Ingress ni pods de sistema.
emptyDir 1 GiB + 64 MiB por pod es límite, no reserva ni nuevo disco Azure;
con esas réplicas, 9,5625 GiB de límites agregados compartidos con OS/imágenes.
Prometheus limita retención a 1 h/128 MB. No PVC de observabilidad añadido.
El único PVC explícito del perfil es PG managed-csi 8 GiB.
Riesgos: imágenes/logs/IO compiten por disco y memoria, DaemonSet se duplica;
requests bajos no demuestran capacidad runtime. Medir en ensayo autorizado sin
crear un pool adicional automáticamente. Señales emptyDir no sobreviven retirada.

## 13. Run Command

AzureRM v4.50.0, código kubernetes_cluster_resource.go:
run_command_enabled es bool Optional con Default true; expansión envía
DisableRunCommand = !run_command_enabled. main.tf omite ese atributo:
el true del plan anterior es default implícito, no decisión explícita del dueño.

Permite command invoke/Run Command mediante API ARM; permisos
Microsoft.ContainerService/managedClusters/runcommand/action y
Microsoft.ContainerService/managedClusters/commandResults/read.
Es vía administrativa adicional, no un endpoint sin autenticación; /32 del API
no representa una restricción equivalente sobre esa vía ARM.
Compromiso de identidad ARM autorizada puede permitir comandos remotos en clúster.

A — Mantener: utilidad de diagnóstico con conectividad API limitada; exige RBAC ARM
muy controlado, operador MFA y auditoría/aceptación de esa vía. Aumenta superficie
innecesaria para esta demo, aunque no se confirma vulnerabilidad explotada.
B — Deshabilitar: elimina vía adicional; pierde esa herramienta de diagnóstico,
pero conserva Entra/kubelogin/kubectl/port-forward por /32. Los scripts inspeccionados
no invocan command invoke/runcommand; no dependencia funcional identificada.
Las políticas recuperadas no lo exigen ni prohíben. No se afirma ausencia universal
de políticas futuras o de errores de conectividad.
**Recomendación B:** futuro cambio explícito run_command_enabled=false en main.tf,
con nueva autorización y revisión posterior de plan. No se modifica aquí.
[Esquema 4.50.0](https://github.com/hashicorp/terraform-provider-azurerm/blob/v4.50.0/internal/services/containers/kubernetes_cluster_resource.go#L1324-L1328),
[Expansión](https://github.com/hashicorp/terraform-provider-azurerm/blob/v4.50.0/internal/services/containers/kubernetes_cluster_resource.go#L3026-L3029),
[Microsoft Run Command](https://learn.microsoft.com/en-us/azure/aks/access-private-cluster).

## 14. Matriz de riesgos

| Área | Evidencia | Estado | Riesgo residual | Acción |
| --- | --- | --- | --- | --- |
| SKU | REST región, coincidencia exacta, restrictions=[] | PASS / SUPPORTED | Capacidad física | Revalidar antes de fase autorizada |
| Cuotas | 16 DSv5, 26 regional, usado 0 | PASS | Consumo futuro/surge | Revalidar capacidad para 12 vCPU con surge |
| Azure Policy | 3 heredadas, definiciones/exenciones leídas | PARTIAL | MFA efectivo de sesión/retirada sin demostrar | Confirmar autenticación MFA antes de crear y retirar |
| Costes | Tarifas oficiales y modelos 4/8 h | PARTIAL | Consumos, SKU disco y remanentes | Aceptar supuestos/margen y medir |
| Run Command | Default true, sin uso en scripts | PARTIAL | Vía ARM adicional | Autorizar deshabilitación o aceptar explícitamente A |

## 15. Bloqueos confirmados

No SKU restringido ni cuota insuficiente o prohibición Sweden confirmados.
West Europe sí tiene bloqueo regional, pero no es el destino aprobado.
MFA para escritura/borrado es requisito confirmado, **no fallo actual demostrado**
de la sesión. Sin evidencia de claims no se declara aptitud completa.
La falta de autorización de despliegue sigue siendo absoluta.

## 16. Incertidumbres pendientes

Condición MFA vigente para CREATE y DESTROY; capacidad/admisión durante ejecución;
discos/volúmenes/IO/red reales; consumos y cargos tardíos; comportamiento runtime
de observabilidad y duración de todo el ciclo en 4 horas.
La lectura efectiva atScope mejora la visibilidad, pero no es un test de provisión.
Ninguna requiere improvisar cambios cloud hoy.

## 17. Recomendación Gate B

**CONDITIONAL GO como recomendación para aceptación humana**, no cambio de gate.
Condiciones antes de apply: propietario confirma/realiza MFA sobre identidad aprobada
en la fase futura autorizada, con disponibilidad para reautenticar durante retirada;
acepta los supuestos económicos, margen y duración, y resuelve Run Command.
Se recomienda autorizar B y revisar un plan nuevo después del cambio mínimo.
Plan de retirada debe contar con operador y tiempo de margen; DenyAction por MFA
no se resuelve con force/delete ni cambiando roles.
Si estas condiciones no se aceptan/completan, mantener NO-GO; no arriesgar recursos
facturables cuya retirada no esté operativamente preparada.

## 18. Estado Gate A

GO histórico mantenido; no se consulta ni modifica backend/estado en esta iteración.

## 19. Estado Gate B

NO-GO efectivo. La recomendación condicional no cambia el estado formal.

## 20. Estado AKS

NO-GO. Sin clúster, VM o recursos de prueba creados.

## 21. Evidencias

REST SKU API 2021-07-01, ubicación filtrada y nextLink null; cuotas CLI de región.
Policy assignments API 2023-04-01 con atScope, definiciones BuiltIn y exenciones
API 2022-07-01-preview. GET management-group directo AuthorizationFailed documentado.
No acciones de evaluación Policy que creen recursos.
Azure Retail Prices API: USD/Consumption/Sweden Central; LB Standard Global.
Consultas sin paginación pendiente; filas correctas seleccionadas por producto,
SKU, medidor, unidad y tramo. No Premium Page Blob confundido con Managed Disk,
ni SKU Global Load Balancer confundido con precio armRegionName Global.
Primera salida de catálogo se truncó; se recuperó mediante proyección compacta,
sin guardar catálogo completo ni afirmar que truncamiento fuera un fallo de API.

Fuentes de precios reproducibles:
- https://prices.azure.com/api/retail/prices (filtros armRegionName=swedencentral,
  armSkuName=Standard_D4s_v5; P6/E2 Managed Disks; IP Addresses Standard IPv4).
- Misma API: serviceName=Load Balancer, armRegionName=Global, skuName=Standard.
- Misma API: serviceName=Bandwidth, producto Rtn Preference: MGN, tramo mínimo100.
- Misma API: General Block Blob v2 / Hot LRS; Standard SSD E4 LRS Disk Operations.
[API Retail](https://learn.microsoft.com/en-us/rest/api/cost-management/retail-prices/azure-retail-prices),
[AKS Free](https://learn.microsoft.com/en-us/azure/aks/free-standard-pricing-tiers),
[Discos](https://learn.microsoft.com/en-us/azure/virtual-machines/disks-understand-billing).

Solo campos operativos sanitizados; sin tokens, credenciales, estado, IP doméstica
o información de autenticación persistida. La política describe claims, pero
no se leyeron claims ni tokens del usuario.

## 22. Integridad del repositorio

Único archivo nuevo: este informe. 66 pendientes preexistentes preservados.
TF, lock, caché/metadatos del backend e históricos sin cambios por SHA-256.
HEAD e índice vacío intactos; git diff --check: PASS, exit 0, sin diagnósticos.
No limpieza, staging, commits o push.

## 23. Próxima acción recomendada

Revisar condiciones MFA/retirada, supuestos de coste y alternativa B de Run Command.
Autorizar separadamente el mínimo cambio local si se acepta y su posterior
validación/plan; esta iteración no ejecuta ninguna fase posterior.
No terraform plan/apply/destroy/init/state/import/refresh/force-unlock;
no Azure/Entra/RBAC/firewall/recursos/cuotas/backend/estado/lock modificados.
