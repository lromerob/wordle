# FIN-01C - Impacto arquitectónico

Fecha: 08/11/2026. Evaluación, no cambio autorizado. Evidencia del código en el [inventario](FIN-01C-DEPENDENCY-INVENTORY.md). Se mantienen React/Nginx, FastAPI, PostgreSQL 16, Docker, Kustomize, AKS, Terraform y Actions/GHCR. Se evalúa retirar el servicio y SDK Supabase, no sustituirlos por otro servicio administrado.

## 1. Arquitectura actual y propuesta

Actual: navegador -> Nginx /api -> FastAPI -> SDK Supabase/HTTP Data API -> PostgreSQL externo. En tests, MemoryDB reemplaza el cliente. El estado de Supabase queda fuera del ciclo de vida AKS.

Propuesta: navegador -> Nginx /api -> FastAPI -> psycopg/libpq -> Service PostgreSQL interno -> una instancia PostgreSQL 16 con volumen. El frontal y la API pública conservan contratos. En AKS, Blue y Green comparten ese Service/DB/PVC; no hay dos bases por color.

La nueva conexión directa exige cambiar acceso a datos; no basta con apuntar SUPABASE_URL al puerto 5432. Se deja de depender de PostgREST, no se añade un PostgREST propio como puente. La validación SQL FIN-01B demuestra tablas y operaciones análogas, no serialización del driver ni comportamiento HTTP de la aplicación.

## 2. Compatibilidad funcional

| Función | Actual | Equivalente directo y criterio |
|---|---|---|
| Selección de palabra | Recupera todas, random.choice en Python, upper | Mantener flujo y diccionario aprobado; no introducir ORDER BY random ni reglas nuevas por optimización ajena. |
| Nueva partida | INSERT cuatro campos; ID devuelto por API | INSERT parametrizado RETURNING con los mismos campos/defaults y UUID reutilizable como cadena HTTP. |
| Intento | Lee partida/diccionario, valida, evalúa dos pasadas y escribe | Mantener evaluador y checks. Una transacción engloba escrituras del intento y finalización; bloqueo por partida evita aceptar dos veces el mismo número. |
| Evaluación | Función Python pura | Sin cambios; conservar pruebas de repetidas y estados correcto/presente/ausente. |
| Finalización | Actualiza estado y estadísticas en llamadas separadas | Misma conexión/transacción y commit antes de confirmar éxito HTTP; datos de ambos colores coherentes. |
| GET de partida | Diccionario de partida e intentos ordenados; oculta solución activa | Filas dict y normalización JSON equivalente; no añadir campos internos. |
| Estadísticas/ranking | Contadores, promedio y rachas; porcentaje Python | Mismos cálculos y ceros si no hay fila. UNIQUE usuario_id ya existe; decidir upsert/actualización atómica para carreras entre partidas del mismo usuario. |
| Usuario | UUID local enviado como texto; no sesión Auth | Conservar esa identificación sin llamarla autenticación. No requiere migrar usuarios Supabase Auth: no hay FK informada a auth.users. |

No se identificó funcionalidad utilizada que dependa exclusivamente de Supabase. Se perdería disponibilidad de servicios del SDK no usados (Auth/Storage/Realtime), no una función Wordle comprobada. Confirmar con el propietario que no hay consumidores externos fuera del repositorio antes de retirar el proyecto existente. Transferir datos históricos no está autorizado ni incluido en la estimación: elegir entre demo sintética nueva o migración de datos independiente.

## 3. Alternativas de acceso

| Opción | Complejidad y FastAPI | Transacciones/pruebas/mantenimiento | Evaluación |
|---|---|---|---|
| psycopg 3 con SQL explícito | Driver PostgreSQL; admite async. Consultas pequeñas para cuatro tablas, sin ORM | Transacciones y adaptación nativas; integración real PG sencilla; SQL visible y poco código de mapeo | Recomendada. Pool async pequeño y acotado si se incluye el extra necesario. |
| SQLAlchemy Core + driver | Añade motor/expresiones/metadata sobre un driver; requiere configurar su modo async | Buen soporte transaccional y pooling; más conceptos/configuración y dependencia adicional | Válida, pero aporta menos en este esquema pequeño con DDL ya preparado. |
| SQLAlchemy ORM + driver | Modelos, sesiones y ciclo de vida adicional | Útil con relaciones/objetos complejos; habría que contrastar modelos con DDL, sin eliminar migraciones | No justificado por el alcance actual. Alembic tampoco es requisito automático por usar SQLAlchemy. |

No se propone una cuarta tecnología ni un framework de repositorios genérico. El módulo de acceso puede exponer pocas operaciones del juego para permitir dobles de prueba; no reimplementar una API fluent supabase.table(). Elegir y fijar versiones estables de psycopg/distribución binaria y psycopg_pool durante la implementación, comprobando Python 3.12/Linux x86_64 y el build con hashes. La documentación consultada puede mostrar versiones de desarrollo: no se elige una versión dev por ese motivo.

Conexiones: pool por proceso, abierto/cerrado en lifespan, tamaño y timeout explícitos; préstamo y devolución seguros, sin compartir una transacción global entre requests. En Windows se debe comprobar compatibilidad del bucle asyncio elegido antes de validar dev local. No bloquear el event loop con operaciones síncronas dentro de async def ni crear un pool por petición. Dimensionar max_connections con suma de pools Blue+Green+workers y reservas para migración/administración; no fijar números de capacidad sin medir.

## 4. Contratos de datos, errores y transacciones

- Parámetros SQL separados de cadenas; nunca interpolar usuario_id/palabra/ID en SQL. RETURNING sustituye response.data. dict_row o mapeo equivalente evita acoplar routers a tuplas.
- UUID se recibe como cadena en HTTP, se adapta explícitamente al driver y se serializa con el mismo formato de salida; no comparar UUID Python con str sin normalizar.
- resultado se adapta como JSONB, no como lista PostgreSQL ni JSON doblemente codificado. Leer devuelve una estructura de lista/dict compatible.
- numeric puede volver como Decimal; elegir conversión JSON coherente con el contrato y comprobar fracciones (1,5) y porcentaje. No convertir a texto ni truncar a integer por accidente. Timestamps vuelven datetime: comprobar su ISO y semántica sin zona; no añadir UTC ficticio.
- Mantener HTTP 400/403/404, campos resultado/estado/intentos_usados/palabra_secreta y la ocultación de solución. Que .fetchone() devuelva None no debe convertirse en un 500 accidental.
- UniqueViolation/ForeignKeyViolation, fallo de conexión, timeout y transacción abortada no son las mismas excepciones del SDK. Definir traducción limitada, rollback y mensajes genéricos sin DSN. Un UUID inválido enviado como str requiere decisión de compatibilidad: no prometer que el transporte REST anterior tenía un manejo uniforme.
- Registrar intento bajo transacción y bloqueo de fila de partida (o alternativa equivalente probada), con contadores actualizados en SQL. Un conflicto en estadísticas del mismo usuario entre partidas distintas requiere tratamiento por UNIQUE/upsert o bloqueo adecuado; no basta con el lock de una sola partida.
- El cambio transaccional mejora atomicidad de persistencia, no cambia las reglas del juego. Probar rollback por fallo después de insertar intento y antes de estadísticas; no aceptar resultados parcialmente escritos.
- No reintentar escrituras automáticamente tras pérdida de conexión si el commit es incierto. La UI existente usa GET para recuperar estado de un intento incierto; conservar ese comportamiento.
- Columnas nullable siguen siendo nullable. No endurecer esquema, añadir triggers ni sanear datos históricos silenciosamente. Su tratamiento se valida explícitamente y cualquier cambio adicional necesita revisión.

## 5. Docker Compose propuesto

Servicios: frontend, backend, postgres y operación de migración/seed one-shot. PostgreSQL 16 oficial por versión/digest confirmado, volumen nombrado exclusivo del proyecto en el path de datos de esa versión. Sin puerto DB publicado; backend accede por DNS de servicio y red interna. No usar network:none para integración: el aislamiento sin red de FIN-01B era apropiado para psql por exec, no para comunicación backend-DB.

Credenciales de DB externas/ignoradas o fichero secreto montado según diseño acordado; nunca imagen/build args/VITE_. No copiar trust sin red del test FIN-01B a un servicio en red. Separar usuario técnico de aplicación de propietario/migrador, con permisos operativos requeridos; no usar superusuario para acreditar acceso del backend. No se rediseña identidad de usuarios.

Orden: postgres healthy -> migración una vez con historial/versionado y lock -> carga de lista aprobada cuando corresponda -> backend -> frontend. pg_isready por sí solo no verifica tablas ni diccionario; los gates deben comprobar versión de esquema y datos mínimos. Cambiar POSTGRES_PASSWORD después de inicializar volumen no rota por sí solo la contraseña del rol existente.

No confiar únicamente en /docker-entrypoint-initdb.d: se ejecuta al inicializar un directorio de datos vacío y no actualiza volúmenes existentes. La baseline ya validada crea objetos una vez; una rutina de migración debe registrar su aplicación, serializar ejecuciones y fallar ante drift. La implementación del control/historial es decisión operativa posterior, no un cambio de las tablas Wordle en este análisis.

El SQL supabase/ está fuera del contexto backend y su .dockerignore. Elegir entrega explícita al migrador (archivo montado en local; artefacto/ConfigMap/job en Kubernetes), sin presumir que existe dentro de la imagen web. No ejecutar baseline en cada arranque de FastAPI ni por cada worker.

El diccionario sigue bloqueado por fuente aprobada. Reutilizar prepare_dictionary.py y separar fixture de test del seed de demo. Un restart mantiene datos si conserva volumen; down no debe implicar down -v. Respaldar antes de cualquier eliminación autorizada del volumen; volumen no es backup. Restaurar en otro volumen vacío es criterio de aceptación.

## 6. Kubernetes/AKS y persistencia

Recursos propuestos, todavía inexistentes:

- Una instancia PostgreSQL 16, preferiblemente StatefulSet de una réplica.
- Service interno estable para clientes; el StatefulSet puede necesitar además su Service headless gobernante. Sin NodePort/LoadBalancer/Ingress para PostgreSQL.
- Un PVC con StorageClass CSI explícita, capacidad, modo de acceso y política de conservación revisados. No confiar en que el default de AKS sea la opción más económica.
- Secret de credenciales y configuración no sensible de conexión. Backend Blue y Green referencian la misma base, Service y configuración.
- Job de migración único y separado del rollout de cada color, con gate de finalización; seed aprobado como paso controlado, no concurrente por pod.
- Requests/limits y probes apropiados para PG; tmp/data/socket y permisos compatibles con UID real de la imagen. No copiar a ciegas el securityContext/read-only del contenedor FastAPI al servidor DB.

### StatefulSet frente a Deployment

Un StatefulSet aporta identidad estable y asociación declarativa pod/PVC, y evita el rolling surge típico de un Deployment. Para una sola réplica no da replicación ni alta disponibilidad. Un Deployment con estrategia Recreate y PVC fijo también puede servir y es una alternativa aceptable; debe evitar dos procesos PostgreSQL usando el mismo directorio.

Se recomienda StatefulSet de una réplica por claridad de datos y mantenimiento, manteniendo el diseño pequeño. Un PVC ReadWriteOnce restringe nodos, no garantiza por sí mismo un único pod escritor; verificar soporte de ReadWriteOncePod si se elige y no presentarlo como obligatorio universal. Políticas de retención y comportamiento de borrado deben documentarse, no darse por implícitos.

Un reinicio/recreación del pod conserva datos si se reatacha el mismo PVC/disco. Un fallo de nodo o detach/attach puede interrumpir servicio; la ausencia de HA se acepta para el TFG, sin prometer continuidad de DB. Revisar zonas/afinidad/topología, tiempo de montaje y capacidad real antes de la defensa.

Retirar un StatefulSet puede conservar PVC; eliminar PVC puede borrar disco según reclaimPolicy. **Retain no garantiza sobrevivir a eliminar todo el clúster o el Resource Group de nodos.** Antes de destroy-demo exportar un backup consistente fuera de AKS y ensayar restore. Los backups y estado Terraform no deben depender del mismo PVC ni del RG temporal. Conservar un disco fuera del entorno añade coste y no sustituye una copia restaurable.

Mantener DB/PVC fuera de manifiestos de promoción y borrados de namespace de Blue/Green. Seleccionar límites de propiedad y orden de retirada; despliegue de app no debe borrar la persistencia. No hace falta Azure Database, ACR, replicación ni operador. Sí habrá coste de disco CSI, espacio de backup y memoria/CPU del nodo; reducir dependencia externa no garantiza coste total inferior a Supabase Free.

## 7. CI/CD y Blue-Green

Unit tests offline mantienen prohibición de sockets. Integración PG debe ir en entorno separado: servicio PostgreSQL 16 temporal con credenciales de test, migraciones, fixture y TestClient/HTTP contra backend directo. Red estrictamente de runner/servicio local; evitar colisiones de volumen de desarrollo. Publicar logs sanitizados y limpiar solo recursos creados, también al fallar. Si se usan servicios de Actions, su ciclo lo administra el runner; si contenedores manuales, limpieza explícita/finally.

kind necesita perfil PG real distinto del memory-test: PG Service/PVC/Job y backend driver, seed sintético, checks E2E y reinicio del pod para persistencia. No reutilizar volumen de host ni considerar el storage provisioner de kind evidencia de Azure Disk; aceptación CSI se hace después en AKS autorizado. Configurar diagnósticos de DB/migración/PVC sin volcar Secrets.

Los jobs actuales, incluido el publicador, son código existente; no se modifican en FIN-01C. Si se implementa la propuesta, el gate de integración debe preceder a publicación/promoción y conservar las validaciones actuales. CD, Blue-Green y rollback NO existen actualmente: el cambio debe alimentar FIN-08/09/17/18, no se puede afirmar que ya se mantienen funcionando.

### Primera transición frente al Blue-Green futuro

Blue actual con SDK apunta a Supabase y Green futuro con psycopg apuntaría a otra DB; no comparten mágicamente una instancia. No llamar a ese cambio inicial un Blue-Green de base compartida ni prometer rollback sin pérdida de datos entre dos almacenes.

Para demo sintética se recomienda una transición inicial controlada a una release base PG, con respaldo de lo que deba conservarse y aceptación explícita sobre datos históricos. A partir de ahí, dos releases PG de la aplicación comparten una DB estable. Evitar un puente PostgREST, sincronización dual o doble escritura por complejidad fuera del alcance. Si se necesita preservar datos históricos del servicio real, requiere un plan/permiso independiente; no se ha autorizado extracción.

Una vez ambas versiones usan PG: migrar esquema de forma compatible antes de promover, con patrón expandir -> desplegar/verificar -> conmutar -> retirar lo obsoleto después de la ventana de rollback. La baseline no se reaplica ni se duplica por color. Rollback de aplicación restaura tráfico/versión, NO deshace datos, migraciones destructivas o un borrado de PVC. Los dos pools/versiones deben soportar el esquema compartido y el presupuesto de conexiones.

## Fuentes primarias consultadas

- [Psycopg async](https://www.psycopg.org/psycopg3/docs/advanced/async.html), [pools](https://www.psycopg.org/psycopg3/docs/advanced/pool.html), [transacciones](https://www.psycopg.org/psycopg3/docs/basic/transactions.html) y [adaptación de tipos](https://www.psycopg.org/psycopg3/docs/basic/adapt.html).
- [SQLAlchemy: Core y ORM](https://docs.sqlalchemy.org/en/20/intro.html).
- [Imagen oficial PostgreSQL](https://github.com/docker-library/docs/blob/master/postgres/README.md).
- [StatefulSets](https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/), [Persistent Volumes](https://kubernetes.io/docs/concepts/storage/persistent-volumes/) y [Azure Disk CSI](https://learn.microsoft.com/en-us/azure/aks/create-volume-azure-disk).

Son referencias de capacidades y ciclo de vida, no evidencia de que la propuesta esté implementada o de que AKS funcione en este repositorio.
