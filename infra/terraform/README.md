# DEVOPS-04A: diseño de AKS temporal con Terraform

Estado: código preparado, sin aprovisionamiento ni conexión con Azure. No se ha probado el despliegue. Esta carpeta no despliega Wordle ni modifica CI, GHCR, Supabase o Kubernetes local.

## Arquitectura y límites

- Un Resource Group dedicado, VNet 10.10.0.0/16 y subred AKS 10.10.0.0/24.
- Identidad administrada de usuario para el control plane. Network Contributor únicamente sobre la subred, creado antes de AKS mediante depends_on. AKS administra además su identidad de kubelet y los permisos de su grupo de nodos; no se conceden permisos sobre toda la suscripción a la identidad del clúster.
- AKS Base/Free sin SLA financiero; un pool Linux System parametrizado. Valor inicial: dos Standard_D4s_v5 y discos OS administrados de 64 GB. Sin autoscaler, pools adicionales ni zonas configuradas. Las cargas académicas pueden compartir este pool; no es una recomendación de alta disponibilidad.
- Azure CNI Overlay, pods 10.244.0.0/16 y Services 10.20.0.0/16. Revisar solapamientos antes de conectar redes existentes. No se declara una política de aislamiento de pods.
- API pública restringida a api_authorized_cidrs obligatorios. Autenticación Microsoft Entra administrada, Kubernetes RBAC y grupos administradores preexistentes. Cuentas locales deshabilitadas; no se emiten outputs de kubeconfig, certificados o claves.
- Salida mediante Standard Load Balancer y una IP pública administrada. Son recursos asociados facturables aunque no se exponga ningún Service de la aplicación. No se crea NAT Gateway.
- Sin ACR, base de datos Azure, Log Analytics, Prometheus, Ingress, CD, Blue-Green ni rollback.

Las imágenes de producción proceden de GHCR; Azure Managed Identity no autentica contra GHCR. La visibilidad pública de los paquetes debe verificarse antes de desplegar. Paquetes privados requerirían una decisión posterior de autenticación/imagePullSecrets; no se añaden tokens aquí. Supabase continúa como base de datos externa y no se configura ni contacta desde este módulo. kind sigue siendo el entorno efímero del CI.

Los manifiestos k8s/local NO son manifiestos AKS de producción: usan imagePullPolicy Never, etiquetas locales y memoria con estado efímero. Su futura adaptación a imágenes GHCR por SHA y configuración de producción queda fuera de DEVOPS-04A.

## Versiones y capacidad

Terraform >=1.6 y <2; AzureRM fijado a 4.50.0 para revisar un esquema concreto. El lock del proveedor se versiona tras init -backend=false; revisar sus cambios y hashes antes de actualizarlo. CI utiliza Terraform 1.9.8 y AzureRM 4.50.0. El binario local de validación es temporal, sin instalación global. Revisar versiones y avisos de seguridad antes del aprovisionamiento.

kubernetes_version admite una versión explícita soportada en la región; null deja a AKS elegir y NO garantiza la misma versión entre despliegues. Seleccionar y registrar la versión antes de la prueba real; no asumir que la versión usada en kind está disponible en AKS.

La documentación de Microsoft consultada el 19/10/2026 exige al menos dos nodos en el pool System, al menos 4 vCPU/4 GB y excluye B-series. El ejemplo D4s_v5 es un punto de partida a verificar, no una oferta de precio mínimo ni garantía de cuota regional. La validación rechaza B-series y cantidades inferiores a dos, pero no consulta el catálogo de SKU. No se supone que este tamaño soporte posteriormente toda la observabilidad: medir y dimensionar CPU, memoria, disco, número de pods y reservas de sistema antes de ampliar el stack. Escalar aumenta el coste.

## Prerrequisitos para una fase futura autorizada

1. Suscripción y tenant correctos; región/SKU con disponibilidad y cuota suficientes. Identificar nombres nuevos para evitar colisiones o apropiarse de recursos existentes.
2. Terraform, Azure CLI y, para acceder después al clúster, kubectl y kubelogin compatibles. Su instalación y configuración no se realizan en esta fase.
3. Operador con permiso para crear los recursos dedicados y asignar roles (p. ej. Contributor y Role Based Access Control Administrator con el alcance revisado). Pertenencia al grupo Entra administrador. El acceso al API requiere además una IP pública incluida en la lista autorizada.
4. Proveedores Microsoft.ContainerService, Microsoft.Network, Microsoft.ManagedIdentity, Microsoft.Compute y dependencias requeridas registrados previamente por un administrador. AzureRM tiene resource_provider_registrations="none" para evitar registro automático. La lista exacta de dependencias se verificará antes de provisionar.
5. Recursos del estado ya existentes y aprobados, fuera de este módulo: Resource Group, cuenta StorageV2 y contenedor Blob privado. Configurar TLS, bloqueo de acceso público a blobs, versionado/recuperación y retención apropiados. Revisar firewall y acceso de red del operador; no se crea un private endpoint adicional aquí.
6. Permiso Storage Blob Data Contributor sobre el contenedor para la identidad que ejecuta Terraform. Autenticación Entra mediante Azure CLI u OIDC futuro; nunca claves de cuenta, SAS ni secretos en HCL o argumentos.

Los permisos del backend remoto y los permisos de aprovisionamiento son distintos. Si se endurece Storage deshabilitando las claves compartidas, mantener autenticación Entra. No usar el Resource Group de AKS como almacenamiento del estado: debe sobrevivir a su destrucción.

## Acceso futuro desde GitHub Actions al API de AKS

El CI actual no necesita acceder a AKS: Terraform solo inicializa proveedores localmente y kind está dentro del runner. No añadir Azure login ni modificar api_authorized_cidrs para ejecutar estas validaciones.

Los runners hospedados estándar tienen IP de salida variable. GitHub desaconseja autorizar todos sus rangos compartidos como lista de acceso; tampoco usar 0.0.0.0/0. OIDC autentica una identidad, pero no resuelve conectividad ni restricciones de red.

Para un CD futuro, decidir entre un runner dedicado con salida pública fija (/32 autorizada en AKS), un runner con conectividad privada a un API privado, o larger runners con red/IP fija si el plan y la organización lo permiten. Las dos últimas opciones exigen diseño adicional de red/DNS y pueden tener coste; nada de ello se provisiona aquí. Un runner propio no debe ejecutar código no confiable de pull requests.

No se automatiza añadir y quitar la IP de cada runner: requeriría permisos ARM de modificación de AKS, control de concurrencia, restauración ante cancelaciones y evitar drift respecto de Terraform. Para este TFG, la decisión queda pendiente; mantener mientras tanto solo las IP administrativas de confianza. Cualquier CD futuro deberá usar una identidad OIDC restringida al repositorio/entorno protegido y RBAC mínimo, separada de los grupos humanos de administración. No otorgar cluster-admin al runner por defecto.

## Microsoft Entra con una suscripción personal

Una cuenta Microsoft personal y ser Owner de la suscripción no garantizan privilegios de administración del directorio ni acceso Kubernetes. Identificar el tenant asociado, verificar que el usuario existe en ese tenant y con qué identidad inicia sesión; para invitados, confirmar las restricciones del directorio y que la identidad/grupo son utilizables por AKS.

Antes de provisionar, un administrador autorizado debe crear o identificar un grupo de seguridad Entra y añadir al operador como miembro efectivo. Si la creación de grupos está restringida, solicitarla al administrador del tenant: no asumir que los permisos Azure RBAC conceden permisos Microsoft Graph. Un grupo de seguridad asignado evita depender de grupos dinámicos o funciones premium; no asumir que una suscripción personal incluye Entra P1/P2.

Introducir el object ID del grupo, no su nombre ni client ID, en admin_group_object_ids. Este módulo usa autenticación Entra con Kubernetes RBAC (azure_rbac_enabled=false): ese grupo obtiene administración Kubernetes, pero Owner/Contributor del recurso por sí solos no sustituyen su pertenencia. Verificar además el rol AKS Cluster User para obtener kubeconfig de usuario, acceso de red y kubelogin compatible. Cuentas locales están deshabilitadas: --admin no es una vía de recuperación. Preparar un segundo miembro administrativo autorizado y un procedimiento de recuperación de pertenencia antes de eliminar accesos.

La identidad administrada de AKS, la identidad del operador, la del backend de estado y la futura identidad OIDC del pipeline tienen funciones distintas. No se crean grupos, usuarios, aplicaciones ni credenciales en esta iteración.

## Alternativas de SKU para reducir coste

Se conserva Standard_D4s_v5. Candidatas x86-64 a cotizar, sin afirmar que sean más baratas en una región/suscripción concreta:

| SKU | vCPU / RAM | Evaluación |
| --- | --- | --- |
| Standard_D4s_v5 | 4 / 16 GiB | Referencia actual. |
| Standard_D4as_v5 | 4 / 16 GiB | Alternativa AMD con la misma capacidad nominal; comparar tarifa Linux y cuota regional. |
| Standard_D4ls_v5 | 4 / 8 GiB | Menor RAM; candidata para carga ligera, con menor margen tras las reservas del sistema. |

Las dos candidatas satisfacen nominalmente los mínimos CPU/RAM de System y mantienen arquitectura compatible con las imágenes actuales. Esto no prueba elegibilidad AKS, disponibilidad ni precio inferior: confirmar soporte del SKU para AKS, versión, región, restricciones de suscripción y cuota; comparar precio total de dos nodos más discos/red antes de cambiar node_vm_size en variables privadas. No sustituir por B-series, Spot en System, ARM ni un SKU de dos vCPU solo por precio. Observabilidad futura requiere dimensionamiento independiente.

## Archivos y configuración local

- versions.tf: versiones y backend azurerm parcial, con use_azuread_auth=true.
- providers.tf: proveedor sin registro automático ni credenciales incrustadas.
- main.tf: seis recursos declarados y dependencias.
- variables.tf / outputs.tf: parámetros y outputs sin credenciales.
- terraform.tfvars.example: IDs ficticios y dirección TEST-NET-3; no son valores utilizables.
- backend.hcl.example: nombres ficticios de almacenamiento preexistente; no crea Storage.
- .gitignore: excluye caches, variables locales, planes, estado y backend.hcl. El lock del proveedor sí debe versionarse cuando se genere.

Copiar los ejemplos a terraform.tfvars y backend.hcl (ignorados) y sustituir los marcadores solo en una fase autorizada. subscription_id y tenant_id son identificadores, no credenciales; no se incluyen valores reales. Introducir el ID del grupo Entra y el CIDR público de salida real del operador. Nunca autorizar 0.0.0.0/0. Los planes y el estado pueden contener información sensible aunque los outputs no la muestren: protegerlos, no subirlos como artefactos públicos ni al repositorio. La carpeta .terraform también conserva configuración del backend.

## Validación sin Azure

Desde infra/terraform, cuando Terraform ya esté disponible:

```sh
terraform fmt -check
terraform init -backend=false
terraform validate
```

init -backend=false descarga el proveedor y escribe cache/lock locales, pero no inicializa el estado remoto ni autentica el proveedor. validate no es una prueba de capacidad, permisos, cuota o disponibilidad de AKS. DEVOPS-04A no ejecutó estas comprobaciones. DEVOPS-04A.1 añade el job independiente terraform-validation para pull requests, push a main y ejecución manual; no configura credenciales ni inicializa el backend remoto. El resultado real del job se comprobará en GitHub. Los seis jobs anteriores permanecen sin cambios: este nuevo job no se añade como requisito del publicador GHCR. Para exigirlo como bloqueo de merge, seleccionar su check en las reglas de protección de main mediante una decisión independiente.

## Aprovisionamiento FUTURO: no ejecutado ni autorizado en DEVOPS-04A

Después de revisar coste, cuota, permisos, versión Kubernetes y backend existente, con autenticación Entra ya autorizada y fuera de los archivos versionados:

```sh
cd infra/terraform
terraform fmt -check
terraform init -reconfigure -backend-config=backend.hcl
terraform validate
terraform plan -out=wordle.tfplan
# Revisar el plan íntegro y autorizar explícitamente los recursos y costes.
terraform apply wordle.tfplan
```

No ejecutar estos comandos durante DEVOPS-04A. No configurar credenciales como parte de esta entrega. Si se usa Azure CLI posteriormente, seleccionar explícitamente tenant/suscripción correctos; para el backend, usar el contexto Entra correcto (ARM_SUBSCRIPTION_ID/ARM_TENANT_ID cuando sean necesarios), sin persistir tokens en Terraform. El proveedor recibe los IDs desde variables; el backend se inicializa por separado.

Después de una aplicación futura: comprobar AKS y recursos asociados, obtener kubeconfig solo en un archivo privado y usar acceso Entra (sin --admin). Revisar las IP autorizadas y la propagación del permiso de identidad. Conservar evidencias sanitizadas. Este módulo no configura acceso administrativo de GitHub Actions ni implementa un despliegue de Wordle.

## Costes que deben aprobarse

| Recurso | Posible facturación |
| --- | --- |
| Gestión AKS Free | Sin cargo de gestión, sin SLA financiero; no incluye los recursos subyacentes. |
| VM del pool System | Cómputo por nodo mientras exista/esté activo; el ejemplo utiliza dos nodos. |
| Discos OS administrados | Capacidad/tipo de disco por nodo; discos y snapshots remanentes pueden seguir cobrando. |
| Standard Load Balancer | Reglas/uso y procesamiento de datos según tarifa vigente; aquí proporciona salida. |
| IP pública administrada | Dirección de salida de AKS, facturable aunque el frontend no esté desplegado. |
| Tráfico | Egreso y transferencias entre regiones/servicios, incluidas comunicaciones futuras con Supabase y GHCR. |
| Storage del estado | Capacidad, operaciones, versiones, recuperación/retención y transferencia; persiste tras destruir AKS. |
| Ampliaciones futuras | Services LoadBalancer, IP adicionales, PVC, snapshots y observabilidad no incluidos pueden añadir cargos. |

No se estiman importes sin región, moneda, suscripción y duración confirmadas. Consultar la calculadora y tarifas oficiales antes de autorizar. Crear alertas de presupuesto/etiquetas de caducidad por el procedimiento acordado; las etiquetas no detienen recursos. Detener AKS no equivale a eliminar discos, IP o almacenamiento: verificar recursos remanentes y facturación.

## Destrucción FUTURA y conservación del estado

Solo para este entorno dedicado, usando el mismo backend y las mismas variables, tras recoger evidencias y comprobar que no contiene recursos/cargas ajenos:

```sh
cd infra/terraform
terraform init -reconfigure -backend-config=backend.hcl
terraform plan -destroy -out=wordle-destroy.tfplan
# Revisar el alcance y autorizar la eliminación.
terraform apply wordle-destroy.tfplan
```

Nunca ejecutar ahora. No eliminar manualmente el Resource Group administrado de nodos ni usar borrado general de la suscripción. Terraform eliminaría AKS antes del permiso de subred y de la red por sus dependencias. Después comprobar posibles recursos huérfanos y sus cargos. El almacenamiento del estado no pertenece a este módulo y NO se destruye: su retención y limpieza requieren una decisión independiente. No perder el estado antes de confirmar la eliminación.

## Riesgos y validación pendiente

Pendientes ejecución real del nuevo job en GitHub y, en una fase posterior, revisión del plan real, cuota, capacidad, disponibilidad regional de Free/SKU/versiones, propagación RBAC y prueba en AKS. Las comprobaciones locales de esta iteración se registran al finalizar, sin equivaler a validación en Azure. La configuración no es evidencia de un despliegue funcional. No hay alta disponibilidad garantizada, aislamiento de egress, políticas de red ni endurecimiento completo de producción. El acceso a Supabase, la autenticación efectiva de Wordle y la promoción de imágenes pertenecen a iteraciones posteriores.

## Referencias oficiales

- [AzureRM 4.50: AKS y esquema de atributos](https://github.com/hashicorp/terraform-provider-azurerm/blob/v4.50.0/website/docs/r/kubernetes_cluster.html.markdown)
- [AKS Free y recursos facturables](https://learn.microsoft.com/en-us/azure/aks/free-standard-pricing-tiers)
- [Restricciones de pools System](https://learn.microsoft.com/en-us/azure/aks/use-system-pools)
- [Identidades administradas y permisos de red](https://learn.microsoft.com/en-us/azure/aks/managed-identity-overview)
- [Backend azurerm y autenticación Entra](https://developer.hashicorp.com/terraform/language/backend/azurerm)
- [Calculadora Azure](https://azure.microsoft.com/en-us/pricing/calculator/)

Referencias adicionales para DEVOPS-04A.1:

- [IP variables y alternativas de runners](https://docs.github.com/en/actions/reference/runners/github-hosted-runners#ip-addresses)
- [Rangos autorizados del API AKS](https://learn.microsoft.com/en-us/azure/aks/api-server-authorized-ip-ranges)
- [Autenticación Entra del control plane](https://learn.microsoft.com/en-us/azure/aks/entra-id-control-plane-authentication)
- [Especificaciones Dasv5](https://learn.microsoft.com/en-us/azure/virtual-machines/sizes/general-purpose/dasv5-series)
- [Especificaciones Dlsv5](https://learn.microsoft.com/en-us/azure/virtual-machines/sizes/general-purpose/dlsv5-series)

## Validación local DEVOPS-04A.1 (19/10/2026)

Terraform 1.9.8 ejecutado mediante binario oficial temporal con SHA256 comprobado, sin instalación global ni autenticación Azure:

- El primer fmt -check detectó únicamente formato en variables.tf; terraform fmt lo corrigió y el segundo fmt -check pasó. No cambian tipos, valores ni validaciones.
- init -backend=false -input=false finalizó correctamente y descargó AzureRM 4.50.0 firmado por HashiCorp, sin inicializar el backend remoto.
- validate finalizó correctamente. No se ejecutó plan, apply, destroy ni Azure CLI.
- Se incorpora .terraform.lock.hcl; los hashes zh de los paquetes distribuidos permiten verificar también el paquete Linux usado en CI. .terraform/ permanece ignorado.

Estas comprobaciones no confirman precio, cuota, acceso Entra, conectividad ni despliegue funcional en Azure. La ejecución del séptimo job en GitHub sigue pendiente.
