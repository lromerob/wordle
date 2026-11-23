# FIN-16 a FIN-19 — Preparación Azure y reconstrucción

10/11/2026. Rama `codex/pg01-07-consolidation`; HEAD `4d56cf265cc5f0af8c72c64f2a93373660e8f122`. Sin despliegue real. Criterios originales leídos y conservados.

| Tarea | Estado acreditado | Pendiente obligatorio |
|---|---|---|
| FIN-16 | **PARTIAL**: preflight de lectura y configuración revisados. | Providers, Entra, cuota/capacidad, backend/lease, OIDC/red y presupuesto aprobados. |
| FIN-17 | **PARTIAL**: planes supervisados con guardas y procedimiento operativo. | Workflows protegidos/OIDC, adaptación del runner integrado y primer despliegue autorizado con permisos/señales verificados. |
| FIN-18 | **PARTIAL, preparación local**: perfil completo por digest. | Recorrido real commit→digest→AKS→juego→promoción→rollback→observabilidad. |
| FIN-19 | **PARTIAL**: paquete íntegro y ensayo local real SQL/HTTP. | Retirada/recreación AKS, restauración allí, tiempos y costes remanentes. |

## Preflight observado

Azure CLI disponible, sesión activa y suscripción Enabled, sin imprimir identificadores/tokens. ContainerService, Network y Compute: **NotRegistered**; ManagedIdentity y Storage: Registered. Ninguno registrado por esta ejecución. Cuatro comprobaciones generales de actions sobre AKS/red/identidad/roleAssignments favorables: no prueban permisos efectivos/data-plane ni ausencia de deny assignments.

Se conserva westeurope, dos Standard_D4s_v5. Consulta de versiones disponible, sin selección automática. SKU sin coincidencia utilizable; cuotas sin registros cores/familia Dsv5: **capacidad/cuota NO verificadas**, no se interpretan como suficientes ni como cero. Terraform nativo y kubelogin no están en PATH; kubectl sí. No se instalaron herramientas. Grupo Entra/pertenencia, coordenadas del backend/lease y presupuesto siguen sin verificar; no se leen configuraciones privadas para inferirlos.

## Construido

- Overlay separado `k8s/aks-full`: reutiliza Blue-Green/observabilidad, once imágenes por digest, una DB/PVC managed-csi 8Gi y Services ClusterIP; sin editar perfiles previos. Digests oficiales obtenidos del almacén Docker local; su acceso desde AKS sigue pendiente. Aplicación fijada a las imágenes GHCR del HEAD publicado.
- `azure_preflight.py`: lectura sanitizada, sin login/register/set. `azure_supervised.py`: workspace externo, backend independiente, destino/tenant exactos, allowlist de recursos, plan/hash/config revisados y confirmaciones CREATE/DESTROY. Retirada exige inventario revisado y sin cambios; el operador debe identificar recursos ajenos.
- `aks_recovery.py`: verifica FQDN/tag AKS y rechaza kind/PG-05/PG-06; bootstrap solo en namespaces nuevos con secretos externos. Backup binario con aplicación detenida; restore rechaza tablas existentes y verifica transacción/contratos/hash de datos y secuencia. Sus guardas se probaron offline, no en AKS.
- `azure_release.py`: paquete externo de 94 fuentes/configs y once referencias inmutables, con hashes; excluye secretos/estado/dumps/informes. Contiene nuevos archivos locales: el HEAD publicado solo no reconstruye este incremento. Variables/backend/secretos y backup quedan externos.
- Dos ejemplos JSON sin credenciales, doce pruebas focalizadas y [guía operativa](../../operations/azure-demo.md) con comandos/checkpoints. El runner kind usa creación/borrado de kind e inspección Docker del nodo: no se presenta como portable a AKS. FIN-18 conserva la mención histórica Supabase; la arquitectura aprobada PG-01 sigue siendo PostgreSQL directo, sin cambiar criterios para cerrar tareas.

## Validaciones reales

- **12 pruebas offline aprobadas, cero omitidas**: contextos/subscripción/grupo incorrectos, CIDR abierto, credenciales de backend, configuración alterada, plan sin hash y paquete manipulado rechazados.
- Python AST/JSON y siete perfiles Kustomize correctos: 6/10/19/19/27/63/**63** objetos. AKS completo: once digests, una DB/PVC, sin valores de Secret ni Services públicos.
- Terraform **1.9.8**, imagen oficial existente y copia temporal: fmt -check, init -backend=false y validate, **exit 0**. Sin backend remoto, plan, apply/destroy ni credenciales; .tf/lock originales intactos.
- Paquete externo creado y verificado; alteración rechazada en prueba negativa.
- Ensayo existente FIN-02B `1f6456bcf7f0`: **PASS** en PostgreSQL **16.15**, dos contenedores nuevos. Dump custom 7098 bytes; SHA-256 `3a78108351f77ebb5a1f17dd4078176818cadae781a8a502c31b8582564a207d`. Datos/estructura/relaciones/secuencia iguales: cinco palabras, tres partidas, ocho intentos y una estadística antes de HTTP. Ocho comprobaciones HTTP incluyeron lecturas restauradas, inválido sin escritura, victoria/estadísticas y partida nueva. Backend, contenedores, red y dump temporales propios eliminados. **No es FIN-19 Azure PASS**.

## Costes, autorización y límites

Potencialmente facturables: VM/surge, discos OS/PG, Load Balancer/IP de salida, egreso/GHCR, Storage/operaciones/versiones del estado y remanentes. Free no elimina esos cargos. No hay cotización/presupuesto aprobado. Señales en emptyDir: exportar evidencia antes de retirar; sin recuperación histórica garantizada.

Autorización posterior necesaria para registrar providers/bootstrap Storage, instalar herramientas, configurar Entra/OIDC/RBAC/red, comprobar lease, plan remoto, crear AKS/PVC, desplegar/inyectar secretos, provocar fallos y retirar/reconstruir. Guía enlazada incluye revisión de planes e inventario, confirmaciones separadas y conservación del estado; referencias oficiales de red/bloqueo/coste allí.

Sin recursos Azure creados/modificados/eliminados, nuevas imágenes publicadas, commits/push o cambios PG-05/PG-06. Doce históricos preservados por SHA-256 e índice vacío. FIN-04/05 y demás tareas conservan su estado; no se acredita aceptación cloud con renders o pruebas locales.

## Preparación final — ampliación ejecutable, 10/11/2026

Los pendientes **de implementación** de la revisión anterior quedan resueltos: `aks_run.py` automatiza credenciales de usuario, bootstrap/deploy, runtime contra manifests GHCR, Ingress/SQL/HTTP, aceptación integral, backup y restauración con réplicas/selector/lock originales. `aks-restore` mantiene cuatro cargas a cero hasta pg_restore. No se duplican promoción ni comprobaciones de señales: se reutilizan PromotionController y validate; la única extensión común es disk_reader opcional y el exportador de eventos compartido, conservando el comportamiento kind por defecto.

`azure-demo.yml` y `azure_dispatch.py`: despacho manual, opt-in, rama/repositorio exactos, reviewers comprobados antes de login, inputs previos a autenticación, OIDC y ejecución serial. Plan/inventario permanecen privados y se atan a commit/hash. **No se han publicado ni activado**; requieren registro del workflow, environment protegido, runner Linux dedicado con salida autorizada e identidad federada. No se configura GitHub ni Azure en esta fase. Estos prerrequisitos externos no se ocultan como si dependieran solo de Azure.

Validación actual: **31 casos focalizados aprobados, cero omitidos** (16 guardas/preflight, 11 adaptador/controlador real con dobles, 4 telemetría). Los dobles prueban orquestación/guardas, no despliegue AKS. Ocho renders Kustomize correctos; Python/YAML/Bash/Python embebido y controles estáticos del workflow correctos. Terraform 1.9.8 fmt/init sin backend/validate aprobados. GHCR real: hashes de manifest/config, plataforma Linux/amd64 y revisión coincidente para ambas imágenes. No se repiten 87 pruebas ni demos kind/dump-restore completas: la evidencia real FIN-02B anterior se conserva.

Preflight Azure posterior: sesión Enabled, los tres providers siguen NotRegistered. D4s_v5 ahora listado (4 vCPU/16 GB) **con una restricción**, sin cuota utilizable acreditada: no equivale a disponibilidad. Estado/lease, grupo Entra, presupuesto y herramientas faltantes siguen pendientes.

Estados individuales: **FIN-16 PARTIAL; FIN-17 PARTIAL; FIN-18 PARTIAL; FIN-19 PARTIAL**. Preparación ejecutable local ampliada; para aceptación faltan configuración externa y ejecución real Azure, no se cambian criterios. Costes/limitaciones de las secciones anteriores vigentes. Comando seguro: `python -B scripts/azure_preflight.py --check-ghcr`; flujo futuro de plan/deploy/acceptance/backup/restore en la guía existente. Paquete offline regenerado con los nuevos ejecutores; sin secretos/estado/informes históricos.

Sin apply/destroy, despliegues, publicación GHCR, cambios de aplicación, commits ni push. PG-05/PG-06 y doce informes históricos preservados.
