# PG-02 — Traspaso de riesgos a PG-03

Fecha: 08/11/2026. Trabajo futuro sujeto a autorización. Este documento no inicia PG-03/PG-04 ni actualiza FIN-01 a FIN-22. FIN-01 permanece pendiente.

## Estado recibido

psycopg 3.3.8 async + psycopg_pool 3.3.3; pool por proceso 0–4, ocho esperas máximas, adquisición/conexión de 3 s y sentencias de 5 s. Una conexión se presta por request mediante get_repository; se cierra su cursor en cada consulta y vuelve al pool al finalizar, fallar o cancelar. Está en autocommit para mantener escrituras independientes hasta definir la unidad transaccional.

Las 45 pruebas offline preservan los 26 casos previos y cubren adaptación/contratos/lifecycle. No son evidencia de PostgreSQL real ni de las garantías P3. No se modificó SQL. Los contratos PG-01 siguen siendo referencia; GET final ganada conserva solución, POST ganador devuelve null. No homogeneizar estas ramas por accidente.

## Riesgos pendientes

| Riesgo | Situación actual | Trabajo PG-03 por autorizar |
|---|---|---|
| Intento parcialmente persistido | INSERT intento, UPDATE partida y actualización stats son sentencias confirmadas separadamente. Un fallo intermedio no revierte anteriores. | Unidad explícita de transacción que confirme antes del éxito HTTP; pruebas de fallo entre todas las escrituras y rollback. |
| Dos intentos de una partida | Dos requests pueden leer el mismo estado/número y escribir dos veces, superar seis o contabilizar finalización incorrectamente. No hay lock de aplicación/SQL. | Serialización por fila compatible con procesos/colores; releer/validar bajo la unidad transaccional. |
| Primera estadística simultánea | SELECT seguido de INSERT puede competir con UNIQUE(usuario_id). Hoy llega al 500 sanitizado. | Resolver la carrera sin nuevas restricciones ni cambiar promedio/rachas; incluir dos partidas distintas del mismo usuario. |
| Estadísticas existentes simultáneas | El cálculo Python lee valores y luego escribe; puede perder incrementos. | Lectura/actualización transaccional coherente y tests deterministas de promedio/rachas. |
| Pérdida de conexión durante confirmación | El cliente puede recibir error aunque una escritura ya esté confirmada. No existe replay ni idempotency key. | Conservar incertidumbre controlada, no reintentar POST a ciegas. La UI recupera GET; no prometer exactamente una vez. |
| Cancelación y pool | Retorno/cierre comprobados con conexiones simuladas, no estado real de transacción libpq. | Probar rollback/limpieza/reutilización ante fallo y cancelación reales en entorno autorizado; distinguir conexión descartada de conexión recuperable. |
| Presupuesto de conexiones | Máximo cuatro por proceso; Blue+Green/múltiples workers multiplican consumo. | Medir/dimensionar globalmente; no añadir locks Python locales como sustituto de coordinación DB. |

No se implementaron SELECT FOR UPDATE, reintentos por carreras, UPSERT/rediseño de estadísticas, nuevas restricciones, ALTER TABLE ni mecanismos de migración. Tampoco se añadieron autenticación, PK/índices nuevos o un esquema alternativo. usuario_id sigue siendo texto no acreditado; su comparación NO proporciona autorización efectiva. GET de partidas/estadísticas carece de autenticación y este riesgo continúa.

## Criterios de aceptación futuros

Usar P3-01 a P3-08 del documento PG-01 de aceptación, preservando rutas, modelos y errores de negocio. Inyectar fallos tras INSERT y antes de UPDATE/stats; dos requests sincronizados de la misma partida y última oportunidad; dos partidas del mismo usuario creando/actualizando stats; conexión útil tras error/cancelación; confirmación antes de respuesta y sin replay incierto. No reducir aserciones ni alterar esquema para facilitar esos casos.

PG-03 puede preparar pruebas con dobles, pero su aceptación de atomicidad/concurrencia requiere evidencia de base real según el gate acordado. La autorización PG-02 actual no permite arrancar PostgreSQL: si PG-03 necesita ejecutar esa validación, pedir permiso específico en esa tarea. PG-04 deberá ejecutar los handlers y SQL del driver con PostgreSQL 16 nuevo, probar UUID/JSONB/numeric/timestamp y recuperar errores reales. FIN-01B valida estructura histórica, no sustituye esa integración.

## Gates operativos posteriores, fuera de PG-03

- PG-04: SQL/driver/API reales en DB nueva aislada, sin historia Supabase ni servicios externos; compatibilidad Linux y comprobación del loop Selector si se admite ejecución Windows con conexión real.
- PG-05: Compose con PG y configuración privada; baseline/seed one-shot, diccionario aprobado y persistencia. Compose actual no proporciona PG al runtime nuevo.
- PG-06/07: perfil de datos Kubernetes/CI separado; mantener claro que el perfil existente usa memoria. No exponer DB, incluir secretos en frontend ni recrear PVC con el color de aplicación.
- PG-08: backup/restore autorizado sobre datos de ensayo, con copia externa antes de cualquier limpieza. Una instancia es un punto único de fallo aceptado, no HA.
- Autenticación/rol operativo/TLS/diccionario: decisiones pendientes del alcance correspondiente, sin aprovechar esta migración para inventar identidad ni permisos. No aplicar prototype/allow_all.sql automáticamente a PG directo.

La primera transición a una DB nueva no tiene rollback de datos hacia Supabase. Blue-Green futuro solo entre versiones PG compatibles compartiendo DB; no rollback de tablas ni doble escritura. Ninguno de estos gates se declara ejecutado.
