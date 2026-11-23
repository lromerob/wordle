# FIN-AKS-SWEDEN-CONFIG — 16/11/2026

## 1. Resumen ejecutivo

**PASS de preparación local de configuración**, sin prueba de despliegue.
Sweden Central, Kubernetes 1.35.9, AKS Free, dos Standard_D4s_v5 y surge de un nodo.
API administrativo deliberadamente incompleto y bloqueado hasta aprobación.
Gate A GO por evidencias anteriores; Gate B y AKS NO-GO.

## 2. Alcance y autorización

Se aplicó únicamente la autorización del propietario FIN-AKS-SWEDEN-CONFIG:
Terraform, ejemplos asociados, README local e informe nuevo. Sin operaciones Azure,
Entra ID, Terraform o Git de escritura; sin instalación de dependencias.
Se consultaron selectivamente CONFIG-DECISION, CONFIG-VALIDATION, GATE-B-READINESS,
ENTRA-PREP, SWEDEN-BACKEND-BOOTSTRAP y BACKEND-LEASE-VALIDATION.
Las evidencias históricas permanecen intactas; no se revalidó su estado remoto hoy.

## 3. Inventario inicial

Módulo infra/terraform: main.tf, variables.tf, outputs.tf, providers.tf, versions.tf;
backend parcial azurerm; dos ejemplos HCL y dos JSON; README, .gitignore,
lock y caché preexistentes. No módulos hijos; seis recursos declarados.
Inicialmente location=westeurope, kubernetes_version=null, sin upgrade_settings;
grupo/tenant ficticios y CIDR de documentación en los ejemplos. Backend HCL ficticio
y JSON con Storage pendiente.

Clasificación regional antes de editar:
- variables.tf, terraform.tfvars.example y azure-variables.example.json:
  región efectiva de AKS y recursos asociados; se cambian a swedencentral.
- Referencias históricas de docs/analysis, incluidas West Europe, denegación Storage
  y selección de región: evidencias anteriores; se conservan íntegramente.
- RG persistente rg-wordle-state: ubicación histórica westeurope, válida;
  no confundir con la ubicación swedencentral de su Storage Account.
- scripts/azure_preflight.py: cuatro referencias operativas a westeurope
  (resultado local, comprobación, argumento por defecto y función).
  scripts/azure_supervised.py: un fallback de validación de formato.
  Fuera de esta edición Terraform, permanecen identificadas como mantenimiento
  pendiente antes de reutilizar esos helpers. No pipelines regionales incompatibles
  encontrados en .github. No se hizo sustitución global.
- README Terraform: explicación de RG histórico y advertencia de helpers.

## 4. Archivos modificados

Siete archivos existentes de infra/terraform:
1. variables.tf: región, versión explícita no nula, validación API y confirmación obligatoria.
2. main.tf: upgrade_settings.max_surge="1".
3. terraform.tfvars.example: configuración aprobada y entradas API bloqueadas.
4. azure-variables.example.json: equivalente JSON.
5. backend.hcl.example: coordenadas reales no secretas y autenticación Entra.
6. azure-backend.example.json: Storage Account aprobado.
7. README.md: configuración vigente, backend, uso de ejemplos y pendientes.
Además se crea exclusivamente este informe. No cambian aplicación, pipelines,
manifiestos, recursos declarados, proveedores ni lock.

## 5. Cambios de región

location predeterminado y ejemplos: swedencentral.
RG de aplicación, VNet, identidad de control plane y AKS mantienen referencias a esa
variable/RG. El grupo de nodos lo administra AKS. No se altera el RG del backend,
no se declara ni importa su Storage y no se modifica su región histórica.

## 6. Configuración AKS

Tier Free; kubernetes_version predeterminada 1.35.9, nullable=false;
node_count=2; Standard_D4s_v5; OS disk administrado 64 GB; Ubuntu.
upgrade_settings.max_surge es string "1", conforme al bloque documentado de
AzureRM 4.50.0: un nodo temporal de upgrade, no porcentaje ni capacidad permanente.
Ocho vCPU nominales en operación, doce con un surge; sin autoscaler ni pools nuevos.
Se conservan parámetros existentes; disponibilidad, aceptación ARM y capacidad
actual deberán revalidarse en fase autorizada. La configuración no reserva recursos.

## 7. Integración Entra ID

Ejemplos tenant aff0390f-c390-4edc-919f-77da2a811eb9 y grupo administrador
f35832fa-d632-43b1-a83e-112d17cc8ccc, grp-wordle-aks-admins.
main.tf conserva Entra administrada, Kubernetes RBAC habilitado,
azure_rbac_enabled=false y local_account_disabled=true.
No creación de grupos, miembros, roles ni identidades nuevas por esta iteración;
la identidad administrada ya declarada permanece sin cambios.
Los IDs son identificadores autorizados, no credenciales.

## 8. Configuración de red

Azure CNI Overlay conservado:
VNet 10.10.0.0/16, subnet 10.10.0.0/24, pods 10.244.0.0/16,
Services 10.20.0.0/16 y DNS 10.20.0.10.
Comprobación Python ipaddress: subnet contenida en VNet; VNet, pods y Services
sin solapamiento entre sí; DNS dentro de Services. La superposición subnet/VNet es
intencional. Referencia AKS a azurerm_subnet.aks.id conservada.
No demuestra ausencia de solapamiento con redes externas no aportadas.
Load Balancer Standard y salida existentes conservados; sin recursos adicionales.

## 9. Tratamiento del API Server

api_authorized_cidrs sigue siendo list(string), obligatorio, sin default,
nullable=false. Exige lista no vacía, IPv4 válida con sufijo /32; rechaza rangos
más amplios, placeholders, 0.*, loopback y los tres bloques de documentación.
try protege la evaluación frente a elementos inválidos/nulos.
api_access_approved es un bool obligatorio, sin default, nullable=false,
cuya validación exige true. Los ejemplos contienen [] y false deliberadamente:
no sirven para plan/apply hasta aprobación explícita y configuración posterior.
No se introduce un default inválido en esta variable, para no romper validate
por un valor predeterminado permanentemente rechazado.

No IP detectada, copiada del firewall, histórica ni ficticia configurada.
La validación no acredita autorización humana, titularidad, carácter público
global ni accesibilidad del /32: siguen siendo decisiones/verificaciones del
propietario. El booleano es confirmación explícita, no un control de identidad.
API público restringido no es API privado ni autorización para desplegar.

## 10. Configuración del backend

Única declaración parcial backend azurerm en versions.tf con use_azuread_auth=true.
Ambos ejemplos incluyen rg-wordle-state / stwordletfgstate7c92d4 /
tfstate / wordle/aks-demo.tfstate y autenticación Entra.
RG metadata westeurope; Storage swedencentral; Shared Key deshabilitada según
bootstrap autorizado, sin nueva consulta en esta iteración.
No claves, SAS, connection strings ni tokens. La futura inicialización deberá
recibir los parámetros del ejemplo y el contexto autorizado; no ejecutada hoy.
Backend fuera del módulo y del ciclo de destrucción AKS. No estado ni blobs creados.

## 11. Versiones Terraform/AzureRM

Restricción Terraform >=1.6.0,<2.0.0 y AzureRM =4.50.0 conservadas.
.terraform.lock.hcl sin cambios comprobado por SHA-256.
Sin descargas ni ejecución de Terraform, incluidos fmt, init o validate.
Compatibilidad declarada de upgrade_settings/max_surge, Entra/RBAC y perfil de
API revisada contra documentación oficial de la versión fijada:
[AzureRM 4.50.0 AKS](https://github.com/hashicorp/terraform-provider-azurerm/blob/v4.50.0/website/docs/r/kubernetes_cluster.html.markdown).
No equivale a validación ejecutada del proveedor.

## 12. Ejemplos y placeholders

Confirmados: región, versión, nodos, SKU, tenant, grupo y coordenadas backend.
Configurables: nombres y etiquetas existentes, parámetros del pool.
Pendientes: subscription_id explícito en los ejemplos (sin deducirlo ni cambiar
contexto remoto), lista API /32 y aprobación. El marcador de suscripción no
constituye una decisión de nueva suscripción: debe suministrarse la ya autorizada.
No se escriben terraform.tfvars, backend.hcl privados, estado o workspace.

## 13. Validaciones estáticas

Ejecutadas con Python existente, sin instalar paquetes:
- Revisión léxica de delimitadores en cinco .tf y dos ejemplos HCL: satisfactoria.
- JSON de ambos ejemplos parseado y valores aprobados comprobados.
- 19 variables declaradas y 19 referencias resueltas; claves JSON conocidas.
- Aserciones de configuración AKS, seis recursos, backend único, versiones y RBAC.
- Rangos y referencias de red: satisfactorios.
- Revisión de casos equivalente al predicado API: doce negativos y uno positivo
  exclusivamente sintáctico. Ninguna dirección de prueba guardada como configuración.
  No es ejecución de expresiones Terraform ni prueba de aprobación real.
- Revisión focalizada sin hallazgos de claves privadas/tokens/credenciales en los
  siete archivos editados; solo identificadores operativos autorizados.
- Índice vacío y preservación por SHA-256 de pendientes ajenos y lock.
- git diff --check dirigido a los archivos editados: PASS; revisión de espacios finales en ocho archivos: PASS.

Limitación: no hay parser HCL completo instalado en el entorno Python del proyecto;
se hizo revisión textual/léxica y de tipos/referencias, no parseo HCL completo,
terraform fmt ni terraform validate. Se omiten para conservar el alcance sin
ejecución Terraform. No se afirma validación semántica real del proveedor ni Azure.

## 14. Riesgos e incertidumbres

Gate B no resuelto: /32, redes externas, presupuesto/ventana y autorizaciones
operativas pendientes. Helpers operativos históricos requieren reconciliación
acotada antes de reutilizar su diagnóstico local o defaults.
No garantía de disponibilidad regional futura, aceptación del proveedor/API,
propagación RBAC, coste final o funcionamiento de cargas. No AKS desplegado.
La demo sigue privada/sintética; esta edición no cambia su seguridad funcional.
El surge produce coste temporal; Free no elimina costes de nodos, discos, LB/IP,
tráfico ni almacenamiento persistente del estado.

## 15. Decisiones pendientes

Aprobar /32 administrativo y confirmar redes externas; aceptar presupuesto y ventana.
Completar explícitamente la suscripción autorizada al preparar configuración real.
Reconciliar helpers antes de nuevo preflight; luego autorizar por separado
validación Terraform, init/plan y, solo tras revisión, eventual despliegue.
No se inicia ninguna de estas operaciones.

## 16. Estado de Gate A

**GO mantenido**, por bootstrap y lease previos. Backend sin cambios ni nueva
validación remota en esta edición.

## 17. Estado de Gate B

**NO-GO. AKS NO-GO.** Preparación local de región/versión/surge/grupo resuelta;
restantes decisiones y validaciones requieren sus propias autorizaciones.

## 18. Próxima acción recomendada

Aceptar esta configuración y resolver el /32/redes/presupuesto pendientes.
Después autorizar la revisión acotada de helpers y validación Terraform antes
de cualquier inicialización/plan. No continuar automáticamente.

Confirmación: no Terraform ejecutado, AKS creado, Azure/Entra modificados,
historial Git alterado, staging, commits ni push. No recursos PG-05/PG-06 tocados.
