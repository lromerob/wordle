# FIN-AKS-PREFLIGHT — 15/11/2026

## Decisión

**CONDITIONAL GO para preparar una solicitud de despliegue; no autorizado ni listo para ejecutar hoy.** La implementación local permite una demo académica temporal, pero deben resolverse los gates externos siguientes. FIN-04 aceptada documentalmente por el propietario; FIN-05/18 no se cierran sin evidencia AKS. No se altera el plan ni se despliega.

Repositorio: rama `codex/pg01-07-consolidation`, HEAD `4d56cf265cc5f0af8c72c64f2a93373660e8f122`. Se reutilizan el informe FIN-16/19, `docs/operations/azure-demo.md`, Terraform, `aks-full`, `aks-restore` y los ejecutores existentes. Las primeras secciones históricas de la guía dicen que falta adaptación AKS; la ampliación final documenta `aks_run.py` implementado: falta validarlo realmente, no volver a implementarlo.

## Comprobaciones realizadas

| Comprobación | Estado | Resultado y límite |
|---|---|---|
| Sesión CLI y contexto | PASS | Sesión existente, suscripción Enabled; sin login, cambio de contexto ni difusión de IDs. Coincidencia con un destino aprobado: BLOCKED, variables privadas no aportadas. |
| Permisos generales ARM | PASS | Lectura de actions permite AKS, red, identidad y roleAssignments. No acredita ámbitos efectivos, deny assignments, Entra ni permisos data-plane. |
| Providers requeridos | FAIL | ContainerService, Network y Compute NotRegistered; ManagedIdentity y Storage Registered. No se registra ninguno. |
| Grupos/nombres previstos | PASS | Lectura correcta; ninguno de los dos RG predeterminados existe. Cero RG y recursos con tag project=wordle. No demuestra ausencia de recursos sin esa etiqueta ni reserva nombres DNS/Storage. |
| Disponibilidad regional AKS | PASS | Consulta westeurope devuelve versiones 1.31–1.37; listado no equivale a selección soportada de parche ni capacidad real. |
| SKU | BLOCKED | D4s_v5 listado, x64, 4 vCPU/16 GB; restricción NotAvailableForSubscription en zonas 1 y 3. El pool no fija zonas: no prueba imposibilidad regional ni garantiza asignación. Confirmar capacidad antes de autorizar. |
| Cuotas | BLOCKED | Consulta completada, sin filas utilizables de cores/familia. No se interpreta como cuota cero ni suficiente; mínimo nominal 8 vCPU más margen de surge. |
| Entra y acceso API | BLOCKED | Grupo administrador/pertenencia y CIDR de salida aprobados no aportados. API pública restringida por CIDR; cuentas locales deshabilitadas. Sin abrir 0.0.0.0/0. |
| Estado remoto | BLOCKED | Backend azurerm declarado; coordenadas, existencia, RBAC/red y acceso no verificados. No se leen estados, no se ejecuta init remoto ni se adquieren leases. Prueba de bloqueo NOT RUN, requiere autorización posterior. |
| Herramientas | FAIL | Azure CLI, kubectl y Docker CLI presentes; Terraform nativo y kubelogin ausentes del PATH, requeridos por el procedimiento. Motor Docker NOT RUN, innecesario aquí. No se instala software. |
| Kustomize | PASS | Render local aks-full y aks-restore: 63 objetos cada uno; 11 imágenes distintas por digest, solo Services ClusterIP, un PVC RWO managed-csi 8Gi. No dry-run server ni despliegue. |
| GHCR | PASS | Consulta anónima real de manifests/config de ambas imágenes: SHA, Linux/amd64 y revisión coincidente con HEAD. Sin PAT ni publicación. Pull desde nodos AKS NOT RUN; ningún imagePullSecret personal introducido. |
| Scripts | PASS | AST Python y 27 pruebas offline: 16 guardas/preflight + 11 orquestación/controlador con dobles; cero omisiones. No sustituyen AKS real. |
| Terraform | NOT RUN | Ejecutable nativo ausente; se conserva evidencia anterior de fmt/init backend=false/validate, no se presenta como ejecutada hoy. No plan, apply, destroy ni operaciones de estado. |
| OIDC/workflow/runner | BLOCKED | Workflow Azure local opt-in, reviewers, environment protegido, OIDC y runner dedicado de salida aprobada requieren configuración/verificación externa. No se consulta ni modifica GitHub para activarlos. Ejecución supervisada local evita esa dependencia CI, pero requiere herramientas/Entra/red. |
| HTTP/SQL/CSI/rollback/señales en AKS | NOT RUN | Sin clúster creado ni contacto con AKS; no se reutilizan resultados kind como aceptación cloud. |

## Arquitectura, recursos y configuración externa

Terraform define seis recursos: RG, VNet, subred, identidad administrada, asignación Network Contributor sobre subred y AKS (depends_on del permiso). AKS Free, dos D4s_v5 por defecto, discos OS Managed de 64 GB por nodo; red overlay, Standard Load Balancer y una IP de salida gestionada. El RG de nodos lo crea AKS. No ACR, base administrada, NAT Gateway ni Azure Monitor/Log Analytics declarados. Backend del estado externo, separado de ambos RG desechables; no lo provisiona este módulo.

Variables sin default obligatorias: subscription_id, tenant_id, admin_group_object_ids y api_authorized_cidrs. Aprobar además nombres, versión Kubernetes regional compatible, región, capacidad, etiquetas y duración. Mantener CIDRs y parámetros de identidad/estado externos y no secretos en Git. Las tres contraseñas sintéticas externas (admin DB, app DB, Grafana) deben ser distintas, >=32 caracteres y suministrarse por entorno protegido; no se han leído ni generado.

Blue/Green comparte una única instancia PostgreSQL 16 y PVC; no hay HA ni rollback de datos. `aks_run.py` reutiliza el controlador de promoción y validación de señales; las pruebas offline no prueban admission, CSI, RBAC kubelet/cAdvisor ni runtime en AKS. Traefik/Ingress se usa por port-forward loopback con Host wordle.test; backend y PostgreSQL no tienen Service público. La API de control AKS es pública restringida, distinta del acceso público a la aplicación.

Requests renderizados: aks-full con Blue inicial y Green a cero suma 1.125 CPU y 1040 MiB, contando una instancia de DaemonSet. Green activo añade 0.175 CPU/208 MiB; por cada nodo adicional se suma otra instancia Node Exporter. Faltan reservas kube-system, DaemonSets, límites y picos: no prueba capacidad real. Señales en emptyDir, sin historia durable tras reconstrucción. Alertas al webhook interno, no notificación externa a personas.

## Estimación económica limitada

Consulta pública Azure Retail Prices API del 15/11/2026, filtro westeurope/Standard_D4s_v5/Consumption, producto Linux Virtual Machines Dsv5 Series, sin Spot ni Windows: **0.23 USD por nodo/hora**, unitOfMeasure 1 Hour. Precio minorista orientativo, no cotización contractual ni precio EUR/impuestos/suscripción.

Dos nodos: **0.46 USD/h solo VM**. Demo de 4 h: **1.84 USD**; 8 h: **3.68 USD**, excluyendo tiempo de creación/reconstrucción y surge. Fórmula: 0.23 × suma de horas de cada nodo, incluidos nodos adicionales temporales. Una reconstrucción añade sus propias horas; los créditos personales no se presuponen.

Agregar discos OS (2×64 GB provisionados), disco PostgreSQL (8 GiB solicitados, tier real pendiente), LB/IP pública de salida, tráfico/egreso, Storage/operaciones/retención del estado y posibles snapshots/backups. AKS Free no cobra gestión del control plane, pero sí recursos subyacentes; RG/VNet/identidad no añaden aquí un servicio premium declarado. Observabilidad autogestionada consume nodos/discos/tráfico; no hay cargo SaaS de Azure Monitor declarado. Storage remoto no tiene tamaño ni redundancia aprobados. No puede darse un total fiable sin SKU efectivo de discos, moneda/oferta, tráfico, retención y duración completos.

Discos/PVC, snapshots, IP/LB y estado pueden seguir generando cargos después de parar la aplicación; detener Pods no retira infraestructura. Los discos se facturan por capacidad provisionada/tier y tiempo, no solo datos usados. Preparar estimación completa y presupuesto máximo del propietario antes de crear; una alerta de presupuesto no es corte automático.

Fuentes: [tarifas AKS](https://azure.microsoft.com/en-us/pricing/details/kubernetes-service/), [discos](https://learn.microsoft.com/en-us/azure/virtual-machines/disks-understand-billing), [Retail Prices API](https://prices.azure.com/api/retail/prices), [calculadora](https://azure.microsoft.com/en-us/pricing/calculator/).

## Demostración y limpieza futuras — NO EJECUTADAS

1. Aprobar destino, duración/presupuesto y capacidad; resolver providers, herramientas, Entra/CIDR y backend externo. Si se usa Actions, configurar además environment/OIDC/runner y publicar fuentes mediante incremento autorizado.
2. Preservar paquete de fuentes/config por hash (`azure_release.py`) y archivos privados separados. El HEAD por sí solo no incluye la preparación local sin seguimiento.
3. Preparar workspace externo mediante azure_supervised.py; autorización independiente para plan remoto/lease. Revisar plan, hash, inventario y costes antes de autorización explícita CREATE y ejecución del plan guardado.
4. aks_run.py credentials y deploy con confirmación exacta y ack-costs: kubeconfig nuevo externo, secretos sintéticos, aks-full, PVC y rollouts. verify debe comprobar digests/runtime, frontend/proxy HTTP, escritura SQL y juego.
5. acceptance, con autorización de fallos controlados: promoción Green, fallo después de promoción Blue, rollback real a Green, conservación DB/PVC y señales/alertas reales. No confundir rechazo previo con rollback.
6. backup con pausa/reanudación de escritores y evidencias exportadas. Restaurar a destino nuevo independiente mediante restore-deploy/restore; exigir SQL, secuencias/datos y HTTP, no solo dump válido. Reconstrucción requiere autorización separada de retirada y creación.
7. Antes de limpiar, exportar evidencia/backup y revisar inventario de ambos RG, discos, PVC, LB/IP y recursos ajenos. Preparar plan-destroy revisado y solicitar autorización DESTROY separada. No ejecutar borrado genérico de RG ni tocar PG-05/06.
8. Tras retirada autorizada, consultar remanentes/cargos; conservar backend del estado y backups hasta aceptación del responsable, con su coste explícito. Retirada de estado/backups requiere decisión separada.

Guía de comandos existente: `docs/operations/azure-demo.md`, ampliación del ejecutor AKS al final. No repetir fases ya implementadas ni desplegar para completar este preflight.

## Intervención del propietario y repositorio

Antes de solicitar CREATE: confirmar que esta es la suscripción/tenant elegida; autorizar registro de tres providers; resolver capacidad/cuota; aprobar grupo Entra, salida API, backend externo y presupuesto; autorizar instalación/configuración de herramientas ausentes. Publicación de fuentes y activación OIDC/runner, si se elige CI, son incrementos separados. Después solicitar autorización explícita del plan, despliegue, fallos de ensayo y limpieza.

Se preservan los cuatro documentos/scripts versionados modificados y los 29 archivos sin seguimiento previos, incluidos doce históricos. Solo se añade este informe. Sin commits/push, cambios de aplicación/infraestructura/secretos, despliegues, leases ni Azure writes. Un intento de resumen de RG falló por tags nulos; se corrigió únicamente el comando temporal de lectura y la consulta posterior fue satisfactoria, sin editar scripts del proyecto.


---

## Preflight final selectivo — 16/11/2026

### 1. Resumen ejecutivo y autorización documental

**PASS documental; Gate A/B/C sin autorización operativa, AKS NO-GO.** El propietario autorizó expresamente «Añadir sección fechada al existente» tras identificar que el entregable ya existía. Esta sección complementa el informe del15/11, cuyo contenido queda íntegro y fechado; no reescribe sus resultados como si fueran actuales.

Se reutilizan FIN-AKS-CONFIG-VALIDATION y FIN-AKS-EPHEMERAL-LIFECYCLE sin duplicar sus matrices completas o repetir pruebas. Herramientas, providers y cuota ya resueltos en sus incrementos dejan de ser bloqueos históricos: DSv5=16/regional26 verificados en FIN-AKS-QUOTA-REQUEST, sin reconsulta innecesaria. La aprobación de cuota no autoriza backend, AKS, gasto ni plan. No se ejecuta ningún comando operativo futuro.

### 2. Contexto Azure verificado

Lecturas efectuadas en esta iteración antes de la aclaración documental: suscripción `11306565…1bb5`, tenant `aff0390f…1eb9`, Enabled, coincidentes con el destino aprobado. Sin login/cambio de contexto. Región westeurope procede de la configuración existente. Consulta filtrada del grupo exacto grp-wordle-aks-admins: cero coincidencias. `az group exists -n rg-wordle-state --subscription <destino>`: false.

No se inspeccionan Storage/VNet/usuarios de otros proyectos. La falta del RG previsto impide dar por existente ese backend concreto, pero no prueba inexistencia global de Storage; no hay otro backend Wordle identificado y autorizado para reutilizar. No se consultan estados o secretos. Restricciones de oferta/permisos/capacidad conservan los límites del análisis previo; no se certifican permisos efectivos con solo una lista de acciones.

### 3. Identidad y permisos

Grupo propuesto aún ausente: no hay Object ID verificable que proporcionar, ni miembros autorizados definidos. Un nombre coincidente futuro tampoco sería aprobación. El propietario debe indicar administradores/propietarios y tenant; responsable Entra comprueba capacidad/política de crear grupos de seguridad, crea o designa grupo SOLO con autorización posterior y verifica securityEnabled, object ID y pertenencia transitiva. No necesita ser grupo asignable a roles de directorio para administrar Kubernetes.

Separar permisos:

- **Entra/Graph:** crear grupo, propietarios y membresía requiere capacidades del directorio; posible usuario habilitado por política o administrador autorizado. No se deduce de Owner/Contributor ARM ni se prueba creando objetos. Una denegación exige intervención del responsable Entra, no elevar roles automáticamente.
- **ARM:** crear RG/AKS/red/identidades necesita acciones de gestión; asignar Network Contributor sobre subred requiere roleAssignments/write en ámbito adecuado. Las acciones amplias observadas anteriormente no excluyen deny/condiciones/Policy. No se reasignan roles.
- **Kubernetes RBAC:** Entra autentica; grupo admin se usa para bootstrap, cuentas locales siguen off; azure_rbac_enabled=false significa autorización Kubernetes RBAC. Despliegues del stack con namespaces/CRD/RBAC exigen privilegios reales posteriores. Mantener kubeconfig usuario/kubelogin, no --admin.

El grupo AKS **no es prerrequisito intrínseco para crear el backend**: este puede usar una identidad operadora aprobada con permisos Storage específicos, sin concederle por ello administración definitiva AKS. No introducir identidad OIDC/runner adicional para el primer ensayo supervisado si no se elige esa vía.

### 4. Red e IP administrativa

Se conserva la comprobación matemática interna PASS de CONFIG-VALIDATION: VNet10.10.0.0/16, subnet10.10.0.0/24, pods10.244.0.0/16, services10.20.0.0/16, DNS10.20.0.10. **No se repite**. Son candidatos, no rangos aprobados externamente.

Falta declaración/revisión del responsable de red del propietario sobre redes domésticas/corporativas/VPN/peering/rutas que puedan solaparse. No se investiga Nexo para inferir ausencia. Responsable: propietario y administrador de la salida/red usada; evidencia requerida: aprobación de rangos y redes revisadas con fecha/alcance, sin exportar inventario sensible.

IPv4 global observada anteriormente no es IP fija ni /32 autorizado. Procedimiento mínimo: activar exactamente la ruta de administración prevista; comprobar salida con un servicio sin credenciales o método aprobado por red, contrastarla con ISP/corporativa y obtener autorización del /32. No hace falta publicar la IP en este informe. Si es dinámica, aceptar explícitamente el riesgo y procedimiento de actualización autorizada; no llamarla estable garantizada.

Inmediatamente antes de init/plan/deploy: contexto correcto, misma VPN/ruta/IP efectiva y acceso permitido al backend/API. Si cambia entre sesiones: detener operaciones, comprobar nueva salida, solicitar modificación puntual aprobada y revalidar; no0.0.0.0/0 ni ampliar rangos para evitar trámites. No alterar ACL/NSG/VPN hoy. Para backend es necesario un origen autorizado a su firewall; para AKS también ausencia de solapamientos y API /32.

### 5. Backend Terraform

Propuesta no aprobada: RG separado rg-wordle-state, StorageV2 Standard_LRS, contenedor privado tfstate, key wordle/aks-demo.tfstate, Entra, HTTPS y retención controlada. Falta nombre final Storage globalmente único, identidad de acceso exacta y controles de red/retención/coste. No reutilizar una cuenta ajena por estar disponible.

Permisos de bootstrap según vía: Microsoft.Resources/subscriptions/resourceGroups/write, Microsoft.Storage/storageAccounts/write, blobServices/write para propiedades de protección y blobServices/containers/write para creación ARM del contenedor, más lecturas necesarias; Microsoft.Authorization/roleAssignments/write si se autoriza crear asignaciones. La creación de contenedor por data-plane exige los permisos de esa vía, no se supone cubierta por gestión ARM. No mantener roles de suscripción más amplios por comodidad.

Acceso al estado: Storage Blob Data Contributor en el contenedor para la identidad operadora, con Entra; Reader en Storage solo si se usa lookup_blob_endpoint. Sin claves/SAS/PAT. El rol data-plane permite las operaciones de blob/lease necesarias; gestión del Storage no basta para leer/escribir estado. No se ha probado acceso efectivo ni concurrencia. Bloqueo azurerm nativo mediante lease, -lock-timeout del helper; no force-unlock ni borrar estado sin autorización y verificación de propietario huérfano.

Bootstrap mínimo FUTURO: aprobar ficha de backend → autorizar únicamente RG/cuenta/contenedor/propiedades y roles concretos → verificar nombre/disponibilidad/ausencia de recursos ajenos → crear con autenticación/ACL aprobadas → verificar metadatos/RBAC/seguridad → autorizar por separado init/lease/plan cuando proceda. No migrar un estado desconocido ni depender del módulo AKS para crear su propio backend. Preservar estado hasta eliminación efectiva de recursos gestionados.

Decisiones: soft delete de blobs/contenedores7d; versioning más política explícita de versiones (soft delete7d no expira versiones automáticamente); firewall al origen aprobado; Shared Key/anónimo deshabilitados si no hay dependencia aprobada; retenciónB hasta fecha de defensa y eliminación posterior con aprobación. Coste residual: GB actuales/versiones×tarifa + operaciones/egreso durante días entre sesiones. GrupoAKS/versión no bloquean por sí mismos esta fase, pero sí coordenadas/identidad/red/presupuesto del backend.

### 6. Configuración AKS

No se detecta cambio de configuración revisada que obligue a repetir las consultas completas de versión/proveedor: se reutiliza candidato1.35.9 listado en westeurope y ramaGA, AzureRM4.50.0 con argumentos documentados. No se vuelve a consultar catálogo ni a validar schemas por rutina; **no se prueba aquí compatibilidad de provisión**. Si la ejecución se retrasa o cambian Azure/proveedor/OS, revalidar justo antes de plan. Hoy versión sigue null y surge ausente.

Aprobar explícitamente parche1.35.9 y futuro upgrade_settings.max_surge="1" antes de incorporar cambios mediante otra autorización. Dos D4s_v5 y surge usan12vCPU; cuota conocida16/26 ofrece margen aritmético, no reserva hardware ni cubre otros consumos futuros. Revisar acceso API, Entra, CNI, Storage/PVC e imagenUbuntu efectiva durante plan y posterior AKS. No upgrade preventivo ni cambioSKU aquí.

### 7. Presupuesto y controles

Se reutilizan tarifas oficiales fechadas15/11 y cálculo previo: subtotal condicional1.98633USD por sesión4h (VM1.84, discos supuestos0.12633 e IPv40.02); tres sesiones5.95898USD. **No es coste completo ni techo aprobado**. Falta cuantificar LB/datos, tráfico/egreso, operaciones de discos/Storage, tamaño/versiones/retención y posibles remanentes. No repetir consultas de precios que ya dieron medidores incompletos sin un dato nuevo que permita resolverlos.

Presupuesto operativo propuesto: una ventana inicial máxima4h de recursos, sin sobrepasarla por rutina y con retirada preparada; responsable y horas de inicio/límite anotados. Reservar la última hora como margen de cierre/diagnóstico, duración orientativa no garantía de Azure. Un margen técnico de un surge durante1h añade al menos0.23USD de VM más disco/red/operaciones; **no se vende como contingencia monetaria total**. Si no existe cota fiable para los restantes conceptos, el presupuesto monetario sigue BLOCKED y no se inventa un importe máximo.

Supervisar inventario/coste al inicio, tras aprovisionar, durante la sesión y antes del cierre; Cost Management puede tener retraso. Criterios de interrupción de nuevas pruebas: destino/coste no autorizado, recurso imprevisto, IP cambiada, pérdida de evidencia/backups, hora de cierre próxima o fallo repetido sin diagnóstico. No iniciar otro fallo/upgrade que exceda la ventana. Interrumpir pruebas no significa destrucción automática: conservar evidencia/estado, obtener autorización de retirada y actuar sobre inventario revisado.

Iniciar desmontaje solo con evidencias exportadas, backup del dump concreto restaurado SQL+HTTP, plan/inventario revisados y autorización DESTROY, salvo plan de emergencia previamente aprobado. Si no se cumplen, avisar inmediatamente al responsable: no destruir datos a ciegas para ajustarse a coste ni prolongar gasto sin decisión. Las alertas presupuestarias no detienen automáticamente consumo; no se configuran alertas hoy.

Entre sesiones: AKS/nodos/discos/LB/IP exclusivos deben estar retirados y comprobados; conservar solo backend/estado yB aprobado con fecha/retención yC fuera del clúster. No dejar el clúster parado como sustituto de retiro. Facturación y eliminación ARM se evidencian por separado.

### 8. Reproducibilidad y evidencias

FIN-AKS-EPHEMERAL-LIFECYCLE cubre deploy/pruebas/exportación/logs/backups/destroy/redeploy/restore/destroy y matrizE01–E16, que no se duplica. Helpers azure_supervised, aks_run y azure_release existen, sin ejecuciónAKS acreditada; los comandos futuros conservan aprobaciones separadas.

Dependencias críticas: paquete de fuentes/config por hash (HEAD solo no incluye toda preparación); Terraform/providerlock;11imágenes por digest y metadata/revisión; variables y secretos externos bajo custodia, kubeconfig nuevo por instalación; estado con lineage/serial; dumps sintéticos/hash/receipt de restauración; evidencia externa con segunda copia. Rebuild no garantiza mismo digest. Antes de cada sesión verificar disponibilidad de imágenes una vez, no publicar otras por rutina. Los datos emptyDir de observabilidad requieren exportación anterior a retirada.

No se ejecutan backups, probesHTTP/SQL, demoskind, suites o pulls aquí. DisponibilidadGHCR histórica es evidencia fechada, no garantía futura. Capacidad real y tiempos de reconstrucción siguen por medir en sesiones autorizadas.

### 9. Matriz final de decisiones

Estado diferencia verificado/aprobado/pendiente/bloqueado; todas las autorizaciones de la tabla son futuras salvo hechos previos expresamente aprobados.

| Decisión | Estado | Evidencia disponible | Riesgo | Acción necesaria | Responsable | Requiere autorización |
|---|---|---|---|---|---|---|
| Grupo Entra | Bloqueado, ausente | Consulta actual exacta0 | No acceso admin | Elegir/autorizar grupo; creación específica | Propietario/adminEntra | Sí, crear o designar |
| Miembros admin | Pendiente aprobación | No lista aprobada | Otorgar privilegio a quien no corresponde | Aprobar identidades/owners y verificar pertenencia | Propietario/adminEntra | Sí |
| Creación/roles | No comprobado efectivo | Acciones ARM históricas; noGraph/data-plane | Denies/políticas/ámbitos | Validar permisos precisos antes de fase; administrador si faltan | Operador/admin | Sí para cambios, no para lecturas |
| API /32 | Bloqueado | IPv4 observada histórica, no estable/autorizada | Pérdida de acceso o exposición | Confirmar ruta y aprobar /32 | Propietario/red | Sí |
| Solapamientos externos | Bloqueado | Matemática internaPASS previa | ConflictoVPN/peering | Validación de responsable red | Red/propietario | Sí aprobación; no explorar ajenos |
| Backend | Pendiente, RG ausente | group exists=false | Init sin destino válido | Ficha final + bootstrap acotado | Propietario/operador | Sí creación/coste |
| Retención estado | Pendiente aprobación | Propuesta7d/versioning | Borrado/coste residual | Aprobar TTL versiones/fecha final | Propietario/custodio | Sí |
| Custodia secretos/backups | Pendiente aprobación | Procedimiento privado existe | No recuperación/filtración | Asignar custodio, ubicación y segunda copia | Propietario | Sí política y backups futuros |
| Imágenes | Verificado históricamente, no comprobado hoy | Digests/lock yGHCR previos | Digest perdido/rebuild diferente | Conservar y comprobar antes de sesión | Operador/propietario | Retención; publicación nueva separada |
| AKS1.35.9 | Propuesta validada parcialmente | GA/listado anterior | Cambio soporte/API | Aprobar y revalidar antes de plan | Propietario/operador | Sí antes de configurar |
| Surge1 | Propuesta sin aplicar | Argumento soportado, cuota suficiente nominal | Capacidad/pico/coste | Aprobar valor y cambio mínimo posterior | Propietario | Sí |
| Presupuesto | Bloqueado completo | Subtotal1.99 no total | Cargos no cubiertos | Cotizar faltantes y aprobar límite/control | Propietario | Sí |
| Ventana | Pendiente aprobación | Propuesta4h | No acabar/limpiar a tiempo | Fecha/responsable/hitos y emergencia | Propietario/operador | Sí |
| Desmontaje | Documentado, no ejecutado | Helpers/planhash/inventario | Datos/recursos ajenos | Revisar plan/receiptbackup y autorizar cadaDESTROY | Propietario/operador | Sí siempre |

### 10. Gate A — Bootstrap del backend

**NO-GO operativo; propuesta de bootstrap acotado preparable tras decisiones concretas.** Obligatorio: coordenadas completas/nombre disponible, identidad de bootstrap/estado confirmada, permisosRG/Storage/data-plane/roleAssignment necesarios, origen de red aprobado, seguridad/retención, presupuesto del backend y fecha/custodio. Evidencia: ficha aprobada, lecturas de permisos/contexto/ausencia de conflictos dentroWordle y revisión de configuración de creación.

BloqueosA: nombrecuenta no definido; noACL/identidad/retención/coste aprobados; accesoIPv4 no autorizado; permisosGraph no relevantes si no se crea grupo de accesoStorage. **No exige esperar al grupo adminAKS o al parche Kubernetes para bootstrap**. Operaciones posteriores que requieren autorización: crear RG/cuenta/contenedor/propiedades y roles exactos; después acceso/lease/init por separado. Hoy no se concedeGO ni se crea nada.

### 11. Gate B — Terraform y AKS

**NO-GO.** Obligatorio: backend operativo y Entra/RBAC/red/retención comprobados; grupo y miembrosAKS aprobados; /32 vigente; CIDR externos aceptados; versión/surge/variables aprobados; cuota/consumo/capacidad revisados; presupuestoAKS; snapshot de fuentes y herramientas. Evidencia: fichas y pruebas de acceso mínimas autorizadas, versiones/digests/lock, aprobación de plan con hash e inventario.

Separar autorización de init/lease/plan de autorizaciónCREATE del plan revisado; un planPASS no autorizaapply. BloqueosB incluyen A más grupo/membresía, redes, versión/surge ypresupuesto completo. Planpuede detectar incompatibilidadAzureRM/OS; no se promete éxito. Nunca cambiar contexto o adaptarSKU automáticamente.

### 12. Gate C — Sesión de pruebas

**NO-GO operativo; procedimiento documental preparado.** Obligatorio: GateB con infraestructura real verificada, sesión/operador/hora/límite aprobados; backend/frontend/PG privados y datos sintéticos; imágenes disponibles; protocolos de avería/rollback autorizados; almacenamiento externo y segunda copia; backup y ensayo de restore independiente deldumpconcreto; plan de cierre y remanentes; contingencia de coste/tiempo revisada.

Evidencia: Ready/PVC/HTTP/SQL y configuración efectiva, documentosE01–E16 preparados fueraAKS, receiptbackup antes de retirar, y aprobación específica de fallos/backup/destroy. No considerar datoskind como aceptaciónAKS. Desplegar, provocar fallos y limpiar son operaciones futuras independientes; la preparación de scripts no las autoriza.

### 13. Acciones mínimas para desbloquear

1. Aprobar ficha backend: nombrecuenta candidato válido, contenedor/key, identidad acceso, red, retención/coste y custodio. Aprobar origenIPv4 para firewall; no hace falta crear grupoAKS antes.
2. Autorizar bootstrap solo de ese backend tras ficha completa, sinAKS/init/plan. Verificar permisos/recursos propios y resultado con lecturas; después autorizar prueba de acceso/lease/init cuando corresponda.
3. En paralelo resolver grupoEntra/miembros y validación externaCIDR; aprobar candidato1.35.9/surge1 y mínimo cambio de configuración en incremento autorizado, no hoy.
4. Completar presupuesto y ventana; preservar paquete/estado/digests/backups. Solicitar plan/CREATE únicamente cuando GateB reúna evidencias; GateC después de infraestructura real.

No repetir auditorías generales ni encadenar permisos debootstrap con creaciónAKS. No rellenar placeholders con supuestos.

### 14. Próxima iteración recomendada y preservación

**Primera operación de creación futura acotable:** bootstrap del backendWordle independiente, una vez completada y aprobada su ficha y permisos/red/coste; incluir exactamente RG/Storage/container/protecciones/roles acordados y excluirAKS/plan/Entra-grupo no requerido. Actualmente procede aprobar esos datos, no ejecutar bootstrap. Si se quiere resolver antes una decisión humana, propietario confirma identidad/custodia y salida/32 sin modificacionesAzure.

Fuentes oficiales para esta revisión: [backendazurerm y permisos por contenedor](https://developer.hashicorp.com/terraform/language/backend/azurerm), [permisosEntra por defecto](https://learn.microsoft.com/en-us/entra/fundamentals/users-default-permissions), [creación/administración grupos](https://learn.microsoft.com/en-us/entra/fundamentals/how-to-manage-groups). Precios/reproducción detallados y limitaciones permanecen en CONFIG-VALIDATION/EPHEMERAL-LIFECYCLE, sin inventar una cotización nueva.

Alcance efectivo: se añade únicamente esta sección a este informe por autorización expresa; bytes anteriores preservados íntegramente. Los demás archivos pendientes se comprueban porSHA-256, sin modificaciones. Solo lecturasAzure acotadas y consulta oficial; sinTerraform, pruebas operativas, creación/modificación de recursos/Entra/RBAC/red/secretos, imágenes, commits/push o staging. AKS NO-GO; detenerse y esperar revisión.
