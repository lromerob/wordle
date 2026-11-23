# FIN-17-PRIVATE-STORE-02 — 22/11/2026

## 1. Diseño implementado

**PASS local**, exclusivamente con fixtures sintéticos. La decisión del propietario
autoriza arranque supervisado por Windows y confianza en el operador local, sin
atestación criptográfica. Se resuelve el rechazo del bind 0777 mediante un modelo
Windows explícito; POSIX permanece predeterminado y estricto. No se registra runner
ni se activa CD. El almacén definitivo y AKS siguen **NO-GO**.

PowerShell valida NTFS → verifica/fija Compose → repite preflight → emite recibo
privado temporal → Linux verifica recibo separado ro, UUID, marker y estructura.
El recibo no se guarda en el store ni es una variable autoafirmada por el contenedor.

## 2. Modelo de confianza y limitaciones

El operador controla Windows/Docker Desktop y ejecuta código revisado. No se ofrece
resistencia frente a administrador malicioso, contenedor comprometido ni código
hostil. La correspondencia de la ruta Windows con el bind la verifica el lanzador;
Linux no calcula ACL NTFS ni autentica criptográficamente el fingerprint.

La política abarca el árbol del store; la custodia del anfitrión y sus directorios
padres forma parte de la confianza del operador. No es un auditor general de Windows.
El preflight es puntual: antes de cada activación se renueva, con nueva sesión y
recibo de hasta seis horas. Cambios durante la sesión requieren detener y revalidar;
no se afirma detección continua o invalidación instantánea desde Linux.

## 3. Preflight Windows

Ruta absoluta existente en disco fijo NTFS, externa e independiente del checkout,
sin UNC/reparse points en ruta o descendientes. Inspección metadata-only de objetos;
solo se lee el marker, nunca variables/backend, credenciales o archivos secretos.

Política owner-system-administrators-v1: owner igual al usuario Windows activo;
DACL canónica no nula; solo ACE Allow al usuario, SYSTEM y Administrators; usuario
con FullControl directo en cada objeto. Se rechazan otros actores incluso read-only,
Deny y ACE no interpretables. Las ACE heredadas se evalúan por identidad/derechos,
no se rechazan por herencia. Es un subconjunto conservador, no AccessCheck completo.
Cualquier ACL insuficientemente evaluable bloquea el arranque; no se modifica.

También se exige UUID, marker exacto y cuatro directorios. Para un almacén real se
requieren -StorageApproved y referencia no vacía al procedimiento de respaldo,
además de durable_acknowledged=true. Son decisiones del operador, no prueba técnica
de que el backup exista. No se han utilizado esos flags sobre un almacén real.

## 4. Validación Linux

scripts/private_store.py conserva el contrato POSIX sin relajación. ROOT se calcula
junto al propio script (equivalente al cálculo anterior), permitiendo copiar solo
este contrato en la imagen sin arrastrar dependencias operativas ajenas.

Modo explícito windows-supervised: /wordle-private debe ser un mount dedicado y
/run/wordle-host un mount separado ro. approval.json tiene ruta fija; se comprueban
schema, repo, emisor, política, UUID, sesión, ruta, marker SHA-256, formato del
fingerprint ACL y vigencia. Se mantienen marker real exacto, aprobación de durabilidad,
symlinks rechazados y directorios. Únicamente se omite interpretar los bits POSIX
emulados como permisos NTFS.

Modo windows-supervised-test: marker estrictamente sintético con
synthetic_fixture=true y durable_acknowledged=false; recibo fixture_only=true.
Host y entrypoint prohíben usarlo para registro/listener, incluso con autorización.
No se escribe un marker real que afirme durabilidad. Un env aislado o receipt dentro
del propio store provoca rechazo; un administrador Docker puede construir sus
propios mounts y está fuera del modelo de amenaza aprobado.

## 5. Configuración Docker

Imagen local nueva: wordle-actions-runner:fin17-private-store-02.
Referencia observada mediante image inspect:
sha256:96fae3121c10aba66aeead082a7c5ac49696fbe5a2613edb8635433eefbf055f.
Se conserva la imagen anterior fin17-local. Build real satisfactorio; capas de
herramientas en caché, consulta de metadatos de base pública fijada en Docker Hub.
Sin publicación ni instalación global. Contexto principal conserva allowlist;
contexto adicional store_contract copia únicamente private_store.py en la imagen.

El lanzador verifica un único servicio, UID 10001:10001, imagen/comando, no ports,
privileged o entrypoint alternativo, cap-drop ALL, no-new-privileges y exactamente
dos binds con fuentes/destinos aprobados; aprobación separada ro. Congela el Compose
efectivo para evitar otra interpolación. Controles nuevos con ACL restrictiva al
crearse; ningún permiso preexistente cambia. Validate usa network none y --rm.
Limpieza verifica nombre/label propios; no toca recursos ajenos.

Activate queda preparado solo para uso futuro: exige autorización adicional,
almacén real aprobado y respaldo referenciado, rechaza fixtures y pide token
mascarado por stdin únicamente después de todos los controles. Repo fijo, runner
ephemeral, token solo en proceso hijo. Usaría bridge sin puertos. **No se ejecutó**
registro, listener, solicitud de token real o workflow. Retirada remota del registro
sigue requiriendo autorización independiente si una sesión futura queda offline.

## 6. Pruebas positivas y negativas

- **47 unittest del runner/store:** 15 existentes adaptadas + 10 del runner + 22 del
  recibo. POSIX válido/excesivo, no fallback 0777, env falso, JSON autocreado, ruta
  incorrecta/ausente/checkout, UUID, marker ausente/no aprobado/hash alterado,
  directorios incompletos, receipt ausente/writable/inconsistente/caducado/futuro,
  vigencia excesiva, modelo desconocido y prohibición de registro con fixture.
- **68 regresiones operativas offline:** release gates, captura, ejecutor y recovery
  kit, con conexiones socket bloqueadas. Cero fallos/errores/omisiones. El test del
  paquete/hashes se repitió después de actualizar el runbook; también satisfactorio.
- **30 comprobaciones PowerShell, incluidas Docker reales:** fixture NTFS restringido
  pasa preflight; ACL Everyone FullControl en OTRO fixture nuevo se rechaza; DACL
  nula/no canónica, owner y deny no admitidos generan rechazo de política; path/UUID/
  marker/estructura/binds incorrectos se bloquean. Preflight fallido no llama Docker.
  Activate sin autorización y con fixture se rechaza sin solicitar token.
- Lanzador CLI real: sesión final wordle-runner-supervised-17471a82cf744a39bd97a21c7f266934,
  mode=validate, uid=10001, store_validated=true, store_model=windows-supervised-test,
  store_mode=0o777 y registered=false. Termina y se elimina.
- Dos invocaciones Docker reales negativas rechazan env sin mount de aprobación y
  JSON autocreado en store: exit 1 y mensaje exacto Runner refused: ValueError, no
  un mero fallo genérico del motor. Contenedor propio validate-hold listo, SIGTERM, exit 0,
  eliminado. Nunca se ejecuta run.sh o config.sh reales.
- AST Python, parser PowerShell, build de imagen, render Compose efectivo y diff checks.

**115 pruebas Python distintas aprobadas, cero omitidas; 30 aserciones PowerShell
aprobadas.** Solo suites focalizadas, sin tests completos de aplicación/AKS/observabilidad.
Los fixtures sintéticos definen ACL al crear nuevos directorios; no se usa Set-Acl
sobre rutas existentes. Los controles efectivos de ACL se verifican también sobre
NTFS real; los casos DACL especiales se prueban con objetos de política sintéticos.

Incidencias resueltas durante implementación: firma .NET de creación del fixture,
serialización de dos líneas runner.env, código de salida contaminado por inspect
tras --rm y normalización Windows del mock /proc. El inventario R1 inicialmente
incluía el diagnóstico legado validate_local.py y su referencia a scripts/probe.py
generado en runtime: se limitó a dependencias vigentes, sin relajar el checker.
No se omitieron casos para obtener PASS.

## 7. Persistencia

Prueba real 75bb9170b5954667ac84fc2738ed97b1 con la imagen nueva. Fixture Windows externo
temporal, marker false. Contenedor d8553e814e4e790f2a8789f82626424ca531b44574c98c66ff055b40efcfca37
escribe; Windows verifica; se elimina; contenedor independiente
fdfad4d860315107e100adb7d6188f5f00732cdb6a7f1f5bb078e6c2ca0997e7 lee y verifica.

SHA-256 conservado: 94e006c7a2093a3e2afe3bf12d127af86427942232f9cec102ec1e85f65d4834.
Ambos exit 0, network none, sin puertos, no-new-privileges y cap-drop ALL.
Cada contenedor verifica además POSIX real bajo /tmp: 0700/0600 aceptado y root 0777
rechazado (cuatro comprobaciones). Los markers POSIX true son únicamente fixtures
Linux efímeros, nunca aprobación de almacenamiento real. Fixtures y contenedores
propios retirados; imagen conservada. Persistencia entre contenedores **no demuestra
durabilidad ante fallo de disco, backup ni restauración**.

## 8. Retirada humana

Invoke-AksEmergencyTeardown.ps1 conserva su SHA-256 y permanece independiente de
Docker/Actions, ejecutable desde Windows con identidad humana, no OIDC del CD.
TargetFile, WorkDirectory y VariablesFile deben ser externos y aprobados, coherentes
con el backend real; no trasplantar caché/planes Linux al workspace humano.
Rutas, inputs y acceso humano definitivos siguen NOT VERIFIED. No se ejecuta retirada,
Terraform ni Azure. No se modifican PG-05/PG-06. El inventario R1 incorpora los archivos
del procedimiento vigente y su documentación; R2/R4/R6/R8 no se eluden.

## 9. Archivos modificados

Previos, modificados únicamente por este incremento:
- scripts/private_store.py
- scripts/operational_contract.py (dependencias del recovery kit R1)
- docker/runner/Dockerfile
- docker/runner/compose.yaml
- docker/runner/entrypoint.py
- docker/runner/Invoke-WordleRunner.ps1
- docker/runner/Test-WordlePrivateStore.ps1
- docker/runner/test_runner.py
- docker/runner/test_private_store.py
- docker/runner/validate_persistence.py
- docs/operations/wordle-docker-runner.md

Nuevos:
- docker/runner/Test-WordleSupervisedStore.ps1
- docker/runner/test_windows_store.py
- Este informe.

No se modifica el workflow CD/CI, aplicación, Terraform, Kubernetes, procedimiento
humano o evidencias históricas. El validador legado de browser queda intacto en Git.

## 10. Configuración definitiva pendiente

Aprobar explícitamente ruta Windows persistente, UUID, custodia/ACL, procedimiento
de backup y recuperación; preparar inputs privados existentes según gates, sin
crearlos automáticamente. Confirmar TargetFile/WorkDirectory/VariablesFile humanos.
Después verificar prerrequisitos externos y autorizar registro/CD en otra iteración.
No se construye una aprobación real ni se eligen identificadores de producción.

Reproducción local mínima, desde raíz Wordle:

```powershell
./docker/runner/Test-WordleSupervisedStore.ps1 -RunDocker
.venv/Scripts/python.exe -B docker/runner/validate_persistence.py --run-local-validation
```

Build y configuración definitiva futura en docs/operations/wordle-docker-runner.md.

## 11. Criterios GO/NO-GO

**GO local / PASS:** preflight, rechazo de rutas/ACL, modelo explícito, POSIX estricto,
UUID/marker/estructura, prueba positiva sintética, bloqueo antes del arranque,
persistencia y parada demostrados. Sin registro, CD, Azure, secretos nuevos o Git write.
**NO-GO real:** no hay almacén definitivo aprobado ni acceso humano de recuperación
verificado; registro y CD requieren autorización expresa adicional.
No se modifica el estado general del TFG ni se inicia otra iteración.

## 12. Integridad Git

Rama codex/pg01-07-consolidation; HEAD 4d56cf265cc5f0af8c72c64f2a93373660e8f122.
Base de comparación: 486 archivos no ignorados, índice vacío, nueve versionados
previamente modificados y 305 sin seguimiento. Comparación SHA-256 final limitada
a los once previos autorizados y tres nuevos enumerados. Ningún archivo eliminado;
doce informes históricos y evidencias anteriores intactos. Estado final: nueve
versionados modificados (los mismos anteriores), 308 sin seguimiento e índice vacío.
git diff --check sin errores; solo warnings LF/CRLF preexistentes en FIN-04/plan.
Cero contenedores de estas pruebas y cero directorios de control temporales restantes.
Ambas imágenes conservadas y PG-06 sigue funcionando. Sin
add/commit/push/fetch, cambio de rama o configuración global.

Sin operaciones GitHub/Azure, OIDC/RBAC, Terraform remoto, publicación GHCR, credenciales
reales, registro o listener. Solo recursos Docker locales propios; no se alteran
contenedores, volúmenes o imágenes ajenos. Controles/fixtures temporales se eliminan;
se conserva la imagen nueva y la anterior. Sin modificación de ACL preexistentes.
