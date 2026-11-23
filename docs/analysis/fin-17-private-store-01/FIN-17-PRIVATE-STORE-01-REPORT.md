# FIN-17-PRIVATE-STORE-01 — 22/11/2026

## 1. Resumen ejecutivo

**PARTIAL.** Persistencia real Windows entre dos contenedores comprobada y
regresiones de rechazo aprobadas. No se habilita compatibilidad Windows: falta
una prueba de ACL efectiva vinculada de forma auténtica al mount y a la activación.
Se aplica la cláusula del encargo que exige detener esa implementación antes que
simular garantías con un JSON/env. Runner sin registrar; CD/AKS **NO-GO**.

## 2. Causa raíz

Docker Desktop presenta el bind Windows como 0777; este valor Linux no expresa
por sí solo los derechos NTFS efectivos del anfitrión. El contrato POSIX original
rechaza group/other y por ello no acepta el bind. Se reprodujo 0777 en ambos
contenedores; no es un fallo de lectura/escritura. Las ACL Windows y el modelo
POSIX son mecanismos distintos, no controles intercambiables.

## 3. Diseño elegido

Se conserva la arquitectura aprobada: Windows externo persistente → bind
/wordle-private. No se propone otro filesystem ni se relaja private_store.py.
Un helper de metadatos no es una autoridad de aprobación. Tampoco lo son un env,
un JSON dentro del store, un archivo aportado por el contenedor o una firma cuya
clave pública pueda reemplazar ese mismo contenedor.

La separación solicitada necesita una raíz de confianza externa al mount,
verificación efectiva de permisos/actores, validación del Docker mount y aprobación
fresca antes de cada activación. Una opción futura sería firma host con clave
privada inaccesible al contenedor y clave pública fijada en un contexto confiable,
vinculando UUID, ruta, ACL, marker, mount y sesión. No se implementa ni se generan
claves: su custodia, pinning y ciclo de invalidación superan el cambio mínimo
verificado aquí. Se documenta el bloqueo en lugar de afirmar seguridad.

## 4. Cambios implementados

Nuevos:
- docker/runner/Test-WordlePrivateStore.ps1: diagnóstico sin aprobación.
- docker/runner/test_private_store.py: 15 regresiones focalizadas.
- docker/runner/validate_persistence.py: persistencia real y POSIX real.
- Este informe.

Actualizado: docs/operations/wordle-docker-runner.md. Retirado el ejemplo directo
de activación hasta resolver el control previo. Sin cambios en private_store.py,
Compose, Dockerfile, entrypoint, workflow CD o procedimiento de emergencia.

## 5. Modelo POSIX

Comportamiento original idéntico. Se comprueban ruta, UUID, marker exacto, aprobación,
directorios y permisos. Dos tests reales en Linux por contenedor: aceptación de
root/dirs 0700 y marker 0600; rechazo de root 0777. No mocks de stat en esas pruebas.
Los fixtures POSIX efímeros sintéticos sí contienen marker de prueba aprobado;
se eliminan al terminar y no acreditan durabilidad de un almacén real.

## 6. Modelo Windows

No habilitado. Configuración definitiva sin aprobar; ningún UUID o ruta real
inventados. Dos variables autoafirmadas y un JSON autocreado no eluden el rechazo
POSIX en las regresiones. No se incorpora fallback automático por observar 0777.
No se entrega una opción Windows que parezca funcional sin prueba del host.

## 7. Verificación de ACL

Helper PowerShell exige ruta absoluta existente externa, rechaza UNC/device paths,
rutas dentro del checkout o que lo contengan y reparse points en la cadena. Lee
solo metadatos ACL y enumeración, calcula fingerprint, compara owner con operador
y cuenta allow de escritura potencialmente no autorizados. SYSTEM/Administrators
se distinguen de terceros para el diagnóstico, sin aprobarlos como política real.
No rechaza una ACE por ser heredada. No modifica ACL ni imprime cuentas o contenidos.

Resultado sobre fixture externo Windows: path_checked=true, acl_checked=true,
**NOT VERIFIED**, approval_issued=false, effective_access_verified=false; exit 2.
Owner y enumeración no equivalen a acceso efectivo completo. No se implementa
AccessCheck de tokens/grupos/deny, validación de hijos ni del acceso Docker.
No se inspecciona un almacén definitivo. ACL permisiva/no verificable bloquea la
aprobación; no se declara que las ACL actuales sean inseguras por simple inspección.

## 8. Persistencia

Prueba real f157d87e160446c68bf23921c5e8eba1, imagen local existente
sha256:92c225acb3b2adfe517834376ffa5317be0aebe5f80d3d42585587cec3ed8ff9.
Fixture temporal Windows externo al repo, sin credenciales, marker false.

1. Contenedor 32710cf70bbdf550c6c788dcc10c41470c649b283c7a4a50b35cb41caa88d76c
   escribe archivo sintético; Windows confirma hash; contenedor terminado se elimina.
2. Contenedor nuevo 139ed81b3981da4d94d0c030ad9aff9669afe505905c01c11f4c87e851d64ab6
   lee el bind y confirma bytes/hash; Windows vuelve a confirmar.

SHA-256 idéntico antes/después:
f7f1ba94fa9d5958068bfecbf8854f31b1c9976673c062c26ac6ba2af515000e.
Ambos exit 0, bind 0777. Solo se eliminaron los dos contenedores y fixtures propios;
imagen conservada. **No es evidencia de durabilidad ante fallo del disco**.

## 9. Integración Docker

Docker 29.9.2 Linux. Dos contenedores UID 10001:10001, network none, cap-drop ALL,
no-new-privileges, sin puertos ni socket; entrypoint sustituido solo para las pruebas
Python locales. Sin listener, registro, tokens, builds ni descargas. Segundo bind
solo lectura contiene exclusivamente dos helpers Python, nunca el checkout completo.
Contenedor PG-06 preexistente preservado; no exec/start/stop sobre él. Ningún
contenedor, volumen o imagen ajeno se modificó. La configuración Docker no cambió.

## 10. Retirada humana

Revisados documentalmente script y contrato existentes. TargetFile identifica
objetivo y operador; WorkDirectory es workspace Windows externo e independiente;
VariablesFile contiene inputs aprobados. Deben corresponder al mismo backend, sin
trasplantar caches/planes Linux. La identidad humana y OIDC CD permanecen separadas.

Rutas reales de esos tres elementos, accesibilidad humana y backend aprobado:
**NOT VERIFIED**. No se buscan indiscriminadamente ni se abren secretos. No se
modifica o ejecuta Invoke-AksEmergencyTeardown.ps1; sigue independiente del runner.
R1/R2/R4/R6/R8 no se alteran para sortear la validación del store.

## 11. Pruebas ejecutadas

- 15 pruebas nuevas: POSIX modelado válido/excesivo, no fallback 0777, env falso,
  JSON autocreado, ruta ausente/checkout, UUID incorrecto, marker ausente/no aprobado/
  claves extras, directorio ausente y tres diagnósticos Windows reales.
- 10 pruebas existentes del runner, registro siempre simulado.
- 37 pruebas existentes test_release_gate/test_aks_capture, con conexiones socket
  bloqueadas en el proceso de pruebas.
- 4 comprobaciones POSIX reales: aceptación y rechazo en cada uno de los dos
  contenedores; además escritura, hashes Windows, recreación y lectura reales.
- Parser PowerShell, AST de los dos Python nuevos y git diff --check.

No se repitieron suites de aplicación, kind, Terraform o Azure.

## 12. Resultados

62 pruebas unittest aprobadas, cero fallos/errores/omitidas en Windows.
Persistencia real PASS; POSIX real PASS. Diagnóstico ACL seguro PASS como diagnóstico,
**no aprobación Windows**. Compatibilidad funcional Windows y activación NO-GO.

Pendientes, no presentados como tests aprobados: aceptación Windows autenticada,
wrong host mount, permisos efectivos amplios/grupos/deny, caducidad, cambio ACL/ruta/
UUID sobre una aprobación auténtica y frescura por activación. No se crean fixtures
que simulen esas garantías ausentes. Por ello no se cumplen todos los criterios PASS.

## 13. Limitaciones

Inspección puntual no garantiza vigilancia continua. La prueba no acredita backup,
restore, cifrado ni supervivencia a fallo de disco. El helper siempre devuelve código
2; no debe utilizarse como autorización. Un administrador Windows/Docker sigue
siendo actor confiable, no queda aislado por un JSON o marcador. No hay CD operativo.

## 14. Configuración pendiente de aprobación

- Ruta Windows definitiva, UUID, custodia, operadores/ACL, backup y recuperación.
- Mecanismo mínimo de confianza host/contenedor y su configuración explícita,
  sesión/vigencia, invalidación y verificación del bind real.
- Rutas externas TargetFile, WorkDirectory y VariablesFile humanos y backend común.
- Después de resolver y validar lo anterior, autorización separada de registro/CD.

No se crea almacén definitivo, credenciales, claves, marker real aprobado o config.

## 15. Criterios GO/NO-GO

GO para diagnóstico y repetición de pruebas sintéticas locales. NO-GO para aprobar
un almacén Windows, activar/registrar runner, CD o AKS. Mantener PARTIAL hasta
completar verificación efectiva y separación confiable. No se actualiza el plan.

Fuentes oficiales consultadas (solo documentación pública):
- https://learn.microsoft.com/en-us/windows/win32/secauthz/how-dacls-control-access-to-an-object
- https://learn.microsoft.com/en-us/windows/win32/api/securitybaseapi/nf-securitybaseapi-accesscheck
- https://docs.docker.com/desktop/setup/install/windows-permission-requirements/

## 16. Integridad Git

Rama codex/pg01-07-consolidation; HEAD 4d56cf265cc5f0af8c72c64f2a93373660e8f122;
índice vacío. Base de comparación: 482 archivos no ignorados, 9 versionados ya
modificados y 301 sin seguimiento. Solo se cambia el runbook autorizado y se crean
los cuatro archivos indicados. Estado final: 9 versionados modificados (los mismos
previos), 305 sin seguimiento e índice vacío. git diff --check sin errores; únicamente
advertencias preexistentes LF/CRLF en FIN-04 y el plan. Verificación final por SHA-256 de todos los archivos
previos; doce informes históricos y evidencias anteriores conservados sin cambios.

Sin add/commit/push/fetch, cambio de rama o configuración global. Sin operaciones
Azure/GitHub, Terraform remoto, GHCR, workflows, OIDC/RBAC, registro ni tokens reales.
Sin recursos persistentes PG-05/PG-06 modificados. Las únicas consultas remotas fueron
documentación pública oficial. Los recursos temporales propios se retiraron.
