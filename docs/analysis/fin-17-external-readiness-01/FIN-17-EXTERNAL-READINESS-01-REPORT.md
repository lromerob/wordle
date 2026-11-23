# FIN-17-EXTERNAL-READINESS-01

## 1. Resumen ejecutivo

**Auditoría externa BLOCKED para completar la verificación. AKS/CD NO-GO.**
La identidad humana Azure existente pudo verificarse mediante consulta real a
Microsoft Graph y lectura de perfil Azure CLI. No se han podido verificar las
configuraciones remotas de GitHub, GHCR ni los recursos Azure de despliegue.
No se declaran ausentes por falta de acceso o de datos de preflight.

Recuento sobre los 17 controles obligatorios: VERIFIED=1; MISSING=0;
MISCONFIGURED=0; NOT VERIFIED=7; BLOCKED=9; NOT APPLICABLE=0.
VERIFIED se limita a la sesión seleccionada AZ-01; no significa autorización ARM,
configuración OIDC, suscripción desplegable ni preflight completo.

Bloqueos de acceso/contexto: no cliente o sesión GitHub/GHCR autenticada utilizable
en las superficies disponibles; falta una ruta de configuración privada vigente
para contrastar inequívocamente el objetivo de despliegue. Se pidió al propietario
la ruta externa, sin solicitar secretos. No se ha recibido durante esta ejecución.
Los otros servicios no se consultaron mediante credenciales extraídas o nuevas sesiones.

## 2. Alcance y autorización

Solo lecturas de metadatos y este informe nuevo. Se revisaron los informes
FIN-17-PREPARATION-01 y FIN-17-RELEASE-GATES-01 completos, runbooks relevantes,
apply/destroy históricos del 22/11, workflows, helpers, contrato de store y ejemplos.
No se repitieron pruebas locales, builds, Kustomize ni demostraciones funcionales.
No se ejecutó Terraform ni operación Kubernetes alguna.

Se excluyeron expresamente login, account set, get-access-token, listKeys,
lectura/descarga de state, adquisición de lease, escrituras Blob, dispatch, cambios
RBAC y configuración de servicios. No se abrieron .env, caches de tokens,
credenciales Git, estado Terraform ni planes. No se leyeron valores de secrets.
Los UUID de contexto se compararon en memoria y no se reproducen aquí.

## 3. Estado Git inicial

Repositorio local Wordle del Escritorio; origin=https://github.com/lromerob/wordle.
Rama codex/pg01-07-consolidation; HEAD
4d56cf265cc5f0af8c72c64f2a93373660e8f122. Índice vacío; nueve versionados
modificados, 288 sin seguimiento. Inventario inicial: 469 archivos no ignorados,
con SHA-256 registrado para comprobar preservación.

Tracking local origin/codex/pg01-07-consolidation=4d56cf265cc5f0af8c72c64f2a93373660e8f122;
origin/main=86cbf8936dc04abc39b8bee26c37767328db13df.
Son referencias locales: **no** demuestran el SHA remoto actual ni sincronización.
No fetch/ls-remote/pull ni modificación de refs.

## 4. Identidades verificadas

Lecturas reales realizadas usando Azure CLI 2.86.0 ya instalada:

- az account show, proyección exclusiva de id/tenantId/state/user.type: coincidencia
  exacta con tenant/suscripción históricos aprobados de Wordle; perfil Enabled, user.
  account show puede devolver datos de perfil local; no prueba estado ARM fresco.
- az ad signed-in-user show --query id: Microsoft Graph respondió satisfactoriamente;
  coincidencia exacta del humano histórico aprobado. No se imprimieron UUID/email.

No login, cambio de suscripción, emisión explícita ni impresión de tokens. El primer
intento sandbox devolvió denegación de acceso local al perfil; la lectura autorizada
fuera del sandbox funcionó. Telemetría y log de archivo CLI se desactivaron únicamente
en el entorno de esos subprocesos. No se cambiaron configuraciones globales.

**Límite del preflight:** el contexto coincide con historia, pero no se encontró un
archivo privado de variables/objetivo vigente en las ubicaciones operativas conocidas.
Los ejemplos actuales son genéricos y no se usaron como autoridad ni se rellenaron.
Por ello se detuvo la consulta de recursos de esa suscripción hasta confirmar la ruta
aprobada, como exige el encargo. No se deduce una identidad CD a partir del humano.

## 5. GitHub y Actions

GitHub CLI no está en PATH ni en las ubicaciones de instalación habituales consultadas.
No hay GH_TOKEN/GITHUB_TOKEN en este proceso ni configuración gh en las rutas habituales
comprobadas por existencia. No se abrieron archivos de credenciales ni se pidió a Git
que revelase tokens. Las superficies de navegador habilitadas no ofrecen una sesión
GitHub existente: inventario con cero pestañas; no se inició sesión ni se creó una.
Esto describe el entorno accesible, no afirma que el propietario no tenga una sesión
en otro dispositivo o aplicación.

No fue posible realizar consultas autenticadas de repo/refs, runs/jobs, políticas,
permisos o reglas de rama. No se utilizaron lecturas anónimas como sustituto de la
identidad exigida. El CI remoto histórico satisfactorio no se presenta como último
CI verificado hoy. El ci.yml local sigue siendo evidencia de código, no de ejecución.

## 6. Environment

wordle-azure-demo solo está identificado en el workflow local. Existencia, reviewers,
branch policies, prevent-self-review, bypass, protección y nombres de variables/secrets:
**BLOCKED** para consulta GitHub. Ningún resultado vacío se interpretó como ausencia.
No se leyeron valores de secrets ni se consultaron valores de variables genéricas.
El gate local requiere reviewers, pero no prueba que estén configurados remotamente.

## 7. Runner

El YAML exige self-hosted/linux/x64/wordle-azure. No se pudo consultar registro,
online/busy, grupo, scope, repositorios permitidos o compatibilidad con environment.
No se declara MISSING. Sin ejecutar jobs no se puede demostrar salida IPv4,
herramientas, mount ni persistencia entre ejecuciones. No se registra ni propone
sustituir automáticamente por un runner público hospedado.

## 8. Azure OIDC/RBAC

La sesión humana está disponible; el principal destinado a CD no está identificado
inequívocamente mediante metadatos aprobados. El workflow contiene nombres de secretos,
no una identidad real consultable. No se solicitó leer AZURE_CLIENT_ID desde secrets.

Issuer/audience/subject, app/SP, federated credentials y asignaciones/scopes ARM:
NOT VERIFIED. No se enumeraron indiscriminadamente aplicaciones, usuarios o roles.
No se emitió un ID token de prueba ni se modificó federación/RBAC. Incluso una
federación visible sería configuración verificada, no autenticación funcional
probada; aquí tampoco se ha acreditado esa configuración real.

## 9. Terraform backend

Referencia histórica y configuración pública local: rg-wordle-state,
stwordletfgstate7c92d4, contenedor tfstate, key wordle/aks-demo.tfstate; Entra Blob auth.
Se conserva Sweden Central como referencia histórica, **no región actual consultada**.
No se leyó .terraform/terraform.tfstate ni el contenido del estado remoto.

Existencia, ubicación efectiva, public access, network ACL/firewall, auth, retención,
protección, contenedor/blob/lease y compatibilidad con principal CD: BLOCKED por
preflight privado. No GET de recursos/Blob, descarga, claves, lease ni prueba de
escritura. Un destroy histórico CLEAN no demuestra existencia/acceso actual del backend.

## 10. Red y cuotas

VERIFICACIÓN LOCAL ÚNICAMENTE: Terraform mantiene private_cluster_enabled=false,
allowlist API parametrizada, local accounts y Run Command deshabilitados. Es API
pública restringida, no Private AKS. No se conoce el /32 vigente de inputs privados.
No se reutilizó una IP histórica ni se imprimieron direcciones completas.

No se consultó un servicio externo de detección de IP, DNS o conectividad de AKS;
la autorización se limita a GitHub/Azure/GHCR y el clúster histórico fue destruido.
Salida actual operador/runner, compatibilidad de firewall Storage y cuota/SKU/región:
NOT VERIFIED o BLOCKED según matriz. No se creó túnel ni se cambió allowlist/cuota.

## 11. GHCR

images.lock.json conserva source_commit=4d56cf265cc5f0af8c72c64f2a93373660e8f122,
once referencias inmutables, entre ellas backend/frontend de lromerob/wordle.
No se cambió el lock ni se consideró la revisión histórica prueba de disponibilidad.

Consulta actual de manifest/config, plataforma linux/amd64, revisión OCI, digest,
permisos/visibilidad y dependencia de autenticación: BLOCKED. No se identificó un
cliente autenticado aprobado accesible; no se extrajeron credenciales Git, se emitieron
tokens de registro ni se descargaron capas. No se invocó ghcr_check.inspect porque
su flujo obtiene un token anónimo de pull nuevo y esta iteración exige credenciales
existentes aprobadas y prohíbe obtener tokens. Falta de acceso no equivale a digest
inexistente. La comprobación de las otras nueve imágenes no se amplió a registros
externos no autorizados.

## 12. Almacenamiento durable

Contrato private_store.py/runbook revisado: ruta externa, marker/UUID aprobados,
subdirectorios plans/selections/evidence/backups, no enlaces y permisos privados.
WORDLE_AZURE_PRIVATE_DIR y WORDLE_AZURE_STORE_ID no están definidos en este proceso.
Esto **no demuestra** que falten en GitHub; ese environment no pudo consultarse.

En las ubicaciones operativas conocidas del usuario solo se consultaron nombres y
metadatos; no se encontró marker/variables/target privado identificable. No se hizo
búsqueda masiva por el disco ni se abrieron planes/backups. Sin ruta aprobada no se
pueden verificar ACL, lectura, enlaces, ID, marker o directorios del store efectivo.
No se crearon carpetas/markers ni se probaron escrituras. Durabilidad física,
cifrado, backup/restore y continuidad entre runs: NOT VERIFIED; un marker no lo probaría.

## 13. Recuperación humana

Ejecutor parametrizado y runbook presentes. Se conservan confirmaciones exactas
PLAN WORDLE AKS y DESTRUIR WORDLE AKS, revisión de hash/inventario/fingerprint/lease,
control de concurrencia, exclusión del backend y verificación CLEAN/PARTIAL.
Independencia respecto de Actions comprobable en el diseño, no en operación real.

Humano confirmado mediante Graph. Terraform y kubelogin están presentes en sus
ubicaciones de usuario; versiones 1.9.8/0.2.22 son las verificadas históricamente,
no se ejecutaron ahora. No existe un target/workspace aprobado localizado en las
rutas conocidas, por lo que correspondencia e independencia del principal CD siguen
NOT VERIFIED. No se ejecutó el script, ni siquiera preflight; no planes ni simulación
con Azure. Recuperación operativa real NO PROBADA en este incremento.

## 14. Inventario residual

El informe LIVE-DESTROY-EXECUTION acredita históricamente CLEAN. No se ha consultado
inventario ARM actual, por falta de contraste con configuración privada vigente.
AKS/RG/red/IP/discos/identidades huérfanas/backend actuales: BLOCKED para verificación.
No se afirma que estén ausentes ni se recomienda CREATE con un inventario desconocido.
No se buscaron recursos similares o ajenos ni se ejecutó limpieza.

## 15. Matriz de preparación

| ID | Componente | Requisito | Estado | Evidencia | Bloqueo | Acción propuesta |
|---|---|---|---|---|---|---|
| GIT-01 | Repositorio y SHA | Identidad y SHA remoto actual | NOT VERIFIED | origin local apunta a lromerob/wordle; HEAD y tracking local coinciden en 4d56cf2…; no consulta remota autenticada | No cliente/sesión GitHub utilizable | Indicar cliente autenticado aprobado; consultar repo/ref sin fetch |
| GIT-02 | CI | Workflow, runs y siete gates reales | BLOCKED | ci.yml local revisado; último éxito histórico no reconsultado | Sin cliente/sesión GitHub autenticada accesible | Leer runs/jobs para SHA, sin ejecutar workflow |
| GIT-03 | CD | Registro/habilitación/dispatch remoto | BLOCKED | azure-demo.yml existe localmente SIN seguimiento; gate/OIDC/reviewers solo código local | No se pudo consultar API GitHub | Consultar workflows y archivo remoto; no publicar ni activar |
| GIT-04 | Environment | wordle-azure-demo y protecciones | BLOCKED | Nombre y controles esperados en YAML; ningún GET autenticado disponible | Autenticación/cliente GitHub no disponible | Leer reviewers, self-review, bypass, ramas y nombres de variables/secrets |
| GIT-05 | Runner | Linux x64 dedicado y alcance | BLOCKED | Etiquetas esperadas self-hosted/linux/x64/wordle-azure; existencia no consultada | Autenticación/cliente GitHub no disponible | Consultar runners/grupo/acceso sin lanzar job |
| AZ-01 | Sesión Azure | Tenant/suscripción/operador seleccionados | VERIFIED | az account show: user/Enabled y coincidencia exacta con contexto histórico; Graph confirma humano histórico | Contraste con inputs privados de despliegue sigue pendiente; no valida ARM ni identidad CD | Aportar ruta privada vigente; no cambiar contexto |
| AZ-02 | OIDC | Principal CD y federación exacta | NOT VERIFIED | Workflow referencia nombres de secrets; ningún client ID aprobado disponible como metadato externo | No identificación inequívoca del principal CD | Indicar referencia privada al client ID y consultar app/SP/federaciones |
| AZ-03 | ARM | Roles y scopes efectivos del principal CD | NOT VERIFIED | Identidad humana verificada no equivale a identidad CD; no consultas RBAC | Principal CD y objetivo privado no determinados | Lectura acotada de asignaciones/permisos tras resolver preflight |
| AZ-04 | Backend Terraform | Existencia/seguridad actual de Storage y contenedor | BLOCKED | Coordenadas históricas y backend.hcl.example revisados; no GET a recursos o Blob | Preflight exige confirmar instalación contra configuración privada vigente | Consultar metadatos ARM/Blob login, sin state, claves, lease ni escritura |
| AZ-05 | Blob | Roles data-plane y compatibilidad CD | BLOCKED | Entra auth previsto; no principal CD inequívoco ni consulta de roles Storage | Preflight/identidad CD pendientes | Consultar permisos data-plane visibles sin probar escritura |
| AZ-06 | Red | API pública /32 y salidas compatibles | NOT VERIFIED | Terraform mantiene API pública restringida; no input privado /32 ni salida runner verificados | Inputs externos y runner no disponibles | Confirmar /32 privada, reglas Storage y salida aprobada sin abrir reglas |
| AZ-07 | Cuotas/SKU | Capacidad regional/familia y disponibilidad actual | BLOCKED | Sweden Central/D4s_v5 figuran en configuración e historia, no lectura actual de cuota/SKU | Preflight privado no cerrado | Lectura acotada de usage/SKU en suscripción/región aprobadas |
| REG-01 | GHCR | Digests/manifiestos/plataforma/revisión actuales | BLOCKED | Lock local fija once referencias, dos de Wordle en GHCR; no consulta actual al registro | No cliente/autenticación GHCR existente aprobado identificado; no se obtuvieron tokens | Usar cliente aprobado para lectura de manifiestos/config OCI, sin capas ni publicación |
| OPS-01 | Custodia | Mount durable/marker/ID/permisos | NOT VERIFIED | Variables de ruta/store ID ausentes en proceso actual; no archivos privados candidatos encontrados en ubicaciones operativas conocidas | Ruta/ID aprobados no facilitados; runner no inspeccionable | Indicar rutas; revisar metadatos/ACL/marker sin escritura y continuidad por evidencia |
| OPS-02 | Retirada | Objetivo privado/humano/herramientas/independencia | NOT VERIFIED | Humano confirmado; scripts/runbook parametrizados presentes; binarios locales presentes; no target privado localizado | Falta target/workspace externos vigentes; sin prueba operativa autorizada | Indicar rutas y verificar correspondencia; no ejecutar script ni generar plan |
| OPS-03 | Residual Azure | Ausencia o inventario Wordle actual | BLOCKED | Informe histórico destroy CLEAN revisado, no inventario ARM actual | Preflight privado pendiente | Consultar únicamente RG/AKS/recursos aprobados tras confirmar objetivo |
| CAP-01 | Captura | Host efectivo y herramientas configuradas | NOT VERIFIED | Windows actual tiene Node 24.18.0, Playwright 1.62.1 y Edge 158.0.4370.33; variables de captura no configuradas | No host runner/captura acordado ni evidencia de acceso/mount | Definir host aprobado y rutas existentes; no instalar ni ejecutar captura |

Cada acción de consulta sigue siendo de lectura y requiere una identidad/contexto
aprobados y disponibles. Cualquier configuración posterior exige autorización
separada; esta matriz no la concede. No hay MISSING o MISCONFIGURED demostrados
por consultas remotas completas, y no se fuerza esa clasificación por falta de acceso.

## 16. Bloqueantes demostrados

1. No se dispone de cliente/sesión GitHub/GHCR autenticada utilizable en este entorno.
2. No se ha proporcionado/localizado la ruta del objetivo privado aprobado vigente;
   falta cerrar el contraste previo a consultas de recursos Azure.
3. El workflow CD y helpers de release/store siguen sin seguimiento localmente;
   no forman parte del HEAD identificado. La situación de otros commits remotos es
   desconocida: no se afirma ausencia de un workflow remoto por este dato local.

Estos bloqueos son distintos de afirmar runner/environment/federación ausentes.

## 17. Dependencias no verificadas

Runner/environment/reviewers/bypass; identidad CD/federación/RBAC ARM/Blob;
backend real/firewall/retención; /32/salida; cuota/SKU; inventario residual;
GHCR actual; mount durable; objetivo/workspace humano; host capturador efectivo.
No se trasladan resultados offline/históricos a estos controles externos.
No consta una operación cloud pendiente conocida en los informes consultados;
no se ha podido confirmar que no haya operaciones pendientes actuales en Azure.

## 18. Acciones recomendadas

1. Propietario: indicar rutas externas aprobadas de variables/objetivo humano,
   backend/store y metadatos no secretos de identidad CD. No enviar credenciales
   por chat ni completar plantillas dentro del repositorio.
2. Propietario: indicar un cliente/sesión GitHub/GHCR ya autenticado y aprobado,
   accesible al agente. Si requiere nueva autenticación/MFA o instalación,
   intervención manual separada; no forzarla ni extraer tokens.
3. Retomar exclusivamente las lecturas bloqueadas, validar identidad antes de cada
   servicio y registrar resultados reales. Solo entonces decidir si hacen falta
   autorizaciones de configuración (runner, environment, federación, RBAC o custodia).

No se solicita aún autorización para crear/configurar esos recursos: su ausencia
no está demostrada. Tampoco se recomienda ejecutar CD para descubrir qué falta.

## 19. Criterios GO/NO-GO

NO-GO. Faltan controles externos esenciales y comprobación de estado residual actual.
El PASS local de release gates no sustituye las lecturas pendientes. Para GO se
necesitan fuentes consolidadas/CI del SHA final, identidad/runner/protección y
permisos verificados, red/cuota/backend/mount adecuados, imágenes recuperables,
recuperación humana viable y autorización expresa de la ventana/coste.
Este informe no concede ninguna de esas autorizaciones.

## 20. Próximo incremento

Resolver únicamente el acceso al cliente aprobado y las rutas privadas del preflight;
continuar FIN-17-EXTERNAL-READINESS con lectura real. No implementar ni consolidar,
activar workflow, publicar o desplegar automáticamente.

## 21. Integridad Git final

Misma rama y HEAD; índice vacío; nueve versionados modificados y 289 sin seguimiento.
Único archivo añadido por esta iteración: este informe. Los 469 archivos previos
permanecen idénticos por SHA-256; no se elimina ni altera ninguno. Se preservan los
doce informes históricos, siete dossiers y todo el trabajo local anterior.

Sin staging/commit/push/fetch/pull/reset/clean/rebase/cambio de rama. No escritura
Azure, GitHub/GHCR, Terraform/backend, Kubernetes ni recursos PG-05/PG-06; no nuevas
herramientas, autenticación interactiva o lectura/impresión de secretos.
Las lecturas de CLI pueden usar su gestión interna normal de sesión; la integridad
comprobada por hash se refiere al repositorio, no a caches internos de herramientas.

Registro UTC de elaboración: 2026-11-22T16:38:55.795688+00:00
