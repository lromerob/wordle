# FIN-AKS-READINESS — 15/11/2026

## Decisión: NO-GO con la configuración actual

Existe un impedimento acreditado: **Standard DSv5 Family vCPUs = límite 0**, aunque la cuota regional sea 10. No se recomienda solicitar todavía un plan operativo del diseño actual. Se precisa decisión del propietario sobre cuota/SKU, grupo Entra, CIDR, backend y presupuesto. No se modifica configuración ni se solicita cuota. FIN-04 aceptada; FIN-05/18 continúan pendientes de evidencia AKS. No se inicia despliegue.

Contexto autorizado comprobado: suscripción `11306565…1bb5`, tenant `aff0390f…1eb9`, Enabled, principal CLI tipo user. Sin cambio de cuenta ni login. Se consultan solo APIs de lectura; no se leen secretos/estados ni se adquieren leases.

## 1. Región, versión y capacidad

Hechos del repositorio: westeurope, dos Standard_D4s_v5, pool System, OS Ubuntu/Managed 64 GB, sin zonas declaradas. Cada D4s_v5 publicado previamente tiene 4 vCPU/16 GB; suma 8 vCPU nominales, no recursos asignables. Terraform impone >=2 nodos, rechaza B-series y deja tamaño parametrizado; la validación de texto del SKU no comprueba todos los mínimos técnicos. Guía oficial de System pools: >=4 vCPU y >=4 GB; recomendaciones de alta disponibilidad no se convierten en obligación adicional de esta demo temporal.

`kubernetes_version` tiene default **null**: AKS elegiría versión si no se aporta. El ejemplo JSON contiene placeholder. No existe versión configurada concreta que certificar. Consulta real de westeurope devuelve 1.31–1.37 con parches; marca 1.36 como predeterminada e incluye 1.34.12, 1.35.9 y 1.36.5. Listado no garantiza elegibilidad de todas las versiones, soporte comercial o SKU. Propuesta a revisar: fijar un parche admitido y compatible con cliente; si se conserva kubectl 1.34.1, no elegir 1.36 sin revisar compatibilidad de cliente. No se cambia versión ni se instala software.

| Comprobación | Estado | Evidencia actual |
|---|---|---|
| Suscripción y tenant | PASS | Contexto coincide con destino confirmado, Enabled. |
| Providers Compute/Network/ContainerService | PASS | Registered; también Storage/ManagedIdentity Registered. |
| Consulta versiones regionales | PASS | API de AKS devuelve familias/parches; selección concreta BLOCKED. |
| Cuotas Compute CLI y REST | PASS | Ambas devuelven 239 registros concordantes, sin nextLink en REST. |
| Cuota para SKU actual | FAIL | DSv5: uso 0, límite 0; impide los dos D4s_v5 actuales. |
| Cuota total regional | PASS | Uso 0, límite 10; 8 iniciales caben aritméticamente, no en familia DSv5. |
| Cuotas alternativas | PASS | DSv4 uso 0/límite 10; DASv5 y DDSv5 uso 0/límite 0. |
| SKU alternativo D4s_v4 | BLOCKED | Cuota de familia existe, pero listado SKU filtrado agotó tiempo; restricciones/compatibilidad/disponibilidad no acreditadas. |
| Capacidad física real | BLOCKED | Ni catálogo ni cuota reservan capacidad; solo se demuestra al aprovisionar autorizado. |
| API Microsoft.Quota alternativa | BLOCKED | GET devolvió error CLI, sin respuesta utilizable; no registrar otro provider para resolverlo. Compute Usage sí acredita los límites anteriores. |

Las consultas anteriores devolvían cero filas antes del registro de Compute. Ahora CLI y REST (Compute Usage api-version=2024-03-01) devuelven las mismas cuotas: el resultado ya no depende de un filtro local o solo del formato CLI. La relación temporal con el registro es compatible con inicialización/propagación del proveedor; **no se demuestra una causa histórica única**. No reinterpretar los informes anteriores como cuota cero, pero sí la nueva fila DSv5 explícita.

La restricción DSv5 en zonas 1/3 procede del preflight; el listado actual de SKUs agotó tiempo, por lo que no se presenta como revalidada. No hay zonas forzadas en Terraform. DSv4 es candidato, no cambio aprobado y no garantía de capacidad. Dos nodos 4-vCPU usan 8; un nodo de surge elevaría a 12, superior al límite regional 10 y al DSv4 10. Debe revisarse margen/estrategia antes de prometer upgrades/recreación con solapamiento. No se solicita aumento ni se cambia estrategia.

## 2. Identidad y permisos

| Comprobación | Estado | Resultado |
|---|---|---|
| Identidad Terraform supervisada | PASS documental | AzureRM recibe subscription_id/tenant_id explícitos; con sesión local prevista usa autenticación CLI, no managed identity automáticamente. El flujo Actions preparado usa OIDC separado. |
| Permisos ARM declarados por Azure | PASS parcial | API permissions devuelve actions `*` sin notActions en una entrada. No prueba ausencia de deny assignments, condiciones, Azure Policy ni permisos data-plane. No asigna roles. |
| Grupo Entra administrador | BLOCKED | Sin grupo aprobado en ejemplos. GET Graph /me/transitiveMemberOf/microsoft.graph.group devuelve cero grupos y sin página siguiente; no se acredita pertenencia a grupo de seguridad. No crear grupo automáticamente. |
| Storage data-plane | BLOCKED | Entrada ARM con `*` tiene dataActions vacías; no acredita Storage Blob Data Contributor sobre el contenedor previsto. |
| kubelogin/Terraform locales | PASS | Ejecutables por usuario funcionan: Terraform 1.9.8, kubelogin v0.2.22. Sin instalación o cambio PATH en esta revisión. |

Se requiere grupo Entra de seguridad elegido por el propietario y pertenencia verificada por ID: consultar grupo concreto y membresía transitiva con permisos Graph de lectura; no basta rol Owner de Azure ni sesión user. AzureRM configura admin_group_object_ids, cuentas locales deshabilitadas y Azure RBAC para Kubernetes false: el grupo seleccionado recibe administración mediante RBAC Kubernetes. Terraform necesita RG/AKS/red/identidad y roleAssignments; el registro previo no prueba todo el aprovisionamiento.

Terraform crearía una identidad user-assigned del control plane y Network Contributor en subred. AKS gestionaría identidad kubelet y recursos VMSS asociados; no están aprovisionados. Para acceso posterior se prevé kubeconfig de usuario nuevo externo y kubelogin con azurecli, nunca --admin. Actions/OIDC/runner protegido son una opción preparada pero no activada ni probada; no son necesarios para una primera ejecución local supervisada.

## 3. Red y exposición

**BLOCKED:** api_authorized_cidrs y origen concreto siguen sin decisión. API server público (`private_cluster_enabled=false`) restringido por CIDR; el módulo rechaza 0.0.0.0/0. VNet 10.10.0.0/16, subred 10.10.0.0/24, pod overlay 10.244.0.0/16, servicio 10.20.0.0/16 y DNS service 10.20.0.10. Revisar solapamientos con VPN/red autorizada; no se inspeccionan proyectos ajenos.

Alternativas sin ampliar arquitectura: (a) IPv4 pública actual /32 del operador, barata pero si cambia se pierde acceso hasta actualización autorizada; (b) salida corporativa estable ya aprobada, revisar proxy/VPN y permisos; (c) runner dedicado con salida fija si se elige Actions, pendiente configuración y posible coste. No abrir rangos masivos de GitHub ni todo internet para salvar IP dinámica. No se consulta ni publica automáticamente la IP del operador.

Aplicación privada por port-forward loopback a Traefik con Host wordle.test: no precisa DNS público o certificado público para ese recorrido. Services ClusterIP, backend y PostgreSQL sin exposición directa; el Standard LB/IP de salida AKS sí es facturable y no equivale a publicar la aplicación. GHCR tiene evidencia anónima por digest del preflight; salida HTTPS/pull desde nodos, admission, CSI y RBAC de métricas siguen NOT RUN. No se crean redes/NSG/firewalls ni se despliega para probarlo.

## 4. Backend remoto

**BLOCKED.** azurerm con use_azuread_auth=true, configuración parcial; ejemplo: RG rg-wordle-state, cuenta placeholder, contenedor tfstate, key wordle/aks-demo.tfstate. No hay coordenadas aprobadas ni ubicación real verificable. Se listaron metadatos ARM: tres RG y una cuenta Storage en la suscripción; rg-wordle-state no existe. La cuenta existente no se atribuye al TFG ni se reutiliza por estar disponible; no se leen claves ni blobs, no se inspeccionan sus datos.

Se necesita Storage Account + contenedor externo y separado de RG de aplicación/nodos, destino/key explícitos, autenticación Entra de la identidad operadora, Storage Blob Data Contributor al ámbito mínimo y conectividad/red/retención aprobadas. Backend state no lo crea el módulo Terraform. Región/tipo/replicación/coste reales no definidos. Creación de Storage/roles requiere autorización separada. Existencia, lectura efectiva, lease y bloqueo del estado NOT RUN; no init, migración o escrituras sobre estado. Comprobar bloqueo requerirá autorización futura antes del plan controlado.

## 5. Coste académico: escenarios de cuatro horas

Retail API consultada hoy, Linux westeurope Consumption: D4s_v5 **0.23 USD/nodo/h**; D4s_v4 **0.31 USD/nodo/h**. Valores públicos minoristas orientativos, sin impuestos/conversión EUR/oferta personal. DSv4 no es más barato en esta consulta y no está aprobado; cuota disponible no justifica describirlo como ahorro.

| Escenario | Recursos | Cómputo 4 h orientativo | Límite |
|---|---|---|---|
| A: ensayo mínimo de despliegue/juego | Mismos 2 nodos Terraform, discos OS, PG/PVC, salida LB/IP, estado; no se crea otro perfil reducido | 1.84 USD con D4s_v5, **inviable hoy por cuota**; 2.48 USD con D4s_v4 solo hipotético | No acredita por sí solo toda FIN-18. Retirar observabilidad no reduce nodos ni cambia arquitectura sin aprobación. |
| B: demo completa | Igual base + Blue/Green, observabilidad y restore; una DB compartida, sin duplicarla por color | Mismos importes si exactamente 8 nodo-horas | Surge, reconstrucción, solapamiento o duración adicional aumentan nodo-horas; no incluidos. |

Suma adicional **no verificada en importe**: 2 discos OS Managed 64 GB, disco PG managed-csi solicitado 8 GiB (facturación por tier/capacidad real, no solo datos), Standard LB/IP salida y datos procesados/egreso, Storage/operaciones/retención del estado y backups/snapshots si se autorizan. RG/VNet/identidad/roleAssignment no añaden aquí servicios premium declarados; AKS Free no cobra gestión control plane pero sí recursos subyacentes. No ACR, NAT Gateway, Log Analytics ni Azure Monitor premium configurados. Observabilidad autogestionada consume nodos/almacenamiento/tráfico; señales emptyDir no preservan historia al reconstruir.

**Total presupuesto BLOCKED:** no se dispone de SKU efectivo de discos, oferta/moneda, tráfico, tamaño/retención del estado ni duración completa. Propuesta previa de 4 h no es aprobación ni tope automático. En B deben caber arranque/aceptación/restore/limpieza o autorizar ampliación. Los datos locales de sizing no garantizan cabida en nodos AKS con reservas/addons.

Tras parar la app o AKS pueden seguir cargos de discos/PVC, IP/LB según persistencia, snapshots, Storage y backups. Tras retirada autorizada verificar inventario ARM de RG de aplicación/nodos, discos/IP/LB huérfanos, cargos pendientes y estado separado; no borrar automáticamente Storage ajeno o backend. Escalar a cero Pods no equivale a eliminar infraestructura.

Fuentes: [Retail API](https://prices.azure.com/api/retail/prices), [precios AKS](https://azure.microsoft.com/en-us/pricing/details/kubernetes-service/), [facturación discos](https://learn.microsoft.com/en-us/azure/virtual-machines/disks-understand-billing), [System pools](https://learn.microsoft.com/en-us/azure/aks/use-system-pools), [Compute Usage](https://learn.microsoft.com/en-us/rest/api/compute/usage/list), [Quota API](https://learn.microsoft.com/en-us/rest/api/quota/quota/list?view=rest-quota-2025-09-01).

## 6. Evidencias académicas pendientes y ejecución futura

FIN-05 ya tiene perfiles separados kind/runtime, render/ClusterIP, DB de ensayo y pruebas locales: no repetir esa implementación. Aceptación cloud final corresponde a FIN-18. FIN-16/17 aporta helpers y guía, no despliegue acreditado. Requisitos reales:

1. Despliegue AKS autorizado: plan/hash/commit/digests trazables, nodos/Pods Ready, probes y PVC managed-csi Bound, runtime e imágenes verificadas desde el clúster.
2. Juego persistente: HTTP por Traefik/Nginx/API, entradas válidas/inválidas, estados finales y lectura SQL; persistencia tras reinicio. No usar MemoryDB como sustituto.
3. Señales: métricas nodo/contenedor y aplicación, logs reales en Loki, trazas Tempo, dashboard con datos y entregas firing/resolved al webhook autorizado; límites del canal interno explícitos.
4. Blue/Green con una base: preparar candidata, promover, identificar versión, provocar fallo posterior a promoción y demostrar rollback automático, midiendo interrupciones y conservación de datos/PVC. Rechazo previo no sustituye rollback.
5. Recuperación FIN-19: backup real, restore a base independiente nueva, SQL/secuencias y HTTP; reconstrucción de infraestructura tras retirada autorizada, tiempos/coste residual. No basta pg_restore sin HTTP.
6. Limpieza: plan-destroy e inventario revisados, confirmación DESTROY separada, retirada solo de recursos propios; comprobar remanentes conservando estado/backup hasta aceptación. Nada de esto ejecutado hoy.

## 7. Decisiones del propietario y secuencia mínima

1. Resolver **cuota DSv5 0**: autorizar solicitud de cuota (más margen regional para surge) o evaluar SKU de familia con cuota, incluido D4s_v4. No cambiar SKU por precio o catálogo sin confirmar restricciones y aprobar coste. Ninguna solicitud ni modificación hecha.
2. Elegir parche AKS compatible y estrategia de surge con cuota suficiente; concretar grupo Entra/miembro, CIDR de salida y aprobación de red.
3. Aprobar backend externo exacto y sus permisos/coste; autorizar su bootstrap si falta. La existencia de Storage ajeno no lo convierte en disponible para este TFG.
4. Aprobar presupuesto total, ventana y limpieza. Preservar/consolidar fuentes locales mediante autorización Git separada cuando proceda: HEAD publicado no incluye toda la preparación.
5. Con esos gates, solicitar autorización específica para preparar workspace y ejecutar init/plan remoto con sus implicaciones de acceso/lease; revisar plan/hash. CREATE, deploy, fallos controlados, restore y DESTROY son autorizaciones separadas. No hay ejecución posterior automática.

## 8. Validaciones y preservación

**PASS:** comprobación de versiones por rutas instaladas, Terraform fmt -check local (exit 0), lecturas de contexto/providers/versiones/Compute Usage/permisos/Graph/metadatos Storage/RG y precios. **BLOCKED:** API Quota y SKU por error/timeout, capacidad, grupo aprobado, red, backend y presupuesto. **NOT RUN:** init/validate con proveedores, plan/apply/destroy, acceso al estado/lease, pruebas SQL/HTTP en AKS, suites/demos locales repetidas, registros o instalaciones. No se presenta evidencia histórica como ejecutada hoy.

Solo se añade este informe. Los cuatro archivos versionados modificados y 31 sin seguimiento previos se preservan por SHA-256; índice vacío. Sin secretos, escrituras Azure, Terraform remoto, despliegues, publicación, commits ni pushes. FIN-05/16/17/18/19 no se marcan completadas. Esperar revisión del propietario.
