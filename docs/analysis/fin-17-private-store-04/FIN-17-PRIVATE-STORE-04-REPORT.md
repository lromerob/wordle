# FIN-17-PRIVATE-STORE-04 — 23/11/2026
## 1. Autorización humana
El propietario confirmó custodia segura de contraseñas separada del disco externo,
aceptó WD My Passport como respaldo independiente académico y autorizó
durable_acknowledged=true. Fuente: solicitud FIN-17-PRIVATE-STORE-04 de esta fecha.
No autoriza registro, CD, AKS ni retirada del workspace OneDrive.
## 2. Identidad
Workspace C:/WordleTFG/repo, almacén C:/WordleTFG/private.
UUID conservado: 7f280685-26af-424e-b805-acd32a980a45.
Contrato de cuatro campos y directorios backups/evidence/plans/selections intactos.
## 3. Respaldo y referencia operativa
WD My Passport USB D:, disco físico 1, partición 2, FAT32, etiqueta Backup.
GUID de volumen: c26d0a77-41e1-45a7-9c0d-529d372ff138.
Destino D:/WordleTFG-Backup.
repo.7z.001, SHA-256:
be2082236ee0cf0ead4be3d89f1f8cfaf3b7b2370240f0e762aa00c77eef7984.
private.7z.001, SHA-256:
3947a51882645ea4819546e9f331cb6b345f07c35afc42aedb13c358083c50b7.
Ambos hashes reconfirmados idénticos a FIN-17-BACKUP-RECOVERY-03.
Test y restauración verificados el 23/11/2026 en esa iteración: 9.930 archivos
del repositorio, Git fsck correcto, marker privado y cuatro directorios coincidentes.
No se repitieron extracciones ni se solicitaron contraseñas.
IMPORTANTE: private.7z.001 conserva el marker ANTERIOR false, no el aprobado true.
No se editó el archivo cifrado ni su manifest histórico.

### Actualización y restauración futuras
Identificar el disco por GUID, no sólo por letra. Crear nuevos nombres/destinos
versionados sin sobrescribir las copias históricas. Inventariar origen estable;
usar 7-Zip con AES-256, cabeceras cifradas y volúmenes compatibles con FAT32,
contraseña introducida por el propietario en GUI. Probar, extraer en destino
nuevo con ACL restrictivas y comparar inventario interno/SHA-256 y UUID.
Registrar externamente sólo hashes/metadatos de los volúmenes cifrados.
Custodiar contraseñas separadamente del dispositivo. No guardar tokens efímeros.
Una restauración de la copia privada actual recupera durable_acknowledged=false:
recomprobar evidencia de respaldo y renovar aprobación humana antes de activación;
nunca cambiar automáticamente el marker ni reutilizar recibos de sesión.
Este procedimiento no se ejecutó nuevamente en la presente iteración.
## 4. Cambio exacto del marker
Única sustitución de bytes: "durable_acknowledged":false por true.
Conservados UUID, campos, orden y demás contenido.
Escritura de temporal nuevo en el mismo directorio, FileStream exclusivo,
Flush(true), sustitución atómica File.Replace y verificación inmediata.
Incidencia local: primer File.Replace con $null recibió ruta vacía por conversión
PowerShell y falló ANTES de cambiar el marker. Temporal eliminado.
Se corrigió sólo el argumento nulo a [NullString]::Value: sustitución satisfactoria.
No hubo marker parcialmente escrito ni cambios de código del contrato.
SHA-256 nuevo marker:
d6ae18b5b34359b9e08c207648ef5b4c94dc6d7176177e3b5689ce3364910dd6.
## 5. ACL
SDDL de los seis objetos (raíz, marker, cuatro directorios) comparados antes y
después de la sustitución: idénticos. Sin cambios de permisos.
Política existente owner-system-administrators-v1 satisfecha.
Fingerprint preflight antes/después de Docker:
93b94ee2ce42bd7f21afd8b8ca042f282ab23b413fdee15b4d95c88acb1279cd.
## 6. Preflight Windows
Test-WordlePrivateStore.ps1 con StorePath real, UUID explícito,
StorageApproved y BackupProcedureReference hacia informe BACKUP-RECOVERY-03.
PASS: ruta NTFS canónica, sin redirecciones, propietario, ACL, UUID, marker
aprobado y estructura. fixture_only=false. Repetido tras Docker: mismo PASS
y hashes de marker/ACL iguales.
## 7. Docker real
Invoke-WordleRunner.ps1 -Action Validate, StorePath real y UUID existente,
StorageApproved y referencia al respaldo; configuración temporal externa sin
secretos (sólo ruta y UUID), eliminada en finally.
Exit 0. Runtime: mode=validate, registered=false, UID=10001,
store_validated=true, store_model=windows-supervised, store_present=true.
Procedimiento vigente verificó Compose, bind real y recibo Windows independiente
RO, sin modificar contrato ni recurrir a fixtures.
Permisos Linux expuestos 0777 por Docker Desktop: aceptados sólo bajo el modelo
supervisado existente y preflight NTFS; no se relajó el modo POSIX.
No se ejecutaron operaciones Terraform: el validador sólo consultó versiones
de herramientas dentro del contenedor, no init/plan/apply/destroy.
## 8. Runner
NOT REGISTERED. Sin token ni modo activate. Contenedor propio
wordle-runner-supervised-caefee2f60df41b6ba7ddd4d8f3ab6ae terminó correctamente,
retirado por --rm; consulta exacta no encontró remanente.
Sin contenedor wordle-actions-runner-session ni Runner.Listener en Windows.
No se intervinieron contenedores ajenos.
## 9. Recuperación humana
NOT VERIFIED. Pendientes: TargetFile real, VariablesFile real, WorkDirectory
definitivo, backend correspondiente y verificación de acceso humano Azure.
No se prepararon inputs nuevos ni se inició autenticación.
## 10. Git
Inicial: rama codex/pg01-07-consolidation,
HEAD 4d56cf265cc5f0af8c72c64f2a93373660e8f122,
nueve modificados, 313 sin seguimiento, índice vacío.
Única incorporación al repo: este informe. Final: nueve modificados,
314 sin seguimiento, índice vacío, mismo HEAD/rama.
Sin staging, commit, push, cambio de rama ni operaciones remotas.
## 11. OneDrive
Repositorio original no utilizado ni modificado. Informes históricos preservados.
## 12. GO/NO-GO
Durabilidad APPROVED por decisión humana explícita.
Almacén real PASS. Recuperación humana NOT VERIFIED.
Runner NOT REGISTERED; registro sigue sin autorización.
CD/AKS NO-GO. Ninguna operación Azure ni ejecución de workflows.
## 13. Próximo paso mínimo
Revisar los inputs y el procedimiento independiente de recuperación humana en
una iteración autorizada separada. No registrar runner ni activar CD como
consecuencia automática de aprobar el almacenamiento.
