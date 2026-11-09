# PG-03 — Validación pendiente para PG-04

Fecha: 09/11/2026. Preparación documental exclusivamente. No se arranca PG-04 ni se concede autorización para crear contenedores, conectarse a DB o aplicar migraciones. FIN-01 permanece pendiente.

## Estado recibido

La unidad de POST /game/intento usa connection.transaction() sobre la misma conexión del pool PG-02. Se bloquea partida con SELECT FOR UPDATE antes de validar estado/número y se conserva hasta commit/rollback. Al finalizar se inicializan stats con ON CONFLICT(usuario_id) DO NOTHING y luego se bloquea su fila. Contadores/rachas/media se calculan con el algoritmo previo. El pool sigue 0–4/autocommit=True para las operaciones fuera del bloque, sin cambios de configuración.

55 pruebas offline aprobadas, cero omitidas, incluidos los 45 casos anteriores sin cambios de métodos. No hay evidencia PostgreSQL real de transacciones ni locks. No se cambiaron baseline, dependencias ni infraestructura. Los documentos PG-01/02 quedan como historia, no se reescriben para dar por aceptadas estas garantías.

## Matriz mínima de validación real

Utilizar PostgreSQL 16 nuevo y desechable solamente con autorización expresa. Datos sintéticos, configuración independiente, sin Supabase/Azure ni credenciales reales. No reutilizar la autorización de contenedores ya finalizados de FIN-01B.

| Caso | Ensayo necesario | Criterio observable |
|---|---|---|
| P3-01 | Fallo SQL después de INSERT intento y antes/después de UPDATE partida. | Ningún intento, contador o estado parcial tras rollback; no éxito HTTP. |
| P3-02 | Fallo después de inicializar stats y durante su actualización al finalizar. | Intento, partida y stats previos intactos; la fila nueva de ceros tampoco persiste. |
| P3-03 | Dos requests sobre partida activa con varias oportunidades restantes. | Bloqueo efectivo entre conexiones distintas; números consecutivos distintos y contador coherente. |
| P3-04 | Dos requests sobre la sexta oportunidad; y dos intentos ganadores simultáneos. | Solo una finalización; la otra petición relee estado final y se rechaza con contrato previo. No séptimo intento ni doble stats. |
| P3-05a | Dos partidas distintas del mismo usuario sin fila stats finalizan simultáneamente. | Una sola fila UNIQUE, dos partidas contabilizadas, sin UniqueViolation expuesta. |
| P3-05b | Igual con stats existentes; combinar victorias de distinto número y una derrota. | Sin incrementos perdidos; media solo de victorias y rachas coherentes con un orden serial válido. |
| P3-06 | Error SQL/cancelación/timeout mientras espera lock o dentro de la transacción. | Rollback/descartado apropiado, sin locks retenidos; siguiente request obtiene conexión útil. |
| P3-07 | Fallo al confirmar/desconexión. | Sin respuesta 200 si commit no se confirma; sin replay automático. Resultado incierto documentado, no garantía falsa de reversión. |
| P3-08 | Dos procesos de la aplicación PG que implementen este protocolo. | Coordinación por PostgreSQL, independiente de memoria de proceso. No es validación completa de Blue-Green. |

Sincronizar los ensayos con barreras/eventos o control explícito de conexiones. Verificar estado de filas antes y después; no basarse solo en sleeps o respuestas HTTP. Las pruebas nuevas no deben copiar una implementación de locks PostgreSQL a MemoryDB para producir un verde artificial. El orden de llegada no determina qué petición obtiene primero el lock.

## Condiciones que deben comprobarse

- READ COMMITTED real. La inicialización ON CONFLICT seguida del SELECT necesita la visibilidad de la sentencia siguiente; con aislamiento superior puede aparecer SerializationFailure y no existen retries implementados.
- UNIQUE(usuario_id), defaults cero/now y PK/FK de la baseline FIN-01B. No añadir constraints para hacer pasar ensayos ni aplicar prototype/allow_all.sql automáticamente.
- Permisos del rol técnico para SELECT/INSERT/UPDATE y bloqueo de filas sobre las tablas; rol migrador separado. Ni superusuario operativo ni credenciales en frontend.
- UUID, JSONB, numeric/Decimal, timestamps y NULL con el driver real; comparar formas HTTP, no solamente ejecutar SQL parecido. Windows necesita loop Selector al conectar con psycopg async; el target Docker es Linux.
- Inserción transaccional de stats nuevos devuelve ceros que el helper actualiza; valores existentes no se pisan durante ON CONFLICT. Sin filas de ceros visibles después de un fallo.
- Todos los escritores de intentos deben usar el protocolo. Una release PG-02 que escriba fuera de esta transacción no queda protegida por la disciplina de PG-03. Las dos versiones futuras compartidas deben conservarla.
- Presupuesto de conexiones: hasta cuatro por proceso, sumando réplicas/Blue+Green. statement_timeout de 5 s también puede cortar esperas de lock; no se incorpora un retry para ocultarlo.

## Riesgos y límites que se conservan

usuario_id no está autenticado; la comprobación de coincidencia no acredita propiedad. GET/estadísticas no incorporan autorización. No hay cambios de diccionario, roles/esquema, backfill de NULL ni saneamiento general de datos históricos. La transición parte de una DB nueva y no migra historia Supabase.

Los GET conservan lecturas independientes bajo autocommit, sin snapshot global entre partida/intentos. La tarea protege las escrituras del intento y finalización; no pretende convertir todas las operaciones en transacciones SERIALIZABLE. Los escritores SQL ajenos y eliminaciones administrativas no están cubiertos por una nueva capa de permisos.

No se implementan idempotency keys, reintentos, replicación, alta disponibilidad, locks distribuidos, colas, Redis ni infraestructura. Ninguno es necesario para probar esta unidad mínima del TFG. Si PG-04 descubre una incompatibilidad funcional o exige cambiar esquema/arquitectura, informar antes de ampliar el alcance.

Continuación únicamente tras revisión y autorización del propietario; no crear commits, desplegar, actualizar FIN-01..22 o iniciar servicios por este documento.
