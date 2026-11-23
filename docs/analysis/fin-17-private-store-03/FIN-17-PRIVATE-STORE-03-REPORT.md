# FIN-17-PRIVATE-STORE-03 — 23/11/2026
## 1. Estado inicial
Rama codex/pg01-07-consolidation, HEAD 4d56cf265cc5f0af8c72c64f2a93373660e8f122.
Índice vacío; nueve archivos versionados modificados y 309 sin seguimiento.
private/recovery/backups existentes pero vacíos. Sin reparse points en las cuatro
rutas aprobadas. Propietario actual; ACL heredadas amplias incompatibles con preflight.
## 2. Workspace verificado
Todas las operaciones del proyecto desde C:/WordleTFG/repo.
No se utilizó ni modificó el origen OneDrive.
## 3. Identidad y estructura
Almacén C:/WordleTFG/private.
UUID generado una sola vez: 7f280685-26af-424e-b805-acd32a980a45.
Marker .wordle-private-store.json, contrato exacto format=1,
repository=lromerob/wordle, store_id anterior, durable_acknowledged=false.
Directorios plans, selections, evidence, backups vacíos; ningún input privado.
## 4. ACL
Sólo se cambió la ACL del private vacío: herencia desactivada y FullControl
para propietario Windows actual, SYSTEM y Administrators; descendientes heredan.
Preflight contractual atraviesa PATH, IDENTITY y ACL y se detiene en MARKER.
Esto verifica política conservadora existente, no aislamiento frente a administradores.
No se modificaron ACL de repo, OneDrive, recovery, backups ni otras rutas.
## 5. Respaldo
C:/WordleTFG/backups/README.md documenta copia autorizada por inventario,
exclusión de tokens, hashes SHA-256 y restauración a destino nuevo protegido.
No se hizo copia del almacén real. Una copia en C: NO protege del fallo del disco C:.
Destino independiente, custodia y retención siguen pendientes.
## 6. Restauración sintética
C:/WordleTFG/backups/test-synthetic-backup.py ejecutado con Python de .venv.
PASS: dos archivos sintéticos, snapshot SHA-256 idéntico en origen/copia/restauración,
UUID y marker idénticos, cuatro subdirectorios preservados, lista exacta igual.
TemporaryDirectory eliminó exclusivamente sus temporales; no quedan fixtures.
No acredita recuperación de secretos reales, ACL restauradas ni servicios Azure.
## 7. Recuperación humana
C:/WordleTFG/recovery/README.md y directorios inputs/workspace vacíos preparados.
Contrato leído en infra/scripts/Invoke-AksEmergencyTeardown.ps1:
TargetFile externo existente, trece claves exactas y objetivo Wordle;
WorkDirectory externo existente, backend independiente y metadatos coherentes;
VariablesFile explícito para retirada, sujeto al procedimiento vigente.
target.json y variables.json NO creados; workspace sin inicializar.
Secuencia humana documentada independiente de Actions/Docker/OIDC.
No se invocó el script contra Azure. Recuperación real NOT VERIFIED.
## 8. Herramientas
PowerShell 7.6.9; Python .venv 3.12.14; Docker Engine Linux 29.9.2;
Compose 5.6.1; kubectl cliente 1.36.1.
Terraform 1.9.8 ejecutable:
<USER_HOME>/AppData/Local/WordleTFG/tools/terraform-1.9.8/terraform.exe
kubelogin v0.2.22 ejecutable:
<USER_HOME>/AppData/Local/WordleTFG/tools/kubelogin-0.2.22/bin/windows_amd64/kubelogin.exe
Invocación absoluta, sin modificar PATH. CHECKPOINT_DISABLE sólo en proceso.
El sandbox redirige LOCALAPPDATA: se usó la ruta documentada real.
Azure CLI presente, pero az version local en sandbox no completó por permiso
de escritura sobre az.sess; no se elevó ese comando ni se consultó sesión/token.
La imagen sintética sí acredita Azure CLI Linux 2.86.0, no la versión del host.
## 9. Docker
Test-WordleSupervisedStore.ps1 -RunDocker: 30 comprobaciones aprobadas.
Runtime validate, UID 10001, windows-supervised-test, registered=false.
Verifica ACL/UUID/estructura/configuración, binds, recibo separado RO,
negativas sin recibo y recibo falso, rechazo antes de activación y parada limpia.
Se reutilizó imagen wordle-actions-runner:fin17-private-store-02.
Almacén real: preflight BLOCKED en MARKER; launcher Validate exit 2, esperado,
antes de crear contenedor. Su salida es genérica por diseño: etapa verificada
separadamente. Una primera aserción de diagnóstico esperaba erróneamente
MARKER en esa salida; corregida sólo la comprobación, sin cambiar código.
Configuración temporal sin secretos eliminada. Recursos propios del harness limpiados.
## 10. Limitaciones
Durabilidad false no se elevó. Fixtures no sustituyen aprobación humana ni
restauración real. recovery/backups mantienen ACL heredadas: no guardar secretos
allí sin protección específica aprobada. El procedimiento de copia requiere
inventario explícito para excluir tokens; no es un backup automático de producción.
## 11. Decisiones pendientes
Aprobar destino independiente, custodia, retención y prueba de restauración real.
Aportar TargetFile, VariablesFile y backend/workspace humanos aprobados y protegidos.
Aprobar durabilidad sólo con evidencias y autorización posterior expresa.
## 12. GO/NO-GO
Preparación local PASS.
Durabilidad real NOT APPROVED.
Recuperación humana real NOT VERIFIED.
Registro runner NO-GO. CD/AKS NO-GO.
## 13. Git
Sin staging/commit/push/cambio de rama. Cambios previos preservados.
Único nuevo archivo del repo: este informe. Nueve versionados modificados,
310 sin seguimiento, índice vacío; HEAD inalterado. Sin edición de aplicación,
workflow ni configuración de infraestructura.
## 14. Próximo paso mínimo
Confirmar destino independiente y entradas humanas aprobadas; después autorizar
una iteración específica de custodia/restauración. No registrar runner ni operar
Azure en esta iteración.

> Rutas personales normalizadas editorialmente para publicación. Resultados, fechas, hashes y entorno histórico no cambian. <USER_HOME> designa el directorio personal original; variables PowerShell se resuelven para el usuario que reproduce. <LEGACY_REPO_ROOT> identifica el origen histórico, no el workspace vigente.
