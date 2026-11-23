# FIN-AKS-CONFIG-DECISION — Wordle — 15/11/2026

## 1. Resumen ejecutivo

**PASS del análisis; AKS NO-GO.** Se propone conservar la arquitectura y concretar cuatro decisiones: grupo Entra dedicado con Kubernetes RBAC; CNI Overlay con rangos existentes sujetos a aprobación; backend Storage separado con Entra; AKS **1.35.9 GA** como candidato. Son recomendaciones, no configuración aplicada ni autorización de creación.

Hechos verificados hoy: archivos Terraform relevantes leídos; contexto suscripción `11306565…1bb5`, tenant `aff0390f…1eb9`, Enabled; consulta de versiones regionales correcta; rg-wordle-state no existe. La consulta ARM de cuentas Storage con tag project=wordle no obtuvo resultado utilizable (READ_FAILED): no concluir que no existe ninguna. No se examinan cuentas ajenas, credenciales o estado.

## 2. Estado actual verificado

main.tf define RG, VNet/subred, identidad administrada, permiso Network Contributor de esa identidad en subred y AKS. SKU Free, dos Standard_D4s_v5, Ubuntu, discos OS Managed 64 GB, max_pods 30, sin autoscaling ni zonas/max_surge explícitos. Terraform >=1.6,<2; ejecutable instalado 1.9.8; AzureRM =4.50.0, registro automático de providers deshabilitado. Provider usa subscription_id/tenant_id explícitos.

La evidencia FIN-AKS-QUOTA-REQUEST acredita DSv5 16/regional 26 y uso cero; no se repite esa consulta. Dos nodos consumen 8 vCPU y un surge lleva a 12, dentro de ambos límites, siempre descontando otros consumos. No prueba capacidad física ni asignación por zona. Una DB compartida y persistente, sin HA, sin duplicarla por Blue/Green.

## 3. Propuesta de identidad y autorización

**Conservar Entra administrado + Kubernetes RBAC**: role_based_access_control_enabled=true; azure_active_directory_role_based_access_control con tenant explícito, admin_group_object_ids no vacío, azure_rbac_enabled=false; local_account_disabled=true. Cambiar a Azure RBAC para Kubernetes no es necesario para esta primera demo y exigiría revisar roles/flujo. Ambos mecanismos son válidos, pero no se confunden roles ARM con permisos de recursos Kubernetes.

Propuesta de grupo: `grp-wordle-aks-admins`, seguridad, membresía asignada, administradores sintéticos no necesarios: miembros serán los operadores humanos expresamente aprobados. El grupo es exclusivo de administración técnica del clúster, no autenticación de jugadores Wordle. Solo añadir al propietario si autoriza su identidad exacta; no usar automáticamente el usuario CLI. Un operador puede bastar para la demo; un segundo responsable es opcional y no requisito de alta disponibilidad.

AKS no exige universalmente un grupo específico con ese nombre, pero **el módulo actual exige un grupo existente** por validación y lo usa para administración. Crear uno dedicado es la opción mínima si no hay grupo autorizado reutilizable. La evidencia Graph previa no acreditaba grupos de seguridad del operador; no se amplía hoy el inventario del tenant. Procedimiento futuro: propietario confirma tenant/grupo/miembros, administrador Entra o usuario con capacidad de creación autorizada crea/aprueba grupo, se verifica securityEnabled, object ID y membresía transitiva, y solo entonces se proporciona el ID externamente. Permisos Graph/Entra son independientes de Owner de suscripción. No se crean grupos ni roles.

Separar identidades:

- Operador Terraform: autenticación CLI actual como vía inicial supervisada, con tenant/suscripción explícitos. Requiere crear RG/red/AKS/identidad y asignar rol de subred; limitar ámbitos donde sea viable. Un rol Contributor por sí solo no concede roleAssignments/write; autorización de roles debe ser específica, no asignar Owner por comodidad. Las acciones ARM amplias previas no constituyen prueba definitiva de denies/data-plane.
- Control plane: identidad user-assigned que ya define Terraform; Network Contributor exclusivamente en subred, antes de AKS. No usarla como identidad humana ni del backend Terraform.
- Kubelet: sin kubelet_identity precreada, AKS crea identidad user-assigned en el RG de nodos. No necesita AcrPull porque se usa GHCR público. Acceso pull desde nodos pendiente; no introducir PAT por defecto.
- Administración posterior: kubeconfig de usuario nuevo externo + kubelogin azurecli; no --admin. Despliegue de namespaces/CRD/RBAC/observabilidad requiere permisos de clúster para bootstrap; para evolución, separar bootstrap de despliegue normal con RoleBindings al ámbito necesario. Grupo cluster-admin se reserva a operadores supervisados; no representa mínimo privilegio para toda automatización futura.
- OIDC Actions es una evolución ya preparada, no obligatoria para el primer ensayo local ni razón para crear más identidades ahora. No mezcla con autenticación HTTP de Wordle, que continúa ausente.

Fuentes: [Entra administrado](https://learn.microsoft.com/en-us/azure/aks/enable-authentication-microsoft-entra-id), [RBAC Kubernetes](https://learn.microsoft.com/en-us/azure/aks/azure-ad-rbac), [identidades AKS/kubelet](https://learn.microsoft.com/en-us/azure/aks/managed-identity-overview).

## 4. Red y CIDR candidatos no autorizados

Recomendación: conservar **Azure CNI Overlay** y Standard LB de salida, sin NAT Gateway, Ingress público o Private Endpoint nuevos.

| Uso | Candidato existente | Estado |
|---|---|---|
| VNet | 10.10.0.0/16 | No autorizado hasta revisar solapamientos externos |
| Subred nodos | 10.10.0.0/24 | Contenida en VNet; suficiente nominalmente para tres nodos, no sizing completo |
| Pods overlay | 10.244.0.0/16 | No se solapa internamente; cada nodo recibe bloque /24 aunque max_pods=30 |
| Services | 10.20.0.0/16 | Distinto de VNet/pods |
| DNS Service | 10.20.0.10 | Dentro de services, no dirección inicial reservada |
| API origen | IPv4 pública del operador /32, aún no determinada | Se aporta/verifica por el propietario; no sustituir con una IP inventada |

La contención subred/VNet es intencionada. Los rangos de nodos/pods/services son internamente distintos, pero ello no certifica ausencia de solapamiento con VPN, peering o redes corporativas. El propietario debe aportar/verificar inventario aprobado sin consultar otros proyectos, en particular Nexo. Mantener rangos actuales minimiza cambios; no crear otro direccionamiento sin necesidad.

API server público restringido por authorized_ip_ranges, no 0.0.0.0/0; aplicación por Traefik/Ingress y port-forward loopback Host wordle.test, Services ClusterIP, PostgreSQL/backend sin exposición externa directa. Autorización de IP no sustituye Entra ni auth por jugador. IP doméstica dinámica puede romper acceso: comprobar /32 antes de cada ventana; actualización posterior necesita autorización. Alternativa compatible: salida corporativa estable ya aprobada; no abrir rangos enteros ni instalar una VPN para resolverlo. API privada exigiría conectividad/DNS/VPN adicional que no se justifica para este incremento.

Otra variante de red (CNI flat/pod subnet) requiere cambios de subred/IPAM y no aporta valor académico frente al overlay existente; se descarta como cambio inicial. Outbound loadBalancer crea recursos LB/IP facturables, no significa que exista un Service público de aplicación. Permitir DNS/salida HTTPS a endpoints oficiales AKS, registros y GHCR según requisitos; no añadir proxy/rutas/firewalls automáticamente. La API requiere Entra y conectividad desde la salida autorizada; los nodos necesitan pulls reales y DNS. La demo privada no necesita dominio/TLS públicos, pero no debe presentarse ese acceso HTTP loopback como solución web pública.

Fuentes: [CNI Overlay](https://learn.microsoft.com/en-us/azure/aks/concepts-network-azure-cni-overlay), [IP autorizadas API](https://learn.microsoft.com/en-us/azure/aks/api-server-authorized-ip-ranges).

## 5. Backend remoto propuesto

Actual: backend azurerm parcial con use_azuread_auth=true; no storage definido en Terraform principal. Inconsistencia menor de ejemplos: backend.hcl.example usa RG/key genéricos `rg-state-example` y `wordle/academic/terraform.tfstate`; azure-backend.example.json usa `rg-wordle-state` y `wordle/aks-demo.tfstate`. Son ejemplos, no dos backends activos; hay que elegir una coordenada antes de init, sin mezclar claves ni migrar estados implícitamente.

Propuesta a aprobar:

- RG independiente `rg-wordle-state`, westeurope, fuera del RG AKS y del RG de nodos; no destruirlo junto con la demo.
- StorageV2 Standard_LRS, Hot, nombre candidato `stwordletfgstate<suffix>` (minúsculas/números, <=24; sufijo elegido y unicidad verificada posteriormente). No nombre definitivo reservado ni disponibilidad comprobada.
- Contenedor privado `tfstate`, blob key **wordle/aks-demo.tfstate**, para alinearse con el JSON del flujo supervisado actual. Para otro entorno futuro, otra key explícita `wordle/<entorno>/terraform.tfstate`; no workspaces ni organización multiambiente innecesarios hoy.
- Entra para data-plane, HTTPS/TLS1.2 mínimo, acceso anónimo deshabilitado, evitar claves/SAS y deshabilitar Shared Key si no hay dependencia aprobada. Identidad operadora con Storage Blob Data Contributor sobre contenedor; el creador necesita gestión del Storage/RG y roles durante bootstrap, sin mantener privilegios globales innecesarios. Reader adicional solo si se necesita lookup del endpoint según backend; no asumir Owner equivale a Blob Data Contributor.
- Endpoint público Storage con firewall a salida IPv4 aprobada para estación; sin abrir all networks como sustituto de un CIDR pendiente. No Private Endpoint nuevo para esta demo; runner futuro necesita salida autorizada o revisión de conectividad.
- Blob versioning y soft delete de blobs/contenedores 7 días como propuesta inicial. Conservar versiones anteriores según política simple de retención/coste aprobada; configurar lifecycle de versiones si se decide, no prometer que activar versioning las expire automáticamente. Sin inmutabilidad que bloquee escrituras/lease normales de Terraform.
- Bloqueo nativo de azurerm mediante lease; no se ha probado. Test de concurrencia/recuperación de estado requiere autorización posterior de init/lease. No force-unlock automático ni borrar estado para resolver errores.

Reutilización: RG previsto no existe; consulta de cuentas Storage con tag Wordle dio READ_FAILED. No hay backend reutilizable confirmado. La cuenta Storage que aparecía en inventario general previo no está autorizada por eso para Wordle y no se inspecciona/reutiliza. Crear backend y asignar sus permisos son acciones externas futuras separadas; el backend no se crea usando un estado remoto que todavía no existe.

Coste: Standard_LRS y blobs pequeños reducen recursos respecto a servicios dedicados, pero no son gratuitos. Aproximación de cálculo: GB almacenados actuales + versiones/soft-delete × tarifa GB-mes Hot/LRS, más lecturas/escrituras/listados y egress. Aun con una demo de horas, retener 7 días/estado después produce costes residuales. No hay tamaño/operaciones/cotización suficientes para un importe fiable ni se inventa un total. Sin cambio a premium/geo-replicación/Private Link por defecto; revisar riesgo de LRS y respaldar/exportar evidencia autorizada.

Fuentes: [backend azurerm, Entra, permisos y locking](https://developer.hashicorp.com/terraform/language/backend/azurerm), [protección/versiones](https://learn.microsoft.com/en-us/azure/storage/blobs/data-protection-overview).

## 6. Versión AKS recomendada: 1.35.9

Consulta real de West Europe hoy devuelve ramas 1.31–1.37; **1.35.9 está en patchVersions de 1.35**; predeterminado regional 1.36. Los campos isPreview de CLI son null: no se usa null como prueba GA. La documentación oficial clasifica 1.35 GA (marzo 2026), con fin de soporte estándar marzo 2027; 1.34 alcanza fin de soporte estándar noviembre 2026. Por eso se propone 1.35.9: parche listado de una rama GA con margen, sin saltar al predeterminado solo por ser más nuevo. Revalidar oferta/soporte/parche justo antes de plan; si desaparece, volver a decidir, no actualizar automáticamente.

Terraform hoy mantiene kubernetes_version=null; no se cambia. AzureRM 4.50.0 expone kubernetes_version y campos usados; su documentación recomienda proveedor actualizado por evolución rápida AKS. **Compatibilidad de esquema documentada no equivale a validación end-to-end** de esta versión de proveedor con AKS1.35.9, API/OS y todos los recursos. Sin init/plan ni proveedor nuevo aquí. Si un futuro plan autorizado revela incompatibilidad, corregir causa mínima con autorización, no ampliar a upgrade indiscriminado.

Cliente kubectl histórico 1.34.1 está a una minor de 1.35; cumple regla general de skew de una minor, sin acreditar comportamiento completo ni impedir actualizarlo si una prueba posterior lo exige. Ubuntu actual se conserva; versión de imagen/OS efectiva y soporte regional deben confirmarse en plan. No preview/LTS premium por defecto, no cambios automáticos de OS.

Mantenimiento propuesto: fijar parche aprobado para la ventana temporal; sin autoscaling ni canal de auto-upgrade activado automáticamente. Revisar node OS/security defaults del proveedor/servicio en el plan; no afirmar que estén desactivados porque se omitan del código. Si se autoriza operar más tiempo, revisar soporte y ventanas antes de actualizar. Proponer max_surge explícito **"1"** en futuro cambio mínimo para hacer determinista el cálculo (hoy ausente); 12 vCPU durante upgrade dentro de DSv5 16/regional 26, si no hay otros consumos. Surge cuesta VM/disco temporal y requiere capacidad real. No se prueba upgrade ni rollback de plataforma; el rollback app no deshace un upgrade Kubernetes.

Fuentes: [soporte AKS](https://learn.microsoft.com/en-us/azure/aks/supported-kubernetes-versions), [AzureRM 4.50.0 fijado](https://raw.githubusercontent.com/hashicorp/terraform-provider-azurerm/v4.50.0/website/docs/r/kubernetes_cluster.html.markdown), [skew kubectl](https://kubernetes.io/releases/version-skew-policy/), [surge](https://learn.microsoft.com/en-us/azure/aks/upgrade-capacity-cost-planning).

## 7. Compatibilidad, dependencias y limitaciones

Grupo Entra + membresía habilitan autenticación autorizada; CIDR habilita transporte pero no otorga permisos. Terraform necesita acceso ARM y backend Blob, mientras kubelet/control plane usan otras identidades. Firewall de estado y API deben permitir la salida real del operador. No introducir GHCR credenciales si imágenes públicas funcionan. Observabilidad cAdvisor/hostPath/admission/CSI debe demostrarse en AKS, no inferirse de kind. Nodo System de 4 vCPU/16 GiB cumple nominalmente, pero reservas/DaemonSets/picos requieren medidas reales.

Cuota resuelta no equivale a capacidad física; DB de una réplica y PVC son un punto único de fallo aceptado para demo. No activar HA o plataforma permanente. La aplicación sigue privada, sintética, sin aislamiento por jugador. El backend remoto debe sobrevivir a la retirada controlada de AKS; su coste y eliminación requieren decisión separada.

## 8. Matriz de decisiones

| Área | Actual verificado | Propuesta | Riesgo/pendiente | Decisión del propietario |
|---|---|---|---|---|
| Entra ID | Entra + Kubernetes RBAC, admin IDs sin aportar | Grupo grp-wordle-aks-admins y miembros aprobados; cuentas locales off | Privilegio admin de bootstrap, permisos Graph/Entra | Aprobar grupo, responsables/miembros y eventual creación autorizada |
| Red/CIDR | Overlay, rangos existentes; API público restringido sin CIDR real | Mantener rangos candidatos y /32 de salida revisada; loopback demo | Solapamientos externos/IP dinámica; costes LB/IP | Confirmar no solapamiento y origen de red aprobado |
| Backend | azurerm/Entra parcial, RG no existente; ejemplos con claves distintas | RG separado, StorageV2 LRS, tfstate, key wordle/aks-demo.tfstate, firewall y retención 7d | Coste/ACL/data-plane, unicidad, falta bootstrap y lease | Aprobar coordenadas, seguridad/retención/coste; creación futura separada |
| Kubernetes | null, AzureRM4.50 | 1.35.9 GA, max_surge1 futuro | Parche/OS/API/proveedor requieren plan y runtime | Aprobar versión/surge y revalidación antes de ejecución |

## 9. Riesgos y restricciones

PASS de propuesta no es GO para plan ni apply. Coste total y ventana académica todavía sin aprobación; VM histórica 0.46 USD/h para dos nodos es solo cómputo. Estado, discos OS/PG, LB/IP/tráfico y retención no se omiten por desconocer tarifa. Preparación AKS/restore local contiene archivos sin consolidar: HEAD publicado no reproduce por sí solo esos materiales, sin autorización Git para publicarlos aquí.

## 10. Autorizaciones necesarias

Aprobar las cuatro propuestas anteriores y confirmar datos privados no secretos (IDs de grupo/destino, CIDR, coordenadas de backend) por canal apropiado sin contraseñas. Separar autorización de (a) grupo/membresía y roles, (b) bootstrap Storage y seguridad/red, (c) mínimos cambios Terraform/variables externos tras decisiones, (d) init/lease/plan, (e) CREATE/despliegue/ensayos y (f) DESTROY supervisado. Ninguna de esas acciones está autorizada por esta propuesta.

## 11. Próxima iteración recomendada

Aceptar o ajustar esta matriz; después resolver primero el grupo Entra y el backend externo, con CIDR confirmado y autorizaciones acotadas. Solo entonces preparar variables exactas y cambio mínimo de versión/surge, con revisión previa a plan. Reutilizar helpers existentes, no crear otro roadmap ni iniciar fase automáticamente.

Alcance efectivo: solo se crea este informe. Inspección local selectiva y consultas Azure GET/equivalentes de versiones/contexto/metadatos del RG/tag Wordle; consultas oficiales web. Sin cambios Azure, Entra, RBAC, Terraform/configuración, estado, despliegues, cuotas, commits ni pushes. Todos los archivos locales previos preservados por SHA-256. No se ejecutan suites repetidas ni se inspeccionan recursos de Nexo.
