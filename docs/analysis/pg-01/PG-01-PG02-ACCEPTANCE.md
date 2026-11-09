# PG-01 - Aceptación propuesta de PG-02 y PG-03

Fecha: 08/11/2026. Checklist verificable para una implementación futura explícitamente autorizada. No son pruebas ejecutadas, tickets nuevos ni cambio de estado del plan FIN. [Contrato actual](PG-01-HTTP-CONTRACT.md), [decisión](PG-01-TRANSITION-DECISION.md).

## 1. Prerrequisitos y alcance

- Objetivo aprobado: psycopg 3 async/pool acotado, una DB nueva PG16 y ninguna importación de datos históricos Supabase.
- Resolver D01-D09 o registrar cuáles necesitan aprobación específica. En particular no asignar un nuevo código HTTP a UUID malformado como supuesto histórico.
- Mantener baseline y contratos SQL existentes. Nueva integración local requiere autorización de dependencias/runtime; PG-01 no la concede.
- API pública idéntica para los casos definidos; no cambiar el frontend para ocultar una incompatibilidad del backend.
- Mantener modo memoria como nivel distinto de integración PG. Un verde con MemoryDB no satisface una prueba del driver ni la persistencia.

## 2. Criterios PG-02: acceso y paridad funcional

| ID | Criterio verificable | Cómo aceptarlo y evidencia |
|---|---|---|
| P2-01 | Dependencias y configuración | Versiones/lock revisados; psycopg async/pool realmente usados, sin import/llamada Supabase del runtime objetivo; conexión solo a DB nueva local. No reintroducir PostgREST como puente. |
| P2-02 | Import/lifecycle | Importar app no abre sockets; pool por proceso se abre/cierra según decisión, no por request; conexiones devueltas al fallar/cancelar; no tareas/pools sin cerrar en tests. |
| P2-03 | Pool acotado y disponibilidad | Parámetros y timeouts explícitos, prueba con más solicitudes que conexiones y recuperación tras fallo; sin bloqueo sync del event loop. H01 conserva 200/status ok como proceso bajo condiciones acordadas de arranque y sin consulta DB. |
| P2-04 | Nueva partida | H02 responde 200 y solo partida_id; es UUID str reutilizable; insert conserva defaults/reglas; ninguna palabra secreta expuesta. Diccionario vacío devuelve exactamente el 500/detail controlado existente. |
| P2-05 | Validación y precedencia | H03 reproduce todos los 400/403/404 y textos/orden documentados; errores de cuerpo/query siguen validación framework, no 400 inventado. Las validaciones fallidas no escriben. |
| P2-06 | Resultado del juego | Letras correctas/presentes/ausentes y orden; repetidas conservan conteo; seis intentos, victoria al sexto, derrota al sexto y rechazo posterior; null de solución en victoria/activo y solución solo en POST derrota. |
| P2-07 | GET de partida | H04 devuelve partida/intentos, orden numero asc y lista vacía inicial; sin solución para activo/desconocido/null; con solución en GET de ganada y perdida; no modifica DB al filtrar. |
| P2-08 | Estadísticas y ranking | H05 vacío mantiene exactamente cinco claves sin promedio/ID; con fila mantiene campos conocidos y porcentaje Python; media solo sobre victorias y rachas iguales. H06 limita a 10/proyecta cuatro campos, sin exigir desempate no definido. |
| P2-09 | Tipos JSON | UUID a str; JSONB a lista/objetos, sin doble codificación; promedio fraccionario numérico; timestamps y null fieles sin sufijo Z inventado ni nueva zona; no conversión global NULL->0. |
| P2-10 | Errores de driver | UUID sintácticamente inválido según decisión documentada; UUID válido inexistente mantiene 404. Fallos DB controlados sin DSN/SQL/credencial, conexión limpia al recuperarse. No tests que exijan reproducir filtraciones accidentales del proveedor. |
| P2-11 | Capa de pruebas | Casos de evaluador y HTTP previos conservados/adaptados. Nuevos casos driver sobre PG real; mocks/AST no se usan para afirmar SQL. Cada resultado identifica modo, DB de ensayo y versión. |
| P2-12 | Alcance | Backend/requirements/tests mínimos de la implementación autorizada; sin cambios funcionales del frontend, baseline, Auth o infraestructura por sorpresa; código antiguo/history preservados según revisión. |

Aceptar PG-02 significa que el acceso directo reproduce los casos funcionales definidos y su lifecycle; no declara completas las garantías concurrentes de PG-03, el diccionario de FIN-02, backups, CI cloud o AKS. Cualquier garantía ya implementada puede aprovecharse, pero debe tener prueba antes de darla por aceptada.

## 3. Matriz mínima de casos de paridad

| Caso | Preparación sintética/entrada | Resultado esperado |
|---|---|---|
| C01 | App accesible, sin operación de datos | H01 200/status ok; no query DB desde handler health. |
| C02 | Diccionario vacío | H02 500, detail No hay palabras disponibles; ninguna partida insertada. |
| C03 | Diccionario controlado, usuario textual | H02 200, solo ID reutilizable; estado DB en_curso, cero intentos. |
| C04 | H03 sin campo obligatorio o query ausente en H02 | Error de validación FastAPI; comprobar 422 y forma detail según versiones, sin congelar mensaje no verificado. |
| C05 | CASA, 12345, CAFÉS, CAßS, espacios internos | H03 400 con texto de cinco letras/alfabeto; cero escritura. |
| C06 | casas con espacios exteriores | Normalización a CASAS, si existe en diccionario; no normalizar usuario/ID. |
| C07 | UUID válido que no está en DB | H03/H04 404 Partida no encontrada, sin writes. |
| C08 | UUID malformado | Resultado pendiente de D05; se documenta antes de implementar, no se infiere de fixture missing. |
| C09 | Usuario incorrecto y partida además finalizada | H03 403 por precedencia, sin escritura. |
| C10 | Usuario correcto, partida ya ganada/perdida | H03 400 La partida ya terminó: <estado>; contadores no aumentan. |
| C11 | Partida en_curso incoherente con intentos_usados=6 | H03 400 No quedan intentos; sin escritura. |
| C12 | ZZZZZ de longitud válida pero ausente del diccionario | H03 400 Palabra no válida; no consume intento. |
| C13 | Solución CASAS, intento SACAS | Estados presente/correcto/presente/correcto/correcto. |
| C14 | Solución CASAS, intento AAAAA | Estados ausente/correcto/ausente/correcto/ausente. |
| C15 | Solución CASAS, CASAS en intento 1 y otra partida en intento 6 | Ambas ganan; POST secreto null; solo una contabilización por finalización. |
| C16 | Solución CASAS, seis PERRO válidos | Perdida al sexto, POST revela CASAS; séptimo se rechaza por estado final. |
| C17 | GET activo con varios intentos | Secreto ausente; resultado JSON y orden ascendente; fila almacenada conserva solución. |
| C18 | GET final ganada/perdida; GET estado desconocido/null | Final mantiene solución; desconocido/null la oculta. |
| C19 | Usuario sin stats | Cinco ceros documentados, sin añadir intentos_promedio/usuario_id/id/updated_at. |
| C20 | Dos victorias de 1 y 2 intentos y después derrota | Promedio 1,5 tras dos victorias; derrota conserva promedio; contadores/rachas coherentes con algoritmo. |
| C21 | Más de diez estadísticas y empates | Ranking con máximo diez, cuatro campos, orden descendente sin orden fijo entre empates. |
| C22 | Fallo de DB/transporte simulado local | No secret/DSN en respuesta; error de datos según decisión; sin reintento automático de POST con commit incierto. |

Estos vocablos son fixtures ya existentes, no diccionario de producción inventado ni copia de Supabase. Para API determinista debe controlarse solo el fixture local (por ejemplo elección de solución mediante inyección en tests), sin añadir endpoint de secreto ni modificar reglas de random en producción.

## 4. Criterios PG-03: transacciones y concurrencia

| ID | Escenario | Aceptación verificable |
|---|---|---|
| P3-01 | Fallo después de INSERT intento y antes de UPDATE partida | Tras rollback, ninguna fila de intento nueva ni contador/estado parcial. La respuesta no confirma éxito de transacción fallida. |
| P3-02 | Fallo al actualizar estadísticas de finalización | Intento, partida y estadísticas conservan estado anterior de la unidad; no finalización parcialmente contabilizada. |
| P3-03 | Dos intentos simultáneos de la misma partida activa | Unidad de lectura/validación/escritura serializada por fila o mecanismo equivalente; numeración coherente y no más de seis; sin nuevo índice/constraint no aprobado. |
| P3-04 | Dos peticiones sobre última oportunidad o partida que acaba de ganarse | Solo las que resulten válidas tras leer estado vigente escriben; la posterior ve finalización/límite según contrato, sin doble actualización de stats. |
| P3-05 | Dos partidas distintas finalizan para el mismo usuario | UNIQUE usuario_id y actualización transaccional evitan duplicar fila/perder contadores o promedio; resolver carrera de primera fila sin exponer UniqueViolation cruda. |
| P3-06 | Liberación de conexión tras excepción/cancelación | La siguiente operación obtiene conexión útil, sin transacción abortada o lock retenido; timeout y límites no causan fuga de pool. |
| P3-07 | Commit e incertidumbre de escritura | Commit se verifica antes de retornar éxito normal; si la conexión se pierde en commit, no replay ciego ni deduplicación prometida inexistente. UI puede recuperar GET según contrato. |
| P3-08 | Dos versiones futuras PG compartiendo DB | Frontera transaccional no depende de memoria del proceso o un lock Python local. Ambas releases soportan el mismo esquema y el presupuesto de conexiones. Aceptación Blue-Green completa sigue en tareas posteriores. |

No añadir idempotency keys, rollback de datos, nuevas reglas de intentos o migraciones destructivas dentro de PG-03. Concurrencia puede decidir qué request obtiene primero el lock; no se promete un orden temporal de llegada no definido. Los tests deben sincronizar concurrencia de manera controlada y verificar resultados/estado, no depender solo de tiempos de sleep.

## 5. Evidencia y gates de revisión

Para cada caso: commit, modo (memoria/driver PG), versión Python/driver/PG, configuración sin secretos, datos sintéticos y estado antes/después, salida de prueba y criterio cubierto. Conservar los checks SQL FIN-01B como evidencia separada, con sus hashes. Un test que solo ejecuta SQL análogo no acredita handlers; un test HTTP con mock no acredita PG real.

Gate PG-02: paridad/lifecycle y excepciones decididas, sin cambio funcional inesperado. Gate PG-03: transacciones/concurrencia probadas en DB real local. Gate posterior: volumen/reinicio/backup, CI, StatefulSet/AKS y Blue-Green completo; no adelantarlos por tener un driver.

Estado actual: solo documentos. No se ejecutan los casos anteriores en PG-01; no se da PG-02/03 por comenzado o completado y FIN-01 continúa pendiente. Esperar autorización expresa antes de instalar o implementar.
