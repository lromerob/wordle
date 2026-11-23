# FIN-17-AKS-RECOVERY-03 — 23/11/2026

**READY LOCAL** para esta preparación. Backend remoto **NOT VERIFIED**.
Esto no acredita una recuperación real ni autoriza registro, CD o AKS.

## Configuración y autorización
Se actualizaron exclusivamente api_authorized_cidrs y api_access_approved en
C:/WordleTFG/recovery/inputs/variables.json. Se conservan los diecisiete valores
anteriores y la ACL del archivo.

- api_authorized_cidrs: lista de una IPv4 pública actual, exclusivamente /32.
  Dirección conservada en el input privado, no duplicada en este informe.
- Fuente: consultas HTTPS desde el equipo a https://api.ipify.org y
  https://checkip.amazonaws.com; ambas devolvieron la misma IPv4 global.
  Es la salida pública observada de esta conexión, no una garantía permanente
  de identidad del operador. Revalidar si cambia VPN, conexión o ventana.
- api_access_approved: booleano true, autorizado expresamente por el propietario.
  variables.tf:137-145 indica que aprueba los /32 y NO autoriza desplegar Azure.
  No se heredó autorización de un despliegue histórico.

Contrato api_authorized_cidrs (variables.tf:120-135): list(string), no nulo,
exactamente un IPv4 público /32, sin rangos privados/reservados ni 0.0.0.0/0.

## Validaciones mínimas ejecutadas
JSON válido; tipos, cardinalidad y CIDR público /32 correctos.
Todas las variables obligatorias declaradas presentes, sin claves desconocidas.
Suscripción, tenant, RG y clúster coherentes con TargetFile; UUID válidos.
TargetFile sin cambios por SHA-256, con contrato validado en la iteración anterior.
Workspace externo existente; siete archivos idénticos a fuentes/lock/backend,
sin referencias OneDrive. ACL de VariablesFile idéntica antes y después.
Escritura con temporal exclusivo, flush y sustitución atómica File.Replace.
No se repitieron las 42 pruebas. No se ejecutó Terraform ni Azure.

## Inicialización humana futura — comandos NO EJECUTADOS
Requiere autorización separada de acceso remoto e inicialización. Antes de usar
estos comandos, revisar sesión humana existente, entorno ARM/TF inesperado,
procesos concurrentes y vigencia del /32. No usar sesión OIDC ni credenciales
del runner. No continuar si los IDs no corresponden exactamente al objetivo.

Los parámetros se leen de los archivos reales, sin placeholders ni IDs inventados:

    $TargetFile = 'C:/WordleTFG/recovery/inputs/target.json'
    $VariablesFile = 'C:/WordleTFG/recovery/inputs/variables.json'
    $WorkDirectory = 'C:/WordleTFG/recovery/workspace'
    $Tf = Join-Path $env:LOCALAPPDATA 'WordleTFG/tools/terraform-1.9.8/terraform.exe'
    $Target = Get-Content -Raw -LiteralPath $TargetFile | ConvertFrom-Json

Selección y revisión de contexto humano, FUTURAS:

    az account set --subscription $Target.subscription_id
    az account show --query '{subscription:id,tenant:tenantId,state:state,userType:user.type}' -o json
    az ad signed-in-user show --query id -o tsv

Comparar manualmente tenant/subscription/operator_object_id con TargetFile.
Detenerse ante discrepancias. No asumir que account set acredita el tenant ni
la identidad humana. Esta iteración no cambió la suscripción activa.

Inicialización FUTURA contra el backend existente, con autenticación Entra/CLI
humana y sin copiar .terraform:

    & $Tf ("-chdir="+$WorkDirectory) init -input=false -lockfile=readonly -no-color -backend-config=backend.hcl.example ("-backend-config=subscription_id="+$Target.subscription_id) ("-backend-config=tenant_id="+$Target.tenant_id) -backend-config=use_azuread_auth=true -backend-config=use_cli=true -backend-config=use_oidc=false

backend.hcl.example ya contiene RG/cuenta/contenedor/key contrastados con TargetFile.
Es azurerm, key wordle/aks-demo.tfstate. No crear backend nuevo ni migrar estado.
init puede acceder al estado remoto y adquirir lease: no es una prueba offline.

Inspecciones FUTURAS no destructivas:

    & $Tf ("-chdir="+$WorkDirectory) workspace show
    & $Tf ("-chdir="+$WorkDirectory) state list
    & 'C:/WordleTFG/repo/infra/scripts/Invoke-AksEmergencyTeardown.ps1' -Preflight -TargetFile $TargetFile -WorkDirectory $WorkDirectory -TerraformPath $Tf

Revisar nombre de workspace y correspondencia del backend antes de state list;
no ejecutar workspace new/select para superar discrepancias.
El script -Preflight consulta Azure, verifica identidad/backend/lease/inventario
y registra evidencia local. No se ejecutó aquí. No generar plan ni destruir.

## Estado y límites
Inicial Git: nueve modificados, 316 sin seguimiento, índice vacío,
rama codex/pg01-07-consolidation, HEAD
4d56cf265cc5f0af8c72c64f2a93373660e8f122.
Única incorporación al repositorio: este informe; final previsto 317 sin seguimiento.
Sin staging, commit, push ni cambio de rama.
OneDrive, TargetFile, fuentes/backend, UUID, marker, ACL y respaldos sin cambios.
Backend humano aún no inicializado; remoto NOT VERIFIED.
Runner NOT REGISTERED. CD/AKS NO-GO.

**Próximo paso mínimo:** revisar y autorizar separadamente la inicialización y
validación remota de sólo lectura desde el workspace humano. READY LOCAL se
limita al cierre de inputs y comandos preparados; no significa que el procedimiento
de emergencia esté probado o pueda ejecutarse antes de inicializar el backend.

> Rutas personales normalizadas editorialmente para publicación. Resultados, fechas, hashes y entorno histórico no cambian. <USER_HOME> designa el directorio personal original; variables PowerShell se resuelven para el usuario que reproduce. <LEGACY_REPO_ROOT> identifica el origen histórico, no el workspace vigente.
