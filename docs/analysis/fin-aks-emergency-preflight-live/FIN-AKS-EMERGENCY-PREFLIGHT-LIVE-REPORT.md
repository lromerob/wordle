# FIN-AKS-EMERGENCY-PREFLIGHT-LIVE — 17/11/2026

## 1. Resumen ejecutivo

**BLOCKED.** Una ejecución real de -Preflight terminó con exit 1 por un defecto
local de descubrimiento de Azure CLI: la función interna Az oculta el comando az.
Get-Command az devuelve Function/Source vacío, que Tools acepta como herramienta.
Native falla al ejecutar & sobre ese valor vacío, antes de consultar identidad
a través del script o inventario Terraform.

Contexto aprobado y backend accesible comprobados por lecturas independientes.
Propiedades del blob idénticas antes/después, lease unlocked/available.
No se corrigió código ni se repitió el preflight. No se certifican cero recursos
actuales mediante el script porque state list no llegó a ejecutarse.
Gate A GO; Gate B GO; AKS NO-GO.

## 2. Autorización y alcance

Solo inspección/validación estática, versiones, lecturas Azure/backend,
una ejecución -Preflight, revisión de logs e informe.
Sin -Teardown ni confirmaciones de plan/destrucción. Sin init, plan, apply,
destroy, force-unlock, import, refresh, state pull o escritura cloud.
El script genera un log local fuera del repo; no es modificación de Azure.
No script/pruebas/configuración corregidos automáticamente.

## 3. Referencias revisadas

Invoke-AksEmergencyTeardown.ps1 y Test-AksEmergencyTeardown.ps1;
manual FIN-AKS-EMERGENCY-TEARDOWN y FIN-AKS-DEPLOYMENT-RUNBOOK;
informes EMERGENCY-TEARDOWN, POST-HARDENING-PLAN y
REMOTE-BACKEND-INITIALIZATION. Contexto y coordenadas recuperados de estas fuentes,
no inferidos de una suscripción seleccionada arbitrariamente.
28 pruebas offline previas son evidencia de mocks, no equivalen a ejecución real.

## 4. Auditoría estática del script

Parser PowerShell: sin errores de sintaxis.
Flujo auditado: entrada -Preflight → Start-Emergency Destroy=false → Tools,
version, Context, Backend, State, Inventory y Clean si vacío.
Si no vacío, retorna antes de cualquier consentimiento/validate/plan/apply.
State solo contiene terraform state list; Clean llama lecturas y Backend.
Native es frontera de procesos, no hay scripts auxiliares de despliegue invocados.
No login/context switch/RBAC/firewall, ni lease de prueba.
Escrituras locales esperadas: directorio GUID y audit.jsonl; finally solo retiraría
un plan propio en ese directorio nuevo si existiera, no borra recursos cloud.

La inspección no encontró ruta destructiva alcanzable con -Preflight.
La colisión del comando se evidenció durante la primera ejecución real:
Tools usa Get-Command az sin filtrar tipo. PowerShell no distingue mayúsculas:
la función Az definida en el mismo archivo es seleccionada antes que az.cmd.
Su propiedad Source está vacía. El fallback a az.cmd no entra porque el objeto
Function existe. Native línea 18 recibe comando inválido.
Get-Command az tras cargar solo definiciones: Name=Az, CommandType=Function,
Source vacío; Get-Command az.cmd -CommandType Application localiza el ejecutable
oficial instalado. Diagnóstico sin modificar funciones/archivo.

## 5. Versiones de herramientas

Lectura independiente de la función Tf con version -json, sin Start-Emergency:
Terraform 1.9.8, selección AzureRM 4.50.0, stdout JSON válido y stderr vacío.
La lectura de versión funciona aislada.
Azure CLI oficial disponible en instalación Microsoft SDKs/Azure/CLI2; las consultas
independientes de identidad/Blob por su intérprete oficial funcionan.
Número de versión CLI no acreditado en esta ejecución: consulta local adicional
falló en entorno restringido; no se inventa versión ni se reinstala.
Ejecución real con powershell.exe de Windows, -NoProfile y excepción
-ExecutionPolicy Bypass solo del proceso, como documenta el manual.
Sin cambiar política de usuario/sistema ni herramientas.

## 6. Identidad Azure

Antes del script: account show y ad signed-in-user show con CLI oficial mediante
-IBm azure.cli, operaciones de lectura. Operador coincide exactamente con
b573130a…a831, tipo user, suscripción Enabled.
No tokens/credenciales expuestos, login o cambio de contexto.
La función Context del script falla antes de invocar Azure por el comando vacío;
no es un rechazo de MFA ni de permisos demostrado.

## 7. Tenant y suscripción

Coincidencia exacta con referencias aprobadas:
tenant aff0390f…1eb9, suscripción 11306565…1bb5.
IDs completos usados en memoria; informe sanitizado.
Consulta inicial completada 17/11/2026 10:34:10 UTC.
No account set ni selección de otra identidad/suscripción.

## 8. Backend remoto

Key aprobado: rg-wordle-state / stwordletfgstate7c92d4 / tfstate /
wordle/aks-demo.tfstate.
storage blob show con auth-mode login y suscripción explícita antes/después:
accesible, 180 bytes. No descarga del contenido, state pull o consulta de secretos.
La lectura exitosa acredita acceso al key; las verificaciones completas del backend
dentro del script no se alcanzaron.
No se adquiere lease ni se edita contenido/metadatos/versiones deliberadamente.

## 9. Estado del lease inicial

10:34:10 UTC: status=unlocked, state=available, duration=null.
Sin terraformlockid; metadatos vacíos según proyección sanitaria.
ETag/lastModified/contentMD5 y hash de metadatos capturados en memoria para comparar,
sin abrir el JSON del estado.

## 10. Ejecución del preflight

Una única ejecución:
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File infra/scripts/Invoke-AksEmergencyTeardown.ps1 -Preflight

Inicio 10:34:29.545 UTC; fin 10:34:30.295 UTC; **exit 1**.
Salida: advertencia VERIFICATION FAILED y ubicación del log; error genérico seguro.
No solicitud de PLAN WORDLE AKS o confirmación destructiva, no respuesta enviada.
stdin cerrado para impedir interacción imprevista.
No reejecución de Start-Emergency ni modo Teardown.

Diagnóstico posterior permitido y acotado: cargar definiciones sin iniciar operación,
aislar solo lectura version y función Context (account show/Graph), y consultar
resolución de comandos. No se recorrió de nuevo el preflight completo.
Context confirma RuntimeException de operador &: se esperaba nombre de comando,
ScriptBlock o CommandInfo, pero recibió objeto/comando inválido.
Causa local identificada; no atribuirla a MFA/Azure Policy.

## 11. Inventario Terraform

**NO CONSULTADO por el preflight real**, debido al fallo anterior.
Última observación histórica: cero recursos gestionados en POST-HARDENING-PLAN.
No se repite state list fuera del mecanismo auditado para fabricar PASS.
No conclusión nueva de inventario vacío o CLEAN.

## 12. Resultado de las comprobaciones

| Control | Resultado real |
| --- | --- |
| Sintaxis y ausencia de ruta destructiva -Preflight | PASS estático |
| Terraform/AzureRM | 1.9.8 / 4.50.0 confirmados mediante lectura independiente |
| Descubrimiento Azure CLI del script | FAIL: función Az seleccionada, Source vacío |
| Identidad/tenant/suscripción | Coinciden por CLI independiente |
| Blob accesible / lease | PASS independiente, antes/después |
| Preflight completo / inventario | FAIL / NO CONSULTADO |
| Confirmación o comando destructivo | No solicitado ni alcanzado |
| Registro sanitizado | Dos eventos sin datos sensibles |
| Independencia funcional de IA | Diseño independiente; preflight real todavía no funcional |

## 13. Estado del lease final

10:35:07 UTC: unlocked/available, duration=null.
Sin bloqueo nuevo ni intervención manual.

## 14. Integridad del backend

Antes/después: mismo ETag, lastModified=08:53:57 UTC, contentLength=180,
contentMD5 idéntico y hash de metadatos idéntico (sin lock).
Esto aporta evidencia de no modificación del blob observado; no auditoría universal
de todos los recursos/operaciones Azure.
Código auditado y ruta de fallo solo emitieron lecturas; no recurso creado/eliminado.
No se afirma igualdad a partir exclusivamente del exit code (que fue 1).
No comparación de contenido completo del estado ni cambio de versiones.

## 15. Logs y sanitización

Nuevo registro local:
%LOCALAPPDATA%/WordleTFG/emergency/c317136b104f408b945f1dbe0d2c26a1/audit.jsonl.
Se conserva fuera de Git, sin publicarlo.
Dos eventos: start/STARTED y failure/VERIFICATION FAILED, modo PREFLIGHT y UTC.
Campos exactos utc/mode/event/result; sin tokens, claves, credenciales, IP doméstica,
estado o datos de plan. No destroy.tfplan presente.
El registro evita exposición pero no identifica la causa exacta por sí solo;
esa limitación diagnóstica se registra, no se cambia el logging ahora.

## 16. Independencia de IA

Archivo PowerShell y herramientas locales, sin llamada Codex/ChatGPT/API de modelos.
No requiere generar comandos mediante IA; manual alternativo disponible localmente.
**No demostrada la operación autónoma completa**, porque el script falla al resolver
Azure CLI. No recomendarlo como única salida operativa hasta corregir/revalidar.
Disponibilidad de Internet, sesión/MFA, permisos y Azure son dependencias distintas.

## 17. Limitaciones

Sin inventario real por script, validación de retirada con recursos o de permisos
de destrucción. Versión Azure CLI no acreditada numéricamente.
Lecturas independientes de identidad/backend no rescatan el resultado del script.
No se corrigió el defecto para obtener PASS en contra de las restricciones.
La prueba offline anterior sustituye Tools y Native, por lo que no cubría el
descubrimiento real y la colisión de función; no invalida sus resultados simulados,
pero muestra una brecha de cobertura que requiere regresión nueva.

## 18. Riesgos residuales

El procedimiento de emergencia no está operativo tal cual: bloqueo previo a la
primera ventana. No comenzar CREATE dependiendo de este script sin corregirlo.
Incluso tras corrección/preflight PASS, MFA/Policy/Internet/backend/cascadas y
retirada con recursos siguen requiriendo control humano y autorización.
Propuesta para una iteración separada: resolver únicamente Application az.cmd/az,
validar Source no vacío, probar descubrimiento con función Az presente y ausencia
del ejecutable sin conectar cloud; repetir luego -Preflight real bajo autorización.
No se implementa esa propuesta ahora ni se cambian permisos/políticas.

## 19. Integridad Git

Rama codex/pg01-07-consolidation; HEAD
4d56cf265cc5f0af8c72c64f2a93373660e8f122; índice vacío inicial.
77 archivos pendientes preexistentes registrados por SHA-256 antes de ejecutar.
Único archivo nuevo en repo: este informe. Log runtime nuevo fuera de Git.
Verificación final: los 77 pendientes preexistentes están intactos por SHA-256,
igual que lock/proveedor/caché/metadatos locales de backend. HEAD intacto e índice
vacío; 78 pendientes finales, solo este informe nuevo. git diff --check exit 0.
Advertencias LF/CRLF preexistentes: informe FIN-04, plan FIN y observability/
run_observability.py y validation.py, sin corregir.
No normalización de advertencias LF/CRLF ni modificaciones a script/pruebas/TF.

## 20. Recomendación para la primera ventana

Viernes **20/11/2026**: objetivo, no autorización ni fecha garantizada de despliegue.
Resolver el defecto mínimo de descubrimiento en una iteración autorizada,
añadir regresiones y repetir preflight live antes de abrir AKS GO.
No iniciar creación o aceptar como suficiente el PASS offline anterior.
Mantener disponibles manual local, responsable, tiempo y autorización de retirada.

## 21. Estado Gate A

**GO**, backend observado accesible y lease libre.

## 22. Estado Gate B

**GO**, decisión formal del propietario mantenida. Se registra este bloqueo operativo
nuevo sin modificar automáticamente el gate.

## 23. Estado AKS

**NO-GO**. Ninguna operación de despliegue o destrucción autorizada/ejecutada.
No -Teardown, init, plan, apply, destroy, force-unlock, import, refresh o state pull.
No infraestructura Azure/Entra/Policy/RBAC/firewall/backend/estado/lock modificados.
Sin staging, commits o push. Detenerse y esperar instrucciones.
