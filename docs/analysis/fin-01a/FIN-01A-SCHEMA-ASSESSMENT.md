# FIN-01A - Inventario del esquema Supabase

Fecha: 08/11/2026. Diagnóstico exclusivamente documental. El usuario aprueba TFG-PLAN-001 como hoja de ruta de 22 tareas y autoriza solo FIN-01A. No se modifica el estado de FIN-01 ni el backlog oficial.

Corte local: rama codex/devops-04a1-hardening; HEAD a666b17680781a24889ea774778019995d3fca45. Los cuatro documentos TFG-PLAN-001 ya estaban sin versionar y se preservan. No se hizo fetch ni se afirma que este corte sea el main remoto más reciente.

## 1. Resultado y límite del diagnóstico

Se identifican cuatro nombres de recursos accedidos mediante supabase.table(): palabras, partidas, intentos y estadisticas. Son contratos del consumidor, no una prueba de existencia, esquema PostgreSQL, tabla física frente a vista, ni estructura completa en Supabase. No hay evidencia suficiente del esquema real para escribir una migración compatible.

No se encontraron SQL, migraciones, definiciones de esquema, configuración Supabase local, modelos ORM ni un historial de migraciones en el árbol de código/documentación inspeccionado. Se excluyeron secretos, .env, kubeconfigs, estado Terraform, caches y dependencias. No se inspeccionaron archivos ignorados sensibles ni se puede afirmar qué contienen.

No se contactó ningún proyecto Supabase, no se consultaron claves ni credenciales, no se ejecutaron tests, SQL, migraciones o servicios, no se instalaron dependencias y no se usó Azure. Se leyeron únicamente archivos locales y documentación pública oficial sobre métodos de exportación; consultar esa documentación no es conectarse a la base del proyecto.

**Gate:** detener FIN-01A en este informe. FIN-01B requiere DDL real sanitizado, metadatos de seguridad/dependencias y autorización independiente para la implementación y las pruebas locales.

## 2. Evidencias concretas

Las líneas corresponden al corte indicado y se comprobaron mediante lectura/AST, sin importar ni ejecutar la aplicación.

| Archivo | Evidencia | Lo que no acredita |
|---|---|---|
| [database.py](../../../backend/app/database.py), líneas 6-18 | get_supabase lazy, carga dotenv, nombres SUPABASE_URL/SUPABASE_KEY y create_client; no selección explícita de schema ni identidad de usuario por petición | Valores/tipo de clave, rol efectivo, schema expuesto/configurado, RLS o permisos reales |
| [game.py](../../../backend/app/routers/game.py), líneas 13-16 | IntentoPeticion: partida_id, palabra y usuario_id como str | Tipos UUID/text/integer de SQL ni modelo de persistencia |
| game.py, líneas 38-53 | Lee palabras.palabra e inserta partida sin proporcionar id; devuelve data[0][id] | Qué genera el ID, privilegios de retorno de fila y defaults del resto de columnas |
| game.py, líneas 57-112 | Valida palabra, consulta partida por id, compara usuario_id, inserta intento y actualiza partida/estadísticas | Autenticación, transacción entre escrituras o restricciones SQL |
| game.py, líneas 117-128 | SELECT * de partida e intentos; orden por numero; oculta palabra_secreta fuera de estados finales conocidos | Ausencia de otras columnas sensibles o alcance de autorización |
| game.py, líneas 131-157 | Lectura/alta/actualización de estadísticas por usuario_id; promedio ponderado de victorias | Unicidad de fila, precisión/escala SQL, triggers o cálculo real concurrente |
| [stats.py](../../../backend/app/routers/stats.py), líneas 8-26 y 30-37 | SELECT * por usuario_id y ranking ordenado por partidas_ganadas, límite 10; porcentaje calculado en Python | Esquema físico de estadisticas ni autorización de consultas |
| [test_backend.py](../../../backend/tests/test_backend.py), líneas 57-126 | MemoryDB/MemoryQuery; cuatro recursos, ID ficticio y proyecciones/insert/update | PostgreSQL, secuencias, FK, CHECK, casts, permisos, triggers, fallos PostgREST o RLS |
| [test_stabilization.py](../../../backend/tests/test_stabilization.py), líneas 13-68 | Casos de alfabeto, Ñ, estado desconocido, ausencia de partida y promedio | Validación real del DDL; usa la misma fixture en memoria |
| [App.jsx](../../../frontend/src/App.jsx), líneas 6-13; [api.js](../../../frontend/src/api.js), líneas 21-28 | UUID local de usuario y envío de identificadores/palabra a FastAPI; sin token de usuario en estos contratos | Registro de usuario en Supabase Auth ni pertenencia a auth.users |
| [requirements.txt](../../../backend/requirements.txt) y requirements.lock | Cliente supabase 2.4.6, Pydantic 2.7.1 y dependencias fijadas | Compatibilidad comprobada de ese SDK con categorías de clave/API actuales del proyecto |
| [README](../../../README.md), [SECURITY-NOTES](../../../backend/SECURITY-NOTES.md) y [plan aprobado](../tfg-plan-001/TFG-COMPLETION-PLAN.md) | Integración real y esquema/RLS pendientes; riesgos conocidos; FIN-01/02/03 definidos | Esos pendientes no se cierran mediante documentación o aprobación del plan |

El README general aún contiene referencias históricas a .single() y promedio pendientes que ya no describen exactamente game.py actual; para los contratos prevalece el código inspeccionado. No se modifica el README en FIN-01A.

## 3. Acceso y operaciones por recurso

El cliente usa la API de Supabase/PostgREST; no ejecuta SQL directamente ni mantiene una conexión PostgreSQL desde el código de aplicación. No hay llamadas .schema() o RPC en los routers. Confirmar el schema efectivo y su exposición por Data API: no dar public por comprobado por ser el valor habitual del servicio.

| Recurso | Lecturas | Escrituras | Expectativa lógica, no restricción SQL confirmada |
|---|---|---|---|
| palabras | SELECT palabra de todo el recurso y filtro igualdad palabra=intento normalizado | Ninguna desde el backend actual | Al menos una palabra elegible; coincidencia de diccionario tras normalización |
| partidas | SELECT * WHERE id=... LIMIT 1 | INSERT usuario_id/palabra_secreta/intentos_usados/estado; UPDATE intentos_usados/estado WHERE id | Identificador resoluble y partida coherente; si id estuviera duplicado, la lectura y actualización tendrían efectos distintos |
| intentos | SELECT * WHERE partida_id=... ORDER BY numero | INSERT partida_id/usuario_id/numero/palabra/resultado | Intentos vinculados lógicamente a una partida y ordenables; no se observa UPDATE/DELETE |
| estadisticas | SELECT * WHERE usuario_id; ranking con cuatro columnas y orden desc/limit | INSERT primera estadística; UPDATE contadores, rachas y promedio WHERE usuario_id | Una fila lógica por usuario, asumida por el código pero no confirmada como UNIQUE |

No hay DELETE, upsert, RPC, join o operación sobre Storage/Auth en el código inspeccionado. Que no haya DELETE en la aplicación no determina si el rol de DB lo tiene concedido.

## 4. Columnas y valores que el backend espera

La siguiente tabla expresa forma y semántica a nivel de aplicación. No propone tipos SQL ni declara NOT NULL, PK, FK, DEFAULT, ENUM, CHECK o índices existentes.

| Recurso.columna | Uso/forma de datos esperada | Información SQL pendiente |
|---|---|---|
| palabras.palabra | Cadena; la solución se convierte a mayúsculas y los intentos se consultan ya normalizados | Tipo/longitud/collation, unicidad, nulabilidad, normalización y restricciones del diccionario |
| partidas.id | Devuelto por INSERT sin que el cliente lo envíe; reutilizado como partida_id y filtro | Tipo, generación por default/identity/trigger, clave y serialización JSON |
| partidas.usuario_id | Enviado por cliente como cadena, devuelto comparable al usuario_id de intento | Tipo, relación con usuario real/Auth, FK, política y permiso de inserción |
| partidas.palabra_secreta | Cadena usada por evaluador; para juego correcto debe corresponder a cinco posiciones válidas | Tipo/tamaño, restricción o relación real con palabras; validación de soluciones almacenadas |
| partidas.intentos_usados | Valor inicial 0; operaciones suma/comparación hasta seis | Tipo, rango, null/default y mecanismo de consistencia con intentos |
| partidas.estado | Valores que escribe el código: en_curso, ganada, perdida | Texto/ENUM/CHECK/default y otros estados reales; no se crea un ENUM por inferencia |
| intentos.partida_id | Cadena de petición, usada como vínculo lógico y filtro | Tipo compatible con partidas.id; existencia/acciones de una FK |
| intentos.usuario_id | Cadena declarada por cliente y comprobada contra partida antes de escribir | Tipo, FK y consistencia con propietario; no equivale a auth.uid() |
| intentos.numero | Entero lógico 1..6 calculado en aplicación | Tipo, CHECK, unicidad por partida y generación/concurrencia |
| intentos.palabra | Cadena de cinco letras A-Z/Ñ, normalizada con strip y upper | Tipo, longitud, collation, constraints o relación con diccionario |
| intentos.resultado | Lista JSON serializable de cinco objetos {letra, estado}; estado correcto/presente/ausente | Tipo y formato de almacenamiento: no se puede afirmar jsonb frente a json u otra adaptación |
| estadisticas.usuario_id | Clave lógica de lectura/actualización de estadísticas | PK/UNIQUE/FK/índice/tipo y relación de identidad |
| estadisticas.partidas_jugadas | Contador numérico incrementado por partida finalizada | Tipo, null/default, rango y triggers |
| estadisticas.partidas_ganadas | Contador numérico incrementado al ganar | Tipo, constraints respecto a partidas_jugadas y forma de actualización |
| estadisticas.racha_actual | Contador incrementado al ganar y puesto a 0 al perder | Tipo, null/default, rango y origen de verdad |
| estadisticas.racha_maxima | Número usado en max con racha_actual | Tipo, constraint de coherencia y triggers |
| estadisticas.intentos_promedio | Número con operaciones ponderadas; puede ser fraccionario; derrota conserva promedio | Tipo/escala/serialización que no trunque ni produzca cadena incompatible; compatibilidad histórica |

porcentaje_victorias se calcula en Python, no es una columna exigida por el acceso SQL. Un id en intentos/estadisticas solo aparece por comportamiento genérico de MemoryQuery: el backend no lo exige en sus INSERT, por lo que no se añade a un DDL por ese motivo. Tampoco se exigen created_at, updated_at, tablas usuarios/profiles ni timestamps sin evidencia real.

El modelo Pydantic de petición no declara UUID, límites SQL ni relaciones. No existen modelos ORM de las cuatro tablas. Los identificadores de prueba game-1/owner son valores sintéticos, no evidencia de tipo text ni de validez en el esquema remoto.

## 5. Relaciones y restricciones: observadas frente a desconocidas

Relaciones de negocio observadas:

- intentos.partida_id apunta lógicamente al identificador de la partida consultada.
- partidas.usuario_id, intentos.usuario_id y estadisticas.usuario_id comparten identidad lógica.
- La solución procede de palabras, pero el código guarda el texto; no demuestra FK de palabra_secreta a palabras.palabra.

No se puede confirmar ninguna FK, PK, UNIQUE, política ON DELETE/ON UPDATE, índice, secuencia, columna generada, trigger, función, vista, extensión o relación con auth.users. Tampoco se puede afirmar que todos los objetos sean tablas físicas: la API puede exponer vistas, con comportamiento de permisos distinto.

Reglas del juego que se validan en Python (cinco letras, alfabeto, seis intentos, estados) no prueban CHECKs de DB. A la inversa, añadir restricciones razonables sin contrastar el DDL puede romper datos existentes o la API. Una restricción UNIQUE de intentos por partida/numero podría detectar una carrera, pero no hace atómica la actualización de partida y estadísticas ni define cómo responder a errores; requiere revisión FIN-03.

## 6. Información real necesaria del propietario

Solicitar un paquete de metadatos sanitizado, no valores de conexión ni datos de usuarios:

1. **DDL completo de los objetos de aplicación** para palabras, partidas, intentos y estadisticas, con schema y naturaleza tabla/vista: columnas en orden, tipos exactos/UDT, longitud/precisión, nullability, defaults/generación, PK/UNIQUE/CHECK/FK y acciones, índices y secuencias. Incluir columnas adicionales aunque el backend no las nombre.
2. **Dependencias:** ENUM/dominios, extensiones y versiones necesarias, funciones y triggers con definición y SECURITY DEFINER/search_path, vistas/materializadas y objetos referenciados fuera del schema. Si hay relación con auth.users u otro objeto gestionado, aportar solo definición de la relación y contrato requerido, no registros de Auth.
3. **Seguridad efectiva:** RLS habilitada/forzada por objeto, definiciones de políticas (operación, roles, USING y WITH CHECK), GRANT/REVOKE y default privileges, roles funcionales y atributos relevantes sin passwords/hashes; schema expuesto por Data API y acceso a secuencias/funciones cuando proceda.
4. **Identidad y credencial:** explicar qué entidad representa usuario_id, si requiere usuario preexistente y cómo se crea; indicar solo la categoría de clave usada por backend y rol efectivo (anon/publishable, autenticada o privilegiada, según configuración), si se reenvía JWT de usuario y si el esquema está integrado con Auth. No enviar la clave ni JWT.
5. **Versiones/procedencia:** versión PostgreSQL del proyecto, versión del cliente/CLI usada para exportar, fecha y origen identificado mediante alias no sensible, schemas incluidos/excluidos, estado del historial de migraciones y cambios manuales conocidos. Confirmar si el esquema exportado corresponde al backend de este commit o a otra versión.
6. **Confirmación funcional sin datos reales:** valores permitidos de estado, formato real de resultado, diccionario normalizado, expectativas de promedio y existencia de lógica automática de estadísticas/creación de usuario. Si hace falta, muestras fabricadas expresamente por el propietario, nunca filas exportadas de producción.

No aportar .env, URL privada, contraseña DB, connection string, API keys, JWT, backups con datos, auth.users/auth.identities ni roles con hash. No hace falta compartir credenciales para FIN-01B si el propietario suministra un DDL completo y revisado.

## 7. Métodos para obtener el DDL real, sin ejecutarlos aquí

### Recomendado: exportación por el propietario con revisión previa

El propietario autorizado realiza fuera de este repositorio una exportación de solo esquema de los schemas de aplicación y sus dependencias, usando herramientas ya disponibles o instaladas bajo autorización propia. Mantiene el original en ubicación privada, revisa sanitización y entrega solo el resultado aprobado con el inventario de cobertura/exclusiones.

Alternativas:

| Método | Ventaja | Precaución/cobertura |
|---|---|---|
| Supabase CLI db dump | Flujo oficial orientado a Supabase; por defecto excluye datos/roles personalizados y varios schemas gestionados | Excluye auth/storage y schemas de extensiones: documentar dependencias ausentes; confirmar versión/opciones. No usar data-only/role-only para este diagnóstico ni publicar dry-run si revela parámetros. |
| pg_dump schema-only | DDL de PostgreSQL con alcance explícito y artefacto revisable | Versión compatible; cubrir dependencias fuera del schema. no-owner elimina propietarios, no credenciales que puedan estar incrustadas en funciones/FDW. No usar no-acl si se necesitan GRANT/REVOKE, o entregarlos sanitizados por separado. |
| Exportación de metadatos desde Dashboard/SQL Editor por propietario | Útil sin instalar herramientas adicionales | Tablas de columnas o capturas no bastan: recoger también constraints, índices, políticas, grants, triggers/funciones y dependencias. No se asume que el panel exporte todo con un clic. |
| Migraciones anteriores aportadas por propietario | Preserva intención e historial | Contrastar con estado actual y drift; no asumir que historial equivale al esquema vivo. db pull puede introducir archivos y flujos auxiliares; no ejecutarlo en FIN-01A. |

Sanitizar ANTES de compartir: funciones/triggers/comments, foreign servers/user mappings, comandos programados/webhooks, URLs y roles pueden contener secretos aunque no haya datos. No generar un dump global de roles ni de Auth para obtener un DDL de aplicación. Si se elimina contenido sensible de una función, marcar la definición como incompleta y aportar contrato/descripción: un placeholder no es una migración ejecutable compatible. No versionar el dump bruto ni ejecutar automáticamente SQL recibido como si fuera confiable.

El DDL de solo esquema no garantiza trasladar fielmente privilegios por defecto del proyecto destino; FIN-03 debe verificar permisos efectivos tras reconstruir. No suprimir políticas o grants para conseguir que un test pase. El acceso de la herramienta de exportación se gestiona de forma privada y nunca mediante argumentos con contraseña compartidos en el informe.

No se ejecutó ninguna de estas alternativas. Acceso directo del agente al proyecto, aun de solo lectura, requiere autorización expresa y un alcance concreto; no se solicita entregar credenciales por chat.

## 8. Riesgos de compatibilidad concretos

| Riesgo | Evidencia/efecto | Verificación requerida antes de migrar |
|---|---|---|
| Generación/JSON de id | INSERT partida no envía id; JSON debe permitir uso posterior como partida_id str. Un id numérico en respuesta podría volver como número y causar validación 422 al enviar intento. | Tipo real, default/trigger y serialización real con SDK/API; no corregir con columna inventada. |
| Usuario inexistente/FK | UI genera UUID local, no registra usuario Auth; una FK a auth.users podría rechazar crear partida. | Contrato de identidad y provisión sintética autorizado. |
| Palabras no normalizadas | Búsqueda por igualdad usa mayúsculas; selección de solución no filtra longitud/alfabeto y solo hace upper. | Tipos/collation/datos permitidos y reglas actuales; no inventar CHECK/citext. |
| resultado incompatible | API escribe lista de objetos, no JSON convertido a cadena manualmente. | Tipo/estructura y adaptación PostgREST; tests SQL y API. |
| Promedio truncado o no numérico | El cálculo puede producir fracciones y multiplica/suma valores devueltos. | Tipo/precisión/JSON y datos históricos; no asumir integer ni numeric concreto. |
| Filas duplicadas | Partida lee LIMIT 1 pero actualiza por id; stats lee primera fila y actualiza todas por usuario_id. | Claves/UNIQUE reales; no crear restricciones sin auditar su compatibilidad. |
| Triggers y doble contabilización | Backend incrementa intentos/contadores por separado; triggers reales podrían hacer lo mismo. | Definiciones y ejecución local; distinguir quién es fuente de verdad. |
| Escritura parcial y carreras | Insert intento, update partida y update stats no son transacción única. | FIN-03 decide restricciones/transacción y manejo de error; baseline no promete resolverlo. |
| RLS o grants insuficientes | Lecturas vacías pueden parecer 404; INSERT puede requerir retorno de fila y SELECT permitido; actualización filtrada por RLS puede no modificar nada. | Matriz de permisos efectiva y pruebas de representación/filas afectadas, secuencias y políticas. |
| Clave privilegiada/autenticación | Backend usa una clave global sin token verificado por usuario; usuario_id cliente solo comprueba coherencia. | Categoría/rol sin valor de clave; no asumir auth.uid disponible o que RLS proteja si rol la elude. |
| Exposición de columnas adicionales | GET y stats devuelven SELECT *; quitar palabra_secreta no filtra cualquier otra columna sensible añadida al esquema. | DDL completo y revisión de forma pública antes de exponer datos; no modificar API aquí. |
| PostgreSQL local distinto de Supabase | Roles anon/authenticated, auth.uid(), extensiones o PostgREST pueden faltar en PostgreSQL básico. | Dos niveles de validación; no declarar integración API por restaurar tablas con superusuario. |

## 9. Dependencias FIN-02 y FIN-03

**FIN-02:** depende de tipos/defaults/claves, diccionario permitido, FK de usuario y partida, orden de inserción y serialización de resultado. Solo después se diseñan semillas sintéticas idempotentes y un ciclo de backup/restore. No copiar usuarios reales ni asumir que un UUID aleatorio cumple relaciones. La idempotencia de semillas no implica que cada migración DDL deba poder aplicarse dos veces.

**FIN-03:** debe decidir identidad verificable y autorización, rol efectivo de backend, RLS/grants y concurrencia. No se puede deducir una política USING auth.uid()=usuario_id de una cadena enviada por cliente. Las claves privilegiadas pueden omitir RLS; la categoría no se infiere del nombre SUPABASE_KEY ni se cambia por otra sin probar compatibilidad del SDK 2.4.6. No proponer anon con acceso abierto como atajo ni implementar autenticación nueva en esta tarea.

La primera baseline debe reflejar la estructura confirmada; mejoras de seguridad/coherencia se revisan como cambios explícitos separados. Si la baseline resultara insegura, no usarla para exposición pública: una copia fiel no es una certificación de seguridad.

## 10. Propuesta de migraciones e inicialización local

Solo estructura propuesta, no directorios SQL creados ni comandos disponibles:

```text
supabase/
  config.toml                         # configuración local revisada, sin vincular proyecto remoto
  migrations/
    <timestamp>_baseline_confirmed.sql # DDL real revisado, con procedencia y alcance
    <timestamp>_<approved_change>.sql  # solo cambios posteriores aprobados
  seed.sql                            # FIN-02: únicamente datos sintéticos, separado del DDL
  tests/
    schema_contracts.sql              # futuros checks de catálogo y permisos
    permissions_contracts.sql         # FIN-03: roles/RLS/casos negativos
  README.md                           # versiones, precondiciones, orden y recuperación
```

Elegir una sola fuente de migraciones versionadas. Preferencia de diseño: convención Supabase por el stack existente; confirmar CLI/versiones antes de adoptarla, sin instalar nada ahora. No copiar schemas gestionados completos al baseline ni sustituir auth.uid por stubs presentados como seguridad real. Documentar roles/extensiones/dependencias que debe proporcionar el runtime local.

Secuencia futura propuesta:

1. Recibir paquete sanitizado, verificar cobertura, revisar SQL como código y acordar decisiones abiertas.
2. Comparar cada contrato de esta evaluación con los objetos reales; registrar diferencias y bloquear cualquier cambio incompatible no aprobado.
3. Preparar baseline versionada y documentada. No ejecutar contra producción ni rebaselinar el proyecto real automáticamente.
4. Nivel 1: aplicar en PostgreSQL local desechable vacío de versión compatible; comprobar catálogo, tipos/defaults/constraints/dependencias y permisos usando roles apropiados. Si requiere objetos Supabase, documentarlos y suministrarlos mediante stack local compatible; PostgreSQL básico por sí solo no basta.
5. Nivel 2: verificar con Supabase local/PostgREST y el backend actual, usando configuración y claves exclusivamente locales, nunca credenciales del proyecto remoto. El cliente actual no se transforma en psycopg ni se cambia arquitectura para hacer pasar las pruebas.
6. Crear y reconstruir desde otra base vacía para reproducibilidad; luego FIN-02 añade semillas y restauración. Pruebas contra DB real local no reemplazan la suite MemoryDB, que se conserva.

No aplicar la misma migración dos veces sin control como criterio de idempotencia: el historial debe impedir reaplicación. Tampoco usar reset/db push ligado a remoto. El runtime/servicio/instalaciones locales, generación de SQL y su ejecución requieren autorización FIN-01B.

## 11. Criterios de aceptación propuestos de FIN-01B

FIN-01B es una subtarea propuesta dentro de FIN-01; no cambia sus dependencias ni declara FIN-01 completado.

- Paquete del propietario completo, sanitizado y con procedencia/fecha/versiones/alcance, revisado sin secretos ni datos reales.
- Matriz contrato -> objeto real -> verificación, incluidas columnas adicionales, generación ID, relaciones de usuario, políticas/grants y dependencias de Auth/extensiones.
- Diferencias incompatibles o inseguras documentadas y aprobadas antes de cambiar esquema/API; ninguna PK/FK/ENUM/columna/política inventada.
- Baseline versionada con orden correcto y roles/extensiones requeridos explícitos; no duplicar ni exportar íntegramente schemas gestionados.
- Aplicación local en una base vacía y reconstrucción limpia correctas, con logs sanitizados y comparación de catálogo. No se exige repetición ciega del mismo SQL.
- Smoke de contratos por API local: crear partida devuelve ID reutilizable, intento válido e inválido, repetidas, seis intentos, finalización y estadísticas; GET activo no revela solución. Sin conexión remota.
- Evidencia de permisos efectivos diferenciada por rol; no presentar una prueba como superusuario o con clave que elude RLS como autorización por usuario. Decisiones de seguridad FIN-03 permanecen identificadas.
- Alcance FIN-02 preservado: semillas completas y backup/restore de datos se desarrollan después, sin declarar esos hitos aprobados por migrar el esquema.
- Solo archivos autorizados modificados; no aplicación/Azure/producción ni nuevos accesos externos. Resultados registrados, sin secretos y con commit de referencia cuando esté autorizado.

## 12. Autorizaciones adicionales y siguiente paso

| Acción | Autorización requerida |
|---|---|
| Propietario aporta DDL/metadatos ya sanitizados | Confirmar que puede compartirlos; no requiere compartir credenciales. Es la vía recomendada. |
| Agente consulta proyecto real/catálogos/Data API | Autorización expresa separada, proyecto/alias y alcance de solo lectura; no autorizada actualmente. |
| Instalar CLI/cliente DB o arrancar PostgreSQL/Supabase local | Autorizar herramientas y entorno desechable en FIN-01B; no ejecutado. |
| Crear SQL/migraciones, aplicar a base local o generar semillas | Aprobar implementación de FIN-01B; FIN-02 para semillas completas. No autorizado por FIN-01A. |
| Cambiar RLS, grants, esquema remoto, credenciales o autenticación | Autorización explícita independiente y revisión FIN-03; no implícita por aprobación del plan. |
| Commit/push, cambios de backlog o estado de FIN-01 | No autorizados en esta tarea; permanecen intactos. |

**Información que debe aportar ahora el propietario:** los seis apartados de la sección 6, preferentemente en un DDL de solo esquema sanitizado más un inventario breve de identidad, permisos, exposición API y versiones. Si algún objeto no se puede compartir, indicar cuál, su contrato y por qué; FIN-01B quedará bloqueada en esa dependencia, sin rellenarla con suposiciones. No enviar claves, contraseñas, URL privada, JWT ni dumps con datos.

## 13. Referencias públicas consultadas

- [Supabase CLI: db dump](https://supabase.com/docs/reference/cli/supabase-db-dump): exportación, exclusiones y flags; su lectura no autoriza ejecución.
- [PostgreSQL: pg_dump](https://www.postgresql.org/docs/current/app-pgdump.html): schema-only, selección de schemas, propietarios y privilegios.
- [Supabase: RLS](https://supabase.com/docs/guides/database/postgres/row-level-security): políticas y roles que pueden eludirlas.
- [Supabase: API keys](https://supabase.com/docs/guides/getting-started/api-keys): distinguir categoría de clave de identidad de usuario; no se identificó la clave del proyecto.

No se usaron estas referencias para deducir el DDL real. Son alternativas de obtención/validación; la fuente de verdad del esquema sigue siendo la exportación autorizada y revisada del propietario.
