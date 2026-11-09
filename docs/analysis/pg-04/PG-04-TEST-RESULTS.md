# PG-04 — Resultados reales de validación

Fecha: 09/11/2026. Ejecución Windows/Python 3.12.14 contra PG16 Linux temporal. Esta evidencia no modifica los resultados históricos de PG-02/03.

## Ejecuciones

| Ejecución | Resultado real |
|---|---|
| Primer arranque del ejecutor | Fallo del control de aislamiento antes de conexión/migración: .Mounts no enumera tmpfs en esta versión Docker. Contenedor y red retirados, ausencia verificada. |
| Corrección mínima del ejecutor | Se exige ausencia de bind/volume en .Mounts y presencia de ambos directorios en .HostConfig.Tmpfs. No cambia runtime ni SQL. |
| Primera suite real completa | 11 pruebas aprobadas, cero omitidas; 1.537 s. Caída real del servidor también aprobada. Recursos eliminados. |
| Suite final con controles de limpieza/logs | **11 pruebas aprobadas, cero omitidas; 1.901 s.** Más caída real aprobada. Cuatro tablas vacías, deadlocks=0 y tres errores SQL esperados en logs. |
| Suite offline separada | **55 pruebas aprobadas, cero omitidas; 1.169 s.** Bloqueo de sockets externos, DNS, .env y psycopg nativo. No se cambian las pruebas existentes. |
| Build backend | Éxito real: runtime Linux con instalación de 40 paquetes por hashes/wheels; no publicado. Etiqueta temporal retirada. |

No se suman las dos ejecuciones de once tests como si fueran 22 casos distintos ni la caída como un test unittest adicional. Hay 11 métodos reales con subcasos, una comprobación adicional de outage y 55 métodos offline.

## Repetición autorizada explícitamente

Desde la raíz, con dependencias de backend ya instaladas en un entorno aislado y Docker disponible:

```text
.venv/Scripts/python.exe -B backend/integration/run_pg04.py --run-disposable-postgres
```

En Linux: `python -B backend/integration/run_pg04.py --run-disposable-postgres`. El flag es obligatorio. El ejecutor no admite una DSN ni configuración de una DB existente; crea su propio destino vacío, aplica la baseline y siempre limpia sus IDs. Puede descargar la imagen oficial postgres:16 solo si falta localmente. Cada ejecución futura requiere que ese uso de Docker/DB temporal esté autorizado por su contexto.

La suite está fuera de backend/tests: discovery de unitarias no inicia Docker ni ejecuta integración. Si se descubre directamente la carpeta de integración sin su ejecutor, los casos se omiten deliberadamente en vez de usar un destino arbitrario. El runner exige cero omitidos en su ejecución real. Las contraseñas aleatorias no se escriben a archivos ni se incluyen en los comandos/documentos.

## Matriz de los 22 casos PG-01

| Caso | Evidencia real |
|---|---|
| C01 | Health/lifecycle: 200/status ok y pool_size=0 antes de datos; health 200 tras caída del servidor. |
| C02 | Diccionario vacío: 500/detail exacto, cero partidas creadas. |
| C03 | Nueva partida: 200, únicamente partida_id UUID string reutilizable; defaults/usuario literal contrastados por SQL. |
| C04 | Query/campos ausentes y palabra numérica: 422 de FastAPI. |
| C05 | Longitud, números, espacio interno, acentos y expansión Unicode: 400 exacto y cero intentos escritos. |
| C06 | casas/niños con espacios exteriores y minúsculas: normalización correcta. |
| C07 | UUID válido inexistente: 404/detail exacto en POST y GET. |
| C08 | UUID malformado: 500 genérico según decisión PG-02, sin error SQL crudo. |
| C09 | Usuario incorrecto con partida ganada: 403 antes de comprobar estado final. |
| C10 | Partidas finalizadas: nuevos intentos rechazados, sin nuevas filas. |
| C11 | Fixture en_curso con seis intentos usados: 400/No quedan intentos. |
| C12 | ZZZZZ no presente: 400/Palabra no válida, sin consumo. |
| C13 | SACAS contra CASAS: presente/correcto/presente/correcto/correcto. |
| C14 | AAAAA: ausente/correcto/ausente/correcto/ausente. JSONB coincide con respuesta. |
| C15 | Victoria al primero y al sexto; POST solución null, GET ganador conserva solución. |
| C16 | Seis PERRO: derrota, solución CASAS, séptimo rechazado y seis filas persistidas. |
| C17 | GET activo sin solución y almacenamiento con solución; orden de múltiples intentos comprobado en GET final. |
| C18 | GET final ganador/perdedor; estados desconocido/NULL/vacío ocultan solución y rechazan intento. |
| C19 | Stats ausentes: exactamente cinco ceros, sin ID/promedio/campos adicionales. |
| C20 | Victorias de uno y dos intentos, luego derrota: promedio numérico 1.5, rachas/contadores y porcentaje 67 correctos. PostgreSQL devuelve Decimal. |
| C21 | Trece filas stats con empates: máximo diez filas, cuatro campos y orden descendente, sin prometer desempate. |
| C22 | Error SQL real y caída real: 500 sanitizado; rollback en los casos definidos, sin replay. |

Son escenarios relevantes del contrato; no una comparación byte a byte con respuestas históricas Supabase nunca observadas. UUID, JSONB, numeric y timestamps se contrastan mediante filas nativas y JSON real FastAPI; timestamps sin zona mantienen isoformat sin inventar Z.

## Once métodos reales y propiedades adicionales

- Lifecycle/persisted_types: apertura perezosa, adquisición/devolución, rol app sin superusuario, parámetros con comillas/SQL como usuario textual sin ejecución, UUID/JSONB/timestamp reales, lectura SQL independiente coherente.
- Empty_dictionary/framework_validation: error de diccionario y validación de framework.
- Rejections/UUID/states: precedencia y ausencia de escrituras rechazadas.
- Repeated_letters/enye/win: reglas/normalización, secreto y orden.
- Sixth_loss/sixth_win: límites y finalización.
- Stats_numeric/ranking: média fraccionaria y proyección/orden/límite.
- SQL_failure_rolls_back: tres subcasos con división por cero ejecutada por PG: después de INSERT intento, después de inicializar stats y después de actualizar stats existentes. Compara partida/stats previos y ausencia de intento, seguido de request válido de recuperación.
- Concurrent_attempts: dos requests, dos PID PG, segundo esperando Lock, números 1/2 y contador coherente.
- Concurrent_last_attempt/wins: dos subcasos, sexta oportunidad y dos ganadores; una respuesta 200 y otra 400, única finalización/stats.
- Concurrent_first_statistics: dos partidas del mismo usuario, primera creación de stats; una fila, dos victorias y media 1.5, sin UniqueViolation.
- Concurrent_existing_statistics: victoria y derrota simultáneas con fila existente; tres jugadas/dos victorias/media 1.5/racha actual 0/máxima 2.

Las barreras/eventos solo pausan requests de tests después de adquirir un lock real; no sustituyen el motor ni sus resultados. La espera se verifica en pg_stat_activity antes de liberar la primera conexión. Timeouts: 2 s de observación, 3–4 s de coordinación, 8–10 s de finalización; no hay benchmark ni carga masiva. No se observaron deadlocks y el contador de la DB temporal quedó en cero.

En la comprobación adicional se detuvo el contenedor real después de completar/limpiar la suite; POST nueva dio 500 sanitizado y GET health siguió en 200. No es una prueba de pérdida de conexión exactamente al confirmar COMMIT. El pool se cerró al abandonar lifespan.

## Limpieza y controles finales

TRUNCATE de las cuatro tablas se ejecuta únicamente en la base generada por este runner, entre tests y al terminar. Antes del outage se comprobó cero filas en todas. Tras cada ejecución, docker rm del ID creado y docker network rm de su red finalizaron correctamente; docker inspect/network inspect devolvieron ausencia. Una consulta final por etiqueta wordle.pg04.run no devolvió contenedores ni redes.

La etiqueta local de imagen de build fue eliminada sin force, tras inspeccionar linux/amd64 y usuario 10001:10001. No se limpiaron cachés/capas compartidas ni recursos ajenos. No hubo volúmenes persistentes que eliminar.

Controles estáticos finales: sintaxis de ambos archivos nuevos, hashes de todos los archivos previos, patrones de secretos solo sobre archivos nuevos y git diff --check. No se abren .env/credenciales, se modifican documentos históricos o se hacen commits/push. Los resultados de esos controles se recogen en el cierre del informe.

Cierre verificado: todos los archivos previos permanecen idénticos byte a byte; exactamente dos archivos Python de integración y tres documentos nuevos. Sintaxis, whitespace y patrones acotados de secretos en esos cinco archivos: correctos, sin hallazgos. git diff --check correcto. Índice vacío; rama codex/devops-04a1-hardening, sin commit/push. Docker no devuelve recursos por la etiqueta PG-04 y la inspección de la etiqueta temporal de imagen devuelve No such image, ausencia esperada tras la limpieza.
