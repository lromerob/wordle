# PG-03 — Atomicidad y concurrencia mínima

Fecha: 09/11/2026. Implementación preparada para revisión, con validación exclusivamente offline. FIN-01 permanece pendiente. No se inicia PG-04. Rama existente conservada: codex/devops-04a1-hardening; HEAD de referencia a666b17680781a24889ea774778019995d3fca45. PG-02 y documentos/SQL previos seguían sin commit al comenzar; no se crean commits ni se publica nada.

## Diagnóstico basado en código

Se leyeron los dos informes PG-02 solicitados, el contrato/aceptación PG-01 y FIN-01C-MIGRATION-PLAN. En el código PG-02, autocommit=True confirmaba INSERT intento, UPDATE partida y cambios de estadísticas por separado. Una excepción después del INSERT podía dejar un intento sin contador correspondiente. La lectura de partida no bloqueaba su fila: dos requests podían calcular el mismo número o finalizarla dos veces. La lectura de estadísticas seguida de INSERT/UPDATE también permitía conflictos de primera fila o pérdida de contadores entre partidas diferentes. Son intercalaciones permitidas por las operaciones existentes, no incidencias observadas contra una DB en esta tarea.

La solución utiliza transacciones y bloqueos de fila nativos sobre el esquema existente. No se requiere un cambio importante de arquitectura ni un servicio adicional. Los casos de cargas masivas o HA no se convierten en requisitos nuevos del TFG.

## Cambios frente al estado local PG-02

| Archivo | Cambio PG-03 |
|---|---|
| backend/app/repository.py | transaction() delega al contexto async de psycopg; get_game_for_update() bloquea partida; get_stats_for_update() inicializa con ON CONFLICT y bloquea estadísticas. |
| backend/app/routers/game.py | POST intento entra en transaction() antes de leer/bloquear partida; toda validación dependiente del estado y todas sus escrituras quedan dentro. Estadísticas leen bajo bloqueo. Respuesta se construye tras salir correctamente del contexto. |
| backend/tests/test_backend.py | MemoryDB añade contexto con snapshot para fallos unitarios y métodos de lectura nuevos; no implementa locks ni aislamiento. Los 20 tests anteriores no cambian. |
| backend/tests/test_postgres_adapter.py | La conexión simulada incorpora el protocolo transaction() sin emular PostgreSQL. Sus 19 tests no cambian. |
| backend/tests/test_transactions.py (nuevo) | Diez pruebas focalizadas de uso del contexto, SQL/bloqueos solicitados, errores y contratos. |

Se crean únicamente los tres documentos solicitados en esta carpeta. No cambian database.py/pool, modelos, evaluador, endpoints de GET, dependencias/lock, harness, frontend, Compose, Kubernetes, Terraform, CI/CD, esquema, migraciones ni documentación histórica. Los 45 métodos de prueba PG-02 son idénticos por AST al estado de entrada. Las huellas de archivos previos fuera de los cuatro indicados permanecen iguales.

## Frontera transaccional

1. Se conserva la validación de cinco letras A–Z/Ñ antes de empezar el contexto transaccional. Modelos, normalización y errores no cambian.
2. `async with repository.transaction()` utiliza `connection.transaction()` de psycopg. El pool mantiene autocommit=True; en este bloque psycopg abre una transacción explícita, sin cambiar globalmente el comportamiento de los otros endpoints.
3. Se ejecuta SELECT de la partida por UUID con LIMIT 1 FOR UPDATE. Las comprobaciones de propietario declarado, estado, límite y diccionario usan la fila obtenida bajo bloqueo.
4. INSERT intento y UPDATE partida usan la misma conexión. Si finaliza, inicialización/lectura/actualización de estadísticas también usan esta transacción.
5. Salir del contexto sin excepción solicita COMMIT; con excepción, incluida HTTPException o cancelación, psycopg solicita ROLLBACK. La respuesta exitosa queda después del contexto. No se captura un error para continuar una transacción abortada.
6. La dependencia existente devuelve la conexión al pool; errores de driver, timeout o fallo de commit siguen el 500 sanitizado de PG-02. No se reintenta automáticamente una escritura.

Se conserva el riesgo inevitable de resultado incierto si la conexión se pierde al confirmar: un 500 no demuestra que el servidor haya revertido. No se promete exactamente una vez ni se añade replay/idempotencia. La UI puede consultar GET según su contrato anterior.

## Concurrencia de partida

El bloqueo se toma antes de leer el estado usado para validar/calcular el nuevo intento, y se conserva hasta terminar la transacción. Bajo READ COMMITTED, una segunda petición que espera ese bloqueo debe obtener la versión actualizada de la fila: usa el siguiente contador o rechaza el estado final/límite. GET sigue utilizando get_game(), sin FOR UPDATE ni una transacción de escritura nueva.

Esto coordina procesos distintos y versiones futuras que sigan el mismo protocolo PostgreSQL. Un lock Python local no se utiliza en producción. La garantía requiere que todos los escritores de intentos usen este camino; mezclar una versión antigua PG-02 que lea/escriba fuera del protocolo no queda validado para Blue-Green. No se modifican constraints para evitar duplicados por otros escritores ajenos.

## Concurrencia de estadísticas

Dentro de la misma transacción del intento final:

```sql
INSERT INTO public.estadisticas (usuario_id) VALUES (%s)
ON CONFLICT (usuario_id) DO NOTHING;
SELECT * FROM public.estadisticas WHERE usuario_id = %s LIMIT 1 FOR UPDATE;
```

Son dos sentencias parametrizadas, no interpolación. Se reutiliza UNIQUE(usuario_id) existente. Una primera finalización crea una fila con los valores predeterminados ya definidos en la baseline; si la fila existe no se sobrescriben sus contadores. A continuación se bloquea y se calcula el algoritmo de estadísticas existente. Para una fila nueva con ceros, el resultado equivale a la antigua rama de primera victoria/derrota; se añade una prueba explícita de esa equivalencia. Si no se obtiene la fila tras inicializarla, se lanza DataError y se aborta la operación.

Se asume READ COMMITTED, default normal de PostgreSQL 16 nuevo. Permite que la segunda sentencia vea la fila que una inserción concurrente acaba de confirmar. No se modifica la configuración de aislamiento del servidor. Si el destino impone REPEATABLE READ/SERIALIZABLE, la carrera puede terminar en error de serialización controlado; no se incorpora un mecanismo de retries. PG-04 debe verificar la configuración real.

El orden de adquisición es partida -> estadísticas del usuario. Cada request afecta una partida y un usuario, limitando el escenario de locks del TFG. No se cambia la media sobre victorias, rachas, porcentaje Python, ranking ni updated_at. Las filas nuevas de stats no son visibles a otros lectores como ceros intermedios antes de confirmar el intento completo.

## Compatibilidad y alcance

Rutas/métodos, modelo de tres strings, errores 400/403/404/422/500, precedencia de validaciones, resultados de repetidas y límite de seis se conservan. POST ganador mantiene palabra_secreta=null; POST perdedor revela solución; GET final conserva solución y GET activo/desconocido/null la omite. El diccionario y las reglas no cambian.

usuario_id continúa siendo una afirmación del cliente; compararlo no autentica al propietario. GET/estadísticas no incorporan autorización. Tampoco se añade consistencia de snapshot entre las dos lecturas de GET: su comportamiento previo se conserva y una actualización simultánea podría requerir refresco. Esta fase protege la unidad de escritura del intento, no todas las lecturas ni escritores externos.

Sin dependencias nuevas, instalaciones, contenedores, servicios, consultas a DB, migraciones, Azure o Supabase. No hay alta disponibilidad, replicación, Redis, colas, locks distribuidos ni retries por conflictos. Serían ampliaciones ajenas a este incremento mínimo.

## Criterios de revisión

| Criterio de la solicitud | Estado al finalizar |
|---|---|
| Una transacción para las escrituras del intento | Implementado; frontera y fallo comprobados con dobles. Rollback del servidor pendiente PG-04. |
| Protección de intentos simultáneos | FOR UPDATE dentro de transacción implementado; simultaneidad efectiva pendiente PG-04. |
| Estadísticas sin carreras evidentes | Inicialización UNIQUE/ON CONFLICT y fila bloqueada implementadas; carrera real pendiente PG-04. |
| Contratos intactos | 45 tests previos conservados y aprobados; modelo/evaluador sin cambios. |
| Nuevas pruebas focalizadas | Diez casos; sin simulador de bloqueos de PostgreSQL. |
| Alcance mínimo | Cuatro archivos previos backend, un test nuevo y estos tres documentos; sin infraestructura/esquema/dependencias. |

[Resultados detallados](PG-03-TEST-RESULTS.md). [Validación requerida en PG-04](PG-03-PG04-HANDOFF.md). La implementación queda lista para revisión, no aceptada como integración PostgreSQL real ni como cierre de FIN-01.
