# FIN-17-AKS-RECOVERY-01 — 23/11/2026
## 1. Inventario Terraform
Fuentes: C:/WordleTFG/repo/infra/terraform/{main,variables,outputs,providers,versions}.tf.
Provider AzureRM =4.50.0, Terraform instalado 1.9.8, backend azurerm/Entra.
.terraform.lock.hcl y proveedor windows_amd64 presentes.
terraform.tfvars.example y azure-variables.example.json son PLANTILLAS.
Sin archivo .tfvars real ni JSON privado de ventana encontrado en ese directorio.
Scripts humanos infra/scripts/Invoke-AksEmergencyTeardown.ps1 y guía
docs/operations/FIN-AKS-EMERGENCY-TEARDOWN.md.
CI/CD: .github/workflows/azure-demo.yml usa runner Linux y autenticación OIDC;
no sustituye ni es dependencia del procedimiento humano Entra/CLI.
## 2. TargetFile
NO RESUELTO. Ruta documentada C:/WordleTFG/recovery/inputs/target.json, inexistente.
Fuera del repo; sin ruta relativa interna aplicable.
Plantilla existente: infra/terraform/emergency-target.example.json, NO utilizable
como objetivo real. Contrato exige JSON externo, trece claves exactas, UUID de
suscripción/tenant/operador humano y coordenadas de instalación/backend aprobadas.
Contiene contexto privado de operación, no debe publicarse ni inventarse.
## 3. VariablesFile
NO RESUELTO. C:/WordleTFG/recovery/inputs/variables.json, inexistente, externo.
Plantilla azure-variables.example.json válida pero con valores de ejemplo.
terraform.tfvars.example contiene placeholders, no es el JSON externo del contrato.
VariablesFile aplica a retirada; preflight de lectura no lo requiere.
Debe coincidir con TargetFile en identidad/recursos y sólo usar variables declaradas.
Requiere grupos Entra, CIDR vigente, aprobación de acceso y contexto real revisado.
## 4. WorkDirectory
Histórico REAL: C:/WordleTFG/repo/infra/terraform, relativo infra/terraform.
Informes LIVE-DEPLOYMENT-APPLY, LIVE-DESTROY-EXECUTION y REMOTE-BACKEND-INITIALIZATION
identifican ese directorio, Terraform1.9.8/AzureRM4.50.0 y ciclo create/destroy.
Workspace HUMANO externo: NO RESUELTO.
C:/WordleTFG/recovery/workspace existe vacío, no es workspace preparado.
Set-EmergencyTarget rechaza rutas dentro del checkout. Debe existir copia revisada
externa de fuentes/lock y metadatos de backend humano ya inicializado.
No se copió caché ni se creó una configuración alternativa para fingir preparación.
## 5. Backend identificado
Configuración: C:/WordleTFG/repo/infra/terraform/backend.hcl.example,
relativo infra/terraform/backend.hcl.example. Aunque su nombre dice example, la
evidencia histórica de init lo identifica como archivo realmente usado.
RG rg-wordle-state; cuenta stwordletfgstate7c92d4; contenedor tfstate;
key wordle/aks-demo.tfstate. Sin claves de acceso en la configuración.
Metadatos locales existentes infra/terraform/.terraform/terraform.tfstate:
tipo azurerm, use_azuread_auth=true, cuatro coordenadas coincidentes.
Suscripción y tenant presentes; campos access_key/sas_token/client_secret/
client_certificate_path no poblados. Sólo se inspeccionó la configuración
necesaria en memoria, sin imprimir secretos ni estado remoto.
Estos metadatos son ignorados y privados; no son prueba actual de acceso,
lease libre o contenido vacío del blob. Backend humano externo aún pendiente.
## 6. Contexto esperado
Región swedencentral, confirmada en fuentes y evidencia del ciclo histórico.
Suscripción local enmascarada 1130…1bb5; tenant aff0…1eb9.
No se consultó ni cambió sesión Azure. No se certifica hoy la ausencia de AKS.
El destroy histórico documenta seis recursos retirados y estado vacío el 22/11;
es evidencia histórica, no lectura en vivo.
## 7. Validaciones ejecutadas
terraform -chdir=infra/terraform fmt -check: exit 0.
terraform -chdir=infra/terraform validate -json: exit 0, valid=true,
cero errores y cero advertencias, usando proveedor instalado localmente.
CHECKPOINT_DISABLE=1 sólo en proceso. Sin init ni plan ni acceso a Azure.
Parser PowerShell del script de emergencia: cero errores.
Tres plantillas JSON: sintaxis válida; sólo claves inspeccionadas.
Azure CLI localizada en C:/Program Files (x86)/Microsoft SDKs/Azure/CLI2/wbin/az.cmd.
Terraform 1.9.8 en la ruta de usuario previamente verificada:
<USER_HOME>/AppData/Local/WordleTFG/tools/terraform-1.9.8/terraform.exe.
Obligatorias sin default: subscription_id, tenant_id, admin_group_object_ids,
api_authorized_cidrs, api_access_approved. El resto tiene defaults.
Búsqueda focalizada en scripts/workflows/config de backend: sin rutas activas
OneDrive. La instrucción obsoleta del runbook que enviaba al Escritorio se
actualizó a C:/WordleTFG/repo. Menciones restantes OneDrive son prohibiciones
de almacenamiento, no referencias activas.
## 8. Procedimiento humano
Guía existente actualizada sin ejecutar acciones: independiente de Actions,
runner y Docker. Requisitos: herramientas Windows, autorización e identidad
humana, inputs externos aprobados y backend correcto ya inicializado.
Secuencia futura: verificar contexto y backend, -Preflight (consulta Azure),
revisar estado/lease/inventario, obtener autorización separada de retirada,
-Teardown con VariablesFile, confirmaciones manuales, verificar CLEAN/backend
y costes continuos/diferidos. Backend queda excluido de retirada.
## 9. Comandos sólo documentados
Los siguientes son esquemas NO EJECUTADOS. Las variables de rutas privadas no
están resueltas y no deben sustituirse por plantillas.
    $script = 'C:/WordleTFG/repo/infra/scripts/Invoke-AksEmergencyTeardown.ps1'
    $tf = Join-Path $env:LOCALAPPDATA 'WordleTFG/tools/terraform-1.9.8/terraform.exe'
    & $script -Preflight -TargetFile $PrivateTarget -WorkDirectory $PrivateWork -TerraformPath $tf
Sólo con autorización de retirada independiente:
    & $script -Teardown -TargetFile $PrivateTarget -WorkDirectory $PrivateWork -VariablesFile $PrivateVariables -TerraformPath $tf
El segundo comando puede generar plan y ejecutar destrucción tras confirmaciones;
no es un test local. Sin -auto-approve, force-unlock ni borrado manual de RG.
## 10. Dependencias y límites
Faltan inputs humanos reales, copia externa revisada e inicialización autorizada
de backend humano. No se solicitó acceso ni se leyeron ubicaciones privadas
no documentadas. No se modificó almacén aprobado ni se crearon respaldos.
Nada en esta iteración demuestra acceso actual a estado remoto o retirada real.
## 11. Git
Inicial rama codex/pg01-07-consolidation, HEAD
4d56cf265cc5f0af8c72c64f2a93373660e8f122, índice vacío,
nueve modificados y 314 sin seguimiento.
Cambios autorizados: guía operativa existente y este informe nuevo.
No staging, commit, push, reset, clean, stash ni cambio de rama.
## 12. OneDrive
No utilizado, modificado ni eliminado. Evidencias académicas previas intactas.
## 13. Resultado
PARTIAL. Entorno histórico identificable y validaciones locales satisfactorias,
pero los cuatro parámetros humanos no están todos resueltos.
Recuperación humana NOT READY. Verificación remota NOT VERIFIED.
Runner y CD/AKS siguen NO-GO; no se ejecutaron operaciones Azure.
## 14. Próximo paso mínimo
Aportar o autorizar localizar de forma acotada los TargetFile y VariablesFile
reales de la instalación y decidir el WorkDirectory externo humano aprobado.
Después preparar/contrastar su backend con autorización específica; no ejecutar
init ni consultas remotas automáticamente. No inventar archivos por esta carencia.

> Rutas personales normalizadas editorialmente para publicación. Resultados, fechas, hashes y entorno histórico no cambian. <USER_HOME> designa el directorio personal original; variables PowerShell se resuelven para el usuario que reproduce. <LEGACY_REPO_ROOT> identifica el origen histórico, no el workspace vigente.
