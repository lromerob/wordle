# FIN-17-BACKUP-RECOVERY-03 — 23/11/2026
## 1. Estado inicial
Workspace C:/WordleTFG/repo. Rama codex/pg01-07-consolidation,
HEAD 4d56cf265cc5f0af8c72c64f2a93373660e8f122.
Índice vacío; nueve versionados modificados y 312 sin seguimiento.
7-Zip 26.06 existente en C:/WordleTFG/tools/7-Zip, sin nuevas instalaciones.
## 2. Diagnóstico del repositorio
D: reconfirmado como disco físico 1 USB WD My Passport, distinto de C: disco 0.
FAT32; volumen \?\Volume{c26d0a77-41e1-45a7-9c0d-529d372ff138}\.
Espacio libre inicial 1.830.127.927.296 bytes.
repo.7z.001 conserva 107.793.796 bytes y SHA-256
be2082236ee0cf0ead4be3d89f1f8cfaf3b7b2370240f0e762aa00c77eef7984.
Único volumen repo: no faltan .002/.003 para este archivo.
Firma 7z, CRC de start header y next header válidos; next header completo,
codificado y con identificador AES. Reconocido y procesado por 7-Zip.
No se modificó ni reconstruyó el archivo existente.
## 3. Test del repositorio
7zG.exe t D:/WordleTFG-Backup/repo.7z.001.
Contraseña introducida por propietario en diálogo gráfico nativo.
Código de salida 0: Test completo satisfactorio, sin errores CRC.
## 4. Restauración del repositorio
7zG.exe x sobre el mismo archivo, con -o hacia directorio nuevo protegido
fuera del checkout. Código de salida 0.
Restaurados repo e inventory.json interno. Lista exacta de archivos, directorios,
tamaños y SHA-256 comparada contra ese inventario: 9.930 archivos coincidentes.
No se excluyó ningún archivo en la copia original.
Inventario contemporáneo incluido en el archivo previamente creado; no se inventó
un inventario histórico a partir del origen actual.
Todos los archivos históricos también coinciden con el origen actual.
Única adición posterior detectada antes de este informe:
docs/analysis/fin-17-backup-recovery-02/FIN-17-BACKUP-RECOVERY-02-REPORT.md.
Este informe 03 tampoco pertenece al respaldo histórico.
## 5. Git restaurado
git fsck --full --no-reflogs: exit 0.
Rama y HEAD coinciden con los iniciales. Índice vacío.
Nueve modificados y 311 sin seguimiento, como en el instante de aquella copia.
La diferencia de un informe posterior está explicada, no es corrupción.
Sin cambios de configuración Git ni operaciones remotas.
## 6. Respaldo privado
Creado NUEVO private.7z.001 sólo después del Test y verificación del repositorio.
Origen exacto: marker más backups/evidence/plans/selections vacíos.
Sin datos ficticios ni tokens. Staging nuevo con ACL restrictivas
owner Windows actual/SYSTEM/Administrators antes de copiar.
Comando gráfico: 7zG a -t7z -m0=lzma2 -mx=1 -mhe=on -p -v1900m
D:/WordleTFG-Backup/private.7z private inventory.json, desde staging protegido.
Contraseña solicitada en interfaz gráfica, jamás incluida en argumentos.
Creación exit 0; AES-256, nombres/cabecera cifrados.
No existía archivo privado y no se sobrescribió ninguno.
## 7. Test privado
7zG t D:/WordleTFG-Backup/private.7z.001: exit 0.
Propietario confirmó Test sin errores. Sin errores CRC.
## 8. Restauración privada
7zG x hacia otro directorio NUEVO protegido: exit 0.
Contenido raíz exacto private + inventory.json.
Lista, estructura, tamaños y SHA-256 coinciden entre inventario interno,
staging, restauración y almacén original: un archivo y cuatro directorios.
## 9. UUID y marker
UUID 7f280685-26af-424e-b805-acd32a980a45.
Marker exacto format=1, repository=lromerob/wordle,
store_id anterior, durable_acknowledged=false. Bytes intactos.
No se cambiaron ACL del almacén real ni se emitió aprobación humana.
## 10. Errores
Ningún error en las cinco operaciones gráficas de esta iteración: códigos 0.
El fallo genérico CLI de la iteración 02 no se atribuye a contraseña incorrecta:
su causa exacta no quedó conservada y no puede reconstruirse retrospectivamente.
El archivo era utilizable y pasó Test/extracción mediante GUI.
Ventanas de error no cerradas automáticamente. El proceso padre esperó cada
operación y recogió su exit code antes de continuar.
El propietario introdujo contraseñas varias veces por ser operaciones distintas;
no se almacenaron ni registraron. No se capturaron pantallas de esos diálogos.
## 11. D: final
repo.7z.001: 107.793.796 bytes, SHA-256
be2082236ee0cf0ead4be3d89f1f8cfaf3b7b2370240f0e762aa00c77eef7984.
private.7z.001: 607 bytes, SHA-256
3947a51882645ea4819546e9f331cb6b345f07c35afc42aedb13c358083c50b7.
Dos archivos/volúmenes totales; ambos menores de 1.900 MiB y compatibles FAT32.
manifests/verification-03.json registra resultados y hashes cifrados sin
inventarios privados. Se conserva el manifest parcial previo como evidencia histórica.
AES presente en ambas cabeceras codificadas, CRC válidos y restauraciones reales.
## 12. Limitaciones
Respaldo de archivos, no prueba de recuperación Azure ni de servicios.
FAT32 no conserva ACL: toda extracción futura debe hacerse a un destino protegido,
aplicar/verificar permisos y comparar hashes antes de usarlo.
No se respaldó recovery/backups completos ni se añadieron inputs humanos.
No se actualizó la copia histórica para incluir informes posteriores.
## 13. Git activo
Única incorporación al repo: este informe. Versionados previos preservados.
Índice vacío, HEAD/rama sin cambio, nueve modificados y 313 sin seguimiento.
Sin staging, commit, push ni modificaciones de código o infraestructura.
## 14. OneDrive
No utilizado, alterado, movido ni eliminado.
## 15. Resultado
PASS técnico: ambos respaldos descifrados, probados y restaurados; contenido
íntegro, Git verificado y marker preservado. Durabilidad NOT APPROVED.
Runner NO-GO. CD/AKS NO-GO. Sin Azure, Terraform, Actions ni registro.
## 16. Decisiones pendientes
El propietario debe custodiar las contraseñas separadamente del disco externo
y aprobar expresamente la durabilidad; esta iteración NO cambia el marker.
No iniciar ninguna activación automáticamente.
Para repetir Test/restauración usar la GUI de 7-Zip sobre .001, verificar el
volumen físico por su GUID y hashes externos, extraer en destino nuevo protegido,
comparar inventory.json y conservar errores visibles si falla.

### Limpieza confirmada
Directorio temporal propio, staging, inventarios privados y ambas restauraciones
descifradas eliminados tras confirmar respaldos verificados y ausencia de procesos
7zG activos. No se eliminaron archivos de origen ni del disco externo.
Verificación final de hashes de todos los archivos previos no ignorados: sin cambios.
