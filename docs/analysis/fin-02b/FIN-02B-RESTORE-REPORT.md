# FIN-02B — Restauración independiente PostgreSQL y HTTP

Fecha: 10/11/2026. **FIN-02B PASS**. Actualización autorizada del informe inicialmente BLOCKED BY FIN-02A. FIN-02 completo requiere revisión separada; no se cambia el plan ni se cierra automáticamente.

## Preflight

Rama codex/pg01-07-consolidation; HEAD da99b48b1cf8629ccee2566c03d4d3f6513f7fc9. Índice vacío, ningún cambio versionado y16 archivos sin seguimiento antes del ensayo. Leídos FIN-02-STARTING-POINT.md, informe de bloqueo anterior, baseline, integración/persistencia/roles y los tres archivos FIN-02A. FIN-02A documenta PASS: tres cargas, preservación ajena y55 offline/11 reales. Sus fuentes y evidencia se conservaron intactas, sin reinterpretar fixtures improvisadas como FIN-02A.

## Archivos y ejecución

- Nuevo: backend/integration/run_fin02b.py, procedimiento opt-in con herramientas existentes.
- Actualizado: este informe, único documento previo modificado por autorización expresa.

Desde la raíz, Python3.12 con dependencias existentes, Docker Linux y postgres:16.15 local:

```powershell
.\.venv\Scripts\python.exe -B backend/integration/run_fin02b.py --run-disposable-postgres
```

Sin flag termina con exit2 antes de crear recursos; no acepta DSN ni origen/destino preexistentes, no descarga imágenes ni instala dependencias. Crea nombres únicos comprobando que no existen. El informe es local/sin seguimiento; no se añadió ningún archivo al índice.

## Entorno y procedimiento real

PostgreSQL16.15 (Debian16.15-1.pgdg13+2), imagen local oficial ya disponible; cliente psql/pg_dump/pg_restore de esa imagen. Windows con Docker Engine29.9.2 (comprobado en FIN-02A) y Uvicorn/psycopg del entorno existente. No se modifican instalaciones globales.

Ensayo aceptado74faf16cf20e:

- Origen: wordle-fin02b-74faf16cf20e-source, DB fin02b_74faf16cf20e. Contenedor nuevo, network none, sin puertos.
- Destino: wordle-fin02b-74faf16cf20e-target, otro ID de contenedor y otra instancia PGDATA/tmpfs; misma denominación lógica DB dentro de otro servidor. Red exclusiva wordle-fin02b-74faf16cf20e y puerto127.0.0.1:60686, sin puertos públicos. No se comparte almacenamiento.
- Ambos con PGDATA/socket tmpfs, sin bind mounts/volúmenes; límites512MiB/1CPU. Dos passwords admin distintos más uno app, todos aleatorios solo en memoria/entorno, no impresos. No se leen Config.Env, .env o backups ajenos.
- Baseline aplicada al origen después de comprobar cero tablas public; schema_contracts aprobado. apply_seed FIN-02A se ejecuta dos veces sobre el origen verificado y ambos snapshots coinciden.
- Destino comprobado con cero tablas antes de pg_restore; no se ejecuta allí baseline ni seed para encubrir omisiones del dump.

## Respaldo real

pg_dump -U fin02_owner -d <DB temporal> --format=custom --no-owner --no-acl, ejecutado dentro del origen, salida binaria sin alteración a synthetic.dump en un TemporaryDirectory externo al repositorio. Cabecera PGDMP, tamaño y hash del archivo comprobados; no se copia a Git ni se muestra su contenido.

- Formato: custom.
- Tamaño:7098 bytes.
- SHA256: e7d8f8feb4078eb3d4d16a540ce58b3744cdbd250d1c169121bfaa6b5490b002.
- Tablas: palabras, partidas, intentos, estadisticas y secuencia palabras_id_seq/estructura correspondiente.

pg_restore -U fin02_owner -d <DB nueva> --exit-on-error --no-owner --no-acl recibió por stdin los bytes del archivo. Exit0 y checksum del archivo sin cambios antes/después; el exit0 no se usa como único criterio de aceptación. Se elimina únicamente el archivo/directorio temporales propios al finalizar; la huella es evidencia de esta ejecución, no un backup retenido para operar.

## Comparación SQL antes de HTTP

| Elemento | Resultado comprobado |
|---|---|
| Esquema | Contratos schema_contracts.sql aprobados tras restore; comparación determinista de columnas/tipos/null/defaults/typmod, definiciones constraints e índices origen/destino iguales |
| palabras |5 filas, incluidos IDs integer/valores iguales |
| partidas |3 filas; UUID, usuarios/soluciones/estados/contadores/fechas idénticos |
| intentos |8 filas; UUID/FK/números/palabras/JSONB/fechas idénticos |
| estadisticas |1 fila; dos jugadas, una victoria, media1, racha0/máxima1 y UUID/fecha iguales |
| Relaciones |Cero intentos huérfanos o usuarios incoherentes con partida; FK real preservada |
| Secuencia |last_value5, is_called true en ambas; no inferior al id máximo de palabras |
| Snapshot |Todas las filas/campos ordenadas por id, más last_value/is_called: igualdad exacta, no solo conteos |

SHA256 de datos origen y restaurados, ambos:

`6d3e00b87366427c25e49fe91ea078cd0f4f0cbdc3149567f4b904df8e349890`

Las comprobaciones adicionales a FIN-02A ejercitan recuperación; no se usan mocks para afirmar SQL real. El origen no recibe escrituras después de pg_dump: snapshot final conserva la misma huella, incluso tras las operaciones HTTP del destino.

## Roles y permisos

--no-owner/--no-acl no conserva roles/credenciales/permisos. El propietario local del destino se creó de forma independiente al inicializar la imagen; no se trasladan contraseñas del origen. Tras confirmar restore y SQL se ejecuta el script existente docker/postgres/30-app-role.sh en destino, usando valores nuevos WORDLE_APP_USER/PASSWORD por entorno.

Se crea wordle_app no superusuario (rolsuper false comprobado), USAGE public/secuencias y SELECT/INSERT/UPDATE de tablas según script; no se ejecuta allow_all ni material Supabase histórico. FastAPI recibe únicamente credencial app del destino por entorno del subproceso. Las escrituras HTTP satisfactorias comprueban además los permisos efectivos necesarios para el flujo; no certifican autorización del jugador ni seguridad de producción.

## HTTP real, sin ASGITransport/mocks

Subproceso Uvicorn real sobre127.0.0.1:60690, app.main:app, un worker, psycopg al puerto loopback del PostgreSQL restaurado. urllib usa ProxyHandler({}) y no sigue un servicio externo: las rutas son loopback controladas. No se usa backend del usuario ni frontend5173. Se adopta SelectorEventLoop explícito para el psycopg async del entorno Windows; no se modifica aplicación ni configuración global.

| Endpoint | Resultado real |
|---|---|
| GET /health |200, status ok; liveness no se presenta por sí sola como prueba DB |
| GET /game/{id} para las tres partidas restauradas |200, todos los campos/intentos coinciden con SQL; activa no revela palabra_secreta, finalizadas conservan contrato |
| GET /stats/fin02a-demo |200, datos restaurados y porcentaje50 |
| GET /stats/ranking/global |200, fila restaurada con usuario_id/partidas_ganadas/racha_maxima/partidas_jugadas |
| POST /game/intento:ZZZZZ en partida activa restaurada |400; snapshot destino intacto |
| POST /game/intento:CASAS en esa partida |200, ganada en2 intentos, noveno intento persistido |
| GET /stats/fin02a-demo tras victoria |200, jugadas3/ganadas2/promedio1.5 |
| POST /game/nueva + GET por ID devuelto |200, UUID nuevo generado y partida en_curso consultable |

Las lecturas iniciales no modifican el snapshot. Nuevas escrituras afectan solo destino; la comparación de igualdad con origen se hizo antes de escribir y el origen se verifica intacto al final. No se afirma que ambos permanezcan iguales después de modificar deliberadamente destino. No se repitió una derrota HTTP completa de seis intentos: la derrota restaurada sí se lee y contrasta; el alcance HTTP mínimo original y una escritura posterior están satisfechos.

## Incidencias y correcciones limitadas al ejecutor nuevo

- Ensayo48b7715c9a7b: bootstrap/dump/restore/SQL completos; aserción fallida en fase HTTP. La revisión detectó también una expectativa incorrecta de ranking del propio ejecutor (intentaba comparar intentos_promedio en lugar de partidas_jugadas); se ajustó al repositorio real, sin cambiar el contrato.
- Ensayob145770f1818: fallo localizado en HTTP de estadísticas. Uvicorn instalado usa ProactorEventLoop en Windows; incompatible con el driver async en este entorno. Se corrigió únicamente el lanzador temporal para asyncio.run(..., loop_factory=asyncio.SelectorEventLoop), consistente con la necesidad ya tratada por los ejecutores PG existentes. Se mantuvieron dependencias/backend intactos.
- Ensayo74faf16cf20e: procedimiento completo PASS. La corrección del loop y la aserción no cambian datos ni lógica del juego. No se presentan los dos ensayos previos como recuperaciones completas satisfactorias. El diagnóstico se basa en fase fallida, implementación del loop instalada y éxito posterior; no se imprimieron logs/env con posibles secretos.

## Limpieza y preservación

Cada intento finalizó con retirada del backend propio, dos contenedores y red propia tras verificar etiqueta/ID; sin volúmenes creados. Consultas finales exactas confirmaron ausentes los seis contenedores y tres redes de los tres ensayos. Dump/directorio temporales propios retirados. No prune, enumeración/destrucción ajena, ni cambios de permisos/configuración del sistema.

PG-05/PG-06 y todos los archivos previos se preservan salvo la actualización autorizada de este informe. No Supabase/Azure, descargas de diccionario, binarios en Git, publicación de imágenes, PR, add/commit/push o cambios a Terraform/Kubernetes/CI. No se repiten las55/11 regresiones de FIN-02A como pruebas nuevas: FIN-02B ejecuta su recuperación real/SQL/HTTP, sintaxis y rechazo CLI sin flag. git diff --check y revisión de whitespace de archivos nuevos correctos.

Git final: HEAD sin cambios, índice vacío, ningún archivo versionado modificado; nuevo ejecutor sin seguimiento y este informe continúa sin seguimiento junto a los demás. FIN-02B PASS desbloquea la revisión de aceptación de FIN-02, no su cierre automático. Pendiente revisar evidencias y decidir su consolidación/publicación bajo autorización separada.
