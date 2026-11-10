# FIN-02 — Punto de partida

Fecha: 10/11/2026. Preparación documental FIN-01T. **FIN-02: Pendiente, no iniciado.** No se implementan ni ejecutan semillas, backups o restauraciones en esta tarea.

## 1. Estado de partida y dependencia

FIN-01 **Completado** el 10/11/2026, por aprobación expresa del responsable tras FIN-01R/FIN-01S. Registro: [plan FIN](../tfg-plan-001/TFG-COMPLETION-PLAN.md), sección Seguimiento vigente. Baseline único: `supabase/migrations/20261108000100_initial_wordle.sql` ratificado para base PostgreSQL nueva.

Referencia publicada: `b330ae70caf08ac789786376ca5de0305ea4471f`, rama `codex/pg01-07-consolidation`. [CI 42692713269](https://github.com/lromerob/wordle/actions/runs/42692713269) verificado: 55 offline/11 reales, builds y validaciones correctos; kind CI en memoria, GHCR deshabilitado. No evidencia de AKS ni autorización de exposición pública.

## 2. Criterios originales, sin ampliación

Fuente: `TFG-COMPLETION-PLAN.md`, apartado **FIN-02 - Datos sintéticos y recuperación**. Texto de definición conservado:

- Objetivo/alcance técnico: «Semillas idempotentes, diccionario de cinco letras, usuarios compatibles con FK y partidas/estadísticas sintéticas; respaldo/restauración.»
- Dependencias: «FIN-01.»
- Criterios de aceptación: «Dos cargas no duplican datos; restauración desde cero y E2E persistente superan casos válidos/inválidos, victoria y derrota; reinicio conserva datos.»
- Evidencias: «Seed, checksums no sensibles, log de restauración y pruebas.»
- No requiere Azure; la referencia antigua a un proyecto Supabase dedicado queda sustituida por la arquitectura PostgreSQL directa aprobada en PG-01. Riesgos originales: borrado accidental y uso de datos reales no autorizados. Estimación original 1–2 días, no compromiso nuevo.

No hay tabla usuarios ni FK a Auth en el baseline ratificado: usuario_id es TEXT. «Usuarios compatibles con FK» se cumple con identificadores sintéticos compatibles con las relaciones reales; no inventar Auth/FK ni usuarios Supabase. La FK existente es intentos.partida_id→partidas.id. Semillas de partidas/intentos deben respetarla.

## 3. Ya demostrado frente a pendiente

| Criterio | Evidencia existente | Pendiente concreto FIN-02 |
|---|---|---|
| Semillas de palabras | docker/postgres/demo-words.txt y 20-demo-words.sql: CASAS/GATOS/NIÑOS/PERRO/SACAS; INSERT ON CONFLICT DO NOTHING; generador offline aprobado | Acordar que el corpus de cinco palabras sea suficiente para la demo o aportar lista autorizada/procedencia. Demostrar dos cargas sin duplicación; sintaxis idempotente no equivale a esa prueba. |
| Datos de usuarios/partidas/stats | PG-04 fixtures aisladas; PG-05 smoke crea juegos/stats sintéticos; PG-06 datos reales de ensayo | Definir/reutilizar un conjunto sintético pequeño e idempotente para recuperación, con IDs estables cuando hagan falta y sin reemplazar filas ajenas. No basta afirmar que la fixture de palabras cubre todas las semillas. |
| E2E persistente | PG-05-TEST-RESULTS.md: API/UI válido/inválido/victoria/derrota; PG-06 API real y snapshots persistidos | Repetir los casos requeridos contra el destino restaurado, no solo el origen. |
| Reinicio conserva datos | PG-05 restart/down-up con snapshot idéntico; PG-06 recrea pod/mismo PVC y reinicia app | Reutilizar esta evidencia; verificar reinicio en el ensayo restaurado si forma parte del procedimiento elegido, sin repetir todos los entornos. |
| Backup/restore | PG-05 pg_dump custom sin owner/ACL a DB auxiliar nueva en mismo servidor, tablas idénticas | Restauración desde cero en destino aislado nuevo, con roles/grants/bootstrap documentados y API usando el restore. La prueba previa no arrancó aplicación sobre restore. No exigir restaurar Azure ni todos los roles globales. |
| Evidencias | Informes PG-04/05/06, scripts existentes y baseline validada | Seed/huellas no sensibles, resumen sanitizado de dos cargas/restore/E2E y comandos reproducibles del ensayo FIN-02. |

Dependencia FIN-01 satisfecha. Herramientas/localizaciones privadas se revalidarán si se autoriza el ensayo; no se inspeccionan secretos, dumps o estado local existentes en esta preparación. La copia privada PG-05 no se publica ni se usa sin autorización de su alcance.

## 4. Propuesta mínima para un siguiente incremento autorizado

1. Acordar corpus de demo acotado y fixture sintética mínima, reutilizando generador/seed y contratos existentes; comprobar dos cargas sin duplicados en una DB nueva propia. No descargar un diccionario ni añadir tablas.
2. Crear origen/destino de ensayo separados de recursos PG-05/06, generar datos sintéticos, obtener backup fuera de Git y restaurarlo en una DB/almacenamiento nuevos. Reutilizar mecanismos existentes cuando permitan el aislamiento; proporcionar rol app/grants necesarios sin migrar credenciales ni roles reales.
3. Arrancar la aplicación de ensayo contra el destino restaurado y comprobar lectura de los datos recuperados, válido/inválido, victoria/derrota y conservación tras reinicio. Conservar hashes/comparación de valores y resultados sanitizados. Limpiar solo recursos de esa ejecución conforme a autorización; no borrar recursos persistentes previos.

Son pasos propuestos, no ejecución autorizada por FIN-01T. No se exige repetir Compose y kind ni introducir arquitectura de backup empresarial, HA, retención cloud o un corpus lingüístico grande.

## 5. Evidencias de aceptación a entregar

- Lista/seed sintéticos versionables y procedencia del corpus elegido; resultado de primera/segunda carga, mismos datos y sin duplicados.
- Identificación no sensible del backup, checksum y destino nuevo; resultado de restore y comparación de datos/contratos, sin mostrar passwords o contenido privado.
- HTTP real sobre la base restaurada para casos requeridos y evidencia de reinicio conservando datos; diferenciar de las 11 pruebas CI desechables.
- Comandos reproducibles, alcance/limpieza y limitaciones; ninguna declaración de recuperación de producción o migración histórica Supabase.

## 6. Fuera de FIN-02 y evidencia documental seleccionada

FIN-03: autenticación/propiedad y negativos; no añadir login en FIN-02. FIN-04: pruebas frontend CI, GHCR/digests. FIN-05/06/07: AKS/Ingress/secretos cloud. FIN-08/09: Blue-Green/rollback. FIN-10–22: señales, Azure y memoria/defensa. No moverlos al alcance de datos/restauración local.

Para futuro commit documental, seleccionar sin staging: FIN-01R-ACCEPTANCE-MATRIX.md (incluye diagrama), FIN-01S-ARCHITECTURE-DECISION.md y FIN-01S-CLOSURE-RECOMMENDATION.md. Se conservan exactamente como fueron emitidos; el registro FIN-01T acredita la aprobación posterior. Los otros informes FIN-01R/S y PUB permanecen locales, sin eliminación ni incorporación automática. Para reconstruir evidencia CI publicada más adelante, PUB-05B-CI-RESULTS.md es soporte consultable; su inclusión requerirá selección expresa junto con cualquier enlace que dependa de informes aún locales.

**Próxima autorización recomendada:** ensayo FIN-02 local de semillas idempotentes y restore independiente con HTTP. FIN-02 permanece pendiente hasta que se autorice y ejecute; este documento no certifica su aceptación.
