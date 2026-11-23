# FIN-17-AKS-RECOVERY-04 — 23/11/2026

## 1. Preflight
Inputs target.json/variables.json existentes y coherentes; workspace externo
C:/WordleTFG/recovery/workspace. Backend y UUID de contexto contrastados.
Sin placeholders, estado local previo ni inicialización preexistente.
Terraform 1.9.8 y Azure CLI disponibles. Sin repetir pruebas offline.

## 2. Identidad Azure
Sesión humana existente válida: no fue necesario login interactivo.
Suscripción, tenant y operator_object_id coinciden exactamente con TargetFile;
suscripción Enabled y tipo user. Lectura Graph del usuario autenticado conforme.
Todas las lecturas de recursos usaron --subscription explícita.
No se cambió suscripción predeterminada ni se usó identidad del runner/OIDC.
No se guardaron credenciales ni tokens en archivos del proyecto.

## 3. Backend esperado y observado
RG rg-wordle-state, cuenta stwordletfgstate7c92d4, contenedor tfstate,
blob wordle/aks-demo.tfstate: existen y coinciden con el objetivo aprobado.
Autenticación Entra/CLI humana; sin claves Storage ni credenciales incrustadas.
Antes/después: ETag 0x8DF4888CBDED1B9, tamaño 1853 bytes, lastModified
2026-11-22T12:07:28+01:00, lease unlocked/available.
ETag y propiedades intactos: no se detectó escritura del blob/estado.

## 4. Inicialización
PASS, exit 0. Backend azurerm configurado; AzureRM4.50.0 instalado por init,
firmado por HashiCorp, conforme al lock existente. Lock y siete fuentes originales
idénticos a la copia revisada. Sin migración, reconfigure ni force-copy.
Incidencias de comandos preparados, resueltas sin modificar scripts:
- Argumento backend.hcl.example sin comillas se dividía en PowerShell:
  error Too many command line arguments. Sin inicialización.
- use_cli no existe como argumento de backend en Terraform1.9.8:
  Invalid backend configuration argument. Sin backend configurado.
Se entrecomillaron argumentos y retiró sólo use_cli; autenticación CLI/Entra funcionó.

Comando efectivo (IDs obtenidos del TargetFile real, no placeholders):
    $Target = Get-Content -Raw 'C:/WordleTFG/recovery/inputs/target.json' | ConvertFrom-Json
    $ArgsTf = @('-chdir=C:/WordleTFG/recovery/workspace','init','-input=false','-lockfile=readonly','-no-color','-backend-config=backend.hcl.example',('-backend-config=subscription_id='+$Target.subscription_id),('-backend-config=tenant_id='+$Target.tenant_id),'-backend-config=use_azuread_auth=true','-backend-config=use_oidc=false')
    & (Join-Path $env:LOCALAPPDATA 'WordleTFG/tools/terraform-1.9.8/terraform.exe') @ArgsTf
No repetir ahora: workspace ya inicializado. Esta forma corrige el comando
histórico de RECOVERY-03, cuya evidencia se conserva sin editar.

Archivos locales generados por init:
- .terraform/terraform.tfstate
- .terraform/providers/registry.terraform.io/hashicorp/azurerm/4.50.0/windows_amd64/LICENSE.txt
- .terraform/providers/registry.terraform.io/hashicorp/azurerm/4.50.0/windows_amd64/terraform-provider-azurerm_v4.50.0_x5.exe

Son caché/proveedor y metadatos locales de backend; no copia de estado remoto
impresa. No se cambió la ACL ni se exportaron secretos.

## 5. Workspace
terraform workspace show: default, exit 0.
Corresponde al key aprobado y configuración histórica. No workspace new/select.

## 6. Estado remoto
terraform state list: exit 0, salida vacía, cero recursos gestionados.
Coherente con la retirada histórica; no se ejecutó refresh, plan ni state pull.

## 7. Infraestructura contrastada
Lecturas ARM adicionales: RG de aplicación y RG de nodos no existen;
cero clústeres con el nombre objetivo en la suscripción aprobada.
No se dedujo ausencia sólo del estado vacío. No es auditoría universal de huérfanos.
Una consulta AKS con length(...) falló por parseo de az.cmd; se sustituyó por
lectura de nombres y filtrado exacto en memoria: resultado cero.
Intento de inventario del RG ausente devolvió exit 3; se conserva como limitación,
no como consulta satisfactoria ni como motivo para crear/remediar recursos.

## 8. Límites
No destrucción, plan, apply, import, refresh, cambios RBAC o de infraestructura.
No se ejecutó el script -Teardown. La lectura verificada no demuestra que una
destrucción futura vaya a completarse ni autoriza generar su plan.
Almacén, marker, UUID, ACL, inputs y respaldos no modificados.
Sin registro del runner, workflows ni despliegues.

## 9. Recuperación humana
HUMAN RECOVERY READY hasta autenticación, inicialización e inspección del estado,
independiente de Actions/Docker. BACKEND VERIFIED.
DESTRUCTION NOT TESTED en esta iteración. Un futuro preflight/retirada exige
revalidar contexto, inventario, lease, autorización y confirmaciones del contrato.

## 10. Git
Rama codex/pg01-07-consolidation, HEAD
4d56cf265cc5f0af8c72c64f2a93373660e8f122.
Índice vacío; nueve modificados y 317 sin seguimiento iniciales.
Único archivo nuevo del repo: este informe; final 318 sin seguimiento.
Sin staging, commit, push ni cambio de rama. Fuentes/lock sin cambios.

## 11. OneDrive
No utilizado, alterado ni eliminado.

## 12. Resultado
PASS — BACKEND VERIFIED / HUMAN RECOVERY READY.
Autenticación PASS; contexto MATCH; init PASS; default identificado; estado vacío.
Destrucción NOT TESTED. Runner NOT REGISTERED. CD/AKS NO-GO.

## 13. Próximo paso mínimo
Revisar esta evidencia y decidir expresamente el siguiente gate de FIN-17.
No registrar runner, crear AKS ni probar destrucción automáticamente.

> Rutas personales normalizadas editorialmente para publicación. Resultados, fechas, hashes y entorno histórico no cambian. <USER_HOME> designa el directorio personal original; variables PowerShell se resuelven para el usuario que reproduce. <LEGACY_REPO_ROOT> identifica el origen histórico, no el workspace vigente.
