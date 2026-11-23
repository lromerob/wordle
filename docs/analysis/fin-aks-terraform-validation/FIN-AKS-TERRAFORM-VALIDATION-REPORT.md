# FIN-AKS-TERRAFORM-VALIDATION — 17/11/2026

## 1. Resumen ejecutivo

**PASS de validación técnica local**, con límites explícitos.
Parser HCL nativo de Terraform 1.9.8: cinco archivos del módulo y dos ejemplos
analizados sin errores. Formato final correcto. Variables/referencias/red/AKS
coherentes. Once pruebas focalizadas aprobadas, cero omitidas.
Correcciones: reforzar filtro de /32 privados/reservados, añadir regresión y
formatear exclusivamente el ejemplo tfvars.
No validación completa del esquema AzureRM ni prueba de despliegue.
Gate A GO; Gate B y AKS NO-GO.

## 2. Alcance autorizado

FIN-AKS-TERRAFORM-VALIDATION permite lectura, validación/formato local y correcciones
mínimas. Se usaron únicamente binarios/librerías existentes.
Sin init, plan, apply, destroy, refresh/import/state/workspace, descarga, Azure CLI,
consultas de IP/red, acceso Azure/Entra ni operaciones sobre blobs.
No helpers de despliegue ejecutados. Sin staging/commits/push/historial alterado.
Informes anteriores consultados selectivamente por nombre y contenido:
GATE-B-READINESS, SWEDEN-CONFIG, DEPLOYMENT-DECISIONS y BACKEND-LEASE-VALIDATION.
Se mantienen íntegros; código real contrastado con sus decisiones.

## 3. Inventario inicial

infra/terraform contiene:
- main.tf: local tags y seis recursos; RG, VNet, subnet, identidad de usuario,
  permiso Network Contributor sobre subnet y AKS.
- variables.tf: 19 variables; sin módulos hijos.
- outputs.tf: seis outputs de nombres/IDs no secretos.
- providers.tf: AzureRM con subscription_id/tenant_id explícitos y registro automático none.
- versions.tf: restricciones y backend azurerm parcial.
- terraform.tfvars.example / backend.hcl.example y dos ejemplos JSON.
- README, .gitignore, .terraform.lock.hcl y caché .terraform preexistentes.
Caché previa: licencia y ejecutable AzureRM 4.50.0 windows_amd64. No fue creada ni
actualizada aquí; no se ejecutó ese proveedor.
No estados/planes/inputs privados generados. No se leyó contenido de secretos/estado.
Índice inicialmente vacío y 61 archivos pendientes registrados por hashes.

## 4. Versiones de herramientas locales

Terraform **1.9.8 windows_amd64**, consultado con version -json.
Ejecutable existente bajo %LOCALAPPDATA%/WordleTFG/tools/terraform-1.9.8/terraform.exe.
Selección registrada AzureRM 4.50.0, coincidente con restricción y caché.
Python del .venv existente; librerías estándar usadas sin instalación.
No hcl2/lark instalados en ese entorno, pero **sí hay parser HCL2 real disponible
dentro de Terraform**, utilizado por fmt. No se confunde revisión textual con parseo.
CHECKPOINT_DISABLE=1 y TF_IN_AUTOMATION=1 solo en procesos de validación.

## 5. Validación HCL

terraform fmt -check -recursive -no-color desde infra/terraform aceptó main.tf,
variables.tf, outputs.tf, providers.tf y versions.tf antes y después del cambio.
El parser nativo analiza bloques, objetos/listas, expresiones e interpolaciones
presentes; sin errores sintácticos.
Para ejemplos con extensión .example, fmt recibió el contenido por stdin:
fmt -check -write=false -list=false -no-color -.
Ambos ejemplos HCL aceptados. Dos ejemplos JSON parseados con json.loads.
Esto valida sintaxis/formato, no evalúa todas las condiciones ni carga el esquema
del proveedor. No equivale a terraform validate o a un plan real.

## 6. Validación de formato

Módulo: fmt -check -recursive, exit 0 inicial y final.
backend.hcl.example: exit 0 por stdin.
terraform.tfvars.example: primer check exit 3, solo formato; sintaxis aceptada.
Se obtuvo formato por fmt -write=false -no-color - y se escribió únicamente ese
ejemplo, conservando CRLF. Comparación de literales y tokens no blancos idénticos.
Segundo check por stdin exit 0. Sin formateo masivo ni cambios al lock/backend.

## 7. Validación de variables

19 declaraciones únicas y 19 referencias a variables resueltas.
Obligatorias sin default: subscription_id, tenant_id, admin_group_object_ids,
api_authorized_cidrs y api_access_approved. Las restantes tienen defaults.
Tipos: string, number, list(string), bool y map(string) según su uso.
Valores efectivos predeterminados: swedencentral, 1.35.9, dos Standard_D4s_v5,
OS disk 64 GiB. Conteos/discos enteros mínimos y exclusión B-series conservados.
nullable=false en versión con default evita una versión efectiva nula; un null
explícito puede resolverse al default por semántica Terraform, no implica rechazo
obligatorio de la entrada null. API y aprobación sin default y no nulos.
No variables nuevas ni parámetros aprobados alterados.

## 8. Validación AKS

Declaración consistente: Free, 1.35.9 mediante variable, dos nodos D4s_v5,
VMSS, Ubuntu, disco administrado, max_pods 30 y upgrade_settings.max_surge string "1".
Región de AKS/VNet/identidad deriva del RG y location=swedencentral.
Sin autoscaling ni node pools adicionales.
Configuración conservada; no incompatibilidad nueva demostrada por estas
comprobaciones. Presencia de atributos no acredita aceptación de AzureRM/API:
esa verificación de esquema y el runtime permanecen pendientes.

## 9. Validación Entra ID

tenant y grupo en ambos ejemplos:
aff0390f-c390-4edc-919f-77da2a811eb9 /
f35832fa-d632-43b1-a83e-112d17cc8ccc.
Recurso referencia las variables; role_based_access_control_enabled=true,
local_account_disabled=true y azure_rbac_enabled=false.
Entra con Kubernetes RBAC; no se confunde con Azure RBAC for Kubernetes Authorization.
Sin cambios de identidad, grupos, miembros, permisos o credenciales.
Membresía y acceso efectivos no se reconsultan hoy.

## 10. Validación del API Server

Una lista explícita de exactamente un IPv4 /32; no default histórico, nullable=false.
Confirmación api_access_approved obligatoria y validación exige true.
Vacío/múltiples, IPv6, CIDR inválido, rangos amplios y placeholders no satisfacen
la condición. authorized_ip_ranges referencia directamente la variable.

Hallazgo corregido: HCL anterior rechazaba loopback/documentación pero permitía
algunos /32 privados/reservados que el helper ya rechazaba.
Se amplía únicamente la expresión de exclusión: RFC1918, compartido 100.64/10,
link-local, loopback, documentación, benchmarking, multicast y reservados altos;
también 192.0.0/24 y 192.88.99/24 de forma conservadora.
No se pretende replicar todo el registro IANA ni determinar conectividad/titularidad.
Alguna excepción especial global puede rechazarse conservadoramente; no afecta al
escenario de IPv4 doméstica convencional, que requiere aprobación explícita.
La sintaxis CIDR se valida además con cidrnetmask y el sufijo /32.
Regresión sobre la expresión real: 20 rechazos y seis casos de borde aceptados,
solo fixtures de sintaxis, sin configurarlos como destinos autorizados.
No se consultó de nuevo ni se guardó la IP pública observada.
La regla no autentica al propietario ni convierte un API público restringido en privado.

## 11. Validación del backend

Una sola declaración backend azurerm con use_azuread_auth=true.
Ambos ejemplos coherentes: rg-wordle-state / stwordletfgstate7c92d4 /
tfstate / wordle/aks-demo.tfstate.
RG histórico westeurope; Storage swedencentral: no contradicción.
Sin claves/SAS/connection strings en estos archivos. Shared Key deshabilitada según
evidencia previa; no se reconsulta seguridad remota en esta iteración.
Ningún recurso Storage/backend administrado por este módulo. Continúa fuera del
ciclo de destrucción de AKS. No init ni lectura/escritura de blobs o estado.

## 12. Validación de networking

Azure CNI Overlay; VNet 10.10.0.0/16, subnet 10.10.0.0/24,
pods 10.244.0.0/16, Services 10.20.0.0/16, DNS 10.20.0.10.
ipaddress confirma subnet contenida y ausencia de solapamientos entre VNet/pods/
Services; DNS dentro de Services. Referencia vnet_subnet_id a azurerm_subnet.aks.id.
Sin modificación de CIDR ni repetición de inventario de interfaces/rutas.
Compatibilidad de capacidad/red efectiva requiere validación posterior.

## 13. Validación de referencias y dependencias

Seis recursos sin direcciones duplicadas; referencias a cinco direcciones de recursos
resueltas, incluidos outputs. Seis outputs de nombres/IDs, sin kubeconfig/secretos.
Grafo estático de seis recursos sin ciclos evidentes; AKS depende del rol de subnet,
que depende de subnet e identidad. VNet/subnet/identidad derivan del RG.
Variables declaradas, local tags existente y no módulos externos referenciados.
No referencias AKS a West Europe en los helpers reconciliados.
Los atributos del proveedor y sus conflictos semánticos no se verifican por regex:
requieren validación de esquema pendiente.

## 14. Validación de ejemplos

Valores aprobados coherentes en JSON/HCL: región, parche, SKU, nodos, tenant y grupo.
Backend HCL/JSON correcto. Marcador de suscripción pendiente y API []/false
deliberados: ejemplos NO listos para desplegar, deben completarse en configuración
privada revisada. Rechazo de defaults abiertos conservado.
Ninguna IP detectada en archivos editados ni credenciales reales.
Runbook inspeccionado por sus referencias operativas, no ejecutado ni cambiado.
Estado/versiones del backend y evidencias históricas permanecen intactos.

## 15. Pruebas locales ejecutadas

Once métodos seleccionados de scripts/test_azure_readiness.py: 11 aprobados,
0 fallos, 0 errores, 0 omitidos. Sin suite general ni pruebas de aplicación.
Casos: defaults de Terraform, overrides, /32/aprobación y filtro HCL real,
variables offline, backend independiente, rechazo de claves/open API,
pool mínimo/B-series, ausencia CLI, borrados indebidos y recurso/grupo inesperados
en un plan JSON sintético.
subprocess.run/Popen, socket.connect y getaddrinfo bloqueados durante los tests.
No prepare/operate/deploy ni cloud calls; fixtures en temporales eliminados.
AST Python del archivo de pruebas y helpers: satisfactorio.
La prueba del filtro usa Python re para los patrones simples compatibles usados,
no ejecuta expresiones Terraform; fmt valida por separado su sintaxis HCL real.

## 16. Correcciones realizadas

1. infra/terraform/variables.tf: filtro público /32 reforzado y mensaje actualizado.
2. scripts/test_azure_readiness.py: regresión focalizada del literal regex HCL.
3. infra/terraform/terraform.tfvars.example: solo espacios/alineación.
4. Este informe nuevo.
No más cambios; sin alteración del contenido aprobado de main.tf, providers.tf,
versions.tf, outputs.tf, lock, backend, helpers operativos o documentos anteriores.

## 17. Hallazgos pendientes

Compatibilidad semántica completa AzureRM 4.50.0 no comprobada mediante esquema.
El proveedor está en caché, pero no se ejecutó ni se invocó terraform validate:
se limitaron comandos a versión y fmt, sin inicialización ni cargas de proveedor.
No se afirma que validate necesariamente requiera descargas con esta caché;
su ejecución deberá revisarse y autorizarse separadamente según el entorno.
Disponibilidad de 1.35.9/SKU/cuota, Policy, permisos efectivos, IP vigente y coste
completo siguen pendientes de comprobaciones remotas autorizadas.
No defecto crítico conocido pendiente dentro de las comprobaciones locales ejecutadas.

## 18. Riesgos y limitaciones

PASS local no prueba provisión, acceso al backend, propagación RBAC ni cargas AKS.
Una caché existente o lock no demuestran esquema compatible ni despliegue viable.
No se instala parser externo; la comprobación sintáctica real es la de Terraform fmt.
Sin acceso remoto ni lectura de secretos. 4 horas y objetivo 5 USD conservados,
sin coste total garantizado. No ampliación de arquitectura para cerrar observaciones.

## 19. Estado de Gate A

GO mantenido por evidencias históricas de bootstrap/lease.
No nueva prueba remota ni cambio a Storage/backend/firewall/retención.

## 20. Estado de Gate B

NO-GO; AKS NO-GO. Validación local no autoriza init/plan/apply ni creación de recursos.

## 21. Recomendación para la siguiente iteración

Revisar este informe y autorizar separadamente la validación de esquema local y/o
inicialización/plan controlados, con inputs privados, contexto y /32 revalidados.
Revisar coste completo antes de eventual CREATE y autorización independiente
de aplicación/retirada. No se inicia ninguna operación automáticamente.

Control final: git diff --check sobre cambios de esta iteración PASS, índice vacío,
HEAD/lock y todos los pendientes ajenos comprobados por SHA-256.
No terraform init, plan, apply, destroy, refresh, import, state ni workspace.
No Azure CLI, Azure/Entra/AKS modificados ni estado remoto consultado/modificado.
Sin staging, commits, push ni cambios al historial.
