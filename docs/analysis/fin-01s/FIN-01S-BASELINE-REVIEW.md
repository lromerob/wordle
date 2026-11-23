# FIN-01S — Revisión del baseline

Fecha: 10/11/2026 (Europe/Madrid). Revisión documental, sin nuevas pruebas. Corte: b330ae70caf08ac789786376ca5de0305ea4471f, rama codex/pg01-07-consolidation.

Fuente: `supabase/migrations/20261108000100_initial_wordle.sql`, cuatro tablas/23 columnas; contraste con `backend/app/repository.py`, `routers/game.py` y `supabase/tests/schema_contracts.sql`. No se encontró incompatibilidad real con el backend en el alcance revisado.

## Tipos, uso y riesgos aceptados

| Tabla | Columnas y tipos exactos del baseline | Uso/evidencia y evaluación |
|---|---|---|
| palabras | id INTEGER; palabra VARCHAR sin longitud | list_words/word_exists leen palabra; seed omite id. UNIQUE evita duplicados exactos. Longitud/alfabeto quedan en API/generador, no SQL. Aceptable con fixture normalizada; escritor SQL ajeno podría introducir palabras incompatibles. |
| partidas | id UUID; usuario_id TEXT; palabra_secreta VARCHAR; intentos_usados INTEGER; estado VARCHAR; created_at TIMESTAMP WITHOUT TIME ZONE | create_game omite id/fecha y usa RETURNING id; fija contador/estado. game_uuid convierte identificadores entrantes, FastAPI serializa UUID. PG-04 C03/C07/C08/C15-C18 y lifecycle/persisted_types. VARCHAR sin límite mantiene contrato sin inventar ENUM o CHECK. |
| intentos | id UUID; partida_id UUID nullable; usuario_id TEXT; numero INTEGER; palabra VARCHAR; resultado JSONB; created_at TIMESTAMP WITHOUT TIME ZONE | add_guess omite id/fecha, convierte partida UUID y usa Jsonb(resultado); get_guesses ordena numero. PG-04 JSONB/repetidas/C13-C18 y FK en FIN-01B. JSONB no impone cinco objetos por SQL; la aplicación los construye. |
| estadisticas | id UUID; usuario_id TEXT; partidas_jugadas, partidas_ganadas, racha_actual, racha_maxima INTEGER; intentos_promedio NUMERIC sin precisión/escala; updated_at TIMESTAMP WITHOUT TIME ZONE | get_stats_for_update inserta usuario y usa defaults; ON CONFLICT usuario_id y FOR UPDATE coordinan finalizaciones. PG-04 stats_numeric/ranking/C20-C21 y carreras reales. NUMERIC conserva fracciones, psycopg devuelve Decimal, respuesta numérica comprobada. |

VARCHAR/NUMERIC sin typmod son decisiones del esquema nuevo, no afirmaciones de equivalencia completa con Supabase. No se declara precisión infinita: existen límites del motor y el cálculo de aplicación no es aritmética decimal exacta universal. TEXT usuario_id no es una relación Auth ni identidad verificada.

Nulabilidad: son NOT NULL los id PK, palabras.palabra, todos los usuario_id, partidas.palabra_secreta e intentos.numero/palabra/resultado. Los restantes campos son nullable, incluso contadores con DEFAULT. DEFAULT no evita un NULL explícito: puede romper operaciones aritméticas de la aplicación si un escritor externo lo introduce. El flujo normal usa defaults/valores definidos y fue probado; se acepta para la demo controlada, no como contrato seguro para SQL arbitrario.

TIMESTAMP sin zona conserva el contrato probado; no se añade Z/UTC ficticio. DEFAULT now() utiliza la zona de sesión al convertir al tipo sin zona. updated_at solo tiene default de inserción: ni trigger ni update_stats lo actualizan automáticamente. PG-04 verifica tipos/serialización, no interoperabilidad entre todas las zonas horarias. Riesgo acotado aceptable para la evidencia académica.

## Identificadores, defaults y restricciones

- Las cuatro PK son id; tres UUID tienen DEFAULT gen_random_uuid(), generado por PostgreSQL16, no por el backend. game_uuid solo valida/convierte UUID recibido, no genera uno. UUID de fixtures/tests no cambia el mecanismo de producción.
- palabras.id usa nextval('public.palabras_id_seq'::regclass). CREATE SEQUENCE sin opciones crea secuencia bigint, inicio/mínimo1, incremento1, máximo9223372036854775807, cache1 y no cycle; FIN-01B-POSTGRES-VALIDATION.md lo observó. La columna sigue INTEGER: el rango utilizable está limitado por INTEGER aunque la secuencia admita más; no es un problema de capacidad para cinco palabras/demos pequeñas.
- No hay SERIAL/IDENTITY ni OWNED BY declarado. El default depende de la secuencia, pero esta no tiene vínculo de propiedad automática con la columna para su ciclo de borrado. No se exige corregirlo cosméticamente: no hay borrado/recreación parcial en el flujo. nextval puede dejar huecos tras rollback; no se usa continuidad como regla de negocio.
- DEFAULT 0: contador de partidas y cinco métricas de estadísticas (cuatro contadores y promedio). estado DEFAULT 'en_curso'; tres fechas DEFAULT now(). La API crea explícitamente estado/contador, pero estadísticas nuevas sí dependen de ceros del baseline. FIN-01B comprueba defaults; PG-03/04 inicialización de stats y concurrencia los ejercitan.
- UNIQUE palabras(palabra) y estadisticas(usuario_id), además de cuatro PK: siete constraints incluyendo la FK y seis índices PK/UNIQUE. UNIQUE(usuario_id) permite el ON CONFLICT del repositorio. No hay UNIQUE(partida_id,numero), CHECK de seis intentos, índices extra o triggers de usuario; coherencia de intentos depende de la transacción/bloqueo compartidos por los escritores.

## Única clave foránea real

| Origen | Columna | Destino | Referencia | Borrado | Actualización | Declaración |
|---|---|---|---|---|---|---|
| public.intentos | partida_id UUID nullable | public.partidas | id UUID PK | NO ACTION | NO ACTION | El DDL declara REFERENCES; acciones por defecto, no ON DELETE/UPDATE explícitos |

MATCH SIMPLE y NOT DEFERRABLE son valores predeterminados; sin cláusula DEFERRABLE la comprobación no se difiere al commit. NULL en partida_id es admitido; UUID no nulo exige partida existente. No se borra/cambia una PK referenciada sin resolver sus referencias; no hay cascada. FIN-01B probó rechazo de FK inexistente y aceptación de NULL; no se afirma una nueva prueba específica DELETE/UPDATE en FIN-01S.

create_game no requiere una palabra FK ni un usuario en otra tabla. add_guess recibe el UUID de una partida existente y el handler la bloquea antes de escribir. Estadísticas se consultan por usuario_id text y UNIQUE, sin FK a partidas/usuarios. No hay otras relaciones ni equivalencia automática entre los usuario_id de intento y partida en SQL: la comprobación del handler es coherencia, no autenticación.

## Evidencia y límites

- FIN-01B-RECONSTRUCTION-REVIEW.md §§3–4 y FIN-01B-POSTGRES-VALIDATION.md: baseline/catalog/operaciones en dos DB vacías PG16.15; tipos/defaults/FK/UNIQUE/índices comprobados sin inferirlos de MemoryDB.
- PG-01-HTTP-CONTRACT.md y PG-01-TRANSITION-DECISION.md fijan contrato y base nueva sin historial. PG-03-IMPLEMENTATION-REPORT.md documenta intento atómico y orden partida→stats; sus tests offline no prueban motor.
- PG-04-TEST-RESULTS.md: once métodos reales, tipos/JSONB/promedio/rollback/locks concurrentes; PG-05-TEST-RESULTS.md: volumen nuevo y snapshots tras restart/down-up; PG-06-TEST-RESULTS.md: mismo PVC y filas tras recreación de pod. Ninguno demuestra HA o supervivencia al borrado de kind.
- PG-07-TEST-RESULTS.md registra validación local; PUB-05B-CI-RESULTS.md añade evidencia remota del SHA: https://github.com/lromerob/wordle/actions/runs/42692713269. 55 offline/11 reales sin omisiones por guardas exitosas, siete jobs success y GHCR skipped; logs completos HTTP403, no reconsultados aquí.

Persistencia/compatibilidad suficientes para baseline académico. Migración inicial se ejecuta una vez sobre DB vacía mediante bootstrap, no por worker; no hay aún gestor general de futuras migraciones. El siguiente cambio SQL deberá aportar migración nueva, orden/registro de aplicación y validación. No se convierte esa necesidad futura en bloqueo de la primera versión.
