# FIN-01B - Validación autorizada en PostgreSQL 16

Fecha: 08/11/2026. Validación local autorizada expresamente por el usuario. Aplicación de referencia: a666b17680781a24889ea774778019995d3fca45, rama codex/devops-04a1-hardening. **FIN-01 permanece pendiente.** Este resultado sustituye el estado «SQL no ejecutado» del informe de preparación únicamente para el baseline estructural y las dos comprobaciones descritas aquí.

## Entorno e aislamiento

- Docker Engine respondió con versión 29.9.2.
- Se descargó la imagen oficial postgres:16, no disponible previamente.
- PostgreSQL ejecutado: 16.15, Debian, x86_64.
- Imagen/digest observados: postgres@sha256:f9a7b9ebf6f56201f949db745e47bc423c0f0f8294bafe991cc10bf74b029657.
- Único contenedor creado: wordle-fin01b-0bbc94a0881a, con etiqueta wordle.test=fin01b-disposable.
- Creado con --network none, sin publicación de puertos, bind mounts ni volúmenes persistentes. Datos y socket se ubicaron en tmpfs (/var/lib/postgresql/data, 256 MiB; /var/run/postgresql, 16 MiB).
- Red none y ausencia de PortBindings/Binds/montajes persistentes verificadas mediante docker inspect. Las llamadas psql/createdb se hicieron por docker exec, no por TCP desde Windows.
- POSTGRES_HOST_AUTH_METHOD=trust se utilizó solo en este contenedor sin red ni puertos, sin credenciales del proyecto. No se recomienda esta autenticación para un servicio accesible.
- No se leyó .env, no se ejecutó la aplicación, no se consultó Supabase ni Azure y no se instalaron dependencias del proyecto.

La imagen queda en la caché local de Docker. No se eliminó por no estar solicitado; no es un contenedor ni un volumen de datos del proyecto.

## Archivos ejecutados, sin modificaciones

| Archivo | SHA256 |
|---|---|
| [Baseline](../../../supabase/migrations/20261108000100_initial_wordle.sql) | da743e629094da2b7d126f7889c5d1ca72e63a232844feadea3798254b19b0cb |
| [Contratos del catálogo](../../../supabase/tests/schema_contracts.sql) | de1b56b17a5829a27465451ada7831b1adccb50ef12cdf8dcd47ac90a12f019d |
| [Operaciones SQL](../../../supabase/tests/backend_operations.sql) | 0fd755b0b9ef26f6d2c8a26f7de0015eff2c86065ec34c8c73d2e3af53ef02a4 |

Se ejecutaron con psql -X -v ON_ERROR_STOP=1 como propietario local postgres, enviando cada archivo por stdin. Las huellas se verifican también después de la ejecución. No se corrigió ni se cambió la migración, los tests SQL o el backend.

## Reconstrucción desde cero: dos bases nuevas

Dentro del mismo contenedor nuevo se creó fin01b durante init y fin01b_rebuild mediante createdb. Antes de aplicar cada baseline se consultó information_schema.tables: cero tablas en public en ambos casos. No se reutilizó ninguna base de datos existente.

| Base nueva | Baseline | schema_contracts.sql | backend_operations.sql |
|---|---|---|---|
| fin01b | PASS | PASS | PASS |
| fin01b_rebuild | PASS | PASS | PASS |

Seis ejecuciones SQL finalizaron con exit code 0. El baseline produjo BEGIN, CREATE SEQUENCE, cuatro CREATE TABLE y COMMIT en cada base. La comprobación de catálogo terminó DO sin errores. Las operaciones SQL produjeron BEGIN, DO, ROLLBACK. No son seis tests HTTP ni una ejecución de la suite del backend.

## Catálogo comprobado

En cada base se verificaron las 23 columnas, tipos, nulabilidad y defaults con el script de contratos y se consultó el catálogo resultante:

| Tabla | Columnas observadas |
|---|---|
| palabras | id integer NOT NULL DEFAULT nextval; palabra varchar NOT NULL |
| partidas | id uuid NOT NULL DEFAULT gen_random_uuid(); usuario_id text NOT NULL; palabra_secreta varchar NOT NULL; intentos_usados integer NULL DEFAULT 0; estado varchar NULL DEFAULT en_curso; created_at timestamp without time zone NULL DEFAULT now() |
| intentos | id uuid NOT NULL DEFAULT gen_random_uuid(); partida_id uuid NULL; usuario_id text NOT NULL; numero integer NOT NULL; palabra varchar NOT NULL; resultado jsonb NOT NULL; created_at timestamp without time zone NULL DEFAULT now() |
| estadisticas | id uuid NOT NULL DEFAULT gen_random_uuid(); usuario_id text NOT NULL; partidas_jugadas/partidas_ganadas/racha_actual/racha_maxima integer NULL DEFAULT 0; intentos_promedio numeric NULL DEFAULT 0; updated_at timestamp without time zone NULL DEFAULT now() |

Los tipos varchar/numeric quedaron sin typmod de longitud/precisión, conforme a la interpretación explícita del inventario aportado. No se añadió ninguna restricción de longitud, rango de intentos o estados.

Se comprobaron siete restricciones: cuatro PRIMARY KEY(id), UNIQUE palabras(palabra), UNIQUE estadisticas(usuario_id) y FOREIGN KEY intentos(partida_id) REFERENCES partidas(id). Ningún CHECK adicional ni trigger de usuario. Los mecanismos internos de la FK no se confunden con triggers de aplicación.

Se observaron exactamente seis índices B-tree únicos, todos respaldando PK/UNIQUE:

- palabras_pkey
- palabras_palabra_key
- partidas_pkey
- intentos_pkey
- estadisticas_pkey
- estadisticas_usuario_id_key

No se creó índice independiente para intentos.partida_id ni otro índice no aportado por el propietario.

## Operaciones realmente probadas

En las dos bases, utilizando únicamente fixtures sintéticas CASAS/PERRO ya presentes en MemoryDB:

- Inserción de palabras y rechazo esperado de palabra duplicada por UNIQUE.
- Creación de partida sin id y generación de UUID; defaults de intentos/estado/created_at.
- Inserción y lectura de intento con lista de cinco objetos JSONB.
- Rechazo esperado de partida_id inexistente por FK.
- Actualización de partida a ganada y contadores de estadísticas.
- Promedio fraccionario 1,5 conservado por numeric al pasar de una victoria de un intento a otra de dos.
- Rechazo esperado de una segunda estadística del mismo usuario por UNIQUE.
- Aceptación de NULL en intentos.partida_id y en las columnas nullable de partida, sin endurecer el esquema.

Las excepciones de unicidad/FK se provocaron y capturaron dentro del test como resultados esperados; no son fallos de ejecución. Todas las tablas quedaron con cero filas tras ROLLBACK, confirmado con SELECT count(*). Las asignaciones nextval consumidas no se revierten por rollback, comportamiento PostgreSQL previsto; la secuencia y todo el clúster temporal desaparecieron al eliminar el contenedor.

## Errores y diferencias respecto al inventario Supabase

**No se encontraron errores de migración, contratos o operaciones SQL. No se modificaron archivos técnicos para conseguir esos resultados.**

No hubo discrepancias respecto a los tipos, defaults de columnas, nulabilidad, claves e índices descritos por el propietario, bajo los supuestos documentados. Esta comparación es contra su inventario, no contra un dump completo ni una consulta nueva al proyecto remoto.

Diferencias deliberadas de alcance e incertidumbres pendientes:

1. El baseline solo crea estructura. RLS/políticas/GRANT del prototipo NO se aplicaron ni se probaron; PostgreSQL simple no trae necesariamente los roles Supabase. Por tanto esta base local no reproduce su estado de acceso y no prueba seguridad ni autorización por usuario.
2. La secuencia creada por defaults PostgreSQL es bigint, start/min 1, max 9223372036854775807, incremento 1, cache 1, no cycle. El inventario real solo aportó su nombre/default de columna; tipo/ownership/OWNED BY/parámetros reales siguen sin confirmarse. No declarar identidad exacta de secuencia.
3. Nombres locales de constraints/índices son los generados por PostgreSQL; nombres originales y detalles FK (acciones/MATCH/diferibilidad) no aportados siguen pendientes de confirmación. Se conservan los defaults previamente documentados.
4. pg_get_expr mostró nextval('palabras_id_seq'::regclass) sin public al ser visible en search_path. Es la misma secuencia public creada por el DDL; no es una discrepancia funcional del default.
5. Se usó PostgreSQL 16.15 local, no una versión del proyecto Supabase confirmada. No se probaron su exposición Data API, rol de clave, grants de schema/secuencia ni privilegios por defecto.
6. No se cargó diccionario real; las fixtures no sustituyen su fuente/licencia pendiente ni completan FIN-02.

## Limpieza y límites de la autorización

La ejecución usó try/finally para eliminar por su ID únicamente el contenedor creado. docker rm --force finalizó con exit code 0. La consulta docker ps --all con el nombre exclusivo confirmó ausencia del contenedor. No se borraron volúmenes, redes, imágenes o recursos preexistentes.

No se ejecutaron prototype/allow_all.sql, tests/prototype_access.sql, local_backend_smoke.py, Supabase local, FastAPI, CI ni Azure. No se avanza automáticamente a esas validaciones. Las comprobaciones SQL son análogos de operaciones del backend, no una prueba del SDK/PostgREST o HTTP.

## Estado y siguiente decisión

Validación estructural y operaciones SQL: aprobadas en dos bases nuevas. FIN-01 permanece pendiente de las validaciones restantes y revisión de supuestos. Se propone revisar este resultado y los metadatos no aportados antes de autorizar otra fase. El stack Supabase local y el smoke HTTP requieren una autorización separada; no se solicitan credenciales reales ni se implementan cambios de autenticación/RLS.

Esta entrega modifica solo documentación de resultados y sus referencias; conserva el código y los SQL validados. Sin commits ni push.
