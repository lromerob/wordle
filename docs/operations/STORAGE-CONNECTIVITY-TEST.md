# Prueba supervisada de conectividad Storage — preparación FIN-17-TEST-02

Estado: preparada, NO ejecutada. No demuestra acceso desde Actions ni CD.

## Contrato y alcance

Identidad administrada `wordle-storage-connectivity-test`, en `rg-wordle-state`.
Federación: issuer `https://token.actions.githubusercontent.com`, audience
`api://AzureADTokenExchange`, subject
`repo:lromerob/wordle:environment:wordle-azure-demo`.
Único rol: Storage Blob Data Contributor sobre
`stwordletfgstate7c92d4/blobServices/default/containers/wordle-connectivity-test`.
No permisos ARM de escritura, claves, AKS ni acceso concedido al estado `tfstate`.
El contenedor es privado y se preparó mediante ARM sin abrir el firewall.

Variables no secretas del environment: `WORDLE_STORAGE_TEST_CLIENT_ID`,
`WORDLE_STORAGE_TEST_TENANT_ID`, `WORDLE_STORAGE_TEST_SUBSCRIPTION_ID`,
`WORDLE_STORAGE_TEST_ACCOUNT`, `WORDLE_STORAGE_TEST_RESOURCE_GROUP`,
`WORDLE_STORAGE_TEST_CONTAINER`. No exportar tokens ni contraseñas.

La identidad federada puede ser utilizada por otros jobs aprobados que compartan
el mismo environment/subject: el subject no restringe un archivo workflow concreto.
El operador debe revisar el SHA, los scripts y cada solicitud de aprobación.

## Publicación y lanzamiento futuros: requieren autorización nueva

No lanzar la prueba durante la preparación. Revisar y publicar los cuatro archivos
nuevos sólo después de autorización. GitHub requiere que un workflow manual exista
en la rama predeterminada para habilitar su despacho normal; verificar su registro
antes de intentar ejecutarlo. Si falta, solicitar una integración revisada en `main`;
no cambiar de rama ni modificar `main` automáticamente.

Reservar una issue pública abierta del repositorio para confirmación (no PR).
Si no existe, el operador puede crearla en una iteración autorizada. No poner
secretos, identificadores privados de Azure ni reglas administrativas en ella.
No necesita permisos de escritura en GitHub el token del runner: la consulta de
comentarios es pública, con un máximo aproximado de 11 consultas por espera.
Un error de API/rate limit hace fallar la prueba, no autoriza continuar.

Tras autorización futura: lanzar manualmente con el SHA completo revisado del
workflow nuevo y el número de issue. Autorizar el environment. Sólo `lromerob`,
la rama autorizada y el SHA exacto despachado se aceptan.
PREPARE y WAIT/VERIFY son pasos del MISMO job y VM; la IPv4 se vuelve a observar
antes de usar Blob. No usar otra ejecución para continuar la primera.

Esperar el resumen del paso PREPARE. Guardar run_id, run_attempt, commit, IPv4,
frase exacta de confirmación y nombre del blob sintético que aparecerá en FINISH.
El resumen y logs muestran la IP temporal: es metadato de red público, no un secreto.

## Apertura manual — NO ejecutar durante la preparación

Exclusividad supervisada: un solo operador; nadie modifica el firewall durante esta
ventana. GitHub serializa este diagnóstico, pero no bloquea Portal/CLI ni otros
workflows. Si existe otra intervención activa o no se puede reservar la ventana,
abortar. No confiar sólo en la concurrencia GitHub.

PowerShell 7, Azure CLI del operador y sesión ya autenticada. No `az account set`.
Obtener `$ExpectedSubscription` y `$ExpectedTenant` de los metadatos aprobados
locales, sin enviarlos a logs públicos. Tomar `$Ip` y `$Confirmation` del resumen
PREPARE, nunca de un tercero. `$Issue` y `$Run` identifican esa ejecución.

```powershell
$Account = 'stwordletfgstate7c92d4'
$Group = 'rg-wordle-state'
# Definir ExpectedSubscription/ExpectedTenant/Ip/Issue/Run/Confirmation antes.
$context = az account show --only-show-errors -o json | ConvertFrom-Json
if ($LASTEXITCODE -ne 0 -or $context.id -ne $ExpectedSubscription -or
    $context.tenantId -ne $ExpectedTenant -or $context.state -ne 'Enabled') { throw 'Contexto incorrecto' }
$parsed = [Net.IPAddress]::Parse($Ip)
if ($Ip.Contains('/') -or $parsed.AddressFamily -ne 'InterNetwork') { throw 'Sólo IPv4 individual' }
# Validación pública completa con la misma lógica offline del diagnóstico:
& C:\WordleTFG\repo\.venv\Scripts\python.exe -B -c "import sys;sys.path.insert(0,'C:/WordleTFG/repo/scripts');from storage_connectivity_test import public_ipv4;public_ipv4(sys.argv[1])" $Ip
if ($LASTEXITCODE -ne 0) { throw 'IPv4 no pública' }
$before = az storage account show -g $Group -n $Account --subscription $ExpectedSubscription --only-show-errors -o json | ConvertFrom-Json
if ($LASTEXITCODE -ne 0 -or $before.networkRuleSet.defaultAction -ne 'Deny' -or
    $before.publicNetworkAccess -ne 'Enabled' -or $before.allowSharedKeyAccess -ne $false -or
    $before.allowBlobPublicAccess -ne $false -or $before.networkRuleSet.bypass -ne 'None') { throw 'Baseline inesperado' }
$originalIps = @($before.networkRuleSet.ipRules.ipAddressOrRange | Sort-Object)
if ($originalIps.Count -ne 1) { throw 'Reconciliar reglas antes de continuar' }
if ($originalIps -contains $Ip) { throw 'IP ya existente: abortar; no añadir ni retirar' }
# Conservar snapshot y Run/attempt/SHA/Ip en una ubicación privada externa aprobada.
# No publicar el snapshot. Confirmar que la regla original es la administrativa.
# Releer justo antes de escribir: abortar si cambió cualquier regla.
$latest = az storage account show -g $Group -n $Account --subscription $ExpectedSubscription --only-show-errors -o json | ConvertFrom-Json
if ($LASTEXITCODE -ne 0 -or ($latest.networkRuleSet | ConvertTo-Json -Depth 12 -Compress) -ne
    ($before.networkRuleSet | ConvertTo-Json -Depth 12 -Compress)) { throw 'Cambio concurrente' }
az storage account network-rule add -g $Group --account-name $Account --subscription $ExpectedSubscription --ip-address $Ip --only-show-errors --output none
if ($LASTEXITCODE -ne 0) { throw 'Resultado incierto: consultar ARM y recuperar; no confirmar' }
$opened = az storage account show -g $Group -n $Account --subscription $ExpectedSubscription --only-show-errors -o json | ConvertFrom-Json
$expectedIps = @($originalIps + $Ip | Sort-Object)
if ($LASTEXITCODE -ne 0 -or $opened.networkRuleSet.defaultAction -ne 'Deny' -or
    (Compare-Object $expectedIps @($opened.networkRuleSet.ipRules.ipAddressOrRange | Sort-Object)) -or
    $opened.networkRuleSet.bypass -ne $before.networkRuleSet.bypass -or
    ($opened.networkRuleSet.virtualNetworkRules | ConvertTo-Json -Depth 12 -Compress) -ne
    ($before.networkRuleSet.virtualNetworkRules | ConvertTo-Json -Depth 12 -Compress)) { throw 'Revisar y recuperar; no confirmar' }
& 'C:\Program Files\GitHub CLI\gh.exe' issue comment $Issue --repo lromerob/wordle --body $Confirmation
if ($LASTEXITCODE -ne 0) { throw 'No confirmado: cerrar excepción o confirmar dentro del timeout' }
```

El comentario debe ser exactamente la frase emitida por PREPARE y pertenecer a
`lromerob` con asociación OWNER, creado después de PREPARE. Incluye run, intento,
SHA, IPv4 y nonce. La confirmación es pública, no un token. No copiarla de otro run.
El cuerpo se compara sin recortar espacios ni saltos de línea. Se exige issue_url
exacta del repositorio/issue consultados, autor User/OWNER y created_at posterior a
PREPARE, con updated_at igual a created_at. Si se editó, publicar un comentario
nuevo; no reutilizarlo. Las marcas de GitHub tienen resolución de segundos: no son
un historial completo de ediciones. El ID, timestamps, issue y hash del texto se
registran al aceptar para conservar trazabilidad aun si se modifica después.
No se siguen redirecciones HTTP de issues, servicios IP ni Blob.
La identidad Azure y el run/attempt/SHA/issue se comprueban otra vez antes de Blob.
API fallida, canal saturado o timeout: rechazo seguro, sin petición Blob de prueba.

## Verificación y cierre manual — también tras cancelación

WAIT: máximo 10 minutos; permisos Blob pueden tardar en propagarse. VERIFY usa
seis intentos de escritura como máximo ante HTTP 403, con pausas de 10 segundos.
El job completo tiene timeout de 30 minutos. Fallos DNS/TLS, HTTP y RBAC se registran
por etapa; un 403 no demuestra por sí solo si la causa es firewall o RBAC.

El nombre del blob se publica para recuperación: `diagnostic-<run>-<attempt>-<nonce>.json`.
No usa datos reales. PUT sin sobrescritura, GET idéntico y DELETE; limpieza en
`finally` y paso `always()`. Si muere la VM no se garantiza limpieza.

Antes de cerrar la IP, confirmar que el blob se eliminó; si falta esa evidencia,
el operador podrá eliminar exclusivamente ese blob con su sesión y `--auth-mode login`
desde su dirección administrativa. No listar ni tocar `tfstate`.

```powershell
# Reutilizar snapshot y variables de la sesión. Si se perdió, recuperar el registro
# privado de esa ejecución; no reconstruir ni sustituir la baseline por conjeturas.
$current = az storage account show -g $Group -n $Account --subscription $ExpectedSubscription --only-show-errors -o json | ConvertFrom-Json
if ($LASTEXITCODE -ne 0) { throw 'No se pudo consultar; no declarar cierre' }
if ($originalIps -contains $Ip) { throw 'No pertenece a la prueba: no retirar' }
if ($current.networkRuleSet.defaultAction -ne 'Deny' -or
    (Compare-Object $expectedIps @($current.networkRuleSet.ipRules.ipAddressOrRange | Sort-Object))) {
    throw 'Cambio concurrente: detener automatismos, reconciliar manualmente y retirar sólo la IP propia'
}
az storage account network-rule remove -g $Group --account-name $Account --subscription $ExpectedSubscription --ip-address $Ip --only-show-errors --output none
if ($LASTEXITCODE -ne 0) { throw 'Cierre no verificado; consultar ARM y recuperar' }
$closed = az storage account show -g $Group -n $Account --subscription $ExpectedSubscription --only-show-errors -o json | ConvertFrom-Json
if ($LASTEXITCODE -ne 0 -or ($closed.networkRuleSet | ConvertTo-Json -Depth 12 -Compress) -ne
    ($before.networkRuleSet | ConvertTo-Json -Depth 12 -Compress) -or
    $closed.publicNetworkAccess -ne $before.publicNetworkAccess -or
    $closed.allowSharedKeyAccess -ne $before.allowSharedKeyAccess -or
    $closed.allowBlobPublicAccess -ne $before.allowBlobPublicAccess) { throw 'Restauración no verificada' }
'Firewall restaurado; registrar evidencia ARM de cierre fuera del repositorio'
```

Estos comandos de CLI no son una transacción ni una comparación y escritura atómicas.
Ante conflictos no sobrescribir un snapshot completo; preservar reglas ajenas y
reconciliar con el otro operador. La excepción no caduca por sí sola. ARM permite
cerrarla aunque Actions haya terminado o perdido el runner. No depender de `always()`.
Un resultado Blob satisfactorio sigue siendo parcial hasta registrar el cierre ARM.

## Recuperación por causa

- OIDC/permisos: no confirmar ni ampliar roles; revisar issuer/subject y asignación.
- IPv4 inválida/inestable/ya existente: abortar y cerrar sólo una excepción propia.
- Timeout/cancelación/pérdida de VM: recuperar run e IP del resumen; comprobar blob
  y retirar manualmente la excepción, manteniendo la dirección administrativa.
- DNS/TLS/403: no cambiar Deny a Allow; cerrar y diagnosticar la ruta y Blob RBAC.
- Misma región Azure: la regla IPv4 puede no habilitar la ruta; un fallo es evidencia
  válida, no autorización para redes generales ni para reintentos indiscriminados.
- Fallo de DELETE: registrar el nombre exacto; operador borra sólo ese blob.
- Fallo de cierre/cambio concurrente: resultado operativo PARTIAL hasta reconciliación.

## Registro académico preparado

**Control humano de excepciones de red en un pipeline CD supervisado.**
Se descartó otorgar escritura ARM de la cuenta al workflow porque ese permiso no
se limita a una regla IP. Se separa el operador que administra el firewall de la
identidad OIDC con datos de un único contenedor. La coordinación conserva el mismo
runner, usa una confirmación pública del propietario vinculada a ejecución e IP,
y tiene timeout. La recuperación ARM es independiente de Actions. Se requiere
capturar aprobación, identidad, etapas DNS/TLS/Blob, integridad, limpieza y cierre.
La prueba aún NO se ha ejecutado y no demuestra CD autónomo ni Terraform remoto.

## Revisión y secuencia de publicación — FIN-17-PUBLISH-01

Revisión realizada sin publicar ni ejecutar. Rama predeterminada confirmada: `main`.
El nuevo workflow no está en ella. Las protecciones de ambas ramas y del environment
siguen activas. Consulta de comentarios pública y anónima: no se necesita `issues:write`
ni un token adicional; rate limit o fallo HTTP provocan rechazo seguro.
Se mantienen `actions/checkout@v4` y `azure/login@v2`, ya utilizados por el proyecto;
no se actualizan dependencias ni se ejecuta código remoto durante esta revisión.
Las etiquetas mayores son mutables: fijación por SHA queda fuera de este cambio.

Publicación futura propuesta, cada operación pendiente de autorización:

1. Commit de exactamente los cuatro archivos de este diagnóstico en
   `codex/pg01-07-consolidation`, con mensaje
   `test(devops): prepare supervised OIDC storage connectivity diagnostic`.
2. Push normal de esa rama. El diagnóstico NO se activa por push, pero el CI
   existente sí puede ejecutarse automáticamente y publicar GHCR al superar sus gates.
   Esa consecuencia debe incluirse en la autorización de publicación.
3. Incorporación separada a `main` de SÓLO el mismo archivo
   `.github/workflows/storage-connectivity-test.yml`, partiendo de `main` actualizado,
   mediante un cambio mínimo autorizado. No fusionar toda la rama de trabajo ni
   incorporar los 133 informes. No cambiar protecciones o restricciones del environment.
   El push a `main` también activa el CI/publicador existentes; no prometer ausencia de runs.
4. Verificar que GitHub registra el workflow sin despacharlo. Su if impide ejecutar
   el job diagnóstico desde main; el environment sólo permite la rama de trabajo.
   Los scripts se obtendrán de esa rama al ejecutar el commit revisado.
5. En otra autorización, reservar issue y ventana exclusiva; despachar seleccionando
   la rama de trabajo y su SHA exacto. Aprobar el environment; seguir apertura,
   confirmación, diagnóstico y cierre ARM del runbook. No usar un segundo job/run
   para continuar el primero.

Referencia: https://docs.github.com/en/actions/how-tos/manage-workflow-runs/manually-run-a-workflow
La publicación no demuestra conectividad ni implica permiso para modificar el firewall.
Permanece pendiente comprobar la ruta de salida real del runner hacia Storage.
