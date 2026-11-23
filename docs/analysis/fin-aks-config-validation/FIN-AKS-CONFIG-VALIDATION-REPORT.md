# FIN-AKS-CONFIG-VALIDATION — Wordle — 15/11/2026

## 1. Resumen ejecutivo: PASS documental, AKS NO-GO

La propuesta es técnicamente coherente en configuración/documentación: AKS1.35.9 listado regional y rama GA, AzureRM4.50 admite sus argumentos, CNI Overlay y Entra/RBAC previstos. **No se certifica compatibilidad end-to-end ni provisión**: sin plan, init o clúster. Los bloqueos concretos son grupo/membresía y permisos Entra, CIDR /32 autorizado/estable, solapamientos externos, backend inexistente confirmado por coordenadas previstas y presupuesto completo.

Se crea solo este informe; no se implementa configuración. PASS significa evaluación completada con límites explícitos, no aprobación de diseño ni autorización de gasto/despliegue.

## 2. Contexto y evidencias

Sesión existente: suscripción `11306565…1bb5`, tenant `aff0390f…1eb9`, Enabled, sin cambio de contexto. Región leída en infra/terraform/variables.tf: westeurope. Cuota DSv5 16/regional26 procede de FIN-AKS-QUOTA-REQUEST aprobado y verificado; no se repite solicitud/consulta. Solo lecturas actuales de versiones, permisos ARM, grupo Entra exacto, recursos Wordle etiquetados y existencia del RG de estado. Cero recursos con project=wordle y rg-wordle-state ausente: no prueba ausencia de recursos ajenos/sin etiqueta ni autoriza reutilizarlos.

Archivos inspeccionados: infra/terraform/main.tf, variables.tf, versions.tf; ejemplos del backend y decisiones anteriores; overlay k8s/aks-full. Sin lectura de secretos, blobs/estados, políticas de otros proyectos ni recursos Nexo.

## 3. Compatibilidad AKS/Terraform: PASS condicionado

Consulta Azure AKS get-versions hoy: rama1.35 contiene parches1.35.0–1.35.9. isPreview es null y no se usa como prueba GA; el calendario oficial clasifica1.35 GA marzo2026 y soporte estándar hasta marzo2027. 1.34 termina soporte estándar noviembre2026. Se mantiene recomendación1.35.9 por margen, no por ser la versión más nueva. Parche y soporte se revalidan antes de una futura ejecución.

La documentación **del tag AzureRM v4.50.0** confirma kubernetes_version, default_node_pool.upgrade_settings.max_surge, red azure+overlay con pod_cidr, RBAC/Entra y cuentas locales deshabilitadas. El esquema admite definir upgrade_settings { max_surge = "1" }; main.tf aún no lo tiene y kubernetes_version sigue null. No se cambia nada.

Los argumentos actuales satisfacen las dependencias documentadas: local_account_disabled exige Entra administrado y Kubernetes RBAC, ambos presentes; azure_rbac_enabled=false selecciona Kubernetes RBAC, no ausencia de RBAC. azure+overlay permite pod_cidr separado, DNS dentro de service_cidr; no se usa network_mode inválido. Dos nodos4vCPU/16GiB cumplen nominalmente requisitos System; reservas/DaemonSets y picos no se prueban aquí.

AzureRM4.50.0 no publica una matriz que garantice cada parche futuro de AKS. No se demuestra que su API y la imagen Ubuntu efectiva acepten1.35.9 en una provisión real. **Compatibilidad de argumentos PASS documental; compatibilidad completa condicionada a plan/provisión autorizados**. No se afirma que el proveedor esté roto ni se actualiza preventivamente. Si el futuro plan muestra error específico, resolver mínimamente con autorización.

Alternativa GA disponible: **1.34.12**, documentada/listada en la revisión previa; no preferida por fin de soporte estándar en el mes actual y tampoco ofrece garantía end-to-end con ese proveedor. No usar una versión anterior como supuesto remedio sin error concreto. kubectl1.34.1 histórico queda a una minor de1.35, dentro de skew general; no se instala/actualiza cliente.

Surge1 daría12vCPU, dentro de DSv5=16 y regional=26 si no hay otros consumos. No hay autoscaling explícito, ni zonas. No se asume valor efectivo de surge/OS-upgrade por omisión ni capacidad física disponible; revisar defaults/imagen y cambios en plan. Rollback de aplicación no revierte plataforma Kubernetes.

Fuentes: [soporte AKS](https://learn.microsoft.com/en-us/azure/aks/supported-kubernetes-versions), [documentación AzureRM4.50.0](https://raw.githubusercontent.com/hashicorp/terraform-provider-azurerm/v4.50.0/website/docs/r/kubernetes_cluster.html.markdown), [skew cliente](https://kubernetes.io/releases/version-skew-policy/).

## 4. Red: PASS interno, validación externa BLOCKED

Comprobación Python ipaddress ejecutada: subred10.10.0.0/24 contenida en VNet10.10.0.0/16; VNet, pods10.244.0.0/16 y servicios10.20.0.0/16 no se solapan mutuamente; DNS10.20.0.10 pertenece a servicios. La contención VNet/subred es necesaria, no conflicto. Overlay reserva /24 de pods por nodo, aunque max_pods=30; hay espacio nominal para tres nodos, no una evaluación completa de capacidad/red AKS.

Consulta de recursos con tag project=wordle: cero. Por ello no aparecen VNets Wordle etiquetadas a comparar. No se inspeccionan VNets sin relación autorizada, VPN, peering o redes corporativas; **ausencia global de solapamientos no confirmada**. El propietario debe verificar estos rangos con el responsable de red/VPN antes de aprobarlos, sin usar información de Nexo.

API pública restringida por authorized_ip_ranges; no0.0.0.0/0. Traefik/Ingress por port-forward loopback, Host wordle.test; Services ClusterIP, sin PostgreSQL/backend expuestos. LB/IP de salida sí cuesta aunque no haya LoadBalancer público de aplicación. Se requieren DNS/HTTPS y pulls desde registros/endpoints oficiales; el acceso desde nodos sigue pendiente de AKS real. No se añaden NSG, rutas o alternativas CNI.

Fuentes: [CNI Overlay](https://learn.microsoft.com/en-us/azure/aks/concepts-network-azure-cni-overlay), [API autorizada](https://learn.microsoft.com/en-us/azure/aks/api-server-authorized-ip-ranges).

## 5. IPv4 y acceso administrativo: BLOCKED

Una consulta sin credenciales a https://api4.ipify.org devolvió una IPv4 global válida observada. No se persiste/publica su valor ni se declara /32 autorizado. Un punto de observación no identifica contrato de IP fija, NAT corporativo, VPN o estabilidad temporal.

Procedimiento pendiente: propietario identifica si administra desde ISP doméstico o salida corporativa/VPN aprobada; confirma IP pública real con esa ruta activa y si es fija; autoriza explícitamente /32. Contrastar antes de cada ventana. IP dinámica requiere procedimiento autorizado de actualización si cambia, no ampliar a todo internet. Alternativa salida estable existente evita cambios frecuentes pero requiere aprobación corporativa; no se crea VPN/runner público nuevo para simplificar. Estado observado PASS, estabilidad/autoridad BLOCKED.

## 6. Identidad y permisos: PASS condicionado

Modelo válido: Entra administrado + Kubernetes RBAC y cuentas locales off. Grupo dedicado propuesto grp-wordle-aks-admins mantiene administración fuera de usuarios implícitos; admin_group_object_ids exige ID real. Consulta Entra de lectura filtrada exactamente por displayName: **cero coincidencias**. No hay grupo reutilizable confirmado con ese nombre; no se listan grupos ajenos. Un grupo con otro nombre requiere aprobación por ID, no se descarta su existencia por esta consulta.

Crear grupo/membresía requiere política y permisos de Entra/Graph propios (usuario con capacidad de creación autorizada o administrador apropiado), no se deduce de Owner/Contributor Azure. Quién será miembro y propietario del grupo sigue sin aprobarse. No se prueba creación para comprobar permisos ni se asigna el usuario CLI automáticamente.

La API ARM permissions devuelve una entrada actions=* sin notActions y dataActions vacías. Permite identificar acciones de red/AKS/identidad/roleAssignments en la respuesta, pero no certificar acceso efectivo contra denies/condiciones/políticas; tampoco acceso Blob ni permisos Graph. Terraform necesita identidad con ámbito suficiente para bootstrap de RG/AKS/red/identidad y asignación del rol subnet. Despliegues iniciales necesitan RBAC Kubernetes para namespaces/CRD/roles, luego pueden acotarse; un rol ARM no sustituye estos permisos.

Identidad control-plane user-assigned definida por Terraform, Network Contributor solo en subred. Sin kubelet_identity explícita, AKS crea una user-assigned para kubelet en RG nodos; no se crea ahora. GHCR público no requiere AcrPull ni PAT por defecto. Autenticación de operadores vía kubelogin azurecli y kubeconfig usuario; no --admin. No cambia autenticación del juego ni autoriza datos personales.

Fuentes: [Entra control plane](https://learn.microsoft.com/en-us/azure/aks/entra-id-control-plane-authentication), [identidades](https://learn.microsoft.com/en-us/azure/aks/managed-identity-overview).

## 7. Backend remoto: diseño PASS condicionado, existencia BLOCKED

Diseño soportado: backend azurerm con use_azuread_auth=true, StorageV2 Standard_LRS, contenedor privado tfstate y key wordle/aks-demo.tfstate. RG rg-wordle-state separado de los RG AKS/nodos; no existe según lectura actual. Cero recursos Wordle etiquetados: no hay backend reutilizable confirmado; no se inspeccionan cuentas ajenas o claves.

Bootstrap externo exige autorización de creación/seguridad/coste y permisos; no depende de un estado remoto aún inexistente. Autenticación Entra con Storage Blob Data Contributor al contenedor y permisos de gestión adicionales solo donde proceda; no usar claves/SAS. Firewall restringido a salida aprobada, HTTPS, sin acceso anónimo. Backend soporta lease/bloqueo nativo, pero **no se ha probado lease ni acceso efectivo** porque no se autoriza init ni estado.

Retención siete días es propuesta razonable de soft delete de blobs/contenedores. Versioning protege sobrescrituras, pero **sus versiones no expiran automáticamente por fijar soft delete a siete días**: acordar lifecycle/retención de versiones y comprobar costes. No inmutabilidad que bloquee escrituras Terraform. Separación futura por keys explícitas, sin workspaces complejos. Ejemplos anteriores contienen keys diferentes: seleccionar una antes de init, nunca migrar implícitamente.

Fuentes: [backend azurerm](https://developer.hashicorp.com/terraform/language/backend/azurerm), [protección Storage](https://learn.microsoft.com/en-us/azure/storage/blobs/data-protection-overview).

## 8. Estimación económica trazable

Azure Retail Prices API consultada15/11/2026, región westeurope, moneda USD, tipo Consumption, sin descuentos/impuestos/EUR/créditos. Ejecución de cuatro horas con dos nodos, sin surge ni reconstrucción incluidos; nodos permanecen creados durante esas horas. Discos facturados por tamaño/tier/tiempo; para prorrateo orientativo se usa730h/mes, no cotización contractual.

| Componente | Tarifa pública verificada | Hipótesis y coste4h |
|---|---|---|
| 2×D4s_v5 Linux | 0.23 USD/nodo/h | **1.84 USD** |
| 2 discos OS | P6 LRS 11.2272 USD/disco/mes | Si AKS usa Premium SSD Managed64GiB/P6: **0.12304 USD** |
| PostgreSQL | E2 LRS 0.60 USD/disco/mes | Si managed-csi estándar LRS provisiona8GiB/E2: **0.00329 USD**, operaciones adicionales |
| IPv4 salida | Standard IPv4 Static Public IP 0.005 USD/h | Una IP: **0.02000 USD** |
| AKS Free | Sin cargo propio de gestión control-plane | 0 de gestión; no infraestructura gratuita |
| Load Balancer | Consulta Retail por servicio/producto sin filas; web oficial sin importe utilizable en lectura | **No cuantificado**, no asumir cero |
| Tráfico/egreso y operaciones disco | Volumen/medidores sin estimar | **No cuantificado**, no asumir cero |
| Estado Blob Hot LRS | 0.0196 USD/GB-mes (primer tier) | GB/mes reales y versiones desconocidos; fórmula abajo |
| Operaciones estado | Write/list0.054 USD/10K; read/other0.0043 USD/10K | Según número real; no asumir consumo cero |
| Observabilidad | Autogestionada sobre esos nodos, señales emptyDir | Sin SaaS Azure Monitor/Log Analytics declarado; consumo de CPU/OS/red incluido o variable, no persistencia de historia garantizada |

**Subtotal condicional cuantificado: 1.98633 USD ≈1.99 USD**, excluye LB, egreso, operaciones, estado/retención y arranque/reconstrucción fuera de4h. **NO es presupuesto total ni límite de gasto**. Coste total = subtotal + medidores no cuantificados. Las tarifas de Disk Mount de P6/E2 no se añaden como almacenamiento normal: corresponden a funciones/uso de disco compartido no configurados; confirmar parámetros efectivos, no sumar medidores incompatibles.

AKS suele usar Premium SSD para Managed OS cuando no hay ephemeral; aquí Managed64 está explícito y el supuesto P6 se apoya en esa guía, pero debe verificarse en recursos/plan real. managed-csi está documentado como StandardSSD_LRS; clase/tier efectivo se comprueban en AKS, sin prometerlos solo por nombre. Si difieren, recalcular.

Mensual residual orientativo si se conservan recursos: dos P6 + E2 = **23.0544 USD/mes**; una IPv4 a0.005×730 = **3.65 USD/mes** si sigue siendo facturable. No incluye LB ni transacciones. Son equivalentes mensuales, no cobro automático de mes entero tras cuatro horas.

Estado: por ejemplo **1 GB total** incluyendo versiones durante un mes cuesta0.0196 USD solo capacidad; siete días ≈0.00457 USD usando30d/mes. Esto es ejemplo unitario, no tamaño medido o consumo real; añadir escrituras/listados/lecturas.1000writes cuestan0.0054 USD y1000reads0.00043 al precio unitario indicado. Retención y operaciones pueden durar más que los nodos; no confundir coste de blob con coste base fijo de Storage Account.

Un surge una hora añade0.23 USD VM más disco temporal y otros medidores; no se necesita un segundo PostgreSQL para Blue/Green. No se añaden ACR, NAT Gateway ni premium observabilidad. Presupuesto final BLOCKED hasta cotizar LB/egreso/operaciones y aprobar duración/retención/seguridad; no fabricar una cota superior.

Tras parar Pods o nodos pueden seguir discos/PVC, IP/LB según recursos existentes, estado/versiones/backups. Exportar evidencia y backup restaurado; revisar inventario autorizado, plan-destroy y confirmación separada, luego comprobar remanentes/cargos. No borrar backend por limpiar AKS ni recursos de terceros; eliminar discos/IP/estado requiere su autorización. Facturación puede llevar retraso.

Fuentes de precio: [API Retail oficial](https://prices.azure.com/api/retail/prices), [Managed Disks](https://azure.microsoft.com/en-us/pricing/details/managed-disks/), [LB](https://azure.microsoft.com/en-us/pricing/details/load-balancer/), [IP](https://azure.microsoft.com/en-us/pricing/details/ip-addresses/), [Blob](https://azure.microsoft.com/en-us/pricing/details/storage/blobs/), [AKS Free](https://azure.microsoft.com/en-us/pricing/details/kubernetes-service/). Supuestos de discos: [OS AKS](https://learn.microsoft.com/en-us/azure/aks/best-practices-performance-scale), [managed-csi](https://learn.microsoft.com/en-us/azure/aks/azure-csi-disk-storage-provision).

## 9. Matriz de validación

| Área | Propuesta | Validación | Riesgo residual | Decisión |
|---|---|---|---|---|
| Kubernetes |1.35.9 | PASS condicionado: listado y rama GA | Provisión/parche/OS no ensayados | Aprobar candidato, revalidar antes de plan |
| Terraform |AzureRM4.50 | PASS condicionado: argumentos documentados | API runtime no certificada | Conservar salvo incompatibilidad real; no upgrade automático |
| Red |Overlay/rangos actuales | PASS interno, BLOCKED externo | VPN/corporativa/peering no visibles | Responsable confirma solapamientos |
| API Server |IPv4/32 | BLOCKED | IP observada no estable ni autorizada | Confirmar ruta y aprobar /32 |
| Identidad |Entra+KubernetesRBAC | PASS modelo; BLOCKED grupo/permisos Graph | Grupo ausente, membership/denies | Autorizar grupo/miembros y bootstrap preciso |
| Backend |Storage Entra/LRS | PASS diseño; BLOCKED existencia/acceso/lease | Coste/ACL/retención | Aprobar backend/coordenadas/seguridad antes de crear |
| Presupuesto |Demo4h | PASS subtotal trazable, BLOCKED total | Medidores pendientes, residuos | Cotizar/aprobar presupuesto completo |

## 10. Riesgos y restricciones

La evaluación no convierte propuestas en autorización. Cuota aprobada no reserva hardware; aplicación sin auth sigue solo demo privada/sintética. Un PVC de una réplica no proporciona HA; señales emptyDir se pierden al reconstruir. Tiempo/picos/upgrade no caben necesariamente en cuatro horas y necesitan aprobación si se amplía. No repetir kind/87tests para resolver identidad/red o coste.

## 11. Decisiones pendientes

Propietario: aprobar grupo/miembros y capacidad Entra; confirmar CIDR externo/no solapamientos; aceptar backend elegido, firewall/retención y costes; aprobar candidato1.35.9 y futuro surge1 sujeto a validación; completar presupuesto con LB/tráfico y retención. Cada creación/roleAssignment/modificación posterior es autorización aparte. No pedir datos secretos ni publicar IP/IDs innecesariamente.

## 12. Próxima iteración recomendada y preservación

Resolver primero las decisiones humanas de grupo/miembros y salida /32; después autorizar bootstrap del backend con presupuesto y seguridad revisados, sin iniciar plan/apply automáticamente. Usar guía/helpers ya existentes. No se modifica plan general ni se abre un roadmap alternativo.

Único archivo creado: este informe. Todos los archivos modificados/sin seguimiento previos preservados por SHA-256. No cambios Azure, Entra, RBAC, redes, Storage, Terraform/configuración/estado ni historial Git; sin solicitudes, despliegues, commits/push. Sin suites repetidas; solo lecturas selectivas, consultas públicas/ARM/Graph autorizadas y comprobación aritmética local. Esperar aprobación; AKS NO-GO.
