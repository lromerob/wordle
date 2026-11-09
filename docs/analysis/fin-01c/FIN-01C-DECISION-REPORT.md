# FIN-01C - Informe de decisión arquitectónica

Fecha: 08/11/2026. Estado: **propuesta para aprobación, sin implementación**. FIN-01 no se declara completado. Corte inspeccionado: a666b17680781a24889ea774778019995d3fca45, rama codex/devops-04a1-hardening, con trabajo local previo preservado.

## Recomendación

Aprobar, para el alcance académico y temporal del TFG, sustituir el transporte Supabase SDK/Data API por PostgreSQL 16 directo mediante **psycopg 3 async con SQL parametrizado y pool acotado por proceso**. No añadir ORM, operador, réplica o Azure Database. Mantener React/Nginx/FastAPI y los contratos HTTP. PostgreSQL tendría una única instancia: servicio Compose con volumen en local y StatefulSet de una réplica con PVC/Service interno/Secret en AKS. Ambas aplicaciones Blue/Green futuras usan la misma base.

Es una recomendación de simplicidad y control de reconstrucción, no una certificación de producción, HA o ahorro monetario. La decisión requiere aprobación expresa antes de cambiar código/configuración y antes de cualquier instalación o servicio. La evidencia SQL ya obtenida reduce riesgo de esquema, no valida aún el driver.

## Hechos, inferencias y límites

**Hechos:** el backend accede a cuatro tablas mediante el SDK; no se encontró uso funcional de Auth/Storage/Realtime/RPC. usuario_id es text y no tiene una FK Auth informada. La baseline y las operaciones SQL pasaron en PostgreSQL 16.15 en dos bases vacías, con cuatro tablas, 23 columnas, siete restricciones y seis índices. El contenedor ya fue eliminado. Los contratos reales están en los routers, los tests existentes y el [informe FIN-01B](../fin-01b/FIN-01B-POSTGRES-VALIDATION.md).

**Inferencia fundamentada:** no hay una función Wordle inspeccionada que necesite un servicio exclusivo Supabase; esas lecturas/escrituras son reproducibles con PostgreSQL directo. Esto no acredita consumidores fuera del repositorio ni permite retirar un proyecto externo sin confirmación del propietario.

**Pendiente:** integrar/validar driver con FastAPI y JSON, confirmar detalles no aportados del catálogo, aprobar diccionario, demostrar persistencia/restore y elegir almacenamiento/capacidad AKS. No se consultaron la suscripción, el proyecto, runs CI, paquetes publicados o un backlog externo.

## Comparación de alternativas

| Aspecto | Conservar Supabase | PostgreSQL directo propuesto |
|---|---|---|
| Trabajo inmediato | Menor cambio en routers; aún falta Supabase local/PostgREST y datos reproducibles | Reescritura acotada del acceso, tests y configuración |
| Dependencias de aplicación | SDK y componentes transitivos, API REST externa | Driver/pool y conexión directa; menos productos sin uso |
| Persistencia | Administrada por servicio externo, fuera de AKS | Disco/volumen, backups, versiones y disponibilidad a cargo del proyecto |
| Reproducibilidad de demo | Depende de proyecto/clave/estado externos o un stack Supabase local más amplio | Una instancia PG conocida y esquema ya probado; mejor paridad local/AKS |
| Blue-Green | Futuras versiones SDK podrían compartir Supabase | Dos versiones PG comparten DB; primera transición legacy es distinta |
| Coste | Free sujeto a límites/condiciones, no verificado en esta tarea | Consume nodo/disco/backup propios; no se garantiza coste total inferior |
| Riesgo operativo | Menos administración DB, dependencia de disponibilidad/configuración externa | Punto único de fallo aceptado para TFG; responsabilidad de restauración |

SQLAlchemy Core/ORM es técnicamente viable, pero suma conceptos a cuatro tablas y DDL existente. Psycopg 3 encaja con SQL explícito y async; el pool añade solo gestión justificada de conexiones. No se fijan versiones ni se añaden dependencias ahora. Véanse [documentación oficial de psycopg](https://www.psycopg.org/psycopg3/docs/advanced/async.html) y [Core/ORM de SQLAlchemy](https://docs.sqlalchemy.org/en/20/intro.html).

## Ventajas para el TFG

- Paridad PostgreSQL local/Compose/kind/AKS con el mismo DDL y versión fijada.
- Elimina autenticación del servicio Supabase y transporte PostgREST no necesarios para el juego inspeccionado.
- Permite verificar transacciones y fallos contra una DB real sin reproducir un producto externo completo.
- Hace visible persistencia, backup, restore y ciclo efímero como evidencias académicas.
- Facilita compartir una DB entre versiones de aplicación cuando ambas ya usan el driver.

## Desventajas y riesgos principales

1. **Compatibilidad HTTP/driver:** UUID, JSONB, Decimal y fechas llegan con tipos Python distintos; conservar payloads y estados exige tests de integración, no solo MemoryDB.
2. **Transacciones/conexiones:** la secuencia actual de escrituras no es atómica. Pool, rollback y concurrencia por partida/estadísticas deben diseñarse y probarse; no compartir una conexión global entre solicitudes.
3. **Disponibilidad:** un PostgreSQL de una réplica dentro de AKS puede interrumpirse por reinicio, fallo de nodo o attach de disco. Blue-Green de app no soluciona ese punto único de fallo.
4. **Retirada de AKS:** PVC/Retain no equivalen a backup fuera de cloud temporal; destruir el RG/clúster puede perder la base. Debe existir exportación restaurable fuera del entorno antes de autorizar retirada.
5. **Datos iniciales:** sigue sin fuente/licencia del diccionario real; fixtures no resuelven FIN-02. No se autoriza extracción de datos del proyecto anterior.
6. **Transición inicial:** Blue antigua con SDK no usa automáticamente el PG de Green. Recomendar una release base PG aceptada en ventana controlada para demo sintética; solo después demostrar Blue-Green compartido. Si hay datos históricos que preservar, requiere alcance/permiso adicional.
7. **Presupuesto/capacidad:** DB y observabilidad compiten por memoria/disco/conexiones; medir y revisar sizing. No se puede afirmar que los nodos mínimos previstos basten.
8. **Supuestos de esquema:** secuencia, nombres de restricciones y detalles FK/typmod siguen con los límites FIN-01B. No modificar baseline para ocultarlos ni afirmar igualdad completa con remoto.

Seguridad limitada al objetivo: credenciales técnicas externas a Git/imágenes, conexiones internas, permisos operativos necesarios y ausencia de secretos en logs. No se introduce autenticación de usuarios ni rediseño RLS. La comparación usuario_id del cliente conserva su limitación conocida y no se presenta como seguridad efectiva. El script allow_all queda histórico/opt-in de Supabase, no forma parte de la inicialización PG directa propuesta.

## Esfuerzo y alcance estimado

Nueve incrementos PG-01..PG-09: **44-74 horas efectivas**, equivalentes a 7,3-12,3 jornadas de 6 horas. Con 20 % de contingencia: aproximadamente 53-89 horas. Incluye acceso/serialización/transacciones, tests, Compose persistente, perfil Kubernetes, integración CI y backup/documentación. La aceptación CSI/AKS se coordina con FIN-18/19; no incluye desplegar Azure por esta autorización, resolver cuotas/tenant, mover datos reales, rehacer autenticación ni implementar el resto de Blue-Green/observabilidad del TFG.

El esfuerzo se solapa con FIN-01/02/04/05/07 y otras tareas futuras: revisar el total del plan, no sumar 44-74 h automáticamente a todas sus estimaciones. Es estimación, no tiempo medido ni promesa de calendario.

## Decisiones necesarias antes de empezar

- D1: confirmar PG directo como arquitectura objetivo y aceptar instancia única sin HA para demo.
- D2: elegir demo nueva con datos sintéticos/diccionario aprobado o requerir traslado de datos históricos bajo otro permiso.
- D3: aprobar psycopg 3 async, distribución/versión y pool; compatibilidad Python 3.12/Linux/Windows a verificar.
- D4: fijar contrato JSON y tratamiento de excepciones/UUID inválido, sin cambios silenciosos de API ni reglas.
- D5: acordar rol DB de aplicación frente a migrador, nombres de variables y Secret; no se necesitan claves Supabase nuevas.
- D6: decidir cómo registrar/serializar migraciones y entregar SQL al servicio/Job; no aplicar baseline en cada arranque.
- D7: aprobar política de volumen/PVC, StorageClass, backup externo, retención y restauración, con presupuesto/capacidad posteriores.
- D8: acordar transición inicial y compatibilidad expand/contract de futuras dos versiones PG; rollback de app nunca equivale a rollback de datos.

## Efecto sobre FIN-01 a FIN-22

Sí afecta al plan: se sustituye el gate Supabase/PostgREST por PG directo en FIN-01 y se trasladan datos/secretos/persistencia/recuperación a Compose/AKS. Los 22 IDs y dependencias generales se mantienen propuestos; cambios detallados de criterios se enumeran uno a uno en el [plan incremental](FIN-01C-MIGRATION-PLAN.md).

Cambios principales: FIN-01/02 (driver, semillas y backup), FIN-03/07 (conexión/Secret), FIN-04/05 (tests/perfil PG), FIN-08/09 (DB compartida y rollback), FIN-15/16 (sizing/CSI), FIN-17/18/19 (deploy, evidencia cloud y reconstrucción) y FIN-20/21/22 (manual/defensa). FIN-06 e instrumentación FIN-10..14 conservan su objetivo académico; se ajustaría contexto, sin nuevos requisitos como un exporter PostgreSQL obligatorio.

No se actualiza ni elimina una tarea del plan anterior en FIN-01C. Tampoco se declara FIN-01 cerrado por elegir tecnología. Será necesario aceptar API directa, persistencia y los criterios revisados antes de cambiar su estado.

## Resultado y siguiente paso

Evaluación lista para revisión: inventario, impacto funcional, driver recomendado, Compose/AKS/CI, plan verificable y estimación están documentados. Este análisis no modifica el comportamiento actual de Wordle ni prueba una migración de runtime.

Si el propietario aprueba la decisión, autorizar un primer incremento PG-01 (contrato/transición y dependencias exactas) y después el cambio mínimo de acceso PG-02 bajo alcance concreto. No iniciar servicios, instalaciones, código, cambios de SQL o CI por defecto. No crear commit/push con estos documentos sin autorización posterior.

Documentos relacionados: [inventario](FIN-01C-DEPENDENCY-INVENTORY.md), [impacto arquitectónico](FIN-01C-ARCHITECTURE-IMPACT.md), [plan](FIN-01C-MIGRATION-PLAN.md).
