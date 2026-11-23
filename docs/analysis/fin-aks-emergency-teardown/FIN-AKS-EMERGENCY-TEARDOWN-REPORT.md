# FIN-AKS-EMERGENCY-TEARDOWN — 17/11/2026

## Resultado

**PASS de implementación y validación OFFLINE.** Procedimiento autónomo sin IA:
preflight seguro por defecto, retirada explícita con plan binario revisable y
confirmaciones humanas, comprobaciones posteriores y manual alternativo.
No se ha ejecutado el script productivo contra Azure ni un Terraform real.
No es una prueba de retirada AKS ni un temporizador de autodestrucción.

Gate A GO; Gate B GO; **AKS NO-GO**. Ejecución real exige autorización independiente.

## Archivos

- infra/scripts/Invoke-AksEmergencyTeardown.ps1 — nuevo.
- infra/scripts/Test-AksEmergencyTeardown.ps1 — nuevo, sin Pester.
- docs/operations/FIN-AKS-EMERGENCY-TEARDOWN.md — nuevo manual.
- docs/operations/FIN-AKS-DEPLOYMENT-RUNBOOK.md — solo referencia añadida al final.
- Este informe — nuevo.

Sin cambios a Terraform de infraestructura, manifiestos, aplicación, lock,
backend/configuración remota o informes históricos.

## Referencias y decisión de diseño

Revisados runbook, DEPLOYMENT-WINDOW-PREP, POST-HARDENING-PLAN,
MFA-WRITE-DELETE-TEST, REMOTE-BACKEND-INITIALIZATION y EPHEMERAL-LIFECYCLE,
además de Terraform real y azure_supervised.py.
El helper Python existente ya protege planes/inventarios; se preserva.
El nuevo script responde al requisito explícito PowerShell sin dependencias nuevas
y evita init y consultas a RG inexistentes que dificultarían un create parcial.
Conserva las seis direcciones Terraform y el mismo alcance/backend.

## Modos y controles

Sin switches o -Preflight: versiones/herramientas, identidad humana/tenant/suscripción,
coordenadas backend inicializado, RG/cuenta/container/key, lease libre, state list
y recursos Azure de ambos RG. Solo lecturas cloud y registro local.
Estado vacío: no plan/apply, comprobación de residuos.
Estado inesperado o condición crítica inaccesible: fallo seguro.

-Teardown exige variables JSON externas revisadas. No empieza destruyendo:
1. Repite preflight.
2. Pide PLAN WORDLE AKS para generar un único plan -destroy guardado y lease normal.
3. Verifica direcciones, IDs exactos, acciones delete/no-op, igualdad con inventario
   Terraform, ausencia de objetos ajenos del RG app y propiedad managedBy de RG nodos.
4. Muestra contexto, IDs Terraform y dependencias Azure, hash y advertencia.
5. Exige exactamente DESTRUIR WORDLE AKS, con revisión humana de toda la cascada.
6. Antes de aplicar, comprueba otra vez identidad, hash/fingerprint, ETag del blob,
   estado, inventario y procesos concurrentes; vigencia de diez minutos.
7. Aplica únicamente ese binario con bloqueo normal; Terraform añade su control de
   plan obsoleto. Sin -Force, auto-approve, init, state pull o force-unlock.
8. Verifica backend, estado vacío, grupos/AKS ausentes e IDs observados ausentes.

No elimina huérfanos por CLI, prefijo, import o state rm. Sin reintentos automáticos.
La revisión humana sigue siendo indispensable para recursos ajenos infiltrados en
un RG administrado: managedBy del grupo no prueba propiedad de cada hijo.

## Estado y protección de datos

Backend fijo: rg-wordle-state/stwordletfgstate7c92d4/tfstate/
wordle/aks-demo.tfstate, tenant/subscription exactos y use_azuread_auth=true.
Sin claves/SAS o cambio automático de contexto. Solo scopes/IDs app exactos en plan.
Direcciones/destrucción parciales permitidas como subconjunto de seis, sin inventar
recursos ausentes; cualquier objeto ajeno del RG app detiene la ejecución.
No leer ni registrar el contenido completo del estado.

Plan temporal bajo LOCALAPPDATA/WordleTFG/emergency/<GUID>, fuera de Git.
Se borra en finally; ningún borrado recursivo del script operativo.
Cancelación brusca/PC apagado puede dejar plan privado: manual explica custodia.
No se garantiza borrado forense SSD ni ACL especiales; utilizar perfil/disco privado
cifrado, no directorios compartidos.
Logs JSONL sanitizados: UTC, modo, fases, direcciones Terraform, SHA, aceptación,
resultado; nunca stdout/errores crudos, inputs o credenciales.
No modificación de .gitignore: todos los artefactos runtime se generan fuera del repo.

## Pruebas ejecutadas

28/28 escenarios offline aprobados, cero llamadas nativas desde el código probado.
Se ejecutaron en Windows PowerShell con -NoProfile -ExecutionPolicy Bypass limitado
al proceso. La ejecución inicial sin excepción fue rechazada por política local;
no se cambió política de usuario/sistema ni se ocultó esta limitación.
Parser PowerShell 7.6.9: ambos archivos válidos; ejecución Windows PowerShell real
de las pruebas demuestra además compatibilidad de las rutas probadas con ese motor.

26 casos del flujo simulado:
herramientas presentes/ausentes (Terraform/Azure CLI), versión incorrecta,
tenant/suscripción/backend equivocados, estado inaccesible/vacío/esperado/ajeno,
backend en plan, lease bloqueado, MFA caducado, conectividad, confirmación incorrecta
y correcta, fallo de apply simulado, limpieza parcial y completa, huérfanos,
logs sin datos sensibles sintéticos, plan inesperado/acciones update, binario
manipulado y estado vacío con huérfano.
Dos casos adicionales del validador: plan completo de seis recursos y parcial de tres.

La función Native es la única frontera de procesos; las pruebas la sustituyen
completamente y rechazan cualquier comando no previsto, sin fallback real.
También sustituyen herramientas y lectura interactiva. Entradas/backend/plan/logs
son fixtures temporales, jamás los del backend real.
Aserciones: apply solo en casos previstos, confirmación correcta llega exactamente
a un apply simulado, ningún init/destroy/force-unlock, planes temporales retirados,
logs sin marcador sensible ni contenido de plan/inputs.
Directorio temporal de cada ejecución eliminado tras verificar que permanece dentro
del directorio temporal con prefijo propio; no recursos ajenos limpiados.

Durante desarrollo, pruebas detectaron una comparación de rutas por prefijo demasiado
amplia, corregida para usar separador, y se ajustó la fixture de residuo posterior
para que no fuera confundida con huérfano previo. Suite final 28/28 satisfactoria.
No se presentan mocks como evidencia de Azure.

## Manual y recuperación sin IA

Manual contiene apertura de PowerShell, localización por ruta, ejecución sin PATH
global, revisión, dos confirmaciones, logs/exit codes y procedimiento manual completo.
Alternativa manual usa herramientas instaladas, mismo backend, inventarios/hash,
plan -destroy guardado, aprobación explícita y apply del mismo binario, sin script/IA.
Contingencias: MFA solo humano autorizado, Policy/RBAC sin elusión,
red/firewall sin apertura automática, lock sin force-unlock y fallos parciales con
inventario/coste/permiso de recuperación.
Clasificaciones CLEAN, PARTIAL CLEANUP y VERIFICATION FAILED definidas.
CLEAN no equivale a coste cero ni auditoría universal de la suscripción.

## Limitaciones y siguiente iteración

No validación Azure real: versión/admisión/permisos/MFA/backend/retirada real
deben comprobarse únicamente cuando se autorice. Sin Internet/equipo encendido
o sesión válida no puede actuar; no resuelve corrupción de estado ni borra huérfanos.
No garantiza detectar recursos desconocidos ajenos al inventario observado;
revisión humana de cascadas y control económico posterior siguen siendo obligatorios.
Autodestrucción cloud solo evaluada conceptualmente en manual, no implementada.
No ejecutar una demo si el responsable no puede revisar/autorizar recuperación.

Recomendación: propietario ensaya lectura del manual y comandos offline,
custodia inputs y decide autorización futura acotada de preflight; AKS sigue NO-GO.
No iniciar automáticamente otra iteración.

## Integridad y restricciones

Capturados 73 pendientes preexistentes, HEAD/índice y hashes Terraform/lock/caché.
Único preexistente autorizado a cambiar: runbook, solo apéndice de referencia.
Verificación final: 77 pendientes (73 previos y cuatro nuevos). Los 71
archivos con huella histórica completa están idénticos por SHA-256; el runbook
conserva íntegro su contenido previo por hash y solo añade referencia. El informe
WINDOW-PREP no se editó. El snapshot inicial impreso quedó truncado: no se usó
para afirmar una comparación completa; se reutilizaron huellas históricas íntegras.
Terraform/lock/caché idénticos; HEAD intacto e índice vacío.
git diff --check exit 0; advertencias LF/CRLF previas en informe FIN-04,
plan FIN y observability/run_observability.py y validation.py, sin corregir.
Sin init, plan contra Azure, apply, destroy, state remoto real o modificación cloud.
Sin AKS/recursos creados o eliminados, Entra/Policy/RBAC/firewall/backend/estado/lock
modificados; sin staging, commits o push.
