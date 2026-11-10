# FIN-01S — Decisión arquitectónica

Fecha: 10/11/2026 (Europe/Madrid). Revisión documental, sin nuevas pruebas. Corte: b330ae70caf08ac789786376ca5de0305ea4471f, rama codex/pg01-07-consolidation.

**Decisión técnica: baseline aceptado como versión inicial del esquema PostgreSQL de Wordle.** Evaluación realizada bajo FIN-01S; la revisión de cierre por el propietario sigue separada.

## Referencia exacta

`supabase/migrations/20261108000100_initial_wordle.sql`, blob Git `69fe425eebf6230df904d071f49136b6c194137b`, en el commit de corte. SHA256 local CRLF: `da743e629094da2b7d126f7889c5d1ca72e63a232844feadea3798254b19b0cb`. PUB-04 documenta normalización LF del mismo contenido en Git: SHA256 c499bf3061c98a803d71b96ea7cdc4ce7b51572f7b1d2e70b27f31f8370a23bc. Diferencias de bytes LF/CRLF no se presentan como cambio de esquema.

## Decisiones ratificadas en este registro

1. El DDL existente es la referencia para **instalaciones nuevas** PostgreSQL16: cuatro tablas, 23 columnas, defaults, nulabilidad, cuatro PK, dos UNIQUE, una FK y secuencia. Se aceptan VARCHAR/NUMERIC sin typmod, defaults de secuencia sin OWNED BY añadido y acciones FK NO ACTION/MATCH SIMPLE/no diferible. Son elecciones explícitas para el destino nuevo, sin pretender recuperar metadatos de Supabase desconocidos.
2. Las validaciones existentes FIN-01B y PG-04/05/06/07, junto al run remoto identificado en la revisión, constituyen evidencia suficiente del alcance. FIN-01S no ejecuta pruebas ni presume controles no registrados.
3. El esquema **no es inmutable**. No reescribir esta baseline para evolucionar bases ya creadas. Cambios posteriores mediante migraciones nuevas versionadas, con procedimiento ordenado de aplicación y pruebas desde esquema previo/base vacía según corresponda; compatibilidad entre versiones de aplicación para futuro Blue-Green. No se instala un framework ni se implementan migraciones ahora.
4. Bootstrap operativo: baseline más fixture y rol técnico de `docker/postgres/`, reutilizado por Compose/kind/CI. `supabase/prototype/allow_all.sql`, `supabase/tests/prototype_access.sql` y el smoke Supabase antiguo son archivo histórico, no parte del bootstrap PG. El nombre de carpeta no implica dependencia operativa Supabase.
5. No se garantiza ni se ejecuta migración automática de datos históricos Supabase: la arquitectura aprobó base nueva, sin doble escritura. No se borra ni altera el servicio anterior.
6. La aceptación **no aprueba seguridad de producción**. usuario_id es cliente no autenticado; grants/Secret técnicos no resuelven propiedad del jugador. Integridad de intentos requiere escritores que usen el protocolo transaccional PG-03. CORS/exposición, permisos operativos y pruebas negativas pertenecen a FIN-03/07.

## Consecuencias aceptadas

Se mantienen NULL permitidos, timestamps sin zona y updated_at de inserción; no se inventan CHECKs, cascadas, Auth/FK de palabras, índices o restricciones nuevas. Para el flujo sintético controlado estas limitaciones están documentadas y no han producido incompatibilidad en las pruebas reales. Cambios futuros deben preservar contrato o declarar su evolución; rollback de aplicación no revierte datos/DDL. PostgreSQL de una réplica y PVC local no equivalen a HA o backup.

Esta decisión resuelve la condición técnica de FIN-01R de evaluar y fijar los supuestos como contrato nuevo. No exige otra firma técnica circular para recomendar cierre: la decisión definitiva de marcar FIN-01 completado queda al propietario tras revisar estos documentos.
