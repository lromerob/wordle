# PostgreSQL vigente y archivo histórico Supabase

Nota de alcance PUB-02, 09/11/2026. El backend actual usa PostgreSQL16 con
psycopg3 async: **no requiere Supabase, PostgREST ni sus claves**. El directorio
conserva su nombre para no romper referencias. FIN-01 continúa pendiente.
La sección FIN-01B más abajo se conserva íntegra como registro histórico; sus
procedimientos Supabase y trabajos pendientes describen aquel momento, no la
ruta operativa vigente ni autorizaciones actuales.

## A. Archivos vigentes o auxiliares reutilizados

| Archivo | Uso actual |
|---|---|
| migrations/20261108000100_initial_wordle.sql | Baseline PostgreSQL original, sin mover/modificar: usado por Compose, bootstrap kind y CI |
| tests/schema_contracts.sql | Catálogo estructural reutilizado por PG-04/06/07 |
| tests/backend_operations.sql | Comprobación SQL auxiliar histórica reproducible solo sobre DB nueva autorizada; no se ejecuta automáticamente en CI |
| tools/prepare_dictionary.py | Generador offline de seed desde fuente aprobada; no conecta a DB |
| tests/test_dictionary_preparation.py | Pruebas offline del generador; no sustituyen integración real |

La inicialización actual vive en `docker/postgres/`: baseline, fixture mínima
de cinco palabras y rol app separado del owner, solo con almacenamiento vacío.
No son datos históricos migrados de Supabase. Para operación usar
[README actual](../README.md),
[PG-05](../docs/analysis/pg-05/PG-05-IMPLEMENTATION-REPORT.md) y
[PG-06](../docs/analysis/pg-06/PG-06-IMPLEMENTATION-REPORT.md).

## B. Material conservado solo como historia

- `prototype/allow_all.sql`: reproduce RLS permisiva y grants amplios del
  prototipo. **No es hardening y NO forma parte de la configuración PostgreSQL
  operativa. No ejecutarlo ni añadirlo a initdb, Kustomize o CI.**
- `tests/prototype_access.sql`: inspección de roles/políticas de aquel prototipo,
  no una prueba vigente de autorización por jugador.
- `tests/local_backend_smoke.py`: smoke opt-in diseñado para Supabase local
  anterior a la transición; no es el ejecutor actual de integración PostgreSQL.

Se recomienda conservar estos tres archivos en el futuro commit únicamente como
archivo histórico explícito junto a esta nota, sin moverlos ni cambiar su código.
No están referenciados por bootstrap/workflows actuales. Su presencia no autoriza
su ejecución. La integración vigente usa `backend/integration/run_pg04.py` y
`run_pg07_ci.py`. El modelo Supabase no se reactiva para obtener un resultado verde.

## Registro FIN-01B original, anterior a PG-01/07

# FIN-01B: reconstrucción local preparada para revisión

La migración estructural y sus comprobaciones SQL han pasado en dos bases nuevas PostgreSQL 16.15 dentro de un contenedor desechable autorizado. Véase el [resultado de validación](../docs/analysis/fin-01b/FIN-01B-POSTGRES-VALIDATION.md). **FIN-01 no está completado:** Supabase/PostgREST, RLS/permisos y smoke HTTP siguen pendientes. La fuente es el inventario aportado por el propietario en la solicitud FIN-01B del 08/11/2026, no una conexión ni un dump revisado por el agente.

## Archivos y separación de responsabilidades

- migrations/20261108000100_initial_wordle.sql: solo estructura public de las cuatro tablas, secuencia y restricciones aportadas. Sin roles, permisos, RLS, semillas, extensiones, CHECKs o índices extra. Ejecutar una sola vez sobre una base nueva autorizada; no es una actualización de una base existente.
- prototype/allow_all.sql: reproducción OPCIONAL del estado inseguro de permisos/RLS, fuera del directorio aplicado como migraciones. No es configuración recomendada de producción. Los roles Supabase deben existir previamente; el archivo no los crea.
- tests/schema_contracts.sql: comprobación de 23 columnas, tipos/defaults/null, PK/UNIQUE/FK, seis índices y ausencia de triggers de usuario/CHECK extra. No comprueba cada posible propiedad PostgreSQL ni es un dump-diff completo.
- tests/backend_operations.sql: operaciones SQL análogas a las del backend con fixtures existentes CASAS/PERRO, FK, JSONB, unicidad, defaults y promedio fraccionario. Requiere tablas vacías y termina ROLLBACK; nextval no revierte su incremento. No es una prueba HTTP/PostgREST ni de aislamiento RLS.
- tests/prototype_access.sql: metadatos de RLS/políticas y privilegios tras el archivo opcional, solo con roles Supabase locales existentes. No demuestra autorización efectiva entre usuarios.
- tools/prepare_dictionary.py: genera SQL desde una lista UTF-8 aprobada, cinco letras A-Z/Ñ, sin descarga o consulta DB; normaliza, elimina duplicados y registra SHA256. No sobrescribe archivos ni modifica filas existentes. No incluye un diccionario de producción.
- tests/test_dictionary_preparation.py: cinco tests offline del generador; sus ejemplos reutilizan fixtures existentes y no constituyen una fuente del diccionario.
- tests/local_backend_smoke.py: prueba futura opt-in de API FastAPI real contra stack Supabase LOCAL desechable. No arranca servicios ni lee claves; rechaza destinos externos, proxies y redirecciones. La ubicación local de FastAPI no garantiza por sí sola que su DB sea local: el operador debe verificarlo antes de autorizar la ejecución.

## Fidelidad y supuestos explícitos

Se conservan la nulabilidad (incluidos intentos.partida_id y contadores), tipos, defaults y restricciones informados. usuario_id es text y no se crea relación a auth.users. No se añaden límites de longitud, estados ENUM, rangos de intentos, unicidad de intentos por partida, cascadas, triggers, timestamps automáticos de update ni mejoras de seguridad.

Detalles no aportados:

1. Se interpreta varchar/numeric sin longitud/precisión indicada como tipos sin typmod. Si las consultas originales omitieron esos parámetros, el propietario debe confirmarlos antes de afirmar igualdad exacta.
2. Nombres originales de constraints/índices no aportados: PostgreSQL genera nombres convencionales; la equivalencia se verifica por definición, no por nombre. Se generan exactamente los seis índices de PK/UNIQUE esperados.
3. La secuencia palabras_id_seq existe como dependencia del default. Sus parámetros, tipo propio, OWNED BY, propietario y estado no fueron aportados. Se crea con valores PostgreSQL por defecto, sin añadir OWNED BY ni restaurar contador de producción. Estos detalles no se presentan como verificados.
4. Acciones FK, MATCH y diferibilidad no aportadas: el DDL adopta los defaults PostgreSQL de REFERENCES (NO ACTION, MATCH SIMPLE, no diferible). Confirmar metadatos originales si se requiere equivalencia completa.
5. PostgreSQL 16 es objetivo local propuesto, no versión confirmada del proyecto. gen_random_uuid() es nativa allí; no se instala pgcrypto ni uuid-ossp por inferencia. public debe existir y estar vacío de los objetos de Wordle; no se elimina/recrea el schema.
6. No se copian propietarios, grants de schema/secuencia, default privileges ni rol efectivo de la clave porque no se proporcionaron. GRANT sobre tabla no acredita permiso de nextval para insertar palabras como anon. El diccionario se cargaría con un operador local autorizado, no mediante privilegios inventados.
7. information_schema.triggers sin filas es la observación aportada; puede depender de la visibilidad del consultante. No se crean triggers de usuario; las FK sí tienen mecanismos internos PostgreSQL.

## RLS del prototipo: reproducir no equivale a asegurar

Las cuatro tablas tienen, según el propietario, RLS activa sin FORCE y una política allow_all PERMISSIVE, TO PUBLIC, FOR ALL, USING(true), sin WITH CHECK explícito. El archivo opcional omite WITH CHECK exactamente; para ALL PostgreSQL reutiliza USING si WITH CHECK está ausente. Por tanto no hay aislamiento por usuario con esta política. Se conceden los cuatro privilegios de tabla informados a anon/authenticated/service_role, sin ampliar a TRUNCATE/REFERENCES/TRIGGER ni secuencias.

El baseline estructural por sí solo NO reproduce el estado de seguridad de Supabase. Aplicar el archivo opcional exige revisión y autorización del entorno local; nunca aplicarlo automáticamente contra un proyecto real ni confundirlo con FIN-03. Tampoco usar la copia estructural sin RLS como runtime público. No se resuelven autenticación, propiedad o transacciones en FIN-01B.

## Diccionario: dependencia aún bloqueada

El backend consulta palabras al crear partida y devuelve HTTP 500 si está vacío; además valida intentos por igualdad. Necesita datos iniciales coherentes. No hay archivo de diccionario real ni fuente/licencia identificable en el repositorio. No se conoce la procedencia de las filas del proyecto Supabase y no se extrajeron.

El propietario debe aportar una lista UTF-8 autorizada, una palabra por línea, con procedencia/licencia y versión. El mecanismo preparado requiere confirmación explícita --owner-approved y calcula su hash. Ejemplo FUTURO, no ejecutado ni aplicable sin fuente aprobada:

```sh
python supabase/tools/prepare_dictionary.py --input <lista-aprobada.txt> --output <seed-local.sql> --owner-approved
```

El SQL generado usa INSERT ... ON CONFLICT (palabra) DO NOTHING y no borra/actualiza datos. No ejecutar sobre una DB existente: en esta fase solo se autorizaría una nueva base local. Los cuatro vocablos de MemoryDB sirven para pruebas sintéticas, no para fingir un diccionario real ni completar FIN-02.

## Validación local futura, requiere autorización antes de arrancar/instalar

En la preparación no había psql ni servidor PostgreSQL en PATH. En la validación posteriormente autorizada se usó psql dentro de un único contenedor PostgreSQL 16.15, ya eliminado, sin instalar dependencias del proyecto. Se verificó estructura y operaciones SQL dos veces; no Supabase local ni HTTP. Los pasos siguientes permanecen como procedimiento de referencia y no autorizan nuevas ejecuciones. Para la reconstrucción debe autorizarse un PostgreSQL 16 o stack Supabase local NUEVO, aislado, con nombres/volúmenes de prueba exclusivos y sin enlace al proyecto remoto. PostgreSQL simple basta para estructura; Supabase/PostgREST local es necesario para probar el SDK/API sin alterar la aplicación.

Procedimiento después de esa autorización:

1. Crear exclusivamente el runtime desechable nuevo autorizado. Comprobar destino, puerto local, DB nueva y ausencia de configuración remota; usar un nombre de servicio de conexión local aprobado por el operador. No reutilizar una DB existente aunque parezca vacía.
2. Usar psql -X -v ON_ERROR_STOP=1 para que falle al primer error y no cargue psqlrc. Aplicar baseline una vez. Ejemplos de archivos, con LOCAL_FIN01B como servicio previamente definido y verificado por el operador (no existe hoy):

```sh
psql -X -v ON_ERROR_STOP=1 service=LOCAL_FIN01B -f supabase/migrations/20261108000100_initial_wordle.sql
psql -X -v ON_ERROR_STOP=1 service=LOCAL_FIN01B -f supabase/tests/schema_contracts.sql
psql -X -v ON_ERROR_STOP=1 service=LOCAL_FIN01B -f supabase/tests/backend_operations.sql
```

3. Solo si se autoriza la reproducción del prototipo en Supabase local, aplicar prototype/allow_all.sql y tests/prototype_access.sql. Confirmar roles/schema/secuecias antes de probar acceso; no inventar grants para conseguir un verde. La validación de catálogo se realiza como propietario local y no acredita seguridad de roles restringidos.
4. Para el smoke HTTP, crear otra DB local nueva o usar las mismas tablas aún vacías tras ROLLBACK, y cargar únicamente CASAS como fixture de MemoryDB para solución determinista; esto es test, no diccionario real. Insertar mediante operador local autorizado, no extraer filas remotas. Arrancar FastAPI con Supabase exclusivamente LOCAL y credenciales locales privadas. Nunca usar memory_server.py para afirmar integración PostgreSQL.

```sh
python supabase/tests/local_backend_smoke.py --base-url http://127.0.0.1:8000 --confirm-disposable-local-stack
```

El smoke verifica UUID reutilizable, estado activo sin palabra secreta, errores de longitud/diccionario/propietario, victoria, rechazo tras finalizar y estadísticas. Los escenarios de derrota/repetidas siguen en los tests MemoryDB existentes y están pendientes de integración DB/API; no se declara que este smoke los cubra. Tampoco comprueba persistencia a reinicio ni recuperación de backup (FIN-02).

5. Recrear desde una segunda DB vacía autorizada para demostrar reconstrucción y registrar versión/resultado. No aplicar repetidamente CREATE TABLE ni usar DROP, reset remoto o db push ligado al proyecto real. Capturar logs sanitizados y catálogo, nunca claves, dumps de datos o conexión privada. La limpieza de recursos locales también debe limitarse a los creados con autorización.

## Pruebas que pueden ejecutarse sin servicios

```sh
python -m unittest discover -s supabase/tests -p test_dictionary_preparation.py -v
```

Estas cinco pruebas solo ejercitan generación de texto SQL con fixtures en memoria. No son un parser SQL, una migración ni una prueba de PostgreSQL. Véase el [informe FIN-01B](../docs/analysis/fin-01b/FIN-01B-RECONSTRUCTION-REVIEW.md) para resultados reales y pendientes.

Referencias: [UUID PostgreSQL 16](https://www.postgresql.org/docs/16/functions-uuid.html), [CREATE POLICY y WITH CHECK implícito](https://www.postgresql.org/docs/16/sql-createpolicy.html), [defaults de CREATE SEQUENCE](https://www.postgresql.org/docs/16/sql-createsequence.html).
