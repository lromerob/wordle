# FIN-AKS-EMERGENCY-PREFLIGHT-LIVE-RETRY — 17/11/2026

## 1. Resumen ejecutivo

**PASS del preflight real de lectura.** Una ejecución corregida terminó exit 0:
Azure CLI invocado correctamente, contexto aprobado, backend accesible,
**0 recursos gestionados** y resultado CLEAN sin plan ni destrucción.
Lecturas Azure independientes: cero recursos en los RG destino, ambos RG ausentes
y AKS objetivo ausente. Blob idéntico antes/después; lease unlocked/available.
Esto valida el preflight autónomo, **no la retirada completa de un AKS real**.
Gate A GO; Gate B GO; AKS NO-GO.

## 2. Autorización y límites

Inspección selectiva, identidad/propiedades/inventarios de lectura, versiones,
un único -Preflight y este informe. Sin modificar código/pruebas/documentación
histórica o Terraform. Sin -Teardown ni respuestas a confirmaciones destructivas.
No init/plan/apply/destroy/refresh/force-unlock/state pull o lease deliberado.

## 3. Estado de la corrección

Script real contiene Resolve-WordleAzureCli con CommandType Application,
Source absoluto/existente y wrapper Invoke-WordleAzureCli.
No antigua función Az ni invocaciones ambiguas. Errores Native conservan exit
y salida sensible suprimida. Rama Destroy=false retorna antes de Consent,
validate, plan o apply; State/Inventory/Backend/Clean solo invocan lecturas.
Corresponde a la corrección con 38 pruebas offline anteriores; no se repiten suites.
Revisados script, manual, runbook, informe LIVE anterior, AZ-RESOLUTION-FIX
y suite nueva de regresión. Históricos no alterados.

## 4. Verificación de Azure CLI

Resolución local real: Application az.cmd de la instalación oficial
Microsoft SDKs/Azure/CLI2/wbin, ruta absoluta con espacios.
Invocación desde el wrapper por ruta resuelta, no función/alias.
Las comprobaciones Context/Backend superadas en el script acreditan llamadas
reales correctas a CLI; no solo un test de descubrimiento.
Inspección posterior de resolver local confirma az.cmd; no ejecuta otro preflight.

## 5. Herramientas y versiones

Terraform **1.9.8** y proveedor **4.50.0** comprobados dentro del modo seguro:
este rechaza versiones distintas antes de Context.
Azure CLI **2.86.0**, consultada independientemente en lectura local.
Windows PowerShell **5.1.26100.9818**.
Ejecución -NoProfile y -ExecutionPolicy Bypass solo del proceso, según manual.
Sin política persistente, PATH global, instalación o actualización.
Una consulta auxiliar local de versión/resolución tuvo error de quoting del
invocador; se corrigió únicamente la llamada local, no el script productivo.
No segundo preflight ni acción cloud adicional por ese error.

## 6. Identidad, tenant y suscripción

Lecturas account show y Graph signed-in-user previas coinciden exactamente con
suscripción 11306565…1bb5, tenant aff0390f…1eb9 y humano b573130a…a831;
user/Enabled. El script repite y supera esas comprobaciones.
IDs completos usados internamente según configuración/informes, sanitizados aquí.
Sin login, cambio de suscripción, nueva identidad o tokens consultados/imprimidos.
Preflight previo completado 11:07:47 UTC.

## 7. Backend remoto

rg-wordle-state / stwordletfgstate7c92d4 / tfstate /
wordle/aks-demo.tfstate. Metadatos locales del backend verificados por el script,
use_azuread_auth=true, tenant/subscription aprobados.
Lecturas del script verifican RG, cuenta, contenedor y Blob con auth-mode login;
sin claves/SAS, nuevos keys o contenido completo del estado exportado.
Lecturas independientes de blob show antes/después confirman acceso al key.

## 8. Estado inicial del lease

11:07:47 UTC: leaseStatus unlocked, leaseState available, duration null.
Sin terraformlockid ni bloqueo inesperado. No se adquiere/libera lease manual.

## 9. Atributos iniciales del blob

contentLength=180 bytes, lastModified=17/11/2026 08:53:57 UTC.
ETag/contentMD5/hash de metadatos capturados en memoria para comparación exacta.
No contenido completo del estado ni secretos guardados como evidencia.

## 10. Ejecución del preflight

Una sola ejecución:
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File infra/scripts/Invoke-AksEmergencyTeardown.ps1 -Preflight

Inicio 11:08:01.882 UTC; fin 11:08:34.395 UTC.
stdin cerrado; sin introducción de frase de confirmación.
Salida sanitaria:
    WORDLE TFG - PREFLIGHT
    Tenant y suscripcion aprobados; backend aprobado OK.
    Recursos gestionados: 0
    CLEAN. No se genera plan ni se destruye.

No Start-Emergency adicional ni -Teardown.

## 11. Código de salida

**0**, stderr vacío.
No se concluye PASS solo por exit: consola, eventos de fases, condiciones del
código auditado y lecturas posteriores aportan evidencia complementaria.

## 12. Inventario Terraform

**0 recursos gestionados consultados realmente** mediante State del script,
que invoca terraform state list.
Para emitir el resumen y evento preflight/VERIFIED, State e Inventory deben
haber terminado correctamente. Estado vacío activa Clean, que repite State y
Backend y consulta inventarios; retorna CLEAN solo si todos son conformes.
No error interpretado como lista vacía, no descarga completa ni state pull.
No se ejecutó state list manual fuera de ese mecanismo.

## 13. Verificación posterior

11:09:13 UTC, mediante CLI oficial independiente:
- Blob aprobado sigue accesible.
- resource list de suscripción, filtrado en memoria a ambos RG: 0 recursos.
- group list: rg-wordle-academic y rg-wordle-academic-nodes ausentes.
- aks list: aks-wordle-academic en RG objetivo ausente.
- Log generado sin plan binario y proceso del preflight finalizado.

Inventario Azure coherente con inventario Terraform vacío.
Sin comandos de escritura en el flujo auditado/ejecutado. No se afirma auditoría
universal de todas las acciones concurrentes Azure o de recursos fuera de alcance.

## 14. Estado final del lease

unlocked/available, duration null, sin metadatos de bloqueo.
No unlock automático, fuerza o cambios de backend.

## 15. Comparación de atributos del blob

| Propiedad | Antes/después | Resultado |
| --- | --- | --- |
| Tamaño | 180 / 180 bytes | Idéntico |
| ETag | Comparado exactamente en memoria | Idéntico |
| lastModified | 08:53:57 / 08:53:57 UTC | Idéntico |
| contentMD5 | Comparado exactamente | Idéntico |
| Metadatos | Hash idéntico, sin lock | Idénticos |
| Lease | unlocked/available / igual | Libre |

No cambio inesperado observado. Comparación de propiedades, no conservación de
estado completo ni certificación global de todos los recursos de la cuenta.

## 16. Logs y sanitización

Log local nuevo fuera de Git:
%LOCALAPPDATA%/WordleTFG/emergency/6274ad7551d5435c890bd3b9b2578d05/audit.jsonl.
Tres eventos:
- 11:08:02.379 UTC start / STARTED.
- 11:08:18.703 UTC preflight / VERIFIED.
- 11:08:34.372 UTC finish / CLEAN.

Solo campos utc/mode/event/result; modo PREFLIGHT. Sin tokens/credenciales/claves,
datos de plan/estado o IPv4 doméstica. No destroy.tfplan generado.
El log es agregado: no tiene eventos independientes para cada subconsulta de
resolución, identidad, backend e inventario. La fase VERIFIED y CLEAN se interpretan
junto al código auditado y consola; no se inventan eventos de detalle inexistentes.
Ningún log publicado ni añadido a Git.

## 17. Independencia de IA

Validado: PowerShell convencional, herramientas locales, CLI externa,
acceso Azure real, lectura del backend y consulta del inventario.
El script no invoca Codex/ChatGPT/API de modelos ni requiere generación dinámica
de comandos. Puede ejecutarse desde su manual local sin historial del chat.
La intervención del asistente en esta prueba no es dependencia técnica runtime.

## 18. Limitaciones

NO validado aquí: plan de destrucción, eliminación de AKS, huérfanos,
recuperación ante desconexión/MFA o retirada con create parcial.
Estado actual vacío no permite demostrar esas rutas reales.
38 pruebas offline anteriores conservan valor simulado, no reemplazan Azure.
Logs agregados suficientes con evidencia complementaria para este ensayo;
no se presentan como traza completa de red o diagnóstico granular.
No cambios del mecanismo para obtener PASS.

## 19. Riesgos residuales

Sesión/Policy/RBAC/IP/red/capacidad pueden variar antes de la ventana.
Preflight PASS no demuestra permiso o éxito futuro de destroy ni garantiza
ausencia de cargos devengados. Backend/retenciones pueden tener coste propio.
La revisión humana del inventario y autorizaciones CREATE/DESTROY siguen siendo
obligatorias; no eliminación automática de huérfanos o recursos ajenos.

## 20. Integridad Git

80 pendientes preexistentes registrados por SHA-256; HEAD
4d56cf265cc5f0af8c72c64f2a93373660e8f122 e índice vacío inicial.
Solo este informe nuevo en repo y el log runtime externo.
Verificación final: los 80 pendientes están idénticos por SHA-256, igual que
Terraform/lock/proveedor/caché/metadatos locales. HEAD intacto e índice vacío;
81 pendientes finales con solo este informe nuevo. git diff --check exit 0.
Advertencias LF/CRLF preexistentes: informe FIN-04, plan FIN y observability/
run_observability.py y validation.py, sin corregir.
Sin staging, limpieza, commits o push; ninguna corrección de código/pruebas.

## 21. Recomendación para la ventana del viernes

Viernes **20/11/2026** continúa como objetivo condicionado, no permiso.
El bloqueo de descubrimiento CLI queda superado para preflight real.
Propietario puede continuar la preparación operativa: fijar hora, revalidar
condiciones vigentes, revisar plan privado guardado y autorizar separadamente
creación/cargas/retirada según runbook. No iniciar ahora esas fases.
No presentar la retirada de emergencia como validada de extremo a extremo.

## 22. Estado de Gate A, Gate B y AKS

**Gate A GO; Gate B GO; AKS NO-GO.**
Sin -Teardown, init, plan, apply, destroy, refresh, force-unlock o state pull.
Sin modificaciones Azure/Entra/Policy/RBAC/firewall/backend/estado remoto;
sin lock modificado, commits o push.
Detenerse y esperar instrucciones.
