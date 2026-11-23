# FIN-AKS-PREREQ — 15/11/2026

**BLOCKED para ejecutar AKS; preparación documental completada.** Sin instalaciones, registro de providers, solicitudes de cuota, Terraform ni escrituras Azure. FIN-04 aceptada; FIN-05/18 conservan aceptación cloud pendiente. Se reutiliza FIN-AKS-PREFLIGHT y la guía operativa existente, sin repetir suites ni demos.

## Resultados actuales

| Comprobación | Estado | Resultado |
|---|---|---|
| Herramientas | FAIL | Terraform/kubelogin no encontrados en PATH, ubicaciones habituales de WinGet, Scoop, Chocolatey, C:/tools y carpetas Azure; tampoco entradas de instalación con esos nombres en Uninstall HKCU/HKLM. WinGet disponible. No es una búsqueda exhaustiva del disco. |
| Conflictos de instalación | PASS | Ningún binario/instalación encontrado en ámbitos revisados. Repetir Get-Command -All antes de instalar; no sobrescribir una carpeta existente. |
| Contexto Azure | PASS | Sesión existente y suscripción Enabled, tenant presente. No se inicia login ni se cambian cuenta/tenant. Selección expresa del destino del TFG: BLOCKED. |
| Providers | FAIL | Compute, ContainerService y Network siguen NotRegistered. Consulta de permisos devuelve una entrada compatible con register/action; no certifica ámbito efectivo/deny ni autoriza usarla. |
| Cuotas | BLOCKED | vm list-usage westeurope completada con cero filas. Ni vCPU regionales ni familia DSv5 quedan acreditadas; no asumir cuota cero o suficiente. Mínimo nominal 8 vCPU más surge. |
| Alternativas SKU | BLOCKED | Consulta global regional de SKU no produjo datos utilizables en el tiempo de comprobación. D4as_v5, D4s_v4 y D4ds_v5 son candidatos a contrastar, no disponibilidad/compatibilidad/precio confirmados. No se cambia D4s_v5. |
| Restricciones zonales | BLOCKED | Se conserva hallazgo del preflight: D4s_v5 restringido en zonas 1/3. No revalidado por la consulta amplia actual. Pool sin zonas explícitas: no prueba imposibilidad regional ni capacidad asignable. |
| Otros límites AKS | BLOCKED | No acreditados límite regional de managedClusters, capacidad VMSS, LB/IP/discos ni concurrencia de provisión. No solicitar incrementos sin decisión del propietario. |
| Nombres y recursos | PASS | Lectura de RG: no existen rg-wordle-academic, rg-wordle-academic-nodes ni rg-wordle-state. Cero recursos con tag project=wordle. No excluye recursos sin etiqueta ni otros nombres; no reserva DNS ni nombre global de Storage. |
| Entra, CIDR y backend | BLOCKED | Ejemplos contienen placeholders; no se leen archivos privados para adivinar el destino. Grupo/pertenencia, IP de salida y coordenadas/ACL del estado no aportados. |
| Validación Terraform y despliegue | NOT RUN | Prohibidos en este incremento. No bloqueo/lease ni init remoto, no AKS. |
| Suites y demostraciones | NOT RUN | No se repiten 27 pruebas ni demos ya acreditadas; no cambió implementación. |

## Herramientas: instalación propuesta, no ejecutada

Terraform **1.9.8 windows_amd64** reproduce CI y cumple >=1.6,<2.0; AzureRM 4.50.0 permanece fijado. Kubelogin **v0.2.22 win-amd64**, release oficial consultada, admite azurecli usado por el proyecto; su compatibilidad completa con el futuro clúster no se presenta como probada. Confirmar arquitectura del equipo y política corporativa antes de descargar. No instalar latest implícitamente.

Método recomendado: ZIP oficiales en carpetas nuevas de usuario; no requiere administrador para escribir allí ni modificar PATH global. Políticas corporativas pueden requerir autorización adicional. Comandos FUTUROS tras autorización:

```powershell
Get-Command terraform,kubelogin -All -ErrorAction SilentlyContinue
$TfDir = Join-Path $env:LOCALAPPDATA 'WordleTFG/tools/terraform-1.9.8'
$KlDir = Join-Path $env:LOCALAPPDATA 'WordleTFG/tools/kubelogin-0.2.22'
if ((Test-Path -LiteralPath $TfDir) -or (Test-Path -LiteralPath $KlDir)) { throw 'Destino existente: inspeccionar antes de instalar' }
New-Item -ItemType Directory -Path $TfDir,$KlDir | Out-Null
Invoke-WebRequest 'https://releases.hashicorp.com/terraform/1.9.8/terraform_1.9.8_windows_amd64.zip' -OutFile "$TfDir/terraform.zip"
Invoke-WebRequest 'https://releases.hashicorp.com/terraform/1.9.8/terraform_1.9.8_SHA256SUMS' -OutFile "$TfDir/SHA256SUMS"
$TfLine = Get-Content "$TfDir/SHA256SUMS" | Where-Object { $_ -match ' terraform_1.9.8_windows_amd64.zip$' }
if (@($TfLine).Count -ne 1) { throw 'Checksum ausente o ambiguo' }
if ((Get-FileHash "$TfDir/terraform.zip" -Algorithm SHA256).Hash.ToLower() -ne ($TfLine -split '\s+')[0]) { throw 'Checksum incorrecto' }
Invoke-WebRequest 'https://github.com/Azure/kubelogin/releases/download/v0.2.22/kubelogin-win-amd64.zip' -OutFile "$KlDir/kubelogin.zip"
Invoke-WebRequest 'https://github.com/Azure/kubelogin/releases/download/v0.2.22/kubelogin-win-amd64.zip.sha256' -OutFile "$KlDir/SHA256SUM"
$KlHash = ((Get-Content "$KlDir/SHA256SUM" -Raw).Trim() -split '\s+')[0]
if ($KlHash -notmatch '^[a-fA-F0-9]{64}$' -or (Get-FileHash "$KlDir/kubelogin.zip" -Algorithm SHA256).Hash.ToLower() -ne $KlHash.ToLower()) { throw 'Checksum incorrecto' }
Expand-Archive "$TfDir/terraform.zip" -DestinationPath $TfDir
Expand-Archive "$KlDir/kubelogin.zip" -DestinationPath $KlDir
$KlExe = @(Get-ChildItem -LiteralPath $KlDir -Filter kubelogin.exe -Recurse -File)
if ($KlExe.Count -ne 1) { throw 'Binario kubelogin ambiguo' }
& "$TfDir/terraform.exe" version
& $KlExe[0].FullName --version
# Opcional, solo proceso actual, si los helpers requieren descubrimiento por PATH:
$env:PATH = "$TfDir;$($KlExe[0].DirectoryName);$env:PATH"
```

Descarga y verificación no ejecutadas; estos comandos no ejecutan Terraform contra Azure. Alternativa documentada por Azure: `winget install --id Microsoft.Azure.Kubelogin -e --version 0.2.22` si esa versión está disponible en su catálogo; privilegios/alcance dependen del manifiesto. Se prefiere ZIP para fijar versiones y evitar cambios persistentes de PATH.

Fuentes oficiales: [Terraform Windows](https://developer.hashicorp.com/terraform/install), [Terraform 1.9.8](https://releases.hashicorp.com/terraform/1.9.8/), [kubelogin instalación](https://azure.github.io/kubelogin/install.html), [release v0.2.22](https://github.com/Azure/kubelogin/releases/tag/v0.2.22).

## Providers: comandos preparados, NO ejecutados

Se requiere `<namespace>/register/action` en la suscripción elegida (normalmente incluido en Contributor/Owner); revisar deny assignments y políticas. No asignar Owner para simplificar. El registro modifica la suscripción pero no crea por sí solo nodos/AKS ni implica autorización de gasto.

```powershell
# SubscriptionApproved debe ser el destino revisado explícitamente por el propietario.
foreach ($Provider in @('Microsoft.ContainerService','Microsoft.Network','Microsoft.Compute')) {
  az provider register --namespace $Provider --subscription $SubscriptionApproved --wait --only-show-errors --output none
  az provider show --namespace $Provider --subscription $SubscriptionApproved --query registrationState --output tsv
}
```

La consulta show puede ejecutarse sola como lectura; register exige autorización posterior. [Permiso de registro](https://learn.microsoft.com/en-us/azure/azure-resource-manager/management/resource-providers-and-types).

## Identidad, red y estado: datos que debe confirmar el propietario

- Suscripción y tenant elegidos; los ejemplos no contienen IDs definitivos. No asumir que la sesión activa es el destino autorizado.
- Grupo Entra de seguridad existente y pertenencia del operador. AKS tiene cuentas locales deshabilitadas y RBAC Kubernetes con grupo administrador; permisos ARM no equivalen a acceso al clúster. Identidad administrada del control plane y Network Contributor sobre subred son recursos futuros Terraform, no existentes acreditados.
- Permisos efectivos para RG, red, identidad, AKS y roleAssignments en los ámbitos previstos; identidad del backend necesita permisos data-plane Storage Blob Data Contributor ajustados al ámbito, más acceso de gestión que proceda. OIDC/environment/reviewers/runner solo si se usa Actions, no obligatorio para primer ensayo supervisado local.
- CIDR IPv4 de salida estable de la estación/runner, sin abrir 0.0.0.0/0; comprobar salida corporativa/proxy antes de elegir /32. No consultar ni publicar IP privada innecesaria. Redes declaradas 10.10.0.0/16, subnet /24, pod 10.244.0.0/16 y service 10.20.0.0/16 deben contrastarse con redes/VPN aprobadas.
- Backend remoto externo a ambos RG desechables: cuenta/contenedor/key existentes y autorizados, red, Entra/RBAC, retención y coste. rg-wordle-state predeterminado no existe; no puede inferirse que no haya otro backend. Crear almacenamiento exige autorización y genera costes. Comprobar lease mediante escrituras queda pendiente y fuera de este incremento.
- Aplicación por port-forward loopback/Host wordle.test, sin DNS público ni certificado público necesarios para esa demo privada. API AKS tiene DNS/FQDN Azure y acceso restringido; requiere conectividad real posterior. GHCR público verificado en preflight; salida HTTPS desde nodos y pulls por digest aún no probados. No introducir PAT innecesario.
- Tres contraseñas sintéticas distintas y externas para admin PostgreSQL/app/Grafana; no leerlas ni pegarlas en informes. Backend HTTP continúa sin autenticación/aislamiento por jugador.

## Costes por escenarios

Retail API reconsultada: Linux D4s_v5 westeurope Consumption **0.23 USD/nodo/h**, mismo dato que preflight; precio público orientativo, no oferta contractual ni total EUR/impuestos.

| Escenario | Supuesto | Cómputo orientativo | Costes no incluidos |
|---|---|---|---|
| Ensayo mínimo técnico | 2 nodos, 2 horas, sin reconstrucción | 0.92 USD | Discos, LB/IP, tráfico, estado y tiempo adicional de aprovisionamiento |
| Demo completa con observabilidad | 2 nodos, hasta 4 horas de vida de recursos | 1.84 USD | Los mismos conceptos, picos/surge y posible reconstrucción |
| Reconstrucción | Nuevas horas de nodos y eventual solapamiento | 0.23 USD × suma de horas por nodo | Nuevos discos, persistencia del origen, backups/estado/red |
| Tras parar app o AKS | Recursos remanentes | No asumir coste cero | Discos/PVC, IP/LB según existencia, snapshots/backups, Storage/retención/operaciones |

Los overlays completos no reducen nodos por quitar observabilidad: el pool Terraform sigue siendo dos. No se implementa otro perfil mínimo. El ensayo mínimo no satisface la evidencia completa FIN-18. Propuesta: ventana inicial **máxima de 4 horas de vida facturable**, incluyendo arranque y margen de limpieza; si no cabe la reconstrucción, no ampliar sin autorización. No es un corte automático: revisar reloj/cargos y solicitar retirada antes de agotar ventana.

Recursos que Terraform crearía realmente: RG, VNet/subred, identidad/roleAssignment, AKS Free con dos VM, dos discos OS Managed 64 GB y red de salida Standard LB/IP gestionada por AKS. Aplicar Kubernetes crearía además disco PG para PVC 8 GiB managed-csi; el backend de estado se crea fuera del módulo. No ACR, NAT Gateway, Log Analytics o monitorización premium declarados. Observabilidad autogestionada consume capacidad de nodos. SKU/tier de discos y tarifas LB/IP/Storage no confirmados: **total económico BLOCKED**, no sumar cero por desconocimiento. Fórmula total: cómputo + discos provisionados por tiempo/tier + LB/IP + tráfico + estado/operaciones/retención + remanentes.

[Precios AKS](https://azure.microsoft.com/en-us/pricing/details/kubernetes-service/), [facturación discos](https://learn.microsoft.com/en-us/azure/virtual-machines/disks-understand-billing), [API Retail](https://prices.azure.com/api/retail/prices).

## Evidencia académica y secuencia mínima

FIN-05 ya tiene render/perfiles separados, ClusterIP, runtime PostgreSQL y ensayo local: no repetirlo para resolver acceso Azure. Su aceptación final depende de FIN-18. FIN-18 exige recorrido real **commit → digest → AKS → juego persistente → promoción → rollback automático**, incluyendo observabilidad y componentes obligatorios. Deben recogerse Pods/rollouts/PVC, SQL/HTTP, runtime por digest, selector/versiones, error provocado tras promoción y recuperación, métricas/logs/trazas/dashboard y entrega firing/resolved. Pruebas kind y guardas offline son soporte suficiente de implementación, pero no sustituyen CSI/RBAC/admission/red o ejecución cloud. FIN-19 exige reconstrucción/restore SQL+HTTP y retirada verificada, no agregar otra plataforma.

1. LOCAL: autorizar instalación ZIP por usuario de versiones fijadas, checksum y comprobación de versiones; confirmar arquitectura/política y destino nuevo. Sin privilegios admin ni PATH global previstos.
2. LECTURAS REMOTAS SIN CAMBIOS: propietario selecciona destino; aportar coordenadas no secretas del backend y grupo; revisar cuotas/alternativas con Portal/soporte de la suscripción si CLI sigue vacía, sin solicitar incrementos. La asignación real nunca está garantizada por catálogo/cuota.
3. CAMBIOS REMOTOS SIN RECURSOS DE CÓMPUTO: autorización independiente para registrar tres providers; crear/asignar grupo/roles/OIDC solo si necesarios y con ámbito revisado. No ejecutados.
4. CAMBIOS POTENCIALMENTE FACTURABLES: bootstrap externo Storage, plan remoto con lease tras autorización, presupuesto y CREATE revisados, AKS/PVC, ensayos y reconstrucción. Ninguno autorizado por este informe.
5. LIMPIEZA VERIFICABLE: exportar evidencias y backup restaurado SQL/HTTP; inventario de ambos RG y recursos ajenos; plan-destroy/hash revisado y autorización DESTROY separada; retirada mediante helper existente; consultar ausencia de recursos esperados y remanentes/cargos. No borrar genéricamente grupos ni estado; conservar estado/backups hasta decisión separada.

**Primera acción que conviene autorizar:** instalación local por usuario de Terraform 1.9.8 y kubelogin v0.2.22 desde ZIP oficiales con checksum, sin PATH global ni Azure. Riesgo acotado a descarga/ejecución de binarios y archivos nuevos fuera del repositorio; requiere revisión de política del equipo. No resuelve por sí sola cuotas, Entra, estado o presupuesto y no autoriza desplegar.

## Preservación

Solo se crea este informe. Se comprueban por SHA-256 los cuatro archivos versionados modificados y los 30 archivos sin seguimiento previos, incluidos doce históricos: sin cambios. Índice vacío; sin commits/push ni alteración de funcionalidades/infraestructura/secretos. Ninguna suite repetida ni nueva tecnología.

## FIN-AKS-PROVIDERS — 15/11/2026: BLOCKED antes del registro

El propietario autoriza registrar únicamente ContainerService, Network y Compute, sujeto a confirmar inequívocamente la suscripción/tenant contra FIN-AKS-PREREQ. Esta referencia no contiene identificadores aprobados: registra expresamente que la selección del destino sigue BLOCKED. No puede afirmarse coincidencia basándose solo en una sesión activa.

Lectura actual: suscripción `11306565…1bb5`, tenant `aff0390f…1eb9`, estado Enabled. Identificadores parcialmente ocultos; no se leen secretos ni se cambia el contexto. Se requiere confirmación expresa de que este par corresponde al destino TFG antes de cualquier register.

| Proveedor | Inicial | Acción ejecutada | Último estado observado |
|---|---|---|---|
| Microsoft.ContainerService | NotRegistered | Solo provider show; sin register | NotRegistered |
| Microsoft.Network | NotRegistered | Solo provider show; sin register | NotRegistered |
| Microsoft.Compute | NotRegistered | Solo provider show; sin register | NotRegistered |

Comandos de lectura ejecutados mediante subprocess, con salida capturada y sanitizada: `az account show`, `az provider show --namespace <cada uno de los tres> --subscription <ID activo>` y `az rest --method get --url https://management.azure.com/subscriptions/<ID activo>/providers/Microsoft.Authorization/permissions?api-version=2022-04-01`; todos con --only-show-errors --output json. No se publican los IDs completos.

Las acciones devueltas permiten `<namespace>/register/action` para los tres; esto no certifica ausencia de deny assignments/condiciones ni acceso efectivo definitivo. No errores de consulta. No se ha probado registro ni se presenta éxito. Operaciones pendientes detenidas por falta de correspondencia inequívoca del destino, conforme a la condición del propietario.

El bloqueo de registro no está resuelto. Tras confirmar el destino, podrá retomarse únicamente el registro autorizado con suscripción explícita y comprobación posterior. Permanecen cuota/capacidad, grupo Entra/pertenencia, CIDR y backend remoto/presupuesto; herramientas instaladas según FIN-AKS-TOOLS. Sin Terraform, cambios de recursos/roles/identidades, cuotas, despliegues, commits ni pushes.

### FIN-AKS-PROVIDERS — continuación tras confirmación del propietario: PASS

El propietario confirmó expresamente «Sí» al par suscripción `11306565…1bb5` / tenant `aff0390f…1eb9`. Se releyó el contexto, comprobando coincidencia con ese par y estado Enabled, sin cambiar la suscripción activa. Queda superado el bloqueo de identificación anterior, que se conserva como evidencia histórica.

Antes de escribir, provider show confirmó NotRegistered para los tres; la consulta de permisos devolvió register/action permitido para cada namespace. Las tres solicitudes terminaron con código 0, sin error de permisos/política observado. Esto acredita la operación concreta, no permisos para crear AKS u otros recursos.

| Proveedor | Inicial | Acción ejecutada | Final verificado |
|---|---|---|---|
| Microsoft.ContainerService | NotRegistered | Una solicitud register | Registered |
| Microsoft.Network | NotRegistered | Una solicitud register | Registered |
| Microsoft.Compute | NotRegistered | Una solicitud register | Registered |

Por proveedor se ejecutó exactamente una vez `az provider register --namespace <proveedor> --subscription <ID confirmado> --only-show-errors --output none`. Se reconsultó previamente para evitar duplicar registros en curso. Después se utilizó exclusivamente `az provider show --namespace <proveedor> --subscription <ID confirmado> --only-show-errors --output json`. Hubo estados intermedios Registering y consultas periódicas sin repetir register. Última consulta: los tres Registered. Sin errores observados, sin secretos/IDs completos en el informe.

**Bloqueo de registro resuelto.** Permanecen cuota regional/de familia y capacidad real/SKU, versión AKS, grupo Entra/pertenencia, CIDR de salida aprobado, backend remoto independiente con RBAC/red y presupuesto/duración. Herramientas ya instaladas según FIN-AKS-TOOLS. No se repiten esas comprobaciones ni se inicia otra fase.

Únicas escrituras Azure: registro de esos tres proveedores autorizado expresamente. Sin Terraform, creación de RG/AKS/red/discos/almacenamiento, cambios RBAC/identidades, solicitudes de cuota, despliegues, commits ni pushes. Solo se actualiza este informe; los demás cambios locales se conservan.
