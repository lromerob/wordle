# PG-01 - Contrato HTTP y reglas funcionales actuales

Fecha: 08/11/2026. Documentación para revisión; no implementación. Corte: rama codex/devops-04a1-hardening, commit a666b17680781a24889ea774778019995d3fca45, con SQL y análisis previos locales preservados. No se hizo fetch ni se afirma que sea main remoto actual. Inspección de fuentes/pruebas sin ejecutar aplicación, servicios, tests o conexiones.

Este documento distingue contrato explícito del código, expectativas de framework y comportamiento de proveedor no verificado. No hay response_model en estos endpoints. Ejemplos son sintéticos y describen forma, no capturas de una ejecución nueva. La futura migración cambia el acceso a datos, no las reglas ni la API consumida por Wordle.

## Fuentes verificadas

- [main.py](../../../backend/app/main.py): FastAPI Wordle ES API 1.0.0, routers, CORS y health.
- [game.py](../../../backend/app/routers/game.py): IntentoPeticion líneas 13-16; evaluación 19-34; nueva_partida 38-53; registrar_intento 57-112; estado_partida 117-128; estadísticas 131-157.
- [stats.py](../../../backend/app/routers/stats.py): estadísticas 8-26 y ranking 30-37.
- [database.py](../../../backend/app/database.py): cliente lazy y ausencia de traducción de excepciones del proveedor.
- [test_backend.py](../../../backend/tests/test_backend.py), [test_stabilization.py](../../../backend/tests/test_stabilization.py): pruebas existentes con MemoryDB; no equivalen a transporte Supabase real.
- [api.js](../../../frontend/src/api.js): consumo de nueva/intento/GET, mensajes y recuperación de escrituras inciertas.
- [baseline SQL](../../../supabase/migrations/20261108000100_initial_wordle.sql) y [resultado FIN-01B](../fin-01b/FIN-01B-POSTGRES-VALIDATION.md): campos reales recuperados y validación SQL local histórica; no prueba de serialización HTTP Supabase.

## 1. Rutas, representación y contexto

| ID | Método/ruta FastAPI | Entrada | Éxito |
|---|---|---|---|
| H01 | GET /health | Sin parámetros de aplicación | 200, {"status":"ok"} |
| H02 | POST /game/nueva | Query usuario_id obligatorio, str; sin cuerpo de aplicación definido | 200, {"partida_id":"<id>"} |
| H03 | POST /game/intento | JSON con partida_id, palabra y usuario_id, todos str obligatorios | 200, resultado/estado/intentos_usados/palabra_secreta |
| H04 | GET /game/{partida_id} | Segmento path str obligatorio | 200, {"partida":{...},"intentos":[...]} |
| H05 | GET /stats/{usuario_id} | Segmento path str obligatorio | 200, ceros si no hay fila o fila completa más porcentaje_victorias |
| H06 | GET /stats/ranking/global | Sin query/body de aplicación | 200, {"ranking":[...]} |

Son cinco endpoints de datos y uno de proceso. /api no es un prefijo de FastAPI: [Nginx](../../../frontend/nginx.conf) lo elimina al proxy; desde navegador Docker se usa /api/game/... y /api/health. Conservar ambos contratos de ruta, sin añadir /api a los routers. /stats/ranking/global tiene dos segmentos tras stats y no se confunde con el path de usuario de un segmento.

FastAPI declara por defecto documentación/OpenAPI en /docs, /redoc, /openapi.json y soporte de redirección OAuth de Swagger; no constituyen autenticación implementada ni endpoints de juego. No se evaluó su representación en un navegador. CORS permite todos los orígenes/métodos/headers, sin configuración explícita allow_credentials; PG-01 no cambia esa política.

Éxitos y HTTPException controladas son JSON. No hay autorización HTTP/token de usuario en las firmas ni cabeceras de aplicación requeridas. usuario_id es identificación declarada por cliente, sin acreditación de identidad. Parámetros de path/usuario no se normalizan ni validan como UUID. No se agrega una restricción UUID al cuerpo Pydantic en PG-01.

## 2. H01 - GET /health

Respuesta exacta de aplicación: {"status":"ok"}, estado 200. No depende de get_supabase ni comprueba DB/diccionario. No declarar esta ruta una prueba de persistencia. Importar la aplicación no crea el cliente Supabase; un nuevo pool debe respetar el objetivo de no conectar al importar y no transformar health silenciosamente en otro chequeo.

## 3. H02 - POST /game/nueva

Entrada: usuario_id en query, obligatorio, tipo str sin min_length, formato UUID ni normalización. Un string vacío no tiene rechazo explícito en la aplicación. El backend no crea usuario Auth ni consulta una tabla de usuarios. No existe body de negocio para esta operación.

Flujo actual: SELECT palabra de palabras -> si no hay filas, error -> elección random.choice en Python -> upper de solución -> INSERT con usuario_id, palabra_secreta, intentos_usados=0 y estado=en_curso -> retornar solo partida_id desde la fila insertada. No copia timestamps a la respuesta ni revela solución.

Éxito: 200 con una única clave partida_id. En el esquema recuperado el ID es UUID, esperado como cadena JSON reutilizable en H03/H04; las fixtures antiguas usan game-1 y no prueban el formato real. Ejemplo sintético de forma:

```json
{"partida_id":"00000000-0000-4000-8000-000000000001"}
```

Error explícito: 500, {"detail":"No hay palabras disponibles"}. El formato de error cuando falla el INSERT o no devuelve filas no está manejado; no inventar que es el mismo 500 JSON. La selección no filtra el diccionario por longitud/alfabeto ni fuerza mayúsculas antes de cargarlo; la validez del vocabulario es precondición de datos, no una funcionalidad nueva del endpoint.

## 4. H03 - POST /game/intento

Cuerpo JSON de aplicación:

```json
{"partida_id":"00000000-0000-4000-8000-000000000001","palabra":" casas ","usuario_id":"demo-sintetico"}
```

Los tres campos son str requeridos, sin defaults. No son parámetros query. Solo palabra recibe strip y upper; usuario_id/partida_id no se recortan ni convierten. La validación se hace antes de upper: exactamente cinco caracteres del conjunto A-Z/a-z/Ñ/ñ. No se normalizan tildes, no se admiten dígitos/símbolos ni expansiones Unicode como ß. El modelo no declara extra=forbid ni modo estricto personalizado; no introducir cambios de configuración Pydantic por cambiar el driver.

### Orden de comprobaciones explícitas

Tras resolver dependencia y cuerpo, la función comprueba:

| Orden | Condición | HTTP / detail |
|---|---|---|
| 1 | Longitud o alfabeto incorrectos | 400 / La palabra debe tener 5 letras de A a Z o Ñ |
| 2 | SELECT por id no devuelve partida | 404 / Partida no encontrada |
| 3 | usuario_id no coincide exactamente con el almacenado | 403 / El usuario no coincide con la partida |
| 4 | estado no es en_curso | 400 / La partida ya terminó: <estado almacenado> |
| 5 | intentos_usados >= 6 con estado aún activo | 400 / No quedan intentos |
| 6 | Palabra normalizada no está en diccionario | 400 / Palabra no válida |

El cuerpo de error controlado es {"detail":"<texto>"}. Conservar textos, códigos y precedencia: una partida finalizada con usuario incorrecto devuelve primero 403; longitud inválida se comprueba antes de buscar partida. Una dependencia rota puede fallar antes de llegar al handler, por lo que esta tabla no promete errores de negocio cuando la conexión ni siquiera está disponible.

Un UUID con sintaxis inválida no es igual que un UUID válido inexistente: el primero puede provocar excepción del proveedor, mientras el segundo conduce al 404 si la consulta retorna cero filas. No se probó contra Supabase real ni hay traducción dedicada en el código. No convertir los IDs ficticios de tests en prueba de aceptación SQL de cualquier string.

### Resultado correcto

Se evalúa el intento con dos pasadas: primero coincidencias exactas, después presentes limitados al conteo restante de la solución. El resultado conserva el orden de las cinco letras, ya en mayúsculas. Valores de estado por letra: correcto, presente, ausente.

Se incrementa intentos_usados en uno solo para una palabra admitida. Todas correctas -> ganada, incluso en intento seis. Si no gana y alcanza seis -> perdida. En otro caso -> en_curso. Inserta intento con numero nuevo, actualiza partida y, al terminar, estadísticas.

Respuesta siempre con cuatro claves: resultado (cinco objetos letra/estado), estado, intentos_usados y palabra_secreta. Esta última vale null durante juego activo y al ganar; solo en derrota contiene la solución. No omitir la clave null ni devolver la solución al ganar por analogía con GET.

```json
{"resultado":[{"letra":"C","estado":"correcto"},{"letra":"A","estado":"correcto"},{"letra":"S","estado":"correcto"},{"letra":"A","estado":"correcto"},{"letra":"S","estado":"correcto"}],"estado":"ganada","intentos_usados":1,"palabra_secreta":null}
```

Las validaciones rechazadas anteriores no escriben datos. Después del sexto fallo, la séptima petición de usuario correcto normalmente falla por estado final (orden 4), no por el mensaje del orden 5. El mensaje No quedan intentos corresponde al caso activo incoherente ya al límite. Una petición posterior a victoria también debe rechazarse sin modificar intentos/estadísticas.

Hoy las escrituras son llamadas separadas: un fallo durante persistencia puede dejar estado parcial. Eso es un riesgo técnico actual, no un comportamiento a preservar como requisito; PG-03 debe asegurar atomicidad sin cambiar las reglas de éxito.

## 5. H04 - GET /game/{partida_id}

Busca partida por id, limit 1; si no existe, 404 con {"detail":"Partida no encontrada"}. Obtiene intentos por partida_id ordenados ascendentemente por numero. El código no exige usuario_id query ni autentica propietario para GET. Path sin segmento no es un 404 de partida emitido por este handler; es enrutamiento del framework.

Respuesta: {"partida": <fila copiada>, "intentos": <lista de filas>}. Sin intentos: lista vacía. El backend quita palabra_secreta si estado no pertenece a ganada/perdida, incluidos estados desconocidos/null; no modifica el dato almacenado.

Campos de partida según esquema recuperado: id, usuario_id, intentos_usados, estado, created_at y, solo en estados finales conocidos, palabra_secreta. Campos de cada intento: id, partida_id, usuario_id, numero, palabra, resultado, created_at. Hay SELECT *, no response_model: describir estos campos no acredita una allowlist de columnas adicionales desconocidas.

**Diferencia deliberada de contrato:** GET de ganada conserva palabra_secreta en la fila, mientras POST de intento ganador devuelve esa clave como null. No homogeneizarlo al cambiar el acceso. GET de perdida también conserva la solución. No hay filtro adicional de usuario en intentos de una partida.

Los UUID se esperan como cadenas y resultado como JSON, no texto JSON anidado. created_at es timestamp sin zona en DB y puede ser null; el formato temporal exacto del transporte Supabase no está congelado por una respuesta real observada. No añadir sufijo Z o zona horaria por inferencia.

## 6. H05 - GET /stats/{usuario_id}

SELECT * de estadísticas por usuario_id; no hay normalización ni autenticación de usuario. Si no hay fila, 200 con exactamente estos cinco campos:

```json
{"partidas_jugadas":0,"partidas_ganadas":0,"racha_actual":0,"racha_maxima":0,"porcentaje_victorias":0}
```

No devuelve usuario_id, id, updated_at o intentos_promedio=0 en esta rama. No añadirlos por uniformidad de modelo durante PG-02.

Si hay fila: devuelve la fila completa más porcentaje_victorias. Con el esquema recuperado: id, usuario_id, partidas_jugadas, partidas_ganadas, racha_actual, racha_maxima, intentos_promedio, updated_at y porcentaje_victorias. El porcentaje es round(ganadas/jugadas*100) si jugadas>0; si no, 0. Es el round de Python actual, sin precisión decimal explícita, y no una columna almacenada. Las columnas nullable pueden provocar errores si contienen datos incompatibles con las operaciones Python; no inventar una conversión general de NULL a cero.

### Actualización de estadísticas al finalizar partida

Fila nueva: jugadas=1; ganadas=1 si gana, 0 si pierde; racha_actual/maxima=1 si gana, 0 si pierde; intentos_promedio=intentos si gana, 0 si pierde.

Fila existente: jugadas +1; ganadas +1 solo si gana; racha_actual +1 al ganar y 0 al perder; racha_maxima=max(anterior,nueva racha). Si gana: promedio=(promedio_anterior*ganadas_anteriores+intentos)/(ganadas_anteriores+1); para ese cálculo, promedio nulo/falsey se usa como 0. Si pierde: conserva promedio anterior o 0 si era falsey. No aplicar esa tolerancia a todos los campos por extrapolación.

El backend no actualiza updated_at explícitamente ni hay trigger informado para hacerlo; no introducir timestamp de actualización automático. Una partida finalizada solo se contabiliza una vez bajo flujo secuencial válido; concurrencia/atomicidad quedan para PG-03.

## 7. H06 - GET /stats/ranking/global

Proyecta solo usuario_id, partidas_ganadas, racha_maxima y partidas_jugadas; ordena por partidas_ganadas descendente y limita a 10. Respuesta 200, {"ranking": []} si vacío, o lista de esos cuatro campos. No devuelve ID, promedio, timestamp o porcentaje. Sin filtros/parametrización de página de aplicación.

No hay desempate ni orden de NULL explícito en la llamada SDK. No prometer un orden determinado entre empates ni cambiarlo silenciosamente por conveniencia SQL. No se ha observado el transporte real para fijar detalles adicionales.

## 8. Validación de framework y errores no definidos

Los parámetros/campos obligatorios y tipos Pydantic originan validación FastAPI (normalmente 422 con detail como lista). No hay handler personalizado para ese error. Falta de query usuario_id, cuerpo incompleto o tipos incompatibles no son errores de negocio 400. La forma exacta de cada item/detail, mensajes de Pydantic, tratamiento de campos extra y de JSON malformado depende de las versiones declaradas y no se ejecutó en PG-01; conservar configuración y añadir casos en aceptación futura antes de prometer bytes exactos.

Errores de ruta/método y redirecciones de slash pertenecen al framework/proxy; no se redefine su comportamiento aquí. FastAPI declara éxito 200 por defecto en los POST, no 201. No añadir 204 u otros códigos al sustituir SDK.

No hay captura explícita de excepciones Supabase/PostgREST, de configuración faltante o de filas inesperadas. Un error no controlado suele terminar en 500 gestionado por framework/servidor (TestClient puede propagar excepción), pero no hay contrato de detail JSON uniforme para esos casos. No exponer excepciones internas/DSN; clasificar su traducción mínima antes de PG-02 sin preservar filtraciones o un fallo incidental como requisito funcional.

## 9. Reglas y compatibilidad que deben permanecer

- Cinco letras, seis intentos; letras repetidas con conteo y prioridad de posición.
- Normalizar solo palabra; A-Z/Ñ y lookup de diccionario, sin acentos añadidos.
- No consumir intento ni actualizar estadísticas al rechazar validaciones.
- Propietario declarado comprobado antes del estado/límite; sin llamar a esto autenticación.
- Victoria en el sexto válida; derrota al sexto fallido; partida terminada no admite nuevos intentos.
- Solución activa oculta en GET; clave null en POST salvo derrota; GET final conserva fila/solución.
- Estadísticas solo al terminar, media sobre victorias, rachas y ranking con formas distintas ya descritas.
- No nuevas funciones, endpoints, rediseño RLS, campos o restricciones SQL.

La UI marca errores >=500/transporte como escritura incierta y recupera GET; no reintenta automáticamente el POST. La futura capa DB debe evitar reintentos ciegos de escrituras tras un commit incierto.

## 10. Incertidumbres y evidencia siguiente

Faltan muestras reales de serialización Supabase, manejo uniforme de UUID malformado/proveedor y comportamiento concurrente. Se congelan los contratos explícitos del código y los casos respaldados por tests, no resultados remotos no observados. La nueva base no contiene datos históricos, por decisión del propietario; no se necesita extraerlos para construir pruebas sintéticas.

Los IDs no UUID game-1 y missing de MemoryDB prueban ramas del handler, no casts SQL. PG-02 debe conservar las ramas usando UUID válidos en integración y resolver separadamente entradas malformadas. Fechas, números, NULL y validación framework requieren nuevos casos de compatibilidad en entorno aislado autorizado. No se ejecutaron en esta tarea.
