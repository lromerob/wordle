# FIN-02A — Semillas sintéticas idempotentes

Fecha: 10/11/2026. Resultado: **FIN-02A PASS**. **FIN-02B queda desbloqueado**; no se ejecuta en este incremento. FIN-02 no se declara completado.

## Alcance y archivos

Preflight: rama codex/pg01-07-consolidation, HEAD da99b48b1cf8629ccee2566c03d4d3f6513f7fc9; índice vacío, sin cambios versionados y trece informes locales sin seguimiento. Se leyeron punto de partida FIN-02, bloqueo FIN-02B, baseline, init/fixtures, ejecutores/tests PostgreSQL y persistencia/evaluador del backend.

Solo tres archivos nuevos:

- backend/integration/fin02a_seed.sql: datos deterministas, transacción y guardas.
- backend/integration/run_fin02a.py: ejecutor opt-in, PostgreSQL nuevo propio y validaciones reales.
- Este informe.

Sin dependencias nuevas, cambios a aplicación/API, baseline, Compose, Kubernetes, Terraform o Actions. No se integra la semilla en initdb ni en el arranque normal del backend.

## Datos de demostración

Palabras internas de la fixture existente PG-05: CASAS, GATOS, NIÑOS, PERRO y SACAS; no se descarga un diccionario. Usuario sintético fin02a-demo, sin tabla Auth. UUID con prefijo f102a000 y fechas fijas enero2026.

| Partida | UUID final | Intentos | Resultado |
|---|---|---|---|
| Ganada | …000000000001 | CASAS | Victoria en1 contra CASAS |
| Perdida | …000000000002 | PERRO seis veces | Derrota al sexto contra CASAS |
| En curso | …000000000003 | SACAS | Amarillo/verde/amarillo/verde/verde contra CASAS |

Totales del conjunto: cinco palabras, tres partidas, ocho intentos y una fila estadística: jugadas2, ganadas1, racha_actual0, racha_maxima1, promedio1. La partida en curso no incrementa estadísticas. UUID/usuario/fechas explícitos son sintéticos; los IDs integer de palabras usan la secuencia existente y su valor depende de las palabras ajenas preexistentes.

## Ejecución y protección

Desde raíz, Docker Linux y entorno Python con dependencias existentes:

```powershell
.\.venv\Scripts\python.exe -B backend/integration/run_fin02a.py --run-disposable-postgres
```

El flag es obligatorio antes de cualquier llamada Docker. Requiere imagen local postgres:16.15, sin descarga implícita ni instalación. No acepta DSN, host, contraseña, contenedor o base destino por CLI: crea únicamente un nombre aleatorio wordle-fin02a-<12hex> tras comprobar que no existe.

PGDATA/socket tmpfs, network none, cero puertos y volúmenes, memoria512MiB/CPU1. Password aleatorio transmitido por entorno del proceso, nunca impreso; operaciones psql -X -v ON_ERROR_STOP=1 mediante docker exec/socket del propio contenedor. No consulta .env o Config.Env. Init baseline y schema_contracts exigen DB inicialmente vacía.

apply_seed exige authorized=True y valida nombre fin02a_<12hex> (fin02b_<12hex> reservado al siguiente ensayo), etiqueta wordle.fin02.disposable coincidente, red none, sin puertos/mounts persistentes y tmpfs exactos antes de ejecutar. El SQL exige además setting de autorización y nombre de DB de prueba. Estas guardas previenen accidentes; no son una frontera de seguridad frente a un administrador que las falsifique deliberadamente. Nombres PG-05/06 rechazados antes de conexión SQL.

Para FIN-02B se podrá reutilizar apply_seed en un contenedor nuevo verificado con esas mismas guardas; todavía no hay automatización de backup/restore. No copiar esta semilla al bootstrap de una DB operativa.

## Idempotencia y colisiones

La transacción bloquea las cuatro tablas durante la carga controlada. Primero verifica que filas existentes con UUID/usuario reservados coincidan exactamente. Si hay diferencias, aborta; nunca actualiza ni borra esos registros. Inserta solo filas ausentes, respaldándose en PK/UNIQUE existentes, y comprueba el conjunto esperado completo antes de commit.

Palabras usa NOT EXISTS antes de generar id; no consume nextval en cargas repetidas, a diferencia de un INSERT ON CONFLICT que invoque el default para filas ya existentes. Reutiliza palabras existentes por su UNIQUE, sin cambiar sus IDs. No usa setval, TRUNCATE, DELETE, UPDATE o recreación de tablas públicas en la semilla. El UPDATE del ejecutor pertenece exclusivamente a la prueba negativa de colisión en su DB desechable; comprueba que el seed no lo sobrescribe.

Si una partida de demostración ha avanzado por escrituras posteriores, una nueva carga no la reinicia: falla por colisión preservando su estado. Esta es una carga inicial repetible, no un reseteador de sesiones existentes.

## Evidencia real

Entorno Windows/Python3.12 y Docker Engine29.9.2; PostgreSQL16.15 (Debian16.15-1.pgdg13+2), imagen local sha256:f9a7b9ebf6f56201f949db745e47bc423c0f0f8294bafe991cc10bf74b029657. Sin red PostgreSQL, conexiones externas o credenciales productivas.

Contenedor propio wordle-fin02a-12d0f4ba57fa; DB fin02a_12d0f4ba57fa. Baseline/catálogo ejecutados con PostgreSQL real; no mocks SQL. Cuatro registros de control ajenos, uno por tabla, se insertaron únicamente en esta DB para verificar preservación. Conteos totales tras cargar: palabras6, partidas4, intentos9, estadísticas2.

| Comprobación | Resultado |
|---|---|
| Primera carga | Crea el conjunto5/3/8/1 |
| Segunda carga | Estado idéntico, sin duplicados |
| Tercera carga | Estado idéntico, también secuencia |
| Snapshot completo | Filas de cuatro tablas ordenadas por id, todos sus campos y last_value/is_called de la secuencia |
| FK/numeración/resultados | Todas las referencias encuentran partida, usuario coherente, intentos1..N y límite6; feedback contrastado con evaluar_intento real |
| Estadísticas | Coinciden con una victoria de1 intento y una derrota de6, posterior; activa no contabilizada |
| Datos ajenos | Las cuatro filas iniciales permanecen idénticas por todos sus campos |
| Sin autorización | CLI sin flag exit2; apply_seed sin permiso lanza PermissionError; SQL directo sin setting rechazado por PostgreSQL, snapshot intacto |
| Destinos persistentes | Nombres wordle, pg05_private y wordle_pg06 rechazados antes de SQL |
| Colisión incompatible | Falla sin reparar ni modificar estado; snapshot posterior idéntico al previo al rechazo |

Huella SHA256 idéntica después de las tres cargas (incluye los registros de control y secuencia):

`e18da1cf60b701776f44251258d64391a064edb8cfa41d8e5ec57ba64ac6990e`

Es una huella del ensayo con centinelas, no un hash universal de cualquier DB que tenga datos ajenos distintos. La semilla no preserva el contador previo a primera carga: nextval avanza por las palabras nuevas como corresponde; cargas siguientes no lo alteran.

## Regresiones y controles

- 55 pruebas backend offline aprobadas, cero omitidas,1.267s; se ejecutó el wrapper exacto extraído del workflow existente, con bloqueo sockets externos/DNS/dotenv/libpq.
- 11 pruebas PostgreSQL reales existentes aprobadas, cero omitidas,1.691s; run_pg04.py en otro destino temporal. Incluye rollback, tipos y concurrencia. Caída real adicional:500 sanitizado,/health200,pool cerrado; tres errores SQL esperados y cero deadlocks.
- Sintaxis Python compile() sin bytecode y rechazo CLI: correctos. git diff --check correcto; controles acotados sobre archivos nuevos, sin valores de credencial productiva.

Las pruebas PG-04 utilizan sus propias fixtures y limpieza en su DB exclusiva; no se usan para afirmar idempotencia de FIN-02A, demostrada separadamente por las tres cargas anteriores. No se realiza smoke de restauración ni se inicia FIN-02B.

## Recursos, limpieza y cierre

FIN-02A eliminó únicamente el ID de su contenedor tras confirmar etiqueta; ausencia verificada. No creó red ni volumen persistente. PG-04 creó wordle-pg04-6f9dd9f16c4e y su red propia: ambos eliminados y ausencia verificada. No prune ni operaciones sobre PG-05/06, backups o credenciales anteriores. La imagen oficial permanece en caché.

Todos los archivos previos e informes sin seguimiento se preservan; índice vacío, HEAD sin cambios y sin modificaciones versionadas. Los tres archivos FIN-02A quedan sin seguimiento. Sin add/commit/push/PR, publicaciones o Azure.

FIN-02B puede retomarse, con autorización propia, cargando este conjunto en origen nuevo, pg_dump/pg_restore a instancia independiente y validación SQL/HTTP del destino. Este PASS no acredita todavía backup/restore, aplicación tras recuperación o cierre total FIN-02. El informe bloqueado FIN-02B anterior se conserva íntegro como registro histórico.
