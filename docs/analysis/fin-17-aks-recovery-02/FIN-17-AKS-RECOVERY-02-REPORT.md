# FIN-17-AKS-RECOVERY-02 — 23/11/2026
## 1. Estado inicial
C:/WordleTFG/repo, codex/pg01-07-consolidation,
HEAD 4d56cf265cc5f0af8c72c64f2a93373660e8f122.
Índice vacío, nueve modificados, 315 sin seguimiento.
recovery/inputs y recovery/workspace vacíos al comenzar.
## 2. Fuentes verificables
Contrato infra/scripts/Invoke-AksEmergencyTeardown.ps1 y plantillas JSON existentes.
Fuentes reales infra/terraform/*.tf y lock; metadatos locales existentes de backend
.terraform/terraform.tfstate leídos para coordenadas e identidad, sin copiarlos.
FIN-AKS-ENTRA-PREP-REPORT.md: sección 8 grupo real, sección 10 operador humano
real (corroborado por membresía documentada), tenant contrastado con metadatos.
LIVE-DEPLOYMENT-PLAN/APPLY acreditan uso de defaults y grupo en el ciclo histórico.
No se consultó Azure ni se abrió un almacén global de credenciales.
## 3. TargetFile
CREADO C:/WordleTFG/recovery/inputs/target.json.
Trece claves exactas del contrato: subscription_id, tenant_id, operator_object_id,
resource_group_name, node_resource_group_name, cluster_name, vnet_name, subnet_name,
identity_name, backend_resource_group, backend_account, backend_container, backend_key.
IDs UUID reales; nombres de instalación tomados de defaults Terraform vigentes;
backend de metadatos locales coincidentes con configuración histórica.
Tenant de Entra coincide con backend, sin ambigüedad.
Set-EmergencyTarget con este archivo y workspace externo: PASS local.
No implica identidad actual o acceso Azure confirmado.
Archivo privado operativo nuevo protegido owner/SYSTEM/Administrators;
no contiene tokens/contraseñas. Sin placeholders ni campos ajenos como location.
## 4. VariablesFile
CREADO C:/WordleTFG/recovery/inputs/variables.json.
Diecisiete campos reales: subscription_id, tenant_id, location,
resource_group_name, node_resource_group_name, cluster_name, dns_prefix, vnet_name,
subnet_name, identity_name, node_pool_name, node_vm_size, node_count,
os_disk_size_gb, kubernetes_version, admin_group_object_ids.
Defaults leídos de variables.tf, UUID de grupo recuperado de evidencia real.
JSON válido, sin claves inventadas, identidad/RG/clúster coherentes con TargetFile.
PENDIENTES: api_authorized_cidrs y api_access_approved, obligatorios sin default.
No se persistió una dirección histórica como dirección vigente ni se falsificó
la aprobación true. Se omitieron expresamente, no se usaron placeholders.
El archivo existe pero NO satisface todavía todos los requisitos para plan.
ACL restrictiva aplicada sólo a este archivo nuevo y al TargetFile nuevo.
## 5. WorkDirectory
PREPARADO C:/WordleTFG/recovery/workspace, externo al repositorio.
Copiados main.tf, outputs.tf, providers.tf, variables.tf, versions.tf,
.terraform.lock.hcl y backend.hcl.example: siete archivos exactos por SHA-256.
Sin .terraform, estados ni credenciales copiados. Originales sin cambios.
fmt -check del workspace nuevo: PASS.
Contrato exige también .terraform/terraform.tfstate de backend humano inicializado:
NO EXISTE; no puede ejecutar Backend/Fingerprint todavía.
No se ejecutó init ni se trasladó caché OIDC o caché histórica.
## 6. Backend
Mismo backend existente azurerm/Entra, RG rg-wordle-state,
cuenta stwordletfgstate7c92d4, contenedor tfstate, key wordle/aks-demo.tfstate.
backend.hcl.example copiado conserva coordenadas reales, no backend alternativo.
Suscripción y tenant proceden de metadatos ya contrastados.
Inicialización futura debe completarlos explícitamente con la identidad humana,
en una operación autorizada separada; no usar credenciales persistentes ni OIDC.
No se verificó lease, acceso, existencia de recursos o contenido remoto actual.
## 7. Histórico y dinámico
Históricos verificables: UUID de operador/grupo, tenant/suscripción y nombres.
Valores de configuración actuales: región swedencentral, dos Standard_D4s_v5,
Kubernetes 1.35.9 y demás defaults copiados; no prueban existencia actual de AKS.
Dinámicos pendientes: CIDR API de la futura ventana y su aprobación expresa,
sesión humana/autorizaciones vigentes, estado/lease e inventario de recursos.
En futura emergencia obtener esos datos mediante consultas autorizadas;
no ampliar esta iteración ni resolverlos por inferencia histórica.
## 8. Validaciones
- Parseo de JSON/UUID y claves TargetFile: PASS.
- Contrato real Set-EmergencyTarget invocado localmente: PASS (no ejecuta cloud).
- Identidad/RG/clúster VariablesFile frente a TargetFile: PASS.
- Hashes de siete copias frente a fuentes: PASS.
- WorkDirectory externo y ausencia de .terraform: confirmados.
- Terraform 1.9.8 fmt -check del workspace: exit 0.
- Test-AksEmergencyTeardown.ps1: 28/28 casos OFFLINE, exit 0.
- Test-AksEmergencyAzureResolution.ps1: 14/14 regresiones OFFLINE, exit 0.
Son pruebas del procedimiento con dobles: no validación real de Azure.
La primera suite sustituye todos los procesos nativos; la segunda sólo ejecuta
un az.cmd temporal inerte. Sus mensajes PLAN/CLEAN/errores pertenecen a fixtures.
No se ejecutó un plan, retirada o CLI Azure real.
No se repitió validate del workspace: falta proveedor inicializado y está
prohibido init remoto. Las fuentes idénticas validaron en RECOVERY-01; ese resultado
histórico no se declara como validate ejecutado en este workspace.
## 9. Limitaciones
Inputs materiales no equivalen a READY: faltan dos variables y metadatos humanos
generados por inicialización autorizada. No se garantiza vigencia de IDs/grupo
ni existencia/ausencia actual de AKS sin consulta remota.
No se modificaron scripts, contrato, fuentes Terraform ni configuración global.
No se alteraron UUID/marker/ACL del almacén privado ni respaldos cifrados.
## 10. Guía operativa
Actualizada docs/operations/FIN-AKS-EMERGENCY-TEARDOWN.md, sección 10.
Rutas definitivas, origen histórico, carencias y pasos futuros explícitos.
No invocar -Preflight real hasta autorizar lecturas y preparar backend.
-Teardown sólo tras autorización independiente, revisión de inventario y
confirmaciones PLAN WORDLE AKS / DESTRUIR WORDLE AKS.
Procedimiento independiente de runner Docker y GitHub Actions.
Si cambian fuentes, revisar/copiar .tf y lock de nuevo por hashes; nunca copiar
caché/planes entre Linux y Windows. Conservar backend independiente.
## 11. Git
Nueve modificados y 315 sin seguimiento iniciales, índice vacío.
Sólo guía operativa y este informe cambian en repo; inputs/fuentes copiados quedan
fuera de Git. Sin staging/commit/push/reset/clean/stash ni cambio de rama.
HEAD conservado. Evidencias académicas anteriores preservadas.
## 12. OneDrive
No utilizado, alterado ni eliminado.
## 13. Resultado
PARTIAL. TargetFile válido localmente; VariablesFile real pero incompleto;
WorkDirectory con fuentes válidas pero no inicializado.
Recuperación humana NOT READY, remoto NOT VERIFIED.
Runner NOT REGISTERED. CD/AKS NO-GO.
Sin Azure, Terraform remoto, registro, Actions ni cambios de infraestructura.
## 14. Próximo paso mínimo
Resolver y aprobar CIDR API y api_access_approved para la ventana prevista.
Autorizar por separado inicialización Entra/CLI del workspace humano con backend
existente y eventual comprobación remota de sólo lectura.
No ejecutar automáticamente ninguna operación pendiente.
