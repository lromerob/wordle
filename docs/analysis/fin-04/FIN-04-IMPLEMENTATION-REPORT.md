# FIN-04 — Baseline CI y artefactos

Fecha: 10/11/2026. Resultado: **FIN-04 PARTIAL**.
Rama: `codex/pg01-07-consolidation`. HEAD sin cambios: `3a149b8964e631a22666ba4ea13281bf39188f8f`.

## Implementación

- `.github/workflows/ci.yml`: el job frontend ejecuta `npm ci`, los 12 casos Vitest y el build. El guard exige 12 aprobados, cero pendientes/todo y éxito; cualquier error detiene el job. Conserva el JSON de pruebas como artefacto durante siete días.
- El job Docker etiqueta ambas imágenes con la revisión y ejecuta `scripts/verify_ci_images.py`. Conserva un JSON con revisión, ID local inmutable, tamaño, arquitectura, usuario, RepoDigests disponibles y comprobaciones de runtime. No exporta variables de entorno ni logs.
- El script arranca los runtimes de producción por ID, con `--pull=never`, sin red, puertos ni volúmenes, filesystem de solo lectura y usuario no privilegiado. Comprueba HTTP y healthcheck; elimina únicamente sus contenedores identificados mediante etiqueta aleatoria.
- GHCR permanece deshabilitado con `false`; se añade además la condición explícita push a main. No se otorga permiso de escritura a paquetes. Los otros cinco jobs no han cambiado.

## Validación y evidencia

- Vitest: **12 aprobados, cero omitidos/todo**. Guard real ejecutado con ese JSON; rechaza cuatro fixtures con omisión, todo, recuento incorrecto o fallo.
- `npm run build`: satisfactorio. Builds Docker de ambos targets runtime: satisfactorios.
- backend: `sha256:aeaecb09e25db037a0cada651faef8d4db2ef8b54c8486e4804b06a97a041a9c`; 314418106 bytes; usuario `10001:10001`; HTTP 200 y healthy. Runtime verificado contra el mismo ID.
- frontend: `sha256:424c2fdfd6b21dd93dfcf53a7071714eab9470879ad28564ae867daf51003407`; 92817635 bytes; usuario `nginx`; HTTP 200 y healthy. Runtime verificado contra el mismo ID.
- Los dos contenedores temporales se eliminaron; no quedan contenedores con etiqueta `wordle.fin04`. Las imágenes locales se conservan bajo `wordle-fin04-backend:local` y `wordle-fin04-frontend:local`.
- YAML parseado y estructura de ocho jobs comprobada; sintaxis Python válida; `git diff --check` satisfactorio. No hay actionlint disponible: no se afirma validación con ese validador específico.
- Último baseline remoto consultado: [run 42795319821](https://github.com/lromerob/wordle/actions/runs/42795319821), correspondiente al HEAD indicado: siete jobs satisfactorios (backend, PostgreSQL, frontend, Docker, Kustomize, kind y Terraform); GHCR omitido. Los guards versionados exigen 55 casos offline, nueve CORS y once PostgreSQL sin omisiones. No se descargaron logs autenticados ni se repitieron esas suites sin cambios.
- Se preservaron por SHA-256 los doce informes históricos y todos los archivos preexistentes, salvo el workflow autorizado.

## Reproducción local

Desde la raíz, con Node, Docker y Python disponibles (en Windows se puede usar `.venv\Scripts\python.exe`):

```sh
npm --prefix frontend ci
npm --prefix frontend test -- --reporter=json --outputFile=../frontend-tests.json
npm --prefix frontend run build
docker build --target runtime --label org.opencontainers.image.revision=<SHA_COMPLETO> -t wordle-fin04-backend:local backend
docker build --label org.opencontainers.image.revision=<SHA_COMPLETO> -t wordle-fin04-frontend:local frontend
python -B scripts/verify_ci_images.py --revision <SHA_COMPLETO> --backend wordle-fin04-backend:local --frontend wordle-fin04-frontend:local --output <RUTA_TEMPORAL>/wordle-images.json
```

Para evitar archivos locales de resultados en el repositorio, sustituir también `../frontend-tests.json` por una ruta temporal absoluta. En CI ambas evidencias se guardan en RUNNER_TEMP y se suben como artefactos de Actions; no son imágenes publicadas.

## Pendiente para cierre

1. Autorizar posteriormente commit/push y observar una ejecución remota de los nuevos pasos. El run citado acredita el baseline anterior, no estos cambios.
2. Verificar los paquetes y digests de manifiesto publicados en GHCR cuando exista autorización para ese flujo. El ID local permite demostrar build/runtime inmutable en Docker, pero **no acredita publicación ni un digest recuperado desde GHCR**. Esta iteración no publica imágenes ni consulta paquetes privados.

La comprobación HTTP del backend es de liveness; no acredita conexión PostgreSQL, flujo de juego ni proxy integrado. Esas integraciones tienen evidencia previa en el baseline CI. No se han tocado PG-05/PG-06, aplicación, infraestructura, credenciales ni plan FIN. FIN-04 permanece pendiente; no hay commits ni push.
