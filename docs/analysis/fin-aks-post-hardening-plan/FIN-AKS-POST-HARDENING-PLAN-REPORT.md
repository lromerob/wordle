# FIN-AKS-POST-HARDENING-PLAN — 17/11/2026

## 1. Resumen ejecutivo

**PASS de planificación; recomendación CONDITIONAL GO para revisión humana.**
Un único plan exit 0: 6 altas, 0 modificaciones, 0 destrucciones y 0 reemplazos.
Run Command aparece explícitamente false. Única diferencia observable respecto
a la salida anterior: run_command_enabled true → false.
Estado inicial consultado con cero recursos; backend final accessible y lease
unlocked/available, sin bloqueo residual. Sin apply ni infraestructura creada.
Gate A GO; Gate B NO-GO; AKS NO-GO.

## 2. Autorización y alcance

Lecturas locales/Azure, IPv4 actual, propiedades de blob, state list, fmt,
validate y un único plan con bloqueo normal del estado.
No init, apply, destroy, import, refresh, state pull o force-unlock.
Sin -out, -target, -replace, -destroy, -refresh-only, -lock=false o -refresh=false.
Único archivo nuevo: este informe. Sin configuración/credenciales modificadas.

## 3. Estado inicial

Rama codex/pg01-07-consolidation, HEAD
4d56cf265cc5f0af8c72c64f2a93373660e8f122, índice vacío.
70 archivos pendientes previos registrados por SHA-256.
main.tf ya contiene hardening autorizado run_command_enabled=false.
Blob inicial: 180 bytes, unlocked/available, sin terraformlockid.
Sin Terraform concurrente detectado.
No estado local o plan binario creado.

## 4. Referencias revisadas

FIN-AKS-TERRAFORM-PLAN, RUN-COMMAND-HARDENING, DEPLOYMENT-BLOCKERS,
MFA-WRITE-DELETE-TEST y REMOTE-BACKEND-INITIALIZATION.
Código real main.tf, variables.tf, versions.tf, providers.tf y ejemplo de variables.
Metadatos locales del backend usados solo para verificar coordenadas y método,
no presentados como contenido de estado remoto.
Históricos conservados sin modificaciones.

## 5. Versiones de herramientas

terraform version -json exit 0: Terraform **1.9.8 windows_amd64**;
provider_selections hashicorp/azurerm **4.50.0**.
Restricción y lock coherentes; proveedor existente, sin descarga/upgrade.
No overrides ARM_*, TF_CLI_ARGS*, TF_LOG* o TF_DATA_DIR presentes antes de ejecutar.
CHECKPOINT_DISABLE=1 y TF_IN_AUTOMATION=1 solo en subprocesos.

## 6. Identidad y contexto Azure

account show y Graph signed-in-user show coinciden exactamente con identidad,
tenant y suscripción aprobados; estado Enabled, tipo user.
Identificadores sanitizados: suscripción 11306565…1bb5, tenant aff0390f…1eb9,
operador b573130a…a831. Sin login o cambio de contexto.
Preflight completado 08:52:29 UTC. IDs completos solo en memoria/procesos aprobados.

## 7. IPv4 y acceso al backend

Dos fuentes HTTPS directas curl -4 --noproxy '*':
api4.ipify.org y checkip.amazonaws.com, ambas exit 0 y misma IPv4 global.
Coincide exactamente con la única regla administrativa de Storage, default Deny.
La cadena documental previa vincula esa dirección/regla con el /32 autorizado
para API en la planificación anterior. No se obtiene el valor de un ejemplo vacío,
ni se toma una regla cualquiera como una autorización nueva.
No comparación textual con un IP histórico completo porque los informes lo ocultan;
se contrasta la dirección actual con la regla única vinculada a la evidencia previa.
Se repite verificación de dirección y coincidencia inmediatamente antes del plan.

TF_VAR_api_authorized_cidrs usa la dirección actual /32 solo en memoria.
Sin IPv4 doméstica en este informe o archivos versionados; sin cambiar firewall.
Acceso al blob aprobado verificado con --auth-mode login; sin SharedKey/SAS.
Backend inicializado coincide con rg-wordle-state, stwordletfgstate7c92d4,
tfstate y wordle/aks-demo.tfstate; tenant/suscripción aprobados, Entra habilitado.

## 8. Inventario del estado remoto

Desde infra/terraform:
    terraform state list
Exit 0; stdout y stderr vacíos: **0 recursos gestionados**.
No error confundido con inventario vacío. Sin state pull, contenido JSON completo
conservado o edición de estado. El tamaño del blob no se usa para inferir inventario.

## 9. Validación Terraform

- terraform fmt -check -recursive: exit 0, stdout/stderr vacíos.
- terraform validate -no-color: exit 0,
  Success! The configuration is valid.; stderr vacío.

Sin errores/advertencias. No corrección local ni init.

## 10. Ejecución del plan

Una sola ejecución desde infra/terraform:
    terraform plan -input=false -no-color -lock-timeout=60s

Inicio 08:53:32.705 UTC; fin 08:53:57.098 UTC; **exit 0**, stderr vacío.
    Plan: 6 to add, 0 to change, 0 to destroy.

Variables TF_VAR_* solo en entorno del subproceso: tenant/subscription/grupo
aprobados, IPv4 actual /32 y aprobación previa, Sweden Central, 1.35.9,
2 nodos Standard_D4s_v5. Resto de defaults/nombres/tags actuales preservados.
Sin tfvars privado nuevo, variables sensibles impresas o binario -out.
No segundo plan, refresh separado o escritura deliberada del estado.

## 11. Inventario de recursos previstos

| Dirección | Recurso / alcance |
| --- | --- |
| azurerm_resource_group.wordle | rg-wordle-academic / Sweden Central |
| azurerm_virtual_network.wordle | vnet-wordle-academic / 10.10.0.0/16 |
| azurerm_subnet.aks | snet-aks / 10.10.0.0/24 |
| azurerm_user_assigned_identity.aks | id-wordle-aks |
| azurerm_role_assignment.aks_network | Network Contributor, scope subnet en código |
| azurerm_kubernetes_cluster.wordle | aks-wordle-academic |

Seis bloques create, sin update/destroy/replace ni recursos adicionales.
Scope de rol/IDs futuros computed; código confirma subnet, no suscripción.
VMSS/discos/LB/IP/grupo nodos serán dependencias AKS, no recursos adicionales
Terraform independientes en este recuento. No ACR/backend/DB administrada nuevos.

## 12. Configuración AKS

Plan: swedencentral, Kubernetes 1.35.9, tier Free, 2 nodos System VMSS
Standard_D4s_v5, Ubuntu, OS Managed 64 GiB, max_pods=30, max_surge="1".
Azure CNI Overlay; VNet 10.10.0.0/16; subnet 10.10.0.0/24;
pods 10.244.0.0/16; services 10.20.0.0/16; DNS 10.20.0.10.
UserAssigned control plane; Kubernetes RBAC true; integración Entra con tenant
y grupo aprobados, azure_rbac_enabled=false; local_account_disabled=true.
API público restringido al /32 actual autorizado; coincidencia de IP, tenant y grupo
comprobada en memoria antes de sanitizar salida.
Standard LB, salida loadBalancer y una IPv4 administrada.
Valores known after apply no se presentan como recursos o validaciones runtime.

## 13. Verificación Run Command

Salida explícita del nuevo plan:
    + run_command_enabled                 = false

Evidencia concluyente de intención planificada, no de configuración desplegada.
Ya no se depende del default true. No cambio adicional de API/identidad/RBAC.

## 14. Comparación con el plan anterior

| Aspecto | Anterior | Nuevo | Resultado |
| --- | --- | --- | --- |
| Altas / modificaciones / destrucciones / reemplazos | 6 / 0 / 0 / 0 | 6 / 0 / 0 / 0 | Igual |
| Región | Sweden Central | Sweden Central | Igual |
| Nodos / SKU | 2 / D4s_v5 | 2 / D4s_v5 | Igual |
| Kubernetes / tier | 1.35.9 / Free | 1.35.9 / Free | Igual |
| Surge / OS | 1 / Ubuntu Managed 64 GiB | Igual | Igual |
| Networking / CIDR / DNS | Overlay y rangos aprobados | Igual | Igual |
| Entra / RBAC / cuentas locales | Habilitados / cuentas off | Igual | Igual |
| API /32 | Dirección aprobada oculta | Actual vinculada a aprobación previa | Sin ampliación |
| Run Command | true implícito | false explícito | Único cambio esperado |
| Outputs | Seis outputs no sensibles | Mismos | Igual |

Comparación textual automatizada del bloque text del informe anterior con stdout
nuevo: normalizando CRLF, sustituyendo IDs Entra por los mismos marcadores y
cambiando únicamente run_command_enabled true a false, las salidas coinciden.
No equivalencia absoluta de valores computed ni comparación en claro de IP histórica;
ambas son limitaciones de observabilidad, no diferencias adicionales detectadas.

## 15. Seguridad y valores predeterminados

- private_cluster_enabled=false y private_cluster_public_fqdn_enabled=false:
  API pública con /32 y Entra; no clúster privado.
- local_account_disabled=true; workload_identity_enabled=false.
- node_os_upgrade_channel=NodeImage: actualizaciones pueden consumir tiempo/surge.
- subnet default_outbound_access_enabled=true: no acredita aislamiento de egress.
- network_policy=(known after apply): no afirmar enforcement demostrado.
- Skip_service_principal_aad_check=true en rol existente de diseño, sin cambio.
- Campos kube_config/admin_config sensitive computed: no credenciales extraídas
  ni prueba de cuentas locales habilitadas.
- Bloques NAT/autoscaler computed no prueban NAT Gateway/autoscaling habilitados.

No valor nuevo inesperado que amplíe superficie respecto al plan anterior.
Run Command elimina una vía ARM adicional; no todos los riesgos administrativos.

## 16. Costes

Mismo inventario/tamaños/red; no recurso facturable nuevo por deshabilitar Run Command.
No se observa cambio de hipótesis económica directa.
Referencias modeladas DEPLOYMENT-BLOCKERS: aproximadamente **2,06 USD/4 h**
y **4,36 USD/8 h**, sujetas a VM/discos/LB/IP/tráfico/IO/Storage/surge,
tiempos y remanentes documentados. No tarifas reconsultadas hoy, factura garantizada,
límite automático o autorización para ampliar ventana.
Backend conserva su coste/retención propios entre sesiones.

## 17. Riesgos residuales

Capacidad física regional y admisión real AKS no probadas por plan.
Policy puede evaluar escrituras/eliminaciones distintas del RG vacío ensayado.
Contexto MFA y red/IP pueden cambiar; operador disponible para retirada.
Facturación depende de duración, tráfico/discos y remanentes; conservar margen
de limpieza dentro de cuatro horas y responsable de recuperación.
Acceso /32 y kubelogin/kubectl necesarios tras quitar Run Command.
Plan no demuestra despliegue, observabilidad, restauración o destroy funcional.
Estas condiciones requieren revisión humana antes de una autorización de apply.

## 18. Estado final del backend

08:54:25 UTC: key aprobado accesible, **180 bytes**, leaseStatus=unlocked,
leaseState=available, leaseDuration=null, terraformlockid ausente.
Proceso Terraform finalizado; cero procesos Terraform detectados.
ETag/lastModified cambian durante operaciones normales autorizadas
(última modificación final 08:53:57 UTC); no se interpreta como contenido igual.
Sin descarga/edición deliberada de estado, force-unlock, cambios de blobs/versiones
o firewall. No auditoría completa de cada petición interna de lease.
RG app y nodos consultados al terminar: ambos ausentes.

## 19. Integridad del repositorio

70 pendientes previos intactos por SHA-256. Configuración, lock, proveedor
y caché/metadatos locales del backend idénticos por hash.
HEAD intacto e índice vacío. Único archivo nuevo: este informe.
git diff --check exit 0; sin errores whitespace.
Advertencias LF/CRLF preexistentes, sin corregir: informe FIN-04, plan FIN,
observability/run_observability.py y observability/validation.py.
Sin staging, commits, push o limpieza. Total final esperado: 71 pendientes.

## 20. Recomendación Gate B

**CONDITIONAL GO como recomendación técnica para el propietario**, no apertura.
Plan correcto, hardening verificado y sin diferencias críticas conocidas.
Antes de apply: aceptación explícita de ventana/coste/margen y recuperación,
sesión MFA y conectividad vigentes; autorización independiente de despliegue.
No se necesitan cambios preventivos nuevos por este resultado.

## 21. Estado Gate A

**GO**, backend accesible y desbloqueado.

## 22. Estado Gate B

**NO-GO**, sin decisión automática.

## 23. Estado AKS

**NO-GO**. Sin clúster ni recursos Azure creados.

## 24. Próxima acción recomendada

Revisión del informe por el propietario y decisión sobre Gate B y operación futura
supervisada. No iniciar otra iteración ni apply.
Confirmación: no init/apply/destroy/import/refresh/state pull/force-unlock;
un único plan, sin binario. No Azure/Entra/Policy/RBAC/firewall modificados;
solo lease/metadatos normales autorizados, sin escritura deliberada de estado.
Backend/lock/configuración preservados; sin commits ni push.
