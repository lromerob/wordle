# FIN-AKS-BACKEND-LEASE-VALIDATION — Wordle TFG

Fecha: **16/11/2026**. Ejecución real **16:53:33–16:54:07 UTC**. **PASS. Gate A GO; AKS NO-GO.**

## 1. Resumen ejecutivo

Prueba real con Azure CLI/Entra ID sobre el único blob **validation/backend-lease-test.txt** del contenedor tfstate de stwordletfgstate7c92d4, Sweden Central. Creación/lectura verificadas, lease finito adquirido, escritura sin identificador rechazada específicamente por **LeaseIdMissing**, contenido/ETag intactos durante el bloqueo, liberación explícita, escritura y lectura posteriores correctas y eliminación lógica completada.

Estado final: **cero blobs activos**, ningún archivo de estadoTerraform; seguridad, firewall, RBAC, retención y lifecycle iguales antes/después. Quedan **dos versiones anteriores** del blob de prueba,31 y29bytes, sin purgarlas. **El lifecycle existente solo cubre tfstate/wordle/aks-demo.tfstate; no cubre validation/**. Por tanto no se promete su eliminación automática a7d: son versiones persistentes, no versiones borradas con plazo soft-delete ya iniciado.

## 2. Autorización y alcance

Adjunto FIN-AKS-BACKEND-LEASE-VALIDATION autoriza exclusivamente un blob temporal, su contenido, lease finito, prueba negativa, liberación y borrado lógico, más lecturas e informe. No Terraform, estado, contenedores adicionales, cambios de seguridad/retención/lifecycle, purgas, permisos o redes. No pruebas concurrentes.

Se leyó FIN-AKS-SWEDEN-BACKEND-BOOTSTRAP-REPORT.md; no se modifica. La key futura wordle/aks-demo.tfstate permanece inexistente. No se accede a Supabase/AKS/otros proyectos.

## 3. Identidad y suscripción verificadas

Azure CLI: suscripción **11306565…1bb5**, tenant **aff0390f…1eb9**, Enabled. Graph ID propio verifica **b573130a…a831**, operador aprobado. Sin login/cambio de contexto. Se comprobó ausencia de variables alternativas AZURE_STORAGE_KEY/CONNECTION_STRING/SAS_TOKEN sin mostrar valores. Todas las operaciones Blob llevan **--auth-mode login**, sin claves, SAS o fallback.

El identificador del lease se capturó en memoria únicamente, no se emitió en resultados ni informe; se usó para release y se descartó. Sin logs debug/verbose ni credenciales persistidas deliberadamente. Los archivos locales de contenido/descarga fueron temporales externos y eliminados al finalizar.

## 4. Preflight

Controles de lectura previos, satisfactorios antes de escribir:

- Cuenta aprobada existe en swedencentral, StorageV2/Standard_LRS.
- Contenedor tfstate privado: publicAccess=None, sin legalhold/WORM.
- HTTPStrue, TLS1_2, SharedKeyfalse, anonimatofalse.
- FirewallDeny/None, exactamente una IP administrativa; coincide con salidaIPv4global actual, sin VNet/resourceAccessRules adicionales.
- Asignación exacta Storage Blob Data Contributor al operador en el scope del contenedor verificada; sin cambios.
- versioningtrue, blob/container softdelete7d; configuración y policy guardadas en memoria para comparación posterior.
- Listado realEntra satisfactorio y nombre temporal no ocupado, también al incluir versiones/snapshots/borrados.

No se modificó configuración para resolver acceso. No auditoría generalGit; lecturasGit finales limitadas a preservar pendientes.

## 5. Estado inicial del contenedor

**16:53:33.035318UTC:**0 blobs activos y0 objetos enumerados con --include dsv. No wordle/aks-demo.tfstate ni otro nombre terminado.tfstate. No blob temporal preexistente que sobrescribir. La carga inicial añadió --overwrite false y --if-none-match * para impedir colisión entre listado y creación.

## 6. Prueba de escritura

**16:53:34.494650UTC:** creado únicamente validation/backend-lease-test.txt, BlockBlob, contenidoASCII **WORDLE_BACKEND_LEASE_VALIDATION**, sin salto de línea, **31bytes**. Upload con EntraID satisfactorio.

ETag inicial: **"0x8DF440227071000"**. No metadata ni blobs adicionales. Contenido no sensible. El flag de propiedad del blob se estableció solo tras éxito de creación para impedir limpieza de objetos preexistentes.

## 7. Prueba de lectura

**16:53:37.230054UTC:** download con EntraID a archivo temporal; comparación byte a byte con archivo origen correcta. GET blob muestra31bytes y mismoETag, lease state=available/status=unlocked/duration=null.

La lectura valida contenido exacto, no solo HTTP/exitcode. La descarga no modificó el objeto remoto.

## 8. Adquisición del lease

**16:53:38.633942UTC:** `az storage blob lease acquire ... --auth-mode login --lease-duration 60`. Duración **finita60segundos**, dentro del rango15–60 deAzure; se eligió60 para permitir varias llamadasCLI y liberar explícitamente con margen, en lugar de arriesgar expiración antes de verificar el bloqueo. No lease infinito.

**16:53:40.056467UTC:** GET confirma duration=fixed, state=leased, status=locked. ID no mostrado ni incluido aquí.

[Duración y autenticación leaseCLI](https://learn.microsoft.com/en-us/cli/azure/storage/blob/lease).

## 9. Validación del bloqueo

**16:53:41.542254UTC:** intento único de sobrescribir el mismo blob con contenido actualizado, **sin proporcionar leaseID**. Azure rechaza con código real **LeaseIdMissing**. No se interpreta un error genérico de permisos/red como bloqueo válido.

CLI no expuso un statusHTTP independiente en la salida sanitizada; el [catálogo oficial](https://learn.microsoft.com/en-us/rest/api/storageservices/blob-service-error-codes) asocia LeaseIdMissing con412. El dato observado es el código, no un HTTP412 capturado condebug.

**16:53:44.351776UTC:** nueva descarga coincide con los31bytes originales, ETag **"0x8DF440227071000"** sin cambio y lease sigue leased/locked. Demuestra rechazo sin alteración de contenido y con bloqueo vigente.

## 10. Liberación del lease

Se ejecutó release explícito con el ID conservado en memoria, exclusivamente sobre el blob creado por esta prueba. **16:53:47.104157UTC:** GET confirma state=available, status=unlocked, duration=null. Se descartó el ID.

Liberación verificada aproximadamente8,5segundos tras adquirir; **no dependió de esperar la expiración** de60segundos. No break, renew, lease ajeno ni liberación sobre otro objeto.

## 11. Escritura posterior a la liberación

Se sobrescribió únicamente el mismo blob, con condición --if-match del ETag previo, contenido **WORDLE_BACKEND_LEASE_RELEASED**, **29bytes**, sin salto de línea. **16:53:51.441454UTC:** upload y descarga byte a byte satisfactorios, nuevoETag **"0x8DF44022F77C0AB"**, leaseavailable/unlocked.

Se demuestra que la escritura vuelve a funcionar después de release; no se infiere solo del estado delease. No otro blob ni actualización de metadata.

## 12. Limpieza del blob temporal

Antes del delete se comprobaron leaseunlocked, contenido igual a una de las dos cadenas de prueba y ETag coincidente con el último conocido. Borrado dirigido al nombre exacto y condicionado por --if-match, EntraID; **16:53:55.554930UTC**, éxito.

No versiónID en delete, no borrado de versiones anteriores, purga, contenedor o cuenta. La limpieza estaba protegida en finally para intentar liberar solo un lease propio y borrar solo el objeto creado si no había bloqueo ni modificación inesperada. No hizo falta recuperación excepcional.

## 13. Estado final

**16:54:07.263313UTC:**

| Verificación | Resultado |
|---|---|
|Blobs activos|0, mismo listado vacío inicial|
|Blob temporal activo|Ausente|
|EstadoTerraform|No creado; estadoinicialausente conservado|
|Cuenta/ubicación/SKU/HTTPS/TLS/SharedKey/anonimato|Iguales antes/después|
|Firewall/reglas|Iguales antes/después, IPindividual actual, Deny/None|
|Contenedorprivado/WORM/legalhold|Iguales antes/después|
|AsignacionesRBAC en contenedor|Iguales antes/después|
|Retención/versioning/lifecycle|Iguales antes/después|
|Lease activo|Liberado explícitamente antes del borrado; sin blobactual sobre el que mantenerlo|
|Archivoslocalestemporales|Eliminados|

Se compararon en memoria objetos de configuración relevantes y lista exacta de asignaciones (ID/principal/rol/scope/condition), no solo valores del informe. Sin cambios administrativos o de seguridad.

## 14. Versiones y datos retenidos

Listado Entra con **--include dsv** muestra exclusivamente el nombre de prueba y estas versiones:

|VersionID|Tamaño lógico|Observación|
|---|---:|---|
|2026-11-16T16:53:34.5297408Z|31bytes|Contenidoinicial|
|2026-11-16T16:53:48.6910395Z|29bytes|Contenidoactualizado antes de delete|

Campos isCurrentVersion/deleted devueltosnull; no se los interpreta como confirmación de versión soft-deleted. Ausencia de blobactual demostrada por listadoactivo vacío. La documentación de versionado explica que delete sin versionID conserva versiones anteriores y elimina la versiónactual como tal.

**Importante para limpieza futura:** lifecycle aprobado filtra **tfstate/wordle/aks-demo.tfstate**, no validation/backend-lease-test.txt. Las dos versiones **no tienen expiración automática demostrada** por esa policy. Softdelete7d no elimina por sí solo versiones anteriores que no se hayan borrado. No se garantiza que desaparezcan a7d ni que el coste sea temporalmente acotado por esa retención.

Esto no impidePASS: el alcance permite datos recuperables y prohíbe purgar/versiondelete/cambiarlifecycle. Se conservan; cualquier retirada específica futura necesita autorización y revisión de permisos, sin ampliarlos automáticamente. [Comportamiento oficial de delete con versioning y softdelete](https://learn.microsoft.com/en-us/azure/storage/blobs/versioning-overview).

## 15. Coste residual estimado

Dos versiones, **60bytes lógicos** en total; no se equipara con capacidad facturable exacta (bloques, metadatos/mínimos y medidores pueden influir). Referencia Sweden del preflight16/11: HotLRS0,0184USD/GB-mes, write/list0,050USD/10K y read/other0,004USD/10K, sin impuestos/egreso/otroscargos.

Ejemplo solo aritmético, no factura:60/(1024^3)×0,0184 ≈ **0,00000000103USD/mes** de capacidad lógica. Operaciones de uploads/listados/descargas/lease/delete se facturan según medidor; no se capturó un contador facturable exhaustivo ni se promete coste0 o un totalexacto. El coste de operaciones domina esa capacidad diminuta. Las versiones pueden persistir más de7d por el filtro existente.

No recursos Compute/AKS/red/almacenamiento adicionales aprovisionados. No presupuestos/alertas ni cambio de retención para reducir coste.

## 16. Incidencias

Ningún fallo inesperado en la prueba. **LeaseIdMissing es el resultado negativo esperado**, confirmado por contenido/ETag y lease activo; no incidencia de autenticación o firewall. Release, escritura posterior y limpieza completados dentro de la misma ejecución.

No reintentos de escritura innecesarios, concurrencia, cambios de métodoauth, permisos o red. El único residuo son las dos versiones autorizadas a conservar; su exclusión del lifecycle se documenta expresamente.

## 17. Resultado de la validación

**PASS:** autenticaciónEntra, escritura, lecturaexacta, leasefinitoactivo, rechazo específico sinID, contenidoprotegido, releaseexplícito, actualización/lecturaposteriores, borradológico, ausencia de estado y seguridadintacta comprobados sobreAzure real. Informe creado y pendientes previos preservados.

No equivale a ejecutar el backendTerraform ni a comprobar su protocolo completo/concurrencia entre procesosTerraform. Aquí se probó el mecanismo de leaseBlob con CLI secuencial conforme al alcance.

## 18. Estado de Gate A y AKS

**Gate A permanece GO**, con evidencia funcional adicional de escritura/lectura/lease, y configuración del bootstrap intacta. **AKS permanece NO-GO** hasta sus restantes prerrequisitos y autorización específica.

No Terraform init/plan/apply/destroy, AKS, cambiosRBAC/firewall/lifecycle/retención, claves/SAS, blobsestado o configuraciónTerraform. Sin staging, commits/push o cambioshistorialGit. No alteración de informesprevios u otrosarchivospendientes. Único entregable local persistente nuevo: este informe; contenidos/descargas locales fueron temporales y eliminados.

## 19. Próxima acción recomendada

Revisar esta evidencia y, en incremento separado autorizado, preparar el uso real del backend/configuración externa y resolver los demás prerrequisitos deGateB. **No ejecutar Terraform automáticamente.** Registrar las dosversionesvalidation como remanente para decisión de limpieza específica posterior; no purgar ni ampliar lifecycle/RBAC por rutina.

Se detiene aquí. Fuentesoficiales consultadas16/11/2026: [leaseCLI](https://learn.microsoft.com/en-us/cli/azure/storage/blob/lease), [operacionesBlobCLI](https://learn.microsoft.com/en-us/cli/azure/storage/blob), [erroresBlob](https://learn.microsoft.com/en-us/rest/api/storageservices/blob-service-error-codes), [versioning](https://learn.microsoft.com/en-us/azure/storage/blobs/versioning-overview). Evidenciaprimaria: salidasAzureCLI y comparacionesbyte/configuración de estaejecución, sinIDlease ni credenciales.
