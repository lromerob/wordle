# PUB-02 — Saneamiento y consolidación documental

Fecha: 09/11/2026. Sin add/commit/push, cambio de rama, fetch, pruebas, instalaciones, servicios o infraestructura. FIN-01 sigue pendiente. No se afirma ejecución remota de GitHub Actions.

## Alcance y preservación

Se leyeron íntegros los tres informes PUB-01 y los traspasos PG-07/PG-06, además de README/plantillas/notas, workflow, consumidores CI, scripts y material Supabase. PUB-01 aportó las **nueve rutas** y los **siete informes** exactos; no se sustituyeron por aproximaciones.

Estado inicial: rama codex/devops-04a1-hardening, HEAD a666b17680781a24889ea774778019995d3fca45; 13 archivos modificados, 62 nuevos (incluidos tres PUB-01), índice vacío. Los hashes se registraron solo en memoria, sin copiar backups ni abrir archivos privados.

Se modifican once archivos existentes del árbol, aunque varios aún no están versionados, y se crean estos tres informes. Todo el código, pruebas, dependencias/lock, migración original, Dockerfiles, Compose, Kubernetes, Terraform, workflow y demás documentos previos permanecen idénticos a la entrada PUB-02. No se modifican los scripts históricos ni se mueven archivos.

## Cambios efectivos

| Archivo | Cambio y motivo |
|---|---|
| README.md | Manual PostgreSQL16/psycopg async: instalación, pruebas, Compose, kind, configuración/Secret nuevos, CI pendiente, límites y enlaces; conserva contexto de validación anterior como historia |
| backend/.env.example | Seis variables PG reales, valores locales de ejemplo y password vacío; explica exportación explícita sin carga automática de .env; distingue WORDLE_DB_* de Compose |
| backend/SECURITY-NOTES.md | Sustituye afirmaciones obsoletas por transacciones/locks/roles actuales y límites reales de identidad, CORS, readiness, COMMIT y recuperación |
| supabase/README.md | Añade nota operativa y catálogo vigente/histórico; conserva íntegra la sección FIN-01B original como registro anterior a PG; excluye allow_all del bootstrap vigente |
| docs/analysis/pg-05/PG-05-IMPLEMENTATION-REPORT.md | Sustituye rutas personales de estado/backup por LOCALAPPDATA y añade nota de saneamiento |
| docs/analysis/pg-05/PG-05-PG06-HANDOFF.md | Sustituye prefijo personal del directorio privado; conserva evidencia y alcance temporal original |
| docs/analysis/pg-05/PG-05-TEST-RESULTS.md | Sustituye ubicación personal de capturas por marcador de evidencias privadas; conserva nombres de capturas/resultados |
| docs/analysis/pg-06/PG-06-IMPLEMENTATION-REPORT.md | Sanea ubicación privada y normaliza marcador de entorno; conserva comandos y UID técnicos |
| docs/analysis/pg-06/PG-06-PG07-HANDOFF.md | Revisión sin datos personales nuevos; normaliza LOCALAPPDATA y explica conservación de identificadores de prueba |
| docs/analysis/pg-06/PG-06-TEST-RESULTS.md | Sanea ruta de captura; mantiene literalmente conteos, versiones, tiempos y UID de persistencia |
| docs/analysis/pg-07/PG-07-NEXT-STEPS.md | Revisión y nota de alcance: nombres de recursos retenidos son trazabilidad técnica, no datos personales ni prerrequisitos de otro clon |

En los siete informes se ha comprobado igualdad exacta contra el texto inicial tras aplicar únicamente las sustituciones de rutas y la nota PUB-02. No se han cambiado resultados, fechas, versiones, conteos, conclusiones ni comandos de prueba. LOCALAPPDATA es un marcador de entorno, no una ubicación privada revelada; <evidencias-privadas> conserva el significado de capturas externas sin publicarlas. Los UID técnicos siguen siendo evidencia de igualdad de PVC/pod, no identificadores personales de la máquina.

## Nueve dependencias CI, revisión individual

Todas son **necesarias**, existen, están sin seguimiento y **no están ignoradas**. No se modificó su contenido ni se añadieron al índice. Preparadas significa revisadas/propuestas en el manifiesto, NO versionadas.

| Ruta exacta | Función y consumidor | Revisión de seguridad/portabilidad |
|---|---|---|
| backend/app/repository.py | WordleRepository SQL/locks; importado por database.py, routers/pruebas | SQL parametrizado; sin DSN/password literal ni ruta Windows fija |
| backend/tests/test_postgres_adapter.py | Contratos/adaptador/errores/pool; discovery backend/tests del workflow | Dobles y guardas, sin credenciales productivas; pathlib relativo |
| backend/tests/test_transactions.py | Scope de transacciones, rollback y coordinación; discovery backend/tests | Fixtures en memoria y fallos controlados; sin secretos/rutas privadas |
| backend/integration/run_pg07_ci.py | Adapter PostgreSQL services; invocado por ci.yml | Restringe contenedor/puerto/base/roles, password efímero de proceso; ROOT relativo, no LOCALAPPDATA |
| backend/integration/run_pg04.py | Bootstrap/catálogo/suite/outage; importado por run_pg07_ci y ejecutable opt-in local | Passwords aleatorios en memoria, DB nueva; ROOT relativo; rama Windows selector acotada al proceso |
| backend/integration/test_postgres_integration.py | Once tests reales; cargados por ejecutores PG-04/07 | SQL de fixture/rollback solo tras bootstrap de DB nueva; no credenciales reales |
| supabase/migrations/20261108000100_initial_wordle.sql | Baseline estructural; Compose, bootstrap kind, prepare PG-04/07 | Sin passwords ni RLS allow_all; archivo/ruta/hash intactos |
| supabase/tests/schema_contracts.sql | Contratos catálogo; PG-04/06 y PG-07 por reutilización | No acceso externo ni datos privados; ruta relativa |
| docker/postgres/20-demo-words.sql | Cinco palabras demo; init Compose/kind y seed PG-07 | Solo fixture sintética, no passwords/datos históricos; ruta relativa |

Los scans léxicos no encontraron rutas Windows absolutas codificadas en los Python de estas dependencias. El runtime y todos sus consumidores deben publicarse como conjunto, no solo ci.yml. Los scripts PG-05/06 usan LOCALAPPDATA: el README declara ese requisito Windows y documenta un destino privado de entorno explícito para Linux sin cambiar ejecutores. Esa adaptación se revisó estáticamente; no se afirma una nueva validación Linux de Compose/kind.

## Material Supabase y selección histórica

Se conserva la ruta supabase/migrations/20261108000100_initial_wordle.sql, hash original da743e629094da2b7d126f7889c5d1ca72e63a232844feadea3798254b19b0cb. Catálogo/generador y pruebas auxiliares siguen siendo reutilizables. No se copia un segundo esquema.

allow_all.sql, prototype_access.sql y local_backend_smoke.py se preservan sin cambios como archivo histórico explícito. La nota nueva advierte que las políticas abiertas no son hardening ni parte del PostgreSQL operativo, y que el smoke Supabase es anterior a la transición. Se recomienda incluirlos con esa nota solo como historia; ningún workflow/Compose/bootstrap actual los invoca. No se ejecutaron ni se añadieron a inicialización.

Los informes FIN-01A/B/C y TFG-PLAN-001 se recomiendan como historia de decisiones, sin modificar sus estados/fechas. El README aclara aprobación posterior de la hoja de ruta y diferencia FIN-02 datos/recuperación de FIN-03 seguridad; no actualiza el backlog. PUB-01 también se mantiene intacto como snapshot anterior, no como decisión vigente tras correcciones.

## Estado de cada condición PUB-01

| Condición original | Resultado PUB-02 | Evidencia |
|---|---|---|
| Documentación vigente y plantilla | RESUELTA | README/notas reescritos sobre código real; seis variables de plantilla coinciden con database.py; password vacío |
| Privacidad de siete informes | RESUELTA | Rutas saneadas; comparación exacta demuestra que solo cambian sustituciones/nota; resultados técnicos preservados |
| Selección de históricos | RESUELTA para propuesta de publicación | Manifiesto explícito incluye trazabilidad con nota operativa separada; no se ejecutan scripts abiertos ni se destruyen originales |
| Nueve dependencias/conjunto coherente | RESUELTA en revisión local | Existencia/consumidores/exclusiones/scans comprobados; lista exacta futura, ninguna puesta en índice |
| Base de rama y revisión final del futuro índice | PARCIALMENTE RESUELTA | Comparadas referencias locales: origin/main...HEAD = 0/1; GitHub no actualizado/consultado y no se acuerda/cambia rama ni se crea índice por restricción |
| GitHub Actions real | PENDIENTE POSTERIOR AL PUSH | No es bloqueo por sí solo; conservar evidencias PG-07 como locales, no prometer run remoto |

No se considera resuelta la actualidad de main por limitarse a documentarla. Es la condición concreta pendiente que mantiene la decisión READY WITH CONDITIONS; no hay bloqueo técnico confirmado ni falta de código detectada.

## Validaciones realizadas

- Estado Git, índice vacío, refs locales, diff y git diff --check; sin fetch/operaciones de escritura Git.
- Preservación por hashes: solo los once archivos permitidos cambiaron; baseline/app/scripts/infra/workflow y documentos restantes intactos.
- Nueve archivos: existencia, consumidores, no ignorados, no versionados, lectura/scans acotados y rutas relativas.
- Plantilla backend: mismas seis PG* del código, password vacío, sin variables Supabase ni ruta personal. Plantillas siguen versionables; .env real sigue ignorado y no abierto.
- YAML del workflow analizado con PyYAML ya disponible; ocho jobs, PostgreSQL16.15, dependencia de builds, GHCR if:false y permisos sin packages:write. No actionlint instalado ni validación GitHub remota; workflow no modificado.
- Enlaces Markdown y referencias de archivos comprobados localmente; fences/whitespace y rutas documentales. No se visitaron URLs externas ni se leyeron marcadores privados.
- Búsqueda acotada de tokens/claves/JWT/URI con credenciales y asignaciones privadas sobre candidatos no ignorados; no secretos reales detectados. Los literales públicos exclusivos de CI y referencias a variables/generación aleatoria son los mismos casos justificados en PUB-01; no se muestran valores.

No se repiten 55 offline/once integración ni builds: no cambió código ejecutable. Los resultados anteriores PG-07 son históricos, no nuevas ejecuciones. No se crean contenedores o clústeres ni se operan PG-05/06.

## Riesgos residuales

main remoto/rama de publicación requieren comprobación y acuerdo en tarea autorizada; el índice final requerirá su propio scan/listado al prepararse. Quedan ejecución Actions real, diccionario completo, identidad, CORS/rate limiting, tags móviles y recuperación independiente. El estado Git actual aún contiene el trabajo acumulado sin versionar; esta consolidación no lo publica ni convierte scripts de ejemplo en configuración segura para producción. FIN-01 continúa pendiente.
