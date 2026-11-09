# TFG-COMPLETION-PLAN

Fecha: 08/11/2026. **Backlog propuesto para revisión y aprobación; no es el backlog oficial y no autoriza implementación.** Se conservan arquitectura y tecnologías existentes. Fuente académica y estado: [matriz](TFG-COMPLIANCE-MATRIX.md); decisiones y riesgos: [brechas](TFG-GAP-ANALYSIS.md).

## Estrategia y dependencias

Camino crítico: FIN-01 esquema -> FIN-02 persistencia/restore -> FIN-03 seguridad decidida -> FIN-05/06/07 perfil AKS/Ingress/secretos -> FIN-08/09 promoción y rollback -> FIN-15 stack integrado -> FIN-16 prerrequisitos Azure -> FIN-17 despliegue controlado -> FIN-18 evidencia Azure -> FIN-19 recreación -> FIN-20 memoria -> FIN-21 ensayo -> FIN-22 respuestas a docente.

Es una representación de gates, no una obligación de serializar todo. FIN-04 puede avanzar al principio; FIN-10 a FIN-14 se desarrollan en paralelo a FIN-08/09 por ramas independientes, sin agentes o tareas iniciados aquí. La red/identidad de FIN-16 se decide pronto, pero no se crea infraestructura hasta aprobar presupuesto y recursos. Memoria y captura de evidencias avanzan desde F1. El vídeo depende de preguntas reales, no de una fecha inventada.

## Fases y hitos de aceptación

| Fase | Tareas | Hito de salida | Azure |
|---|---|---|---|
| F1: base reproducible | FIN-01 a FIN-04 | H1: juego persistente reproducible localmente, límites de seguridad acordados y artefactos identificados | No; Supabase real solo si se autoriza por separado. |
| F2: perfil de despliegue | FIN-05 a FIN-07 | H2: perfil tipo AKS probado en local, Ingress y secretos seguros sin romper kind-memory | No para desarrollo. |
| F3: entrega segura | FIN-08 a FIN-09 | H3: promoción y rollback automáticos demostrados con fallo controlado | Local primero. |
| F4: observabilidad | FIN-10 a FIN-15 | H4: juego/errores/rollback observables y notificación entregada; sizing revisado | Local primero. |
| F5: Azure temporal | FIN-16 a FIN-19 | H5: flujo cloud integrado y ciclo completo de retirada/reconstrucción documentado | Sí, autorización explícita. |
| F6: memoria y defensa | FIN-20 a FIN-22 | H6: PDF completo, manual reproducido y entrega; vídeo <=15 min tras preguntas docentes | Reutilizar evidencias; no sostener cloud innecesariamente. |

## Tareas propuestas

Las estimaciones son días efectivos de trabajo de una persona familiarizada con el repositorio, unas 6 horas/día; no son plazos ni compromisos. Las esperas por docente, permisos, cuota o revisión no se incluyen. Cada evidencia debe identificar commit/digest, modo memoria o Supabase y entorno.

### F1

#### FIN-01 - Reproducir esquema Supabase

- Objetivo/alcance técnico: Inventariar con autorización esquema real, tipos/defaults/índices/FK y RLS; redactar migraciones revisables, sin deducirlas solo de MemoryDB.
- Dependencias: Aprobación D01 y acceso de lectura autorizado.
- Criterios de aceptación: DB PostgreSQL/Supabase local vacía acepta migraciones; tablas/contratos coinciden; secretos no versionados.
- Evidencias a conservar: DDL versionado, diagrama de datos, log sanitizado de migración.
- Necesidad de Azure: No; Supabase real requiere autorización independiente.
- Riesgos: Esquema real no disponible; diferencias PostgreSQL/extensiones.
- Esfuerzo orientativo: 1-2 días.

#### FIN-02 - Datos sintéticos y recuperación

- Objetivo/alcance técnico: Semillas idempotentes, diccionario de cinco letras, usuarios compatibles con FK y partidas/estadísticas sintéticas; respaldo/restauración.
- Dependencias: FIN-01.
- Criterios de aceptación: Dos cargas no duplican datos; restauración desde cero y E2E persistente superan casos válidos/inválidos, victoria y derrota; reinicio conserva datos.
- Evidencias a conservar: Seed, checksums no sensibles, log de restauración y pruebas.
- Necesidad de Azure: No; validable localmente antes de proyecto Supabase dedicado.
- Riesgos: Borrado accidental si seed no limita entorno; datos reales no autorizados.
- Esfuerzo orientativo: 1-2 días.

#### FIN-03 - Cerrar límites de seguridad para demo

- Objetivo/alcance técnico: Decidir identidad/propiedad, RLS y alcance de credencial; probar restricciones y riesgos de concurrencia; no añadir login nuevo sin aprobación.
- Dependencias: FIN-01; aprobación D01.
- Criterios de aceptación: Decisión firmada/revisada y pruebas negativas de lectura/escritura ajena; ninguna garantía falsa basada en usuario_id; exposición limitada hasta resolver seguridad.
- Evidencias a conservar: ADR, pruebas negativas y matriz de permisos sanitizada.
- Necesidad de Azure: No; integración Supabase posterior autorizada.
- Riesgos: Puede exigir cambio arquitectónico aprobado; credencial que elude RLS.
- Esfuerzo orientativo: 1-2 días.

#### FIN-04 - Verificar baseline CI y artefactos

- Objetivo/alcance técnico: Revisar runs de siete jobs/paquetes, ejecutar pruebas frontend en CI mediante cambio aprobado, conservar digests, tamaños y resultados.
- Dependencias: Sin dependencia técnica; autorización posterior para cambios/consultas.
- Criterios de aceptación: Backend y 12 casos frontend sin omisiones; build/runtime por digest verificables; publicación solo en main; check Terraform verde.
- Evidencias a conservar: URL/run ID/commit, resumen tests, digests e inspección no sensible.
- Necesidad de Azure: No.
- Riesgos: Run no disponible, límites Actions o paquetes privados; no repetir históricos innecesariamente.
- Esfuerzo orientativo: 0.5-1 días.

### F2

#### FIN-05 - Perfil Kubernetes AKS sin romper kind

- Objetivo/alcance técnico: Overlay Kustomize AKS con imágenes GHCR, backend runtime real, probes/recursos/config; separar memoria y producción; versionar parámetros.
- Dependencias: FIN-02/03/04.
- Criterios de aceptación: Render de ambos perfiles correcto; backend ClusterIP; dos variantes nunca intercambian entrada memory/runtime; validación local con DB de ensayo.
- Evidencias a conservar: Render sanitizado, diagrama y pruebas de configuración.
- Necesidad de Azure: No inicialmente; aceptación final FIN-18.
- Riesgos: Mezcla memoria/real, readiness que solo verifica proceso.
- Esfuerzo orientativo: 1-1.5 días.

#### FIN-06 - Ingress Controller y acceso de aplicación

- Objetivo/alcance técnico: Elegir controlador soportado; configuración declarativa del controlador y recurso Ingress; rutas de frontend y /api; decidir DNS/TLS.
- Dependencias: FIN-05 y D03.
- Criterios de aceptación: En kind, petición atraviesa controlador/Ingress y llega a Nginx/API; host/rutas correctos; diseño TLS y exposición cloud revisado.
- Evidencias a conservar: YAML/chart fijado, pruebas HTTP, diagrama de rutas.
- Necesidad de Azure: No para desarrollo; sí verificación final de LB/TLS en AKS si se usan.
- Riesgos: Controlador obsoleto, costes de IP/LB, DNS/certificados.
- Esfuerzo orientativo: 0.5-1 días.

#### FIN-07 - Secretos reproducibles sin valores en Git

- Objetivo/alcance técnico: Referencias Secret declarativas; inyección de valores externos desde entorno protegido; permisos y procedimiento de rotación/recuperación.
- Dependencias: FIN-03/05, D02.
- Criterios de aceptación: Ningún valor en Git/render/artifacts; pod backend usa Secret correcto; frontend sin claves; recuperación externa probada sin mostrar valores.
- Evidencias a conservar: Plantillas seguras, lista de nombres, permisos y evidencia redaccionada.
- Necesidad de Azure: No inicialmente.
- Riesgos: Base64 no es cifrado; planes/estado/logs pueden filtrar.
- Esfuerzo orientativo: 1-1.5 días.

### F3

#### FIN-08 - Blue-Green demostrable

- Objetivo/alcance técnico: Dos versiones distinguibles sin funciones nuevas del juego; desplegar candidata, gates y promoción del tráfico; compartir persistencia.
- Dependencias: FIN-02/05/06/07; D04.
- Criterios de aceptación: Blue sirve mientras Green arranca; candidata pasa pruebas; Service/Ingress conmuta; respuestas identifican versión; requests registran interrupción medida.
- Evidencias a conservar: YAML/automatización futura, cronología, vídeo y respuestas por versión.
- Necesidad de Azure: No para lógica local; repetir sobre Azure FIN-18.
- Riesgos: Cambios incompatibles de DB, sesiones en memoria, recursos duplicados.
- Esfuerzo orientativo: 1-2 días.

#### FIN-09 - Rollback automático por fallo controlado

- Objetivo/alcance técnico: Reutilizar promoción; fallo de candidata y fallo funcional post-switch; restaurar selector/ruta y comprobar versión antigua; rollback no implica downgrade DB.
- Dependencias: FIN-08.
- Criterios de aceptación: Sin intervención manual se rechaza candidata no sana y se restaura versión previa ante fallo post-promoción; estado/persistencia íntegros; salida/log de fallo conservados.
- Evidencias a conservar: Run fallida esperada, logs, selector antes/después y prueba de continuidad.
- Necesidad de Azure: No para desarrollo; sí repetición final FIN-18.
- Riesgos: Confundir cleanup con rollback; rollback de datos no diseñado.
- Esfuerzo orientativo: 1-2 días.

### F4

#### FIN-10 - OpenTelemetry Collector integrado

- Objetivo/alcance técnico: Instrumentar señales necesarias, desplegar Collector y elegir destino consultable de trazas; métricas OTLP y correlación de request/trace.
- Dependencias: FIN-05; D05; puede avanzar en paralelo a F3.
- Criterios de aceptación: Un intento sintético produce traza de backend y métrica recolectadas/exportadas; error intencionado identificable; no registrar claves ni solución activa.
- Evidencias a conservar: Config, trace ID, captura de span y métrica exportada.
- Necesidad de Azure: No inicialmente.
- Riesgos: Añadir herramientas sin señales reales; destino trazas pendiente.
- Esfuerzo orientativo: 1-2 días.

#### FIN-11 - Prometheus, cAdvisor y Node Exporter

- Objetivo/alcance técnico: Scrape/exporters y targets; preferir endpoint kubelet-cAdvisor existente con RBAC adecuado frente a DaemonSet privilegiado innecesario; validar disponibilidad AKS.
- Dependencias: FIN-05; coordinar FIN-10.
- Criterios de aceptación: Targets UP; consultas muestran métrica de nodo y contenedor Wordle; cAdvisor y Node Exporter identificados; permisos mínimos documentados.
- Evidencias a conservar: Valores/chart fijados, targets y consultas/export de resultados.
- Necesidad de Azure: No local; endpoint gestionado exige validación Azure FIN-18.
- Riesgos: AKS restringe endpoints, duplicación de scrapes y cardinalidad.
- Esfuerzo orientativo: 1-1.5 días.

#### FIN-12 - Loki y recogida central de logs

- Objetivo/alcance técnico: Configurar Loki y un agente soportado; etiquetas limitadas, retención pequeña y destino de datos definido.
- Dependencias: FIN-05; D05.
- Criterios de aceptación: Consulta en Grafana/Loki recupera logs de ambos servicios y error controlado, sin secretos; sobrevive lo necesario o se declara retención efímera.
- Evidencias a conservar: Config, consultas y capturas sanitizadas de logs.
- Necesidad de Azure: No inicialmente.
- Riesgos: Crecimiento de disco, labels de alta cardinalidad y logs sensibles.
- Esfuerzo orientativo: 0.5-1 días.

#### FIN-13 - Dashboards Grafana versionados

- Objetivo/alcance técnico: Provisionar datasources y dashboards personalizados de requests/errores/latencia, nodos/contenedores y navegación a logs/trazas.
- Dependencias: FIN-10/11/12.
- Criterios de aceptación: Dashboard importado desde cero muestra datos de Wordle y sistema con ventanas/unidades claras, no solo dashboard genérico instalado.
- Evidencias a conservar: JSON/provisioning, capturas y fuente de cada panel.
- Necesidad de Azure: No inicialmente.
- Riesgos: Panel vacío por rango temporal/datasource y credenciales por defecto.
- Esfuerzo orientativo: 0.5-1 días.

#### FIN-14 - Alertas y notificaciones

- Objetivo/alcance técnico: Definir una alerta por métrica y una por log crítico; receptor externo autorizado; recuperación y antirruido.
- Dependencias: FIN-11/12/13; D05.
- Criterios de aceptación: Fallo sintético dispara ambas clases, llega notificación real al canal autorizado y se registra resolved; no ocultar diferencia entre firing y delivery.
- Evidencias a conservar: Reglas, tiempos, capturas del receptor redaccionadas y resolved.
- Necesidad de Azure: No necesariamente; requiere servicio/canal autorizado.
- Riesgos: Receptor sin configurar, spam, secreto en webhook.
- Esfuerzo orientativo: 0.5-1 días.

#### FIN-15 - Validar capacidad y observabilidad conjunta

- Objetivo/alcance técnico: Ensayo local de stack completo; medir reservas/uso/disco; fijar retención y estimar recursos Azure sin prometer mínimo universal.
- Dependencias: FIN-09/10/11/12/13/14.
- Criterios de aceptación: E2E + fallo + rollback visibles en señales; sin OOM; recursos solicitados caben en diseño revisado; propuesta de sizing/coste.
- Evidencias a conservar: Mediciones, informe de carga pequeña y correlación de eventos.
- Necesidad de Azure: No; capacidad AKS definitiva FIN-18.
- Riesgos: Kind no representa capacidad gestionada; almacenamiento de señales.
- Esfuerzo orientativo: 0.5-1 días.

### F5

#### FIN-16 - Preflight Azure y estado externo

- Objetivo/alcance técnico: Verificar cuota/región/versiones, identidad/grupo Entra, OIDC futuro, red API, permisos de estado y bootstrap Storage independiente solo con autorización.
- Dependencias: D02/D06, FIN-04; decisiones sin cloud pueden adelantarse.
- Criterios de aceptación: Checklist revisada; backend independiente accesible y bloqueo comprobado cuando autorizado; permisos/red no abren API a internet completo; presupuesto aprobado.
- Evidencias a conservar: ADR, configuración no sensible, validación lock y presupuesto.
- Necesidad de Azure: Sí para comprobar cuenta/crear backend; solo tras autorización.
- Riesgos: Propagación RBAC, tenant personal, coste de almacenamiento y runner.
- Esfuerzo orientativo: 1-2 días.

#### FIN-17 - deploy-demo y destroy-demo controlados

- Objetivo/alcance técnico: Workflows manuales protegidos, planes aprobados, serialización, selección de imágenes, recuperación de secretos y evidencias; no borrar estado/Supabase por defecto.
- Dependencias: FIN-02/07/15/16.
- Criterios de aceptación: Plan despliegue/retirada revisable; rechaza entorno equivocado; primer deploy autorizado termina con servicios y señales verificados; permisos limitados.
- Evidencias a conservar: Workflows posteriores, run IDs, outputs sanitizados y lista de recursos.
- Necesidad de Azure: Sí para aceptación; diseño/pruebas de scripts local.
- Riesgos: Destrucción fuera de alcance, drift, cancelación y estado perdido.
- Esfuerzo orientativo: 1-2 días.

#### FIN-18 - Demostrar CI/CD y stack completos en AKS

- Objetivo/alcance técnico: Promover versión conocida desde GHCR a AKS; Ingress, Supabase, Blue-Green, fallo y rollback con métricas/logs/trazas/alertas; pruebas de seguridad.
- Dependencias: FIN-17; FIN-06/09/14.
- Criterios de aceptación: Un recorrido reproducible conecta commit -> digest -> despliegue -> juego persistente -> promoción -> rollback automático; evidencia todos los componentes obligatorios.
- Evidencias a conservar: Dossier integrado con cronología, vídeos/capturas y consultas.
- Necesidad de Azure: Sí.
- Riesgos: Fallo de identidad/red, capacidad no prevista, evidencia incompleta.
- Esfuerzo orientativo: 1-2 días.

#### FIN-19 - Retirada y reconstrucción ensayadas

- Objetivo/alcance técnico: Exportar/respaldar datos/evidencia; retirada autorizada; revisar remanentes y recrear desde versión fijada; validar de nuevo.
- Dependencias: FIN-18.
- Criterios de aceptación: Backup restaurable; solo recursos autorizados retirados; estado preservado; recreación verde sin pasos ocultos; tiempos medidos y coste residual revisado.
- Evidencias a conservar: Manifest de recuperación, hashes/digests, tiempos y listado sanitizado antes/después.
- Necesidad de Azure: Sí.
- Riesgos: Cuota al recrear, recursos huérfanos, cargos retardados.
- Esfuerzo orientativo: 1-2 días.

### F6

#### FIN-20 - Memoria PDF y manual académico

- Objetivo/alcance técnico: Todos los apartados pp. 5-6, diagramas, requisitos/evidencias, decisiones, manual desde cero, resultados/mejoras; enlace de entrega y revisión final.
- Dependencias: Evidencia progresiva desde FIN-01; cierre FIN-18/19.
- Criterios de aceptación: PDF legible con portada/índice y trazabilidad A01-A58; manual seguido por otra sesión; sin secretos; repositorio y configuración coinciden con release; entrega por plataforma confirmada cuando proceda.
- Evidencias a conservar: PDF, fuentes, diagramas, checksum release y recibo de entrega privado.
- Necesidad de Azure: No para redacción; usa evidencias Azure existentes.
- Riesgos: Documentar funcionalidades no implementadas, reejecuciones costosas.
- Esfuerzo orientativo: 2-3 días.

#### FIN-21 - Ensayo de defensa y contingencia

- Objetivo/alcance técnico: Guion por evidencia, explicación técnica oral, demo el día anterior, respaldo local/vídeo claramente identificado; no sustituir evidencia Azure por local.
- Dependencias: FIN-18/20.
- Criterios de aceptación: Ensayo cronometrado y revisión de legibilidad; entorno listo con margen; problemas y recuperación explicables.
- Evidencias a conservar: Guion, cronómetro y checklist de contingencia.
- Necesidad de Azure: No para guion; entorno real según ventana aprobada.
- Riesgos: Arranque de última hora y dependencia exclusiva de internet.
- Esfuerzo orientativo: 0.5-1 días.

#### FIN-22 - Vídeo de tres respuestas docentes

- Objetivo/alcance técnico: Tras recibir preguntas reales: elaborar respuestas basadas en evidencias, grabar profesionalmente, comprobar duración <=15 min y entregar por canal indicado.
- Dependencias: FIN-20/21 y preguntas del docente.
- Criterios de aceptación: Responde las tres preguntas recibidas; audio/imagen claros; duración del archivo no supera 15 min; revisión y entrega confirmadas.
- Evidencias a conservar: Preguntas conservadas privadamente, guion, metadatos de duración y vídeo final.
- Necesidad de Azure: No; reutiliza capturas para evitar coste de repetir despliegues.
- Riesgos: Espera docente, cambios solicitados, formato de entrega pendiente.
- Esfuerzo orientativo: 0.5-1 días.

## Esfuerzo agregado y calendario condicionado

| Fase | Días efectivos estimados |
|---|---|
| F1 | 3.5-7 |
| F2 | 2.5-4 |
| F3 | 2-4 |
| F4 | 4-7.5 |
| F5 | 4-8 |
| F6 | 3-5 |

Total base: **19-35.5 días efectivos** (aproximadamente 114-213 horas). Añadir alrededor del 20 % de contingencia: 22.8-42.6 días. Trabajo parcial de 3 horas/día aproximadamente duplica los días de dedicación. La falta de esquema, nuevas decisiones de autenticación, servicios de trazas o incidencias Azure puede superar este rango. No se deben sumar tiempos de reconstrucción como si fueran esfuerzo de implementación.

## Primera tarea técnica recomendada

Autorizar solo FIN-01: confirmar el esquema real con acceso de lectura autorizado o DDL sanitizado aportado por el propietario, y preparar una migración revisable probada en una base vacía local. No generar tablas/RLS a ciegas desde los doubles ni consultar Supabase sin autorización. Es el primer bloqueo para persistencia, dos versiones simultáneas y recreación fiable.

La aprobación de este plan no debe interpretarse automáticamente como permiso de crear recursos de pago, enviar notificaciones, cambiar RLS o introducir autenticación nueva: cada acción queda dentro del alcance que se autorice al iniciar su tarea.

## Conservar y retirar

El estado remoto, imágenes GHCR por digest, secretos, base de datos/respaldos y evidencias viven fuera del entorno AKS temporal. deploy-demo y destroy-demo son nombres de propuestas, no comandos disponibles. La retirada debe preservar recursos externos y verificar huérfanos; un stop no equivale a coste cero. Si observabilidad usa PVC, acordar antes si se exportan evidencias y se destruyen o si persisten con coste.

Para la defensa, reconstruir el día anterior y verificar íntegramente; reservar inicialmente 45-90 minutos condicionados para reconstrucción con automatización y prerequisitos listos, hasta disponer de medidas FIN-19. La misma sesión de Azure debe capturar CI/CD, Blue-Green, rollback y todas las señales para evitar recreaciones por falta de evidencias.

## Relación con backlog oficial

No se detectó un archivo de backlog oficial. No se crean tickets ni se modifica ninguna herramienta externa. Tras aprobación, mapear FIN-01..FIN-22 a los IDs oficiales y revisar prioridades, sin duplicar tareas completadas ni reemplazar el enunciado por este plan.
