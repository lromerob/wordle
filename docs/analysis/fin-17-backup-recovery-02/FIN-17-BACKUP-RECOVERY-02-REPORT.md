# FIN-17-BACKUP-RECOVERY-02 — 23/11/2026
## 1. 7-Zip
Instalado 7-Zip 26.06 x64 en C:/WordleTFG/tools/7-Zip, instalador exit 0,
UAC aprobado por el propietario. Ejecutable local comprobado; sin cambio PATH
solicitado. Instalador oficial:
https://github.com/ip7z/7zip/releases/download/26.06/7z2606-x64.exe
La página https://www.7-zip.org/download.html enlaza ese recurso.
Authenticode NotSigned; autenticidad verificada mediante digest de la release
oficial https://api.github.com/repos/ip7z/7zip/releases/tags/26.06.
SHA-256 instalador: 9b697f65ecc2d9b0152f5ee96d72dde522a7827690349d9307935dacf40f42ec.
No se usó una suma calculada localmente como única prueba de autenticidad.
## 2. Disco
D: FAT32, etiqueta Backup, WD My Passport USB, disco físico 1, partición 2,
distinto de C: disco 0 NVMe. Volumen:
\?\Volume{c26d0a77-41e1-45a7-9c0d-529d372ff138}\.
Libres 1.830.235.832.320 bytes. Identidad reconfirmada antes de escribir.
Destino D:/WordleTFG-Backup inexistente al inicio; creado nuevo, sin sobrescrituras.
## 3. Inventario
Staging protegido con ACL owner/SYSTEM/Administrators antes de copiar bytes.
Repositorio completo: 9.930 archivos, 450.805.895 bytes, 1.482 directorios.
Almacén: un archivo de 122 bytes, cuatro directorios.
Inventarios privados con rutas/tamaños/SHA-256 se mantuvieron en zona protegida
y se incluyeron como inventory.json dentro del contenido a cifrar.
Se comparó staging y origen antes de comprimir y se volvió a comprobar el
origen tras el fallo: todos los hashes y estructura permanecían iguales.
## 4. Exclusiones
Ninguna: incluye .git, ignorados, .venv, pendientes y evidencias. No se abrieron
contenidos de .env ni metadatos Terraform para mostrarlos.
Sin nombres de archivos de token/sesión/credential/approval/kubeconfig detectados
en archivos operativos fuera de dependencias/.git; no equivale a auditoría de secretos.
## 5. Cifrado
Comando de creación 7z a -t7z -m0=lzma2 -mx=1 -mhe=on -p -v1900m -bb0.
Se solicitó contraseña exclusivamente mediante prompts nativos de 7-Zip en
ventana local, nunca como argumento, entorno, archivo ni log del agente.
Configuración solicita AES-256 y cifrado de cabeceras/nombres; no se declara
verificada la recuperabilidad mientras no termine prueba y extracción.
No se generó ni almacenó contraseña. El propietario debe custodiarla.
## 6. Volúmenes
Único archivo externo observado: repo.7z.001, 107.793.796 bytes.
SHA-256: be2082236ee0cf0ead4be3d89f1f8cfaf3b7b2370240f0e762aa00c77eef7984.
No existe private.7z.001. Sin sobrescribir ni eliminar el volumen existente.
Manifest externo manifests/partial-verification.json contiene sólo metadatos
no sensibles y hash del volumen, sin inventario de rutas privadas.
## 7. Integridad
NOT VERIFIED para el archivo 7z. El flujo interactivo indicó fallo antes de
crear el destino de extracción. La reanudación conservó el archivo e intentó
verificarlo sin reescribir; también se detuvo antes de extracción.
No se dispone aún del mensaje de error de la ventana para determinar la causa.
Se solicitó al propietario únicamente la línea de error, nunca la contraseña.
El usuario indicó inicialmente PASS, pero no coincide con la evidencia de disco;
prima la evidencia: sin result.json ni manifiesto de verificación satisfactoria.
Una consulta sin contraseña y stdin cerrado terminó exit 255, sin nombres
internos mostrados; no se usa ese resultado como prueba de integridad/cifrado.
## 8. Restauración
NOT VERIFIED. No existen directorios restore-repo/restore-private ni comparación
de un repositorio restaurado. No se ejecutó fsck sobre una copia restaurada.
El hash del volumen por sí solo no acredita descifrado, contraseña ni restauración.
## 9. Almacén
UUID 7f280685-26af-424e-b805-acd32a980a45.
Marker durable_acknowledged=false conservado byte a byte; estructura intacta.
No se alteraron ACL ni se crearon inputs privados reales.
## 10. Recuperación humana
Contrato revisado de infra/scripts/Invoke-AksEmergencyTeardown.ps1 y
C:/WordleTFG/recovery/README.md. Faltan TargetFile, VariablesFile y workspace
Terraform con configuración/backend coherentes y aprobados.
No inventar IDs ni trasladar planes Linux como planes Windows.
Futuro: identificar disco por GUID, comprobar hashes externos, probar y extraer
con contraseña mediante prompt a destino nuevo con ACL restrictivas; comparar
inventario interno y verificar .git/UUID/marker antes de utilizar cualquier archivo.
Nunca restaurar directamente sobre origen. No reutilizar recibos ni tokens.
Retirada humana Azure NOT VERIFIED; no se invocó Terraform ni Azure.
## 11. Git
Rama codex/pg01-07-consolidation; HEAD
4d56cf265cc5f0af8c72c64f2a93373660e8f122.
Inicial 9 modificados, 311 sin seguimiento, índice vacío.
Antes de crear este informe, estado Git y todos los bytes del origen iguales
al inventario inicial. Este informe es el único archivo añadido al repositorio.
Sin staging, commit, push, cambio de rama ni operaciones remotas Git.
El informe posterior no forma parte del volumen ya creado.
## 12. OneDrive
No utilizado ni modificado. Sin borrados, movimientos ni cambios de sincronización.
## 13. GO/NO-GO
PARTIAL: existe un volumen externo, pero respaldo privado y restauración pendientes.
Durabilidad NOT APPROVED; recuperación humana real NOT VERIFIED.
Runner NO-GO. CD/AKS NO-GO. Sin GitHub Actions ni operaciones Azure.
## 14. Próximo paso mínimo
Obtener el error de la ventana local y resolver únicamente esa causa.
Si la contraseña no permite verificar el archivo existente, conservarlo y
solicitar decisión antes de otro destino; nunca sobrescribir ni adivinar contraseñas.
Completar ambas pruebas 7z, extracción y comparación SHA-256 antes de PASS.

### Resultado final y limpieza
El propietario confirma que ambas ventanas están cerradas y no dispone del
mensaje de error. No se atribuye el fallo a una contraseña incorrecta sin prueba.
Staging protegido, inventarios privados y scripts temporales propios eliminados
tras verificar hashes del origen y ausencia de procesos 7z activos. Instalador
temporal eliminado tras verificar su hash; instalación funcional conservada.
No se borró ni alteró repo.7z.001. Ningún temporal era la única copia del origen.
Git final: 9 versionados modificados, 312 sin seguimiento, índice vacío.
Para continuar será necesaria una nueva interacción local observada o una
operación manual de Test en la interfaz de 7-Zip sobre el archivo conservado;
no hay evidencia suficiente para declarar una restauración satisfactoria.
