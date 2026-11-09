# FIN-01C - Plan incremental propuesto

Fecha: 08/11/2026. **No autorizado para implementación.** No se crean tickets, no se cambia el backlog oficial ni estados FIN. [Inventario](FIN-01C-DEPENDENCY-INVENTORY.md), [impacto](FIN-01C-ARCHITECTURE-IMPACT.md), [decisión](FIN-01C-DECISION-REPORT.md).

## Gates y orden

Primero aprobar la decisión, el contrato HTTP y la transición de datos. Después driver y transacciones, tests reales, Compose persistente, Kubernetes/CI y backup/restore. La base se mantiene fuera de la conmutación Blue-Green. La primera transición SDK -> driver no puede usar la versión SDK antigua como si compartiera el PG nuevo.

La reconstrucción SQL FIN-01B ya probada se reutiliza sin repetirla innecesariamente ni modificar su baseline. Falta probar los handlers reales con un driver nuevo; el contenedor anterior ya se eliminó y no se arranca otro en FIN-01C.

## Incrementos pequeños

| ID | Objetivo/alcance | Dependencias | Criterios de aceptación verificables | Horas |
|---|---|---|---|---|
| PG-01 | **Fijar contrato y transición inicial.** Inventariar payloads/status actuales, validar supuestos FIN-01B y elegir demo nueva frente a datos históricos; aprobar driver y configuración técnica. | Aprobación expresa FIN-01C | Contrato de cinco endpoints de datos más /health documentado; decisión de datos y rollback inicial sin doble escritura; baseline SQL no cambia. | 3-5 |
| PG-02 | **Acceso directo mínimo.** Cambiar fábrica/dep a psycopg async, pool acotado/lifespan y SQL parametrizado; RETURNING, UUID/JSONB/Decimal/datetime; regenerar lock. | PG-01; autorización de dependencias | Sin imports Supabase en runtime nuevo; respuestas mantienen claves/tipos; import offline; pool abierto/cerrado y conexiones devueltas incluso ante excepción. | 8-12 |
| PG-03 | **Unidad transaccional de intento.** Agrupar intento/partida/stats, bloqueo por partida y tratamiento de UNIQUE stats entre partidas concurrentes; commit antes de respuesta. | PG-02 | Fallo inyectado no deja escritura parcial; concurrencia no supera seis ni duplica numeración por carrera; estadísticas coherentes y reglas de juego intactas. | 4-8 |
| PG-04 | **Pruebas reales y dobles adaptados.** Adaptar overrides/fixtures sin fingir SDK; preservar evaluación y regresiones; integrar PG16 nuevo aislado y comparar API. | PG-02/03; permiso de runtime local | Unit/HTTP anteriores siguen cubiertos; integración UUID/JSONB/promedio, 404, errores, repetidas/victoria/derrota y sin solución activa; red externa bloqueada donde corresponda. | 6-10 |
| PG-05 | **Compose reproducible de tres servicios.** PG+volumen exclusivo+health, conexión privada, migrador/seed aprobado one-shot y entrega explícita SQL; perfiles test separados. | PG-04; fuente de diccionario aprobada para demo completa | Desde volumen nuevo aplica baseline una vez; restart conserva datos; segundo arranque no repite DDL ni borra filas; desde backup restaura una DB nueva. Fixtures etiquetadas no cierran el diccionario real. | 5-8 |
| PG-06 | **Kubernetes de datos compartidos.** StatefulSet 1 réplica, Service(s), PVC/Secret, migración serial y configuración backend; separar datos de colores y revisar CSI/sizing. | PG-05; permiso kind para ensayo, Azure solo si aprobado después | En kind persiste tras recrear pod; Blue/Green PG usan el mismo DB/PVC; rollout app no modifica almacenamiento. CSI/retirada real AKS quedan para FIN-18/19. | 6-10 |
| PG-07 | **Integración en CI y artefactos.** Job PG temporal con migración+test API, gate antes de publicar; adaptar memoria/kind explícitamente y logs/limpieza; conservar checks existentes. | PG-04/05/06 | PR prueba PG sin secretos externos; main no publica si integración falla; runner limpia solo temporales; imagen contiene driver/lock correcto y ninguna clave. | 5-8 |
| PG-08 | **Backup/restore y vida efímera.** Validar copia consistente fuera del runtime, política PVC/reclaim, versión de imagen y recuperación desde cero; catálogo de recursos facturables. | PG-05/06; copia local primero | Restore en segundo volumen/DB devuelve datos sintéticos y flujo HTTP; documento no depende de retener disco al borrar clúster; sin destrucción hasta comprobar copia. | 4-8 |
| PG-09 | **Actualizar documentos y evidencias tras aceptación.** Actualizar rutas/configuración y referencias FIN aprobadas, memoria/manifiesto de release; conservar Supabase histórico sin aplicar allow_all a PG. | PG-01..08 aceptados en su alcance | Ningún documento presenta lo propuesto como ya desplegado; dependencias FIN-01..22 revisadas con propietario; no duplicar migración baseline. | 3-5 |

Total base: **44-74 horas efectivas**, aproximadamente 7.3-12.3 jornadas de 6 horas. Contingencia 20 %: 53-89 horas. No incluye traslado de datos reales, cambios nuevos de autenticación, HA, operador, nuevos servicios, cuotas/permisos Azure, despliegue Azure aún no autorizado ni el resto del TFG. Se integra con tareas FIN existentes: no sumar automáticamente este rango a todas sus estimaciones porque hay solapamiento.

## Estrategia de pruebas y evidencias

| Nivel | Qué se conserva/prueba | Evidencia y límite |
|---|---|---|
| Unitario offline | Evaluador, reglas y dobles de acceso; imports sin conexión externa | Pruebas sin DB, sin presentar mock como PostgreSQL. Adaptar AST/fixtures acopladas al SDK en vez de eliminar cobertura. |
| SQL real aislado | Baseline/contratos ya preparados y rol local adecuado, UUID, JSONB y numeric | Reutilizar éxito FIN-01B; nueva prueba solo si cambia driver/SQL/runtime o falta cobertura. Ninguna ejecución remota. |
| API con driver | Misma forma HTTP, secretos activos ocultos, 400/403/404, victoria/derrota y media fraccionaria | TestClient con DB temporal real y override de configuración, no MemoryDB para este nivel. Comparar formato de fechas/números/UUID y errores. |
| Transaccional | Fallo entre INSERT y stats, dos intentos paralelos y dos partidas de mismo usuario | Estado posterior consistente, rollback y ausencia de conexiones retenidas. No reintento ciego de escrituras inciertas. |
| Compose persistente | Primera inicialización, segunda ejecución sin DDL repetido y restart | Evidencia de datos conservados; test separado de restore. No borrar volumen de desarrollo para probar. |
| Kubernetes | Un solo PG/PVC; pod recreado, migración única, Blue/Green PG y rollback de app | kind verifica mecanismo; Azure Disk/zonas y eliminación de AKS requieren aceptación posterior real. |
| CI | PR sin publicación; integración PG verde; gate y limpieza al fallar | Run ID, commit/digest y logs sanitizados. Mantener memoria como prueba independiente si se conserva. |
| Recuperación | Dump fuera del entorno -> nueva DB/volumen -> API | Checksum y restauración probada; PVC o snapshot sin prueba no bastan. |

No crear nuevos endpoints ni funciones de juego para facilitar tests. Se puede usar una fixture aprobada de un único vocablo existente (CASAS) para victoria determinista y otras fixtures existentes para derrota/repetidas, siempre en DB de test; no es el diccionario de demo. La fuente aprobada continúa siendo gate de FIN-02.

## Control de cambios y rollback de implementación

Implementar por rama/PR pequeños una vez autorizados, con release de contrato estable. Antes de retirar el SDK, capturar baseline de pruebas y referencias de versión. No mezclar simultáneamente cambio de driver, cambios de reglas y nuevas restricciones SQL. La reversión de código antes del cutover no requiere borrar la DB nueva; después de empezar a escribir en ella, volver a Supabase requiere decidir cómo preservar esos datos. No prometer esa reversión como rollback Blue-Green rutinario.

Mantener migraciones forward-only compatibles durante la ventana de dos releases PG. La migración inicial solo se ejecuta en DB nueva con historial/lock; no arrancar un nuevo baseline desde cada pod. Cualquier mecanismo de seguimiento de migraciones se diseña explícitamente, sin alterar aquí las tablas o SQL existentes.

## Impacto propuesto sobre FIN-01 a FIN-22

Se conservan los 22 identificadores y el grafo general. Los cambios siguientes son propuestas de criterios/alcance y no se aplican al plan aprobado en esta tarea.

| FIN | Revisión necesaria si se aprueba PG directo |
|---|---|
| FIN-01 | Mantener baseline y validación ya logrados; sustituir gate Supabase local/PostgREST por API directa PG y confirmar supuestos. No marcar completo por este análisis. |
| FIN-02 | Semillas/backup/restore pasan a volumen local/PVC y copia externa; fuente del diccionario sigue pendiente. |
| FIN-03 | Sustituir dependencias de roles/clave Supabase por usuario DB operativo y Secret/conectividad interna. Identidad funcional del usuario no se rediseña por esta decisión. |
| FIN-04 | Añadir integración PG real y actualizar dependencias/lock; mantener pruebas de juego y frontend. |
| FIN-05 | Perfil AKS conecta a PG Service; sumar recursos de datos y Job de migración; preservar perfil memoria como tal. |
| FIN-06 | Ingress de aplicación sin cambio de objetivo; PostgreSQL nunca se expone por Ingress. |
| FIN-07 | Secret DB y ciclo de recuperación/rotación sustituyen clave Supabase; no frontend. |
| FIN-08 | Dos aplicaciones PG, una instancia DB estable; primera transición legacy se acepta por separado. |
| FIN-09 | Rollback solo de app con esquema compatible; no duplicar DB ni revertir datos automáticamente. |
| FIN-10 | Trazas futuras deben incluir acceso PG sin consultas/valores sensibles; objetivo Collector permanece. |
| FIN-11 | Métricas requeridas de clúster/exporters se mantienen; PostgreSQL exporter adicional es opcional, no una obligación académica nueva. |
| FIN-12 | Logs PG pueden centralizarse junto a app; evitar DSN/secretos. Objetivo Loki no cambia. |
| FIN-13 | Dashboard puede reflejar disponibilidad DB si hay señal, sin ampliar innecesariamente paneles exigidos. |
| FIN-14 | Umbrales/errores DB pueden ser escenarios, sin añadir canales o requisitos nuevos por la migración. |
| FIN-15 | Medir RAM/CPU/disco y conexiones con PG, Blue+Green y observabilidad; revisar sizing. |
| FIN-16 | Revisar StorageClass/CSI, presupuesto de discos/backups y topología; no crear DB administrada ni cambiar IaC automáticamente. |
| FIN-17 | deploy-demo incluye migración/seed serial y restore; destroy-demo exige backup externo antes de retirar PVC/AKS. |
| FIN-18 | Recorrido cloud prueba driver+PG persistente, promoción y rollback compartiendo DB. |
| FIN-19 | Reconstrucción restaura datos externos en PVC nuevo; conservar discos no es el único plan. |
| FIN-20 | Actualizar arquitectura/manual y explicar decisión con FIN-01B histórico; no reescribir las evidencias antiguas. |
| FIN-21 | Ensayar fallo/reinicio de instancia única y restauración; declarar ausencia de HA. |
| FIN-22 | Respuestas futuras al docente describen arquitectura realmente aceptada; siguen dependiendo de sus preguntas. |

No se agrega FIN-23, no se elimina una tarea y no se alteran dependencias formalmente. Tras aprobar la arquitectura, revisar en conjunto las estimaciones y la matriz académica en una tarea documental autorizada. Una implementación SQL/driver debe preceder al hito H1 y a la integración AKS; observabilidad puede prepararse en paralelo sin afirmar que ya consume PG.

## Próximo paso sujeto a autorización

Aprobar o rechazar PG directo y las decisiones del informe ejecutivo. Si se aprueba, comenzar solo PG-01 y acordar alcance de PG-02. Instalar dependencias, levantar contenedores, crear nuevos SQL o modificar runtime/CI requerirá autorización explícita de implementación; no queda concedida por leer este plan.
