# FIN-04 â€” Baseline CI y artefactos

Fecha: 10/11/2026. Resultado: **FIN-04 PARTIAL**.
Rama: `codex/pg01-07-consolidation`. HEAD sin cambios: `3a149b8964e631a22666ba4ea13281bf39188f8f`.

## ImplementaciÃ³n

- `.github/workflows/ci.yml`: el job frontend ejecuta `npm ci`, los 12 casos Vitest y el build. El guard exige 12 aprobados, cero pendientes/todo y Ã©xito; cualquier error detiene el job. Conserva el JSON de pruebas como artefacto durante siete dÃ­as.
- El job Docker etiqueta ambas imÃ¡genes con la revisiÃ³n y ejecuta `scripts/verify_ci_images.py`. Conserva un JSON con revisiÃ³n, ID local inmutable, tamaÃ±o, arquitectura, usuario, RepoDigests disponibles y comprobaciones de runtime. No exporta variables de entorno ni logs.
- El script arranca los runtimes de producciÃ³n por ID, con `--pull=never`, sin red, puertos ni volÃºmenes, filesystem de solo lectura y usuario no privilegiado. Comprueba HTTP y healthcheck; elimina Ãºnicamente sus contenedores identificados mediante etiqueta aleatoria.
- GHCR permanece deshabilitado con `false`; se aÃ±ade ademÃ¡s la condiciÃ³n explÃ­cita push a main. No se otorga permiso de escritura a paquetes. Los otros cinco jobs no han cambiado.

## ValidaciÃ³n y evidencia

- Vitest: **12 aprobados, cero omitidos/todo**. Guard real ejecutado con ese JSON; rechaza cuatro fixtures con omisiÃ³n, todo, recuento incorrecto o fallo.
- `npm run build`: satisfactorio. Builds Docker de ambos targets runtime: satisfactorios.
- backend: `sha256:aeaecb09e25db037a0cada651faef8d4db2ef8b54c8486e4804b06a97a041a9c`; 314418106 bytes; usuario `10001:10001`; HTTP 200 y healthy. Runtime verificado contra el mismo ID.
- frontend: `sha256:424c2fdfd6b21dd93dfcf53a7071714eab9470879ad28564ae867daf51003407`; 92817635 bytes; usuario `nginx`; HTTP 200 y healthy. Runtime verificado contra el mismo ID.
- Los dos contenedores temporales se eliminaron; no quedan contenedores con etiqueta `wordle.fin04`. Las imÃ¡genes locales se conservan bajo `wordle-fin04-backend:local` y `wordle-fin04-frontend:local`.
- YAML parseado y estructura de ocho jobs comprobada; sintaxis Python vÃ¡lida; `git diff --check` satisfactorio. No hay actionlint disponible: no se afirma validaciÃ³n con ese validador especÃ­fico.
- Ãšltimo baseline remoto consultado: [run 42795319821](https://github.com/lromerob/wordle/actions/runs/42795319821), correspondiente al HEAD indicado: siete jobs satisfactorios (backend, PostgreSQL, frontend, Docker, Kustomize, kind y Terraform); GHCR omitido. Los guards versionados exigen 55 casos offline, nueve CORS y once PostgreSQL sin omisiones. No se descargaron logs autenticados ni se repitieron esas suites sin cambios.
- Se preservaron por SHA-256 los doce informes histÃ³ricos y todos los archivos preexistentes, salvo el workflow autorizado.

## ReproducciÃ³n local

Desde la raÃ­z, con Node, Docker y Python disponibles (en Windows se puede usar `.venv\Scripts\python.exe`):

```sh
npm --prefix frontend ci
npm --prefix frontend test -- --reporter=json --outputFile=../frontend-tests.json
npm --prefix frontend run build
docker build --target runtime --label org.opencontainers.image.revision=<SHA_COMPLETO> -t wordle-fin04-backend:local backend
docker build --label org.opencontainers.image.revision=<SHA_COMPLETO> -t wordle-fin04-frontend:local frontend
python -B scripts/verify_ci_images.py --revision <SHA_COMPLETO> --backend wordle-fin04-backend:local --frontend wordle-fin04-frontend:local --output <RUTA_TEMPORAL>/wordle-images.json
```

Para evitar archivos locales de resultados en el repositorio, sustituir tambiÃ©n `../frontend-tests.json` por una ruta temporal absoluta. En CI ambas evidencias se guardan en RUNNER_TEMP y se suben como artefactos de Actions; no son imÃ¡genes publicadas.

## Pendiente para cierre

1. Autorizar posteriormente commit/push y observar una ejecuciÃ³n remota de los nuevos pasos. El run citado acredita el baseline anterior, no estos cambios.
2. Verificar los paquetes y digests de manifiesto publicados en GHCR cuando exista autorizaciÃ³n para ese flujo. El ID local permite demostrar build/runtime inmutable en Docker, pero **no acredita publicaciÃ³n ni un digest recuperado desde GHCR**. Esta iteraciÃ³n no publica imÃ¡genes ni consulta paquetes privados.

La comprobaciÃ³n HTTP del backend es de liveness; no acredita conexiÃ³n PostgreSQL, flujo de juego ni proxy integrado. Esas integraciones tienen evidencia previa en el baseline CI. No se han tocado PG-05/PG-06, aplicaciÃ³n, infraestructura, credenciales ni plan FIN. FIN-04 permanece pendiente; no hay commits ni push.


## FIN-04B — Evidencia remota posterior a consolidación

Resultado: **FIN-04B PASS** (10/11/2026). FIN-04 continúa **PARTIAL**, pendiente de la comprobación de digests publicados en GHCR.

- Preflight: rama y HEAD esperados; índice vacío; únicamente los tres archivos FIN-04 previstos; remoto sin divergencia. Identidad de autor y committer: Leonardo Romero, noreply personal autorizado.
- Commit y HEAD remoto: `774405e6b92c33b438509832c6722605fee7d289`, mensaje `feat(devops): extend CI with frontend tests and image verification`. Incluye exclusivamente el workflow, `scripts/verify_ci_images.py` y este informe en su versión previa a esta actualización.
- Un único push normal a `origin codex/pg01-07-consolidation`; main intacto.
- [Workflow 42809607914](https://github.com/lromerob/wordle/actions/runs/42809607914), evento push, intento 1, SHA coincidente: **completed / success**.
- Siete jobs satisfactorios: backend offline, PostgreSQL real, frontend, Docker, Kustomize, kind efímero y Terraform. GHCR: **skipped** intencionadamente. No existe despliegue Azure en este workflow.
- Backend: 55 pruebas offline y nueve CORS; integración: once PostgreSQL; frontend: doce. Los pasos respectivos terminaron satisfactoriamente y sus guards versionados exigen esos recuentos sin omisiones. El nuevo paso frontend se ejecutó realmente; no se deduce su ejecución únicamente del éxito global.
- Verificación por ID inmutable: paso `Verify runtime by immutable local image ID and record evidence` ejecutado y satisfactorio; también pasó la conservación del JSON de imágenes. Ambos runtimes debieron alcanzar HTTP 200 y healthy para que ese paso finalizase correctamente.
- Artefactos remotos confirmados mediante API: `wordle-frontend-tests-1` (1207 bytes comprimidos) y `wordle-images-1` (575 bytes comprimidos), no expirados al revisar. Son tamaños de artefactos, no tamaños de imágenes. No se descargó su contenido ni los logs autenticados; los recuentos se acreditan mediante los guards obligatorios y el éxito de cada paso, no mediante una transcripción de logs.
- Advertencia de mantenimiento: acciones que usan Node.js 20/24; no se interpreta como vulnerabilidad confirmada ni se corrige en este incremento.
- Los doce informes históricos conservan sus SHA-256. Índice vacío; esta actualización documental queda sin commit para una consolidación posterior. No hubo segundo commit ni segundo push, publicación GHCR, acceso a Supabase ni cambios en PG-05/PG-06.

El requisito pendiente de publicación/digests GHCR no queda satisfecho por estos artefactos de Actions ni por los IDs locales. El plan FIN no se modifica y no se inicia FIN-05.

## FIN-CONSOLIDATE — preparación de publicación, 10/11/2026

Se consolida FIN-05 a FIN-15 y se habilita el job GHCR existente tras los siete controles CI. Publicación exclusivamente por push a main o a codex/pg01-07-consolidation; la rama de proyecto constituye la excepción expresamente autorizada en FIN-CONSOLIDATE. Pull requests y ejecuciones manuales de CI no publican. GITHUB_TOKEN y packages:write quedan limitados al job publicador; no hay credenciales personales ni latest. Cada imagen llevará el SHA completo y se descargará de GHCR por digest, comprobando revisión/ID y runtime aislado HTTP 200/healthy. Referencias y resultados quedarán como artefacto y anotaciones del run.

Validación local de esta consolidación: Python AST, YAML/JSON, Bash y Python embebido en el workflow; cuatro pruebas de telemetría aprobadas; seis perfiles Kustomize correctos (6/10/19/19/27/63 objetos), sin valores de Secret. Terraform 1.9.8 fmt/init sin backend/validate satisfactorios en copia temporal: el primer intento con lock readonly impidió completar el hash Linux; con el init normal de CI se completó solo en esa copia y validate pasó. No se modifica el lock del repositorio ni se opera Azure. No se repiten demos kind completas; sus JSON existentes confirman PASS local.

FIN-04 permanece PARTIAL hasta la evidencia remota y GHCR. El criterio histórico «publicación solo en main» se conserva en el plan y no se da por satisfecho con la excepción autorizada de rama. FIN-05 conserva aceptación AKS pendiente; publicar imágenes no acredita un despliegue Azure. Los doce informes históricos se excluyen y se verifican por SHA-256.

## FIN-CONSOLIDATE — GHCR y CI verificados

Commit fuente publicado: `782d37abaf96471f8db0e637a415647b5055cb96`. [Workflow satisfactorio](https://github.com/lromerob/wordle/actions/runs/42840960356): ocho jobs success, incluidos los siete controles previos y el publicador GHCR. Guards exitosos: 55 backend, 9 CORS, 11 PostgreSQL y 12 frontend, sin omisiones; cuatro pruebas adicionales de telemetría aprobadas. Se ejecutaron builds, runtime por ID, seis renders Kustomize, smoke kind y Terraform. Advertencia Node.js 20/24 de mantenimiento, sin convertirla en vulnerabilidad confirmada.

Referencias publicadas y verificadas (linux/amd64):

- Backend: `ghcr.io/lromerob/wordle-backend@sha256:cb070479c18b6c0edbdc469774b55a09f31397809d7449f64f9fd86fbd1b388a`; tamaño local descomprimido 315335981 bytes.
- Frontend: `ghcr.io/lromerob/wordle-frontend@sha256:411839215543e410458e5de93850f4ad5de16f66b181285b5a055b583821084f`; tamaño local descomprimido 92817925 bytes.

Ambas usan etiqueta del SHA completo y etiqueta OCI revision coincidente. El publicador, autenticado únicamente mediante GITHUB_TOKEN con packages:write limitado a ese job, descargó ambas por digest, comprobó igualdad con el ID construido y verificó HTTP 200/healthy en contenedores sin red/puertos/credenciales. Artefacto wordle-ghcr-images-1 y anotaciones contienen las referencias. También se ejecutó docker pull por ambos digests desde Windows, exit 0 y revisión coincidente; no se configuraron nuevas credenciales. Los tamaños anteriores no son tamaños comprimidos de descarga. AKS fija estos digests; demo-kind/Blue-Green/observabilidad conservan sus imágenes locales. No se usa latest.

**FIN-04 PARTIAL por criterio original**: la evidencia técnica de artefactos ya está satisfecha, pero el plan exige publicación solo en main y esta publicación usa la excepción de rama autorizada por FIN-CONSOLIDATE. No se afirma haber cumplido ese requisito original ni se modifica silenciosamente. **FIN-05 PARTIAL**: dependencia técnica GHCR resuelta; validación real AKS/FIN-18 sigue pendiente. Ninguna publicación acredita Azure, CSI o capacidad gestionada. No se ha desplegado Azure, ejecutado apply ni modificado PG-05/PG-06. Los doce históricos siguen excluidos e íntegros.
