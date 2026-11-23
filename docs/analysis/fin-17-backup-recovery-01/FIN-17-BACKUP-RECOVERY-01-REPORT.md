# FIN-17-BACKUP-RECOVERY-01 — 23/11/2026
## 1. Resumen ejecutivo
BLOCKED: disco independiente confirmado, pero protección de datos no acreditada.
No se inició la copia del repositorio ni del almacén. No se escribió en D:.
No se omiten silenciosamente archivos privados para aparentar respaldo completo.
## 2. Identificación de D:
Consultas locales Get-Volume, Get-Partition y Get-Disk:
D: etiqueta Backup, FAT32, unidad Fixed, disco 1, partición 2,
WD My Passport 0748, bus USB. C: corresponde al disco 0 NVMe.
Volumen D: \?\Volume{c26d0a77-41e1-45a7-9c0d-529d372ff138}\.
Capacidad 1.999.533.080.576 bytes; libres 1.830.235.832.320 bytes al consultar.
Raíz Directory sin atributo ReparsePoint; accesos de partición D: y GUID,
sin carpeta montada en C:. Independencia física confirmada.
D:/WordleTFG-Backup no existe. No se buscó indiscriminadamente en otros
directorios del disco: existencia de otras copias Wordle no verificada.
## 3. Cifrado y protección
Get-BitLockerVolume no acreditó cifrado: aviso de ausencia de volumen BitLocker
asociado y error CIM de acceso denegado. No demuestra ausencia de cifrado
hardware u otra protección; ésta permanece NOT VERIFIED.
FAT32 no proporciona la política ACL NTFS del almacén.
No se activó cifrado ni se modificó el disco.
## 4. Estructura del respaldo
Destino autorizado D:/WordleTFG-Backup con repo/private/manifests, NO creado.
La ausencia del destino se verificó antes de cualquier copia.
## 5. Copiados y excluidos
Cero archivos copiados. No existe respaldo parcial que se declare completo.
Inspección sólo de nombres ignorados: backend/.env y
infra/terraform/.terraform/terraform.tfstate requieren tratamiento protegido.
No se abrieron sus contenidos ni se afirma que contengan un secreto concreto.
No se copiaron tokens, cachés ni entornos virtuales. La selección definitiva de
exclusiones queda pendiente; .git, cambios y evidencias deben conservarse.
## 6. Manifiestos
No generados, pues no se autorizó transferencia de posibles datos sensibles a
un destino cuya protección no pudo acreditarse.
## 7. Integridad
Copia/hash comparativo no ejecutados; no se declara integridad del respaldo.
Origen sin operaciones de escritura, salvo este nuevo informe autorizado.
## 8. Restauración
No ejecutada: no existe copia real. La prueba sintética anterior no sustituye
lectura/restauración desde D:. Permiso de escritura no probado creando archivos,
al detenerse antes de escribir por el bloqueo de protección.
## 9. Almacén
C:/WordleTFG/private conserva marker y UUID
7f280685-26af-424e-b805-acd32a980a45; durable_acknowledged=false.
Sólo marker y cuatro directorios contractuales, sin inputs privados nuevos.
No se modificó su ACL ni se emitió aprobación.
## 10. Recuperación humana
inputs y workspace bajo C:/WordleTFG/recovery continúan vacíos.
Faltan los archivos externos aprobados TargetFile (target.json) y VariablesFile
(variables.json), además del workspace Terraform revisado y su backend coherente.
El contrato existente exige las trece claves exactas de objetivo, contexto
humano autorizado, backend independiente, metadatos de inicialización y controles
de bloqueo. No inventar valores ni reutilizar planes Linux en Windows.
Referencia: infra/scripts/Invoke-AksEmergencyTeardown.ps1 y recovery/README.md.
Herramientas identificadas en FIN-17-PRIVATE-STORE-03. Sin invocar script contra
Azure, sin autenticación ni Terraform init/plan/apply/destroy.
## 11. Riesgos y limitaciones
Protección externa no verificada; FAT32 también limita cada archivo a menos
de 4 GiB y no conserva ACL NTFS. Antes de repetir deben inventariarse tamaños,
enlaces y archivos activos y definirse protección compatible.
No se verificó consistencia durante copia porque ésta no comenzó.
## 12. Decisiones pendientes
El propietario debe identificar y permitir verificar protección existente del
dispositivo, o autorizar en una iteración separada un método de respaldo cifrado
compatible. No basta autorizar la copia en claro: no trasladar secretos sin
protección. No se solicita formatear ni activar cifrado automáticamente.
Posteriormente aportar inputs humanos aprobados y protegidos.
## 13. OneDrive
No leído, modificado, eliminado ni reconfigurado en esta iteración.
## 14. Git
Rama codex/pg01-07-consolidation; HEAD
4d56cf265cc5f0af8c72c64f2a93373660e8f122. Inicial: índice vacío,
9 versionados modificados y 310 sin seguimiento. Único archivo nuevo: este
informe; final esperado 311 sin seguimiento. Sin staging, commit, push,
cambio de rama ni operaciones remotas. Cambios preexistentes preservados.
## 15. GO/NO-GO
Respaldo externo BLOCKED por protección no acreditada.
Durabilidad NOT APPROVED. Recuperación humana real NOT VERIFIED.
Runner NO-GO. CD/AKS NO-GO. Ninguna operación Azure.
## 16. Próximo paso mínimo
Resolver y acreditar la protección del destino externo mediante decisión
humana específica; después repetir inventario/copia/hashes/restauración real,
sin sobrescribir destino alguno y manteniendo el marker false.
