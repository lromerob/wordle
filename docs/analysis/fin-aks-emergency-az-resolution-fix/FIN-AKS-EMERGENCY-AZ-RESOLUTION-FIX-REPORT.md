# FIN-AKS-EMERGENCY-AZ-RESOLUTION-FIX — 17/11/2026

## 1. Resumen ejecutivo

**PASS de corrección local.** Descubrimiento de Azure CLI limitado a Application,
ruta absoluta existente y wrapper Invoke-WordleAzureCli. Invocación con la ruta
resuelta, sin volver a buscar az de forma ambigua.
**38 pruebas offline aprobadas: 28 anteriores + 10 nuevas.**
No Azure CLI real, Terraform real, backend remoto o preflight live ejecutados.
La validación real corregida sigue pendiente de autorización independiente.

## 2. Alcance autorizado

Solo script de emergencia, regresiones offline, nota operativa pertinente e informe.
Sin cambios a contrato destructivo, infraestructura Terraform, lock o backend.
No operaciones contra Azure ni secretos leídos. Sin staging, commits o push.

## 3. Incidente original

EMERGENCY-PREFLIGHT-LIVE terminó BLOCKED exit 1 antes de state list.
Get-Command az devolvía la función interna Az, con Source vacío.
Native recibía un comando inválido para &. No era un error demostrado de MFA,
permisos o disponibilidad de la CLI instalada. Informe histórico intacto.

## 4. Causa raíz

PowerShell resuelve nombres sin distinguir mayúsculas y prioriza funciones/alias
respecto a aplicaciones. Tools no restringía CommandType y aceptaba un objeto
Function como prueba de ejecutable. El fallback az.cmd no se evaluaba porque
la función existía. Los mocks anteriores sustituían Tools y no cubrían esa resolución.
El error de invocación ocurría antes de cualquier código de salida CLI.

## 5. Código afectado

Revisión previa: definición Az, todas sus invocaciones en Context/Backend/
Inventory/Clean y llamadas Get-Command az/az.cmd de Tools.
Todas las consultas Azure pasaban por Native mediante ese wrapper; no se encontró
otra invocación directa Azure a corregir.
Tf no oculta la búsqueda de terraform porque usa la ruta explícita existente,
no Get-Command tf. Se mantienen funciones heredadas sin refactorización adicional.
Native conserva captura stderr, LASTEXITCODE y errores sanitizados.

## 6. Solución implementada

Nueva función Resolve-WordleAzureCli:
- Busca az y después az.cmd con Get-Command -CommandType Application.
- Rechaza Source vacío/whitespace, rutas relativas o archivo inexistente.
- Selecciona la primera aplicación válida y devuelve su ruta.
- Si no hay aplicación, lanza AZURE_CLI_MISSING; no función/alias como fallback.

Tools almacena esa ruta. Wrapper renombrado a Invoke-WordleAzureCli y referencias
actualizadas. Native sigue invocando & $Tool @Arguments con la ruta recibida.
No rutas personales, az.exe supuesto, instalador, login o configuración PATH global.

## 7. Justificación técnica

Renombrar evita la colisión local, pero no bastaría frente a alias/funciones externas:
el filtro Application es la garantía adicional necesaria.
La validación Source evita propagar otro comando vacío a Native.
az.cmd se contempla para Windows; la regresión usa archivo temporal inocuo y
ruta con espacios. No se sustituye el mecanismo de argumentos o manejo de procesos.
Las garantías se refieren a resolución de comandos, no a certificar autenticidad
de cualquier aplicación instalada en un PATH comprometido.

## 8. Contratos de seguridad preservados

Sin cambios a Preflight/Teardown, confirmaciones PLAN WORDLE AKS y
DESTRUIR WORDLE AKS, identidad/tenant/suscripción, backend, hashes, inventario,
lease, vigencia, plan guardado/apply, limpieza o logging.
Las funciones operativas solo cambian el nombre del wrapper invocado.
No reintentos, bypass de autenticación, silenciamiento de exit distinto de cero
o camino destructivo nuevo desde preflight.
Las 28 pruebas anteriores conservan el archivo y cobertura originales.

## 9. Prueba de regresión

Proceso local de prueba define función Az y crea az.cmd falso:
Get-Command az sin filtro selecciona Function con Source vacío, reproduciendo
el comportamiento defectuoso; Resolve-WordleAzureCli selecciona el archivo externo.
El wrapper invoca exactamente esa ruta y obtiene JSON fixture.
Contador de función sombra permanece cero; no recursión.
Esta comparación demuestra fallo del descubrimiento antiguo y éxito del nuevo,
sin ejecutar contra Azure ni modificar temporalmente el script productivo.

## 10. Pruebas adicionales

10 regresiones nuevas:
1. Incidente original: función Az, selección de aplicación e invocación real falsa.
2. Alias az no intercepta la aplicación ni produce recursión.
3. az.cmd Windows y ruta con espacios.
4. Aplicación ausente: fallo seguro.
5. Source vacío rechazado.
6. Source relativo rechazado.
7. Exit 7 con stderr sensible sintético: fallo sanitizado, no éxito.
8. Error AADSTS simulado exit 9: AUTHENTICATION_REQUIRED, sin filtración.
9. JSON malformado no se acepta como éxito.
10. AST: sintaxis, funciones únicas, ausencia de Az y llamadas ambiguas,
    no recursión, rama preflight y dos confirmaciones conservadas.

Tenant/suscripción incorrectos, logs, preflight sin plan y confirmaciones teardown
también quedan cubiertos por las pruebas anteriores; no se duplican innecesariamente.

## 11. Resultado de las 28 pruebas anteriores

**28/28 PASS**, cero fallos. Sin modificar Test-AksEmergencyTeardown.ps1.
Incluye confirmación correcta con apply simulado, rechazo de confirmación, huérfanos,
backend/locks/identidad, limpieza y planes completo/parcial.
Cero procesos nativos desde el código ejercitado en esa suite.

## 12. Resultado total de pruebas

**38/38 PASS** en Windows PowerShell mediante -NoProfile y
-ExecutionPolicy Bypass limitado al proceso. No política persistente modificada.
Comandos locales:
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File infra/scripts/Test-AksEmergencyAzureResolution.ps1
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File infra/scripts/Test-AksEmergencyTeardown.ps1

Sin preflight/teardown productivo. Los nombres de casos simulados no implican
ejecución de operaciones reales.

## 13. Validación sintáctica

Parser PowerShell: tres scripts válidos (productivo, suite anterior y nueva).
AST de producción comprueba funciones no duplicadas, wrapper antiguo ausente,
sin llamadas directas ambiguas az y sin recursión del nuevo wrapper.
Inspección de la rama -Preflight: return antes de Consent/plan/apply cuando
Destroy=false; helpers State/Backend/Inventory/Clean mantienen lecturas.

## 14. Verificación de aislamiento

Suite original sustituye Tools y Native sin fallback.
Suite nueva reemplaza PATH por directorio temporal único y ejecuta únicamente
az.cmd falso creado por la prueba, que solo imprime fixture y devuelve exit code.
Una guardia delante del Native original rechaza cualquier ruta distinta del archivo
falso exacto. Terraform no puede alcanzarse.
Funciones/alias sombra y CommandInfo inválidos son fixtures locales.
PATH/PATHEXT se restauran; árbol temporal propio se elimina tras validar su raíz.
No red, sesión real, instalación de dependencias o configuración global.
Errores/secretos sintéticos no se registran como stdout crudo; suite anterior
verifica sanitización del log. Sin archivos de estado real utilizados en pruebas.

## 15. Limitaciones

No acredita que la siguiente ejecución live supere las consultas Azure.
No verifica MFA, permisos, inventario ni backend real en esta iteración.
Se prueba Application az.cmd en Windows y selección de Application, no todas las
formas de empaquetado Azure CLI ni sistemas operativos.
PATH comprometido puede seleccionar binario no fiable; custodia del equipo sigue
siendo requisito. No ampliar esta corrección a una auditoría general de herramientas.

## 16. Riesgos residuales

Internet, MFA, Azure Policy/RBAC, contexto, concurrencia, estado parcial y
propiedad de recursos siguen sujetos a controles existentes.
El PASS previo offline y este PASS no garantizan destroy futuro.
Mantener AKS NO-GO hasta revalidación operativa y autorización de despliegue.

## 17. Archivos modificados

- infra/scripts/Invoke-AksEmergencyTeardown.ps1: resolución y nombre de wrapper.
- infra/scripts/Test-AksEmergencyAzureResolution.ps1: nuevo.
- docs/operations/FIN-AKS-EMERGENCY-TEARDOWN.md: solo nota de diagnóstico añadida.
- Este informe: nuevo.

Runbook de despliegue e informes históricos no modificados.
Suite original de 28 pruebas intacta.

## 18. Integridad Git

78 pendientes preexistentes registrados por SHA-256 y script original capturado.
Únicos cambios previos permitidos: script y apéndice del manual.
Verificación final: 76 pendientes ajenos al cambio intactos por SHA-256; solo
script y nota del manual modificados, más dos archivos nuevos (80 pendientes).
Revirtiendo en memoria únicamente resolución y renombrado, el script coincide
exactamente con la versión previa. Manual conserva prefijo original por hash.
HEAD intacto, índice vacío y Terraform/lock/proveedor/caché idénticos.
git diff --check exit 0; advertencias LF/CRLF preexistentes en informe FIN-04,
plan FIN y observability/run_observability.py y validation.py, sin corregir.
Sin staging/commits/push ni limpieza del trabajo previo.

## 19. Próxima acción recomendada

Autorizar separadamente repetir FIN-AKS-EMERGENCY-PREFLIGHT-LIVE de lectura,
sin teardown ni correcciones automáticas. Fecha objetivo 20/11/2026 sigue
condicionada a verificaciones y autorización posterior.
No se inicia esa fase en esta iteración.

## 20. Estado Gate A

**GO**, mantenido sin acceso al backend real.

## 21. Estado Gate B

**GO**, decisión del propietario mantenida.

## 22. Estado AKS

**NO-GO**. No preflight live, -Teardown, Azure CLI real, init/plan/apply/destroy/state,
force-unlock o acceso al estado remoto en esta iteración.
No Azure/Entra/Policy/RBAC/firewall/backend/estado/lock modificados.
Sin commits ni push. Detenerse y esperar instrucciones.
