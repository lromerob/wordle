# FIN-AKS-TERRAFORM-PLAN — 17/11/2026

## 1. Resumen ejecutivo

**PARTIAL.** El primer plan real termina con exit 0: 6 altas, 0 modificaciones,
0 destrucciones y 0 reemplazos. Arquitectura aprobada respetada y sin operaciones
inesperadas críticas. Estado inicial sin recursos gestionados y lease final liberado.
No se recomienda todavía aplicar: consulta SKU agotada, Policy heredada no
acreditada y coste total pendiente. No incompatibilidad crítica confirmada.
Sin apply ni recursos creados. Gate A GO; Gate B y AKS NO-GO.

## 2. Alcance autorizado

Lecturas Azure, state list controlado, validate y un único plan con bloqueo normal.
Variables solo en entorno del proceso; sin binario persistente, cambios de código,
identidad, permisos, Entra, firewall o infraestructura. Solo este informe nuevo.
Backend sin modificaciones fuera del lease/metadatos normales autorizados.

## 3. Estado inicial

Terraform 1.9.8, AzureRM 4.50.0 y backend azurerm inicializado.
65 archivos pendientes previos e índice vacío; hashes/HEAD/caché registrados.
Sin plan antiguo, ni estado local en raíz. Blob aprobado existente, 180 bytes,
available/unlocked y sin lock metadata. Su inventario se comprobó, no se supuso.

## 4. Referencias revisadas

REMOTE-BACKEND-INITIALIZATION, PROVIDER-SCHEMA-VALIDATION,
DEPLOYMENT-DECISIONS, GATE-B-READINESS y SWEDEN-CONFIG.
Código real Terraform, outputs, ejemplos y metadatos del backend contrastados.
Ningún informe histórico modificado.

## 5. Preflight

UTC: 2026-11-17T07:36:42.255999+00:00. version -json exit 0, 1.9.8 windows_amd64 y AzureRM 4.50.0.
Lock/restricción coherentes. Backend local apunta al RG/cuenta/container/key,
tenant y suscripción aprobados; Entra habilitado.
Sin init, descargas, overrides CLI/logging ni credenciales alternativas observadas.
No se imprimen valores de variables de autenticación.

## 6. Identidad y suscripción

Tenant aff0390f-c390-4edc-919f-77da2a811eb9; suscripción Enabled
11306565…1bb5 y operador Graph b573130a…a831 coincidentes.
Sin login, cambio de contexto, tokens conservados o RBAC modificado.

## 7. Verificación IPv4

api4.ipify.org y checkip.amazonaws.com: HTTPS directo curl -4 --noproxy '*',
exit 0 y misma IPv4 global, autorizada por firewall Deny de Storage.
UTC 2026-11-17T07:36:38.494556+00:00 / 2026-11-17T07:36:38.632555+00:00.
Solo se suministra /32 por TF_VAR_api_authorized_cidrs en memoria, con aprobación
explícita. No IP completa en informe o archivo de configuración. Sin cambio de red.
La conexión doméstica/sin VPN es la condición aprobada, no garantía de IP estable.

## 8. Estado remoto

terraform state list: exit 0, stdout/stderr vacíos.
**Cero recursos gestionados inicialmente**, comprobados sobre el key autorizado.
Sin state pull, JSON completo descargado como evidencia, importación o edición.
No se deduce inventario del tamaño del blob.

## 9. Validación Terraform

terraform validate -no-color: exit 0.
Salida: Success! The configuration is valid.
Sin errores/advertencias. Validación previa al plan, sin correcciones.

## 10. Comando de planificación

Desde infra/terraform:
    terraform plan -input=false -no-color -lock-timeout=60s

TF_VAR_* solo del subproceso: suscripción activa, tenant/grupo aprobados,
Sweden Central, 1.35.9, dos D4s_v5, nombres/etiquetas del ejemplo y /32 vigente.
Resto de defaults del módulo, incluido OS 64 GiB. Sin tfvars nuevo o edición de ejemplos.
Sin -out, -lock=false, -refresh=false, -destroy, -target, -replace o -auto-approve.

## 11. Resultado del plan

Exit 0; 2026-11-17T07:37:49.341570+00:00 → 2026-11-17T07:38:10.322268+00:00.
    Plan: 6 to add, 0 to change, 0 to destroy.
stderr vacío; sin avisos Terraform. Sin segundo plan ni binario persistente.
Éxito técnico no implica aceptación operativa o autorización de despliegue.

## 12. Inventario de recursos

| Dirección Terraform | Servicio / región | Finalidad/dependencias | Seguridad y coste |
| --- | --- | --- | --- |
| azurerm_resource_group.wordle | RG rg-wordle-academic / Sweden Central | Raíz efímera | No backend, sin cómputo propio |
| azurerm_virtual_network.wordle | VNet vnet-wordle-academic / Sweden Central | 10.10/16, depende RG | Red y asociados facturables |
| azurerm_subnet.aks | snet-aks / VNet Sweden Central | 10.10/24, depende VNet | Scope del rol; sin egress deny explícito |
| azurerm_user_assigned_identity.aks | id-wordle-aks / Sweden Central | Control plane, depende RG | Sin secreto, identidad separada del operador |
| azurerm_role_assignment.aks_network | Network Contributor / subnet | Depende MI y subnet | Alcance previamente aprobado; no toda suscripción |
| azurerm_kubernetes_cluster.wordle | aks-wordle-academic / Sweden Central | Pool/AKS, depende rol/subnet/MI/RG | Free gestión; nodos/discos/LB/IP/tráfico con coste |

Scope del rol computed en salida, pero código lo fija a azurerm_subnet.aks.id.
VMSS/discos/IP/LB y grupo de nodos serían dependencias administradas por AKS;
no recursos Terraform independientes en el recuento de seis.
Sin ACR, Storage/backend, base administrada, Log Analytics o cargas de aplicación.
Data sources declarados: cero; no significa ausencia de GET internos del proveedor.

## 13. Operaciones previstas

Crear 6, modificar 0, destruir 0, reemplazar 0.
Outputs: cluster_name, resource_group_name, node_resource_group_name, cluster_id,
subnet_id y control_plane_identity_principal_id. IDs futuros computed.
Sin outputs de credenciales. kube_config/admin_config sensitive/computed son
placeholders del proveedor, no credenciales leídas ni prueba de cuentas locales habilitadas.
Ambos grupos destino consultados después continúan ausentes.

## 14. Revisión arquitectónica

Salida consistente: Free, swedencentral, 1.35.9; dos Standard_D4s_v5,
VMSS System Ubuntu, OS Managed 64 GiB, max_pods 30 y max_surge string "1".
CNI Azure Overlay; VNet 10.10.0.0/16, subnet 10.10.0.0/24,
pods 10.244.0.0/16, Services 10.20.0.0/16, DNS 10.20.0.10.
Entra tenant/grupo aprobados, Kubernetes RBAC true, azure_rbac_enabled=false,
local_account_disabled=true; API restringido al único /32 suministrado.
Salida loadBalancer Standard, una IPv4 administrada.
Bloques computed nat_gateway_profile/auto_scaler_profile no demuestran un NAT Gateway
o autoscaler habilitado; no están declarados como recursos/funciones adicionales.

## 15. Seguridad

No API abierto, cambios de backend o ampliación de permisos fuera del rol subnet aprobado.
Defaults relevantes, sin modificar:
- run_command_enabled=true: vía ARM adicional sujeta a RBAC; el /32 no debe
  presentarse como único control administrativo. Revisar/aceptar antes de apply.
- subnet default_outbound_access_enabled=true, con salida LB explícita:
  no se acredita aislamiento de egress ni endurecimiento de producción.
- node_os_upgrade_channel=NodeImage: actualizaciones futuras pueden afectar
  ventana/disponibilidad/surge y coste; no es autoscaling permanente.
No vulnerabilidad crítica confirmada por estos defaults en la demo privada.
[Microsoft Run Command/RBAC](https://learn.microsoft.com/en-us/azure/aks/access-private-cluster).

## 16. Cuotas y restricciones

Consultas UTC 2026-11-17T07:41:35.589944+00:00:
- DSv5: usado 0, límite 16 vCPU; regional: usado 0, límite 26.
- Dos nodos: 8 vCPU; con surge: 12. Cuota suficiente al consultar, sin reserva de hardware.
- AKS get-versions lista 1.35.9 en Sweden Central.
- vm list-skus agotó 60 s; no se repitió. Soporte/restricciones vigentes del SKU
  no acreditados hoy; evidencia anterior favorable no sustituye catálogo actual.
- group exists para RG app y nodos: false; sin colisiones observadas.
- Acciones necesarias RG/VNet/AKS/MI/roleAssignments permitidas en la consulta de
  permisos de suscripción; no prueba ausencia de deny/condiciones/scope/propagación.
- Policy visible en suscripción: 0 asignaciones. Herencia management groups no
  acreditada; no se supone exención por Storage Sweden exitoso.
Providers registrados y pertenencia Entra tienen antecedentes; no auditoría global nueva.
Plan exitoso no garantiza admisión/capacidad reales durante apply.

## 17. Estimación económica

Ventana futura 4 h y objetivo 5 USD, sin límite automático.
Referencia histórica Gate B (precios consultados 16/11/2026, no cotización nueva):
VM 1,632 USD / 4 h + dos OS P6 64 GiB asumidos 0,12304 + IPv4 0,020.
Subtotal conocido de infraestructura: aproximadamente **1,77504 USD**.
El subtotal previo 1,77833 incluía además PG SSD 8 GiB (0,00329);
ese PVC corresponde al despliegue posterior, no a estos seis recursos Terraform.
Surge una hora: referencia VM+OS 0,21938 USD adicionales, sin red.

Pendientes/no cero: LB/reglas/datos, egreso, IO, creación/retirada, remanentes,
Storage/operaciones/retención/versiones, backups y coste de evidencias.
Observabilidad propia consume nodos/disco/red; no Log Analytics añadido ni coste cero.
Backend persistente es una partida separada que continúa entre ciclos.
Plan no estima facturación ni garantiza SKU real de discos; falta total aceptable.

## 18. Riesgos y bloqueos

Sin errores críticos del plan ni operaciones inesperadas de destrucción/reemplazo.
Pendientes relevantes: catálogo SKU, Policy heredada, coste total y aceptación
de defaults administrativos/egreso/actualizaciones. Impiden recomendar apply.
No autorizan cambio de región/SKU/arquitectura, permisos o seguridad automático.

## 19. Evidencias

Version/state list/validate/plan exit 0. Inventario inicial cero recursos.
Contexto/IP/backend verificados; SKU timeout 60 s; resto de consultas descrito.
Salida sanitizada íntegra del único plan a continuación; IP y suscripción ocultadas.
No tokens, secretos, estado JSON o binario guardados.
```text
Terraform used the selected providers to generate the following execution
plan. Resource actions are indicated with the following symbols:
  + create

Terraform will perform the following actions:

  # azurerm_kubernetes_cluster.wordle will be created
  + resource "azurerm_kubernetes_cluster" "wordle" {
      + ai_toolchain_operator_enabled       = false
      + current_kubernetes_version          = (known after apply)
      + dns_prefix                          = "wordle-academic"
      + fqdn                                = (known after apply)
      + http_application_routing_zone_name  = (known after apply)
      + id                                  = (known after apply)
      + kube_admin_config                   = (sensitive value)
      + kube_admin_config_raw               = (sensitive value)
      + kube_config                         = (sensitive value)
      + kube_config_raw                     = (sensitive value)
      + kubernetes_version                  = "1.35.9"
      + local_account_disabled              = true
      + location                            = "swedencentral"
      + name                                = "aks-wordle-academic"
      + node_os_upgrade_channel             = "NodeImage"
      + node_resource_group                 = "rg-wordle-academic-nodes"
      + node_resource_group_id              = (known after apply)
      + oidc_issuer_url                     = (known after apply)
      + portal_fqdn                         = (known after apply)
      + private_cluster_enabled             = false
      + private_cluster_public_fqdn_enabled = false
      + private_dns_zone_id                 = (known after apply)
      + private_fqdn                        = (known after apply)
      + resource_group_name                 = "rg-wordle-academic"
      + role_based_access_control_enabled   = true
      + run_command_enabled                 = true
      + sku_tier                            = "Free"
      + support_plan                        = "KubernetesOfficial"
      + tags                                = {
          + "environment" = "academic"
          + "lifecycle"   = "temporary"
          + "managed_by"  = "terraform"
          + "project"     = "wordle"
        }
      + workload_identity_enabled           = false

      + api_server_access_profile {
          + authorized_ip_ranges                = [
              + "[IPv4 administrativa ocultada]/32",
            ]
          + virtual_network_integration_enabled = false
        }

      + auto_scaler_profile (known after apply)

      + azure_active_directory_role_based_access_control {
          + admin_group_object_ids = [
              + "f35832fa-d632-43b1-a83e-112d17cc8ccc",
            ]
          + azure_rbac_enabled     = false
          + tenant_id              = "aff0390f-c390-4edc-919f-77da2a811eb9"
        }

      + bootstrap_profile (known after apply)

      + default_node_pool {
          + kubelet_disk_type    = (known after apply)
          + max_pods             = 30
          + name                 = "system"
          + node_count           = 2
          + node_labels          = (known after apply)
          + orchestrator_version = (known after apply)
          + os_disk_size_gb      = 64
          + os_disk_type         = "Managed"
          + os_sku               = "Ubuntu"
          + scale_down_mode      = "Delete"
          + tags                 = {
              + "environment" = "academic"
              + "lifecycle"   = "temporary"
              + "managed_by"  = "terraform"
              + "project"     = "wordle"
            }
          + type                 = "VirtualMachineScaleSets"
          + ultra_ssd_enabled    = false
          + vm_size              = "Standard_D4s_v5"
          + vnet_subnet_id       = (known after apply)
          + workload_runtime     = (known after apply)

          + upgrade_settings {
              + max_surge = "1"
            }
        }

      + identity {
          + identity_ids = (known after apply)
          + principal_id = (known after apply)
          + tenant_id    = (known after apply)
          + type         = "UserAssigned"
        }

      + kubelet_identity (known after apply)

      + network_profile {
          + dns_service_ip      = "10.20.0.10"
          + ip_versions         = (known after apply)
          + load_balancer_sku   = "standard"
          + network_data_plane  = "azure"
          + network_mode        = (known after apply)
          + network_plugin      = "azure"
          + network_plugin_mode = "overlay"
          + network_policy      = (known after apply)
          + outbound_type       = "loadBalancer"
          + pod_cidr            = "10.244.0.0/16"
          + pod_cidrs           = (known after apply)
          + service_cidr        = "10.20.0.0/16"
          + service_cidrs       = (known after apply)

          + load_balancer_profile {
              + backend_pool_type           = "NodeIPConfiguration"
              + effective_outbound_ips      = (known after apply)
              + idle_timeout_in_minutes     = 30
              + managed_outbound_ip_count   = 1
              + managed_outbound_ipv6_count = (known after apply)
              + outbound_ports_allocated    = 0
            }

          + nat_gateway_profile (known after apply)
        }

      + windows_profile (known after apply)
    }

  # azurerm_resource_group.wordle will be created
  + resource "azurerm_resource_group" "wordle" {
      + id       = (known after apply)
      + location = "swedencentral"
      + name     = "rg-wordle-academic"
      + tags     = {
          + "environment" = "academic"
          + "lifecycle"   = "temporary"
          + "managed_by"  = "terraform"
          + "project"     = "wordle"
        }
    }

  # azurerm_role_assignment.aks_network will be created
  + resource "azurerm_role_assignment" "aks_network" {
      + condition_version                = (known after apply)
      + id                               = (known after apply)
      + name                             = (known after apply)
      + principal_id                     = (known after apply)
      + principal_type                   = (known after apply)
      + role_definition_id               = (known after apply)
      + role_definition_name             = "Network Contributor"
      + scope                            = (known after apply)
      + skip_service_principal_aad_check = true
    }

  # azurerm_subnet.aks will be created
  + resource "azurerm_subnet" "aks" {
      + address_prefixes                              = [
          + "10.10.0.0/24",
        ]
      + default_outbound_access_enabled               = true
      + id                                            = (known after apply)
      + name                                          = "snet-aks"
      + private_endpoint_network_policies             = "Disabled"
      + private_link_service_network_policies_enabled = true
      + resource_group_name                           = "rg-wordle-academic"
      + virtual_network_name                          = "vnet-wordle-academic"
    }

  # azurerm_user_assigned_identity.aks will be created
  + resource "azurerm_user_assigned_identity" "aks" {
      + client_id           = (known after apply)
      + id                  = (known after apply)
      + location            = "swedencentral"
      + name                = "id-wordle-aks"
      + principal_id        = (known after apply)
      + resource_group_name = "rg-wordle-academic"
      + tags                = {
          + "environment" = "academic"
          + "lifecycle"   = "temporary"
          + "managed_by"  = "terraform"
          + "project"     = "wordle"
        }
      + tenant_id           = (known after apply)
    }

  # azurerm_virtual_network.wordle will be created
  + resource "azurerm_virtual_network" "wordle" {
      + address_space                  = [
          + "10.10.0.0/16",
        ]
      + dns_servers                    = (known after apply)
      + guid                           = (known after apply)
      + id                             = (known after apply)
      + location                       = "swedencentral"
      + name                           = "vnet-wordle-academic"
      + private_endpoint_vnet_policies = "Disabled"
      + resource_group_name            = "rg-wordle-academic"
      + subnet                         = (known after apply)
      + tags                           = {
          + "environment" = "academic"
          + "lifecycle"   = "temporary"
          + "managed_by"  = "terraform"
          + "project"     = "wordle"
        }
    }

Plan: 6 to add, 0 to change, 0 to destroy.

Changes to Outputs:
  + cluster_id                          = (known after apply)
  + cluster_name                        = "aks-wordle-academic"
  + control_plane_identity_principal_id = (known after apply)
  + node_resource_group_name            = "rg-wordle-academic-nodes"
  + resource_group_name                 = "rg-wordle-academic"
  + subnet_id                           = (known after apply)
```

## 20. Estado final del backend y lease

180 bytes antes/después; final available/unlocked, sin terraformlockid.
ETag/lastModified cambiaron durante bloqueo/metadatos normales.
Propiedades/tamaño no demuestran igualdad de contenido; no se manipuló serial/lineage
ni se hizo escritura deliberada de estado. Sin eliminación de versiones o lease manual.
No cambios de cuenta/contenedor/firewall/RBAC. No auditoría de terceros concurrentes.

## 21. Integridad del repositorio

65 pendientes previos preservados por SHA-256; HEAD/índice vacío intactos.
.tf, lock y caché/metadatos locales idénticos. Lock SHA-256:
9c93863becf378540b553dded29161073b4bf3dd94eafac9bf46989142929c83.
Sin plan binario, tfvars privado, secreto o estado local en raíz.
git diff --check: PASS, exit 0, sin diagnósticos. Solo este informe nuevo.
Sin staging, commits, push, reset o limpieza Git.

## 22. Gate A

GO, backend accesible y lease liberado.

## 23. Gate B

NO-GO; requiere revisión independiente. No promoción automática por exit 0.

## 24. AKS

NO-GO. Sin AKS/nodos/cargas o recursos de infraestructura creados.

## 25. Recomendación para la siguiente fase

Cerrar verificación SKU, alcance de Policy, coste total y aceptación de defaults.
Revisar Gate B antes de solicitar autorización de apply. Si procede otra fase,
revalidar contexto/IP/cuotas y generar plan vigente: no hay binario aprobado reutilizable.
No iniciar automáticamente ninguna operación.

No apply/destroy/import/refresh/force-unlock o init adicional. Sin cambios Azure/Entra
de infraestructura; solo bloqueo/metadatos normales de estado autorizados.
No escritura deliberada de estado ni cambios del lock, commits o push.
