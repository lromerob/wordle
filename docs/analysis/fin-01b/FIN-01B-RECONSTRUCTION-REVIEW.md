# FIN-01B - Reconstrucción preparada para revisión

Actualización posterior: la validación estructural y de operaciones SQL ya se ejecutó con éxito en dos bases nuevas PostgreSQL 16.15; consultar [resultados autorizados](FIN-01B-POSTGRES-VALIDATION.md). Las afirmaciones «no ejecutado» de este informe reflejan la preparación inicial. RLS/Supabase local/HTTP permanecen sin ejecutar y FIN-01 sigue pendiente.

Fecha: 08/11/2026. Fuente de metadatos: solicitud FIN-01B aportada por el propietario, que declara consultas de solo lectura al proyecto existente. El agente no se conectó a Supabase ni recibió un dump completo. Corte de aplicación revisado: a666b17680781a24889ea774778019995d3fca45, rama codex/devops-04a1-hardening.

**FIN-01 no está completado:** falta validar efectivamente la reconstrucción y la integración en un entorno aislado autorizado. El esquema está preparado para revisión estática, no certificado como equivalente al catálogo remoto completo. No se modifica el backlog ni los documentos anteriores del plan/FIN-01A.

## 1. Evidencia nueva respecto de FIN-01A

El propietario confirma public, cuatro tablas, 23 columnas, seis índices de PK/UNIQUE y una FK intentos.partida_id -> partidas.id. Se aportan tipos, defaults y nulabilidad; no se inventan relaciones con Auth, CHECKs ni índices adicionales. La consulta de triggers reportada no devolvió registros; no se crean triggers de usuario.

RLS informada: activa en las cuatro tablas, no forzada, política allow_all PERMISSIVE para PUBLIC/ALL/USING true sin WITH CHECK explícito. Privilegios SELECT/INSERT/UPDATE/DELETE para anon/authenticated/service_role. Se reproduce por separado y de forma opcional, sin presentarlo como seguridad por usuario.

Estos metadatos sustituyen varias incógnitas del [diagnóstico FIN-01A](../fin-01a/FIN-01A-SCHEMA-ASSESSMENT.md), pero no demuestran propietarios, privilegios de secuencia/schema/defaults, rol de clave, versión PostgreSQL o todos los detalles de constraints/secuencia.

## 2. Archivos creados

| Archivo | Finalidad |
|---|---|
| [Migración inicial](../../../supabase/migrations/20261108000100_initial_wordle.sql) | DDL de secuencia y tablas con restricciones informadas, sin datos, permisos ni RLS. |
| [Acceso del prototipo](../../../supabase/prototype/allow_all.sql) | RLS/GRANT opcionales, fuera de migraciones; requiere roles locales preexistentes. |
| [Contratos del catálogo](../../../supabase/tests/schema_contracts.sql) | Tipos/defaults/null, restricciones, índices y ausencia de triggers de usuario/CHECKs. |
| [Operaciones SQL](../../../supabase/tests/backend_operations.sql) | Análogos SQL de operaciones del backend con fixtures locales y rollback; no API real. |
| [Metadatos RLS](../../../supabase/tests/prototype_access.sql) | Verifica configuración opcional del prototipo, no aislamiento por usuario. |
| [Preparador de diccionario](../../../supabase/tools/prepare_dictionary.py) | Importación reproducible desde lista aprobada sin conexión DB, con hash y sin sobrescribir artefactos. |
| [Tests del preparador](../../../supabase/tests/test_dictionary_preparation.py) | Cinco pruebas offline con fixtures, sin generar datos de producción. |
| [Smoke HTTP futuro](../../../supabase/tests/local_backend_smoke.py) | FastAPI real contra Supabase local, opt-in; solo loopback y sin redirects/proxies. |
| [Manual de reconstrucción](../../../supabase/README.md) | Supuestos, separación de permisos, autorización local y pasos de validación pendientes. |
| Este informe | Resultado y límites de FIN-01B; no marca FIN-01 completado. |

No se modifican backend, frontend, CI, Kubernetes, Terraform ni requisitos de dependencias. No se crea config.toml, credenciales ni una vinculación a proyecto remoto.

## 3. Compatibilidad revisada contra el código

| Código/operación | Metadato aportado | Resultado estático |
|---|---|---|
| [database.py](../../../backend/app/database.py) create_client y tablas sin schema explícito | Las cuatro tablas son public | Compatible con configuración habitual de cliente/API; exposición y permisos efectivos aún no probados. |
| [game.py](../../../backend/app/routers/game.py) nueva_partida: INSERT sin id y retorno del mismo | partidas.id UUID con gen_random_uuid | Generación compatible; PostgREST debe devolver representación e ID como cadena; smoke local preparado para comprobarlo. |
| game.py: usuario_id str de cliente | usuario_id text, NOT NULL, sin FK de usuario indicada | No requiere inventar/provisionar auth.users para reproducir este contrato. Sigue sin ser identidad verificada. |
| game.py: lectura de palabras y lookup por igualdad | palabras.palabra varchar NOT NULL UNIQUE | Admite el contrato; requiere diccionario no vacío y normalizado. No se confirmó procedencia de datos/collation. |
| game.py: inserción de intento y SELECT ordenado por numero | UUID/partida FK nullable, numero integer, resultado jsonb | Estructura compatible con lista JSON y ordenación; null de partida se conserva aunque la API normalmente no lo use. |
| game.py: actualización de contadores y estado | integer/varchar con defaults indicados | Compatible con valores normales; se preservan NULL permitidos, que pueden causar problemas si aparecen en filas leídas. No se añade NOT NULL para ocultarlo. |
| game.py: promedio ponderado de estadísticas | numeric sin precisión informada | Puede conservar fracciones; respuesta numérica de API pendiente de prueba real. |
| game.py y [stats.py](../../../backend/app/routers/stats.py): primera fila por usuario_id y update por usuario_id | UNIQUE estadisticas.usuario_id | El contrato lógico de una fila queda respaldado por la restricción informada; no resuelve carreras de INSERT concurrentes. |
| stats.py: ranking por partidas_ganadas y porcentaje en Python | Columnas presentes; porcentaje no persistido | Compatible; no se añade columna porcentaje_victorias. |
| GET partida/estadísticas: SELECT * | id/created_at/updated_at además de columnas consumidas | Son campos adicionales reales; no se alteran respuestas aquí. Revisión de exposición de campos sigue en FIN-03. |

No hay triggers aportados para updated_at: su default now() solo se usa al insertar. No se añade actualización automática ni se cambia el backend para escribirlo. No se impone longitud cinco en SQL, estados ENUM, límite seis, unicidad de intentos por partida o cascadas: el propietario no reportó esas restricciones.

La estructura no aporta transacción única entre insertar intento, actualizar partida y actualizar estadísticas; el riesgo descrito en [SECURITY-NOTES](../../../backend/SECURITY-NOTES.md) permanece. Las pruebas MemoryDB son unitarias aisladas, no un catálogo SQL.

## 4. Supuestos adoptados y decisiones pendientes

- varchar y numeric sin dimensiones en el inventario se interpretan sin typmod. Confirmar que el inventario no omitió longitud/precisión.
- Constraint names no aportados: se usan nombres PostgreSQL convencionales. Los seis índices se derivan de cuatro PK y dos UNIQUE; no se ejecuta CREATE INDEX extra.
- CREATE SEQUENCE usa defaults PostgreSQL porque no se conocen AS/start/increment/min/max/cache/cycle, ownership o OWNED BY reales. Se conserva el nombre y default nextval informado. No se restaura estado/contador de producción ni se declara igualdad de propiedades desconocidas.
- REFERENCES sin acciones/MATCH/diferibilidad aportados usa defaults PostgreSQL; confirmar detalles si se exige equivalencia exacta del catálogo.
- PostgreSQL 16 se propone solo como destino local. Usa gen_random_uuid nativa y no requiere añadir extensiones por inferencia; versión real pendiente.
- Baseline estructural requiere schema public existente y destino nuevo. No se incluye CREATE ROLE, grants de schema/secuencia ni default privileges no aportados.
- La categoría/rol efectivo de SUPABASE_KEY no se conoce y no se inspeccionó. Los permisos de tabla del inventario no determinan ese rol ni garantizan uso de nextval o exposición de schema.

Conservar estos supuestos visibles es preferible a inventar propiedades que parezcan razonables. Para fidelidad total, pedir al propietario esos metadatos adicionales o DDL sanitizado; no requieren compartir secretos ni datos.

## 5. Dependencia de diccionario y FIN-02

No se identificó fuente real de palabras en código, ficheros SQL, CSV, TXT o documentación. El backend falla con HTTP 500 si palabras está vacío. No se descarga un diccionario arbitrario, no se reutilizan fixtures como diccionario real y no se extrae contenido del proyecto Supabase.

El propietario debe proporcionar una lista aprobada y su procedencia/licencia/versión. El preparador admite UTF-8 (BOM opcional), una palabra por línea, normaliza mayúsculas y espacios externos, valida A-Z/Ñ antes de upper, deduplica/ordena y genera INSERT ON CONFLICT DO NOTHING con hash de entrada. Rechaza alfabeto/longitud incorrectos y fuente vacía. La fuente y el seed de aplicación siguen pendientes.

Las fixtures CASAS/PERRO proceden de [MemoryDB](../../../backend/tests/test_backend.py) y solo se utilizan en pruebas sintéticas documentadas. No se presenta un par de palabras como la población de Supabase. Semillas completas y backup/restore permanecen en FIN-02.

## 6. Validaciones realmente ejecutadas

1. Lectura y contraste estático del backend, modelos de petición, pruebas y metadatos aportados; sin ejecutar handlers contra servicios.
2. Cinco tests nuevos del preparador: normalización/deduplicación/orden; hash/determinismo; rechazo de longitud/alfabeto/delimitadores; rechazo de vacío/no UTF-8; generación limitada a palabras. Resultado: 5 aprobados, 0 omitidos, con socket connect/connect_ex/DNS bloqueados.
3. Comprobación de sintaxis Python y referencias de archivos; controles de consistencia textual SQL y git diff --check (sin parser PostgreSQL).

**No ejecutado:** baseline SQL, tests de catálogo/operaciones/RLS, smoke HTTP, PostgREST/Supabase local, reconstrucción en segunda base, carga de diccionario real, pruebas de permisos por rol o validación contra Supabase remoto. Los controles de texto no son validación de sintaxis/semántica SQL por PostgreSQL. No afirmar que la migración funciona hasta ejecutarla en el destino aislado.

## 7. Autorización necesaria para la validación efectiva

Docker está disponible como CLI; no se consultó el motor ni se inició ningún contenedor. psql y PostgreSQL no aparecen en PATH; no se detectaron drivers/parsers PostgreSQL en la .venv. No se instaló nada.

La solicitud exige pedir autorización antes de levantar servicios o instalar dependencias. Próximo paso propuesto, solo si se autoriza: crear un PostgreSQL 16 o stack Supabase local nuevo, con recursos de prueba exclusivos, sin credenciales ni enlace remoto; aplicar baseline una vez, ejecutar contratos SQL y repetir en otra base vacía. Para probar los handlers con su cliente real se requiere Supabase/PostgREST local, no solo PostgreSQL.

Si se autoriza un único PostgreSQL primero, cerrar solo la validación estructural/SQL; dejar el smoke API pendiente. Si se autoriza stack Supabase completo, documentar primero nombres, puertos, volúmenes y aislamiento para no tocar recursos existentes. Cualquier descarga de imágenes/herramientas o limpieza de esos recursos debe estar comprendida en el alcance aprobado. No se autoriza implícitamente producción por aprobar lo local.

## 8. Criterios de revisión y estado

Preparado: archivo inicial reproducible como propuesta, contraste del contrato, permisos separados, dependencia de datos identificada, mecanismo y procedimiento de pruebas, incertidumbres explícitas y ningún entorno real alterado.

Pendiente antes de declarar FIN-01 completo: reconstrucción efectiva con PostgreSQL, compatibilidad API local y verificación de metadatos no aportados que afecten al contrato; no confundir una revisión de SQL con aceptación integrada. No se cambia el estado de FIN-01, FIN-02 o FIN-03 ni el backlog oficial. No hay commits, push, despliegues o cambios de código de negocio.
