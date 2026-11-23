# FIN-EVIDENCE-READINESS-01 — 22/11/2026

## 1. Resumen ejecutivo

**Diagnóstico completo; implementación no autorizada en esta iteración.**
Wordle dispone de aplicación React/FastAPI y PostgreSQL directo, Compose persistente,
perfiles kind/AKS, CI y publicación GHCR histórica, Blue-Green/rollback y observabilidad
ensayados localmente. El 22/11 se acreditó además infraestructura AKS real, dos nodos
Ready y retirada CLEAN, preservando backend remoto. **No se desplegó Wordle ni el stack
de observabilidad en ese AKS.** Tampoco se acreditó CD Azure ni reconstrucción completa.

La siguiente inversión útil es preparar evidencia local durable y cerrar los
prerrequisitos del CD ya escrito, antes de otra ventana Azure integrada. No rehacer
PostgreSQL, promoción, exporters o controladores. No hay porcentaje de avance calculado.

Fuentes: enunciado original de7 páginas leído con pypdf del runtime existente;
SHA256 e092aa234334b6cdb5187aeab4be7ee83d4fde92a6ff3698e5c40e3540185ea3,
idéntico al registrado en la matriz histórica. No se renderizó ni escribió una copia.
La normativa del PDF se usa como criterio académico, no como autorización operativa.
Se leyeron matriz/plan/dossier/brechas en docs/analysis/tfg-plan-001/, código y
configuración pertinentes, informes PG/FIN y tres informes AKS del22/11.
No conexión Azure/GitHub/GHCR, pruebas, builds, Docker/Kubernetes/Terraform ejecutados.

## 2. Estado académico actualizado

Etiquetas utilizadas:
- **IMPLEMENTADO**: presencia/relaciones verificadas en código; no garantiza runtime.
- **VALIDADO HISTÓRICAMENTE**: informe fechado de ejecución previa; se indica entorno.
- **VALIDADO EN ESTA AUDITORÍA**: lectura estática, existencia/inspección de archivos,
  importación de herramientas o inventario de superficies, nunca ejecución funcional.
- **PARCIAL**: implementación o evidencia falta para el alcance exigido.
- **PENDIENTE**: entregable/ejecución no acreditados.

FIN-01/02/03 permanecen aceptados según plan y decisiones del propietario; alcance
de seguridad es demo privada/supervisada/sintética, sin autenticación multiusuario.
FIN-04 figura técnicamente completa, pendiente de aceptación documental definitiva;
la excepción GHCR de rama está ratificada y el workflow coincide.
FIN-05 tiene preparación local y perfiles, falta aceptación integrada AKS.
FIN-06..15 tienen PASS local histórico, no PASS Azure por extensión.
FIN-16 dispone de nueva evidencia de backend/cuotas/red/Entra/infra del22/11:
prerrequisitos históricos superados no deben volver a implementarse.
FIN-17 sigue parcial: infraestructura creada/retirada, faltan servicios/señales y
ejecución del CD protegido. FIN-18 parcial: aplicación completa no ensayada en AKS.
FIN-19 parcial: destrucción real CLEAN, restauración local real; recreación/restauración
de aplicación en Azure y revisión de coste residual pendientes.
FIN-20/21/22: memoria final, ensayo/entrega y preguntas/vídeo no acreditados.

La matriz08/11 describe otro corte: Supabase, ausencia de migraciones/Ingress/señales
y porcentajes allí son históricos. Este informe no la sobrescribe ni cierra tareas.

## 3. Matriz de requisitos

Agrupación conserva **todos los A01-A58** originales; no cambia criterios.

| Requisitos | Estado real | Evidencia concreta y límite | Restante mínimo |
| --- | --- | --- | --- |
| A01 aplicación | IMPLEMENTADO; VALIDADO HISTÓRICAMENTE local; PARCIAL Azure | frontend/src/App.jsx, backend/app/routers/{game,stats}.py; PG-05/06 SQL/HTTP/UI | Juego persistente real en AKS y capturas asociadas |
| A02-A04 Docker/seguridad/Compose | IMPLEMENTADO; VALIDADO HISTÓRICAMENTE | backend/Dockerfile Python3.12/hash-lock/non-root; frontend/Dockerfile multietapa/Nginx; compose.yaml y compose.test.yaml; FIN-04/PG-05 | Reusar pruebas, fijar evidencia de release; no nuevo diseño |
| A05-A09 IaC/red/pool/modularización/estado | IMPLEMENTADO; VALIDADO HISTÓRICAMENTE Azure22/11 | infra/terraform, LIVE-DEPLOYMENT-APPLY y LIVE-DESTROY-EXECUTION: seis recursos, backend externo, nodos y CLEAN | Empaquetar evidencia sanitizada y coste diferido; no recrear solo para foto |
| A10-A15 YAML/Services/Ingress/ConfigMaps/Secrets/prácticas | IMPLEMENTADO; validado local histórico; PARCIAL cloud | k8s/aks, demo-kind, postgres, blue-green, observability, aks-full; Secret externo y ClusterIP | Admisión/CSI/Ingress/secretos efectivos en AKS |
| A16 pruebas CI | IMPLEMENTADO; VALIDADO HISTÓRICAMENTE remoto | ci.yml y FIN-04: guards55 offline+9 CORS+11 PG+12 frontend; telemetría adicional | Conservar resultado duradero de release, no repetir hoy |
| A17 imágenes/registro | IMPLEMENTADO; VALIDADO HISTÓRICAMENTE GHCR | publicador con GITHUB_TOKEN, SHA/digest, pull/runtime; FIN-04 | Asociar digests de images.lock al run/commit final sin confundir releases |
| A18 despliegue pipeline | PARCIAL | kind-smoke real histórico; azure-demo.yml y dispatch/runner preparados | Publicar y activar workflow protegido/OIDC/runner; ejecutar CD AKS |
| A19 secretos | IMPLEMENTADO para perímetro; PARCIAL evidencia AKS app | get_repository parametrizado, Secret externo, CORS, FIN-03/07 | Verificar inyección/logs cloud; no pedir login de jugador nuevo |
| A20 Blue-Green | IMPLEMENTADO; VALIDADO HISTÓRICAMENTE kind | promotion.py; FIN-08/09: blue→green, dos parejas y PG compartido | Repetir sobre release AKS; ambos colores actuales usan mismo binario |
| A21 rollback | IMPLEMENTADO; VALIDADO HISTÓRICAMENTE kind | rechazo previo y rollback real post-promoción503; informe y controller | Azure y evidencia durable; no afirmar cero downtime |
| A22-A30 observabilidad/alertas | IMPLEMENTADO; VALIDADO HISTÓRICAMENTE local; PARCIAL Azure | desglose sección4; FIN-10/15 | Targets/cAdvisor/NodeExporter/capacidad/alertas y pantallas AKS |
| A31 automatización completa | PARCIAL | CI/GHCR históricos, CD protegido preparado no validado remotamente | Recorrido commit→digest→despliegue→promoción→rollback→señales |
| A32-A37 fuentes y configs entregables | IMPLEMENTADO parcialmente para release final | repo identificable y fuentes actuales; azure-demo/aks-full/ejecutores aún sin seguimiento | Consolidar fuentes autorizadas antes de afirmar reconstrucción desde commit |
| A38-A40 PDF/portada/índice | PENDIENTE | No PDF propio en árbol inspeccionado; enunciado no cuenta | Memoria propia revisada |
| A41-A42 objetivos/stack | PARCIAL documental | README y planes suficientes para redactar | Consolidar capítulos con versiones reales |
| A43 diagramas | PARCIAL | Diagrama de datos previo en FIN-01R; prosa/runbook; no diagramas finales de todos los flujos | Arquitectura, datos, CI/CD y señales actualizados |
| A44-A49 capítulos Docker/K8s/CD/BG/observabilidad/seguridad | PARCIAL documental | Código e informes por componente | Redacción, trazabilidad y resultados cloud sin inventar |
| A50 funcionales/no funcionales/capturas/código | PARCIAL | Tests, tres capturas reales recuperadas y contratos | Catálogo de evidencias con fecha/entorno/release; no SLA inventado |
| A51 manual desde cero | PARCIAL | README, k8s/README, azure-demo, runbook y recovery | Ensayo independiente del procedimiento completo/restauración |
| A52 conclusiones/incidencias | PARCIAL | PG, DNS/probes, MFA, cuotas, plan/apply/destroy con tiempos | Capítulo final con límites y costes reales disponibles |
| A53 mejoras futuras | PARCIAL documental | Seguridad/retención/HA descritas como límites | Priorizar en memoria, sin implementarlas |
| A54 entrega Tokio | PENDIENTE | Sin recibo de plataforma inspeccionado | Acción del propietario al finalizar |
| A55 revisión funcional docente | PARCIAL/pende evaluación | App local histórica; no evidencia de revisión docente | Demo integrada y respuesta a cambios reales |
| A56-A58 preguntas/vídeo/profesionalidad/≤15 min | PENDIENTE | Sin preguntas o vídeo encontrado | Preguntas reales→guion→grabación/medición→entrega |

El PDF exige ambas estrategias (p4), lista completa de observabilidad (p4), pipeline
funcional (p5), capturas de funcionamiento y manual (p6), vídeo≤15 min tras preguntas
(p6-7). No exige KeyVault, HA PostgreSQL, service mesh, un proveedor de auth concreto,
cAdvisor en DaemonSet separado o pantallas de terminal artificiales.
La aspiración de producción del enunciado no convierte la demo privada aceptada en
servicio de producción: explicar límites honestamente y someterlos a revisión docente.

## 4. Componentes implementados

### Aplicación, datos y contenedores
Frontend React/JS: tablero6x5, teclado virtual/físico, estados/error/carga,
recuperación de intento incierto y mensajes victoria/derrota (App.jsx:15-99).
No SDK ni credenciales Supabase frontend; api.js usa URL configurable y /api en runtime.
No pantalla de estadísticas/ranking comprobada en UI: sí endpoints backend; el PDF
no exige añadirla para este Wordle.

Backend main.py: CORS exacto WORDLE_CORS_ORIGINS, GET/POST/Content-Type, sin credentials.
game.py: cinco letras A-Z/Ñ, evaluación en dos pasadas, máximo6, inválido no consume,
oculta palabra activa, transacción de intento y estadísticas.
repository.py: SQL parametrizado, FOR UPDATE partida/estadísticas, unicidad usuario;
database.py: psycopg3 async y pool acotado4, errores sanitizados, sin dotenv operativo.
usuario_id no autenticado; no aislamiento entre jugadores. /health solo liveness.

Baseline supabase/migrations/20261108000100_initial_wordle.sql: cuatro tablas y
secuencia; nombre histórico de carpeta no implica dependencia Supabase.
docker/postgres inicializa palabras/rolapp; FIN-02A semillas opt-in idempotentes,
FIN-02B pg_dump/pg_restore independientes con SQL+HTTP reales históricos.
PostgreSQL16 directo, una réplica, volumen Compose/PVC K8s; sin HA ni migración de datos
históricos. PG-05/06 probaron reinicios y conservación, no se tocaron ahora.

Conteo estático AST actual: tests backend20+19+6+10=55; CORS9; integraciónPG11.
Frontend12 casos según fuente/guard; no Playwright E2E existente.
Los scripts PG-05/06/FIN-02B/demo-kind/BG/observability sí son E2E SQL/HTTP reales;
Vitest usa respuestas simuladas y no sustituye esos ensayos.
No test ejecutado aquí. Herramientas Docker/kubectl/kind/Node localizadas, sin consultar motores.

### Kubernetes y CD
k8s/local conserva memoria; k8s/postgres runtime PG; aks/demo-kind separan cloud/local.
Deployments y Services por color; PostgreSQL/PVC único; probes, requests/limits,
non-root/capabilities/seccomp en aplicación; controller.yaml implementa Traefik real,
Ingress wordle.test→frontend→/api, no se confunde port-forward con controlador.
Services permanecen ClusterIP; port-forward solo abre acceso local al controlador.
Secret por referencias externas (no valores revisados); permisos/configuración de
exporters mayores que app requieren comprobación de admisión AKS.

ci.yml tiene7 gates más publicador:55 + 9, PG11, frontend12/build, Docker/runtime,
Kustomize, kind memoria y Terraform. PR/manual no publican; push solo main o rama
excepcional exacta publica tras7 gates, packages:write limitado al job.
No consulta remota nueva: runs históricos FIN-04, incluido42840960356, son evidencia
documentada. Run42841990340/HEAD4d56 fue comunicado por propietario; sin revalidación
remota en esta auditoría.
azure-demo.yml: workflow_dispatch, opt-in WORDLE_AZURE_ENABLED, rama/repositorio
exactos, self-hosted Linux wordle-azure, environment/reviewers, OIDC, serialización,
plan/hash/confirmaciones; archivo y scripts no versionados aún. No evidencia de
environment/runner/federación externos activos o de ejecución Azure desde Actions.

### Observabilidad: inventario específico

| Componente | Configuración/integración encontrada | Evidencia histórica y disponibilidad | Pendiente mínimo | Local / AKS |
| --- | --- | --- | --- | --- |
| Instrumentación OTLP | telemetry_app.py ASGI opcional por ConfigMap; spans, contador, gauge duración; logs sanitizados/traceID | FIN-10/15:request200 y500 exportados; JSON original citado no disponible en carpeta actual | Recapturar una request/traza correlacionada; no p95 ni SQL tracing afirmados | Local sí; misma prueba cloud |
| Collector | stack/collector.yaml:OTLPHTTP4318, memory limiter/batch→Tempo/Prometheus/Loki | Ensayo local histórico y código leído | Validar recepción/export en AKS | Local sí |
| Prometheus | prometheus.yaml:backends, collector, NodeExporter, kubelet-cadvisor; reglas | Informe6 targetsUP y series reales | Targets/labels reales en clúster final | AKS confirma endpoints gestionados |
| cAdvisor | scrape vía API nodes/proxy/metrics/cadvisor con token/RBAC | Métricas de12 contenedores históricas | Permisos/endpoint efectivo AKS | No segundo DaemonSet necesario |
| NodeExporter | DaemonSet resources.yaml:707+, /host/proc y /host/sys; sin privileged del contenedor | Métrica MemTotal local histórica | Admisión/hostPath/datos de nodos AKS | Local posible; host no es Windows |
| Grafana | resources/datasources/dashboards.yaml y dashboard.json;8 paneles, Prometheus/Loki/Tempo | API/proxy local PASS; no screenshot histórico de dashboard encontrado | Captura real con datos/unidades/ventana | Local suficiente para UI; cloud para datosAKS |
| Loki/logs | OTLP backend y agentesfilelog Nginx; correlación y eventospromotion | Informe347backend/490frontend/32eventos | Consulta visible y export durable de evidencia | Local sí |
| Tempo | trazasOTLP del Collector y datasourceGrafana | IDs de traza históricos registrados | Abrir span real y correlación error/éxito | Local sí |
| Alertas métricas | WordleUnavailable, Prometheus→Alertmanager | firing/resolved registrados en informe | Conservar respuesta/query/receptor de prueba nueva | Local sí |
| Alertas logs/notificaciones | Loki WordleCriticalLog→Alertmanager→receptor HTTP notifications | firing/resolved de ambas clases entregados HTTP históricos | Captura/reporte de entrega y recovery, no solo firing | Receptor interno suficiente según alcance; no afirmar correo humano |
| Capacidad/E2E | run_observability.py/validation.py integran promoción/fallo/restorepermisos/SQL/métricas | Informe1023 requests/110fallos inducidos, sin OOM observado | Medición actual y capacidad realAKS | No estrés/SLA/HA inventados |

Retención de señales emptyDir, Prometheus1h/128MB, Tempo30min y Loki24 h configurados:
eliminar clúster pierde señales; se requiere exportar antes. OTLP best-effort/cola256,
sin entrega garantizada. Namespace observability permite PSS privileged para hostPath;
eso no equivale a todos los contenedores privileged. Evaluar admisión/RBAC en sesión
AKS, no abrir permisos preventivamente en esta auditoría.

## 5. Componentes pendientes

No faltan implementaciones base de juego, SQL, Ingress, promoción, Collector/exporters.
Faltan publicación/activación del CD existente, validación integrada de aplicación
en AKS, reconstrucción con restauración allí, inventario durable de evidencias,
diagramas/memoria final y revisión/vídeo/entrega docente.
FIN-04 solo requiere aceptación documental pendiente, no reabrir política GHCR.
No convertir Node 20/24 de acciones en vulnerabilidad confirmada: mantenimiento histórico.

## 6. Bloqueantes reales (cinco)

1. **Release reproducible incompleta**:9 archivos versionados modificados y79 sin seguimiento.
   azure-demo.yml, aks_run.py, azure_dispatch.py, aks-full y images.lock no versionados.
   HEAD publicado solo no reproduce el trabajo actual. Autorizar consolidación selectiva,
   preservando históricos/secretos; no commit en este diagnóstico.
2. **CD Azure no acreditado**:environment/reviewers, runnerLinux con salida autorizada y
   federaciónOIDC/permisos no verificados como activos. Publicar YAML solo no lo resuelve.
   Resolver reutilizando azure-demo, sin otra plataforma; requiere decisiones/permisos.
3. **Falta integración cloud completa**:ensayo22/11 fue infraestructura, no workloads,
   CSI/PVC, PG, Ingress, rollback, exporters/alertas. Solo sesión AKS autorizada lo cierra;
   un nuevo ensayo local reduce riesgo pero no sustituye esta evidencia.
4. **Dossier visual/técnico no durable todavía**:3 capturas recuperadas, sin inventario
   final; carpetas JSON finales BG/observability citadas están vacías. Playwright carga
   con Node pero defaultChromium no encontrado. Falta capturador con Edge y verificación
   real de lanzamiento/PNG; no instalación necesaria demostrada todavía.
5. **Entrega académica no producida**:PDF/diagramas/manual validado/recepción docente y
   preguntas/vídeo. No es fallo técnico de aplicación; exige redacción y acciones humanas.

No bloquean por sí solos: ausencia de pantalla PortalAKS, no tener autenticación nueva,
no tener HA o notificaciones SaaS; conservar límites acordados y evaluar con docente.

## 7. Evidencias existentes

- Informes FIN-01/02/03 y PG-04/05/06/07:SQL real, persistencia, restauración, negativos,
  pruebas; corpus de demo5 palabras y usuarios sintéticos. Reusar con fecha/alcance.
- FIN-04:runs remotos, recuentos por guardas, pulls/digests/runtime; artifacts retención7 días,
  vigencia actual no consultada. En memoria no depender exclusivamente de artifact temporal.
- FIN-08/09 y FIN-10/15:relatos de ejecución detallados y código reproducible.
  **No equivalen hoy a disponer de sus JSON originales**:en %TEMP%, carpetas exactas
  wordle-fin0809-evidence-i_c5crtb y wordle-fin1015-evidence-6gsrj2ag existen vacías,
  también sin archivos descendientes. No se declara inexistencia de otras copias.
- LIVE-DEPLOYMENT-APPLY/DESTROY-PLAN/DESTROY-EXECUTION:resultados sanitizados hoy.
- Tres capturas externas abiertas y verificadas visualmente. Base privada local:
  %USERPROFILE%/.codex/visualizations/2026/10/12/01a1309a-0ba8-7e63-8a01-3b60486d1fd7/.
  No nuevas imágenes creadas.

| Archivo | Imagen observada | Formato real / tamaño | SHA256 |
| --- | --- | --- | --- |
| pg05-ui-win.png | Victoria en2 intentos, colores/teclado y Nueva partida | **JPEG**,304x992 | 2df520e3aed5321e97e9175e5551ed0ca0e6d1b92fc72bfb76ce682f07aec99c |
| pg05-ui-loss.png | Derrota tras6 intentos y solución final | **JPEG**,304x992 | 4a410f57b13ac6f661ec3444edba24aca286cd3efa10d59b4ae70032b5debf67 |
| pg06-ui-win.png | Victoria desktop con colores/teclado | **JPEG**,1264x1086 | 547183420295984d2c579fcbbefba8a2739e200f7021d80172d19b359a36afed |

Extensión .png no corresponde al formato real, confirmado por Pillow; no convertidas
ni renombradas. Admitir JPEG como original o exportar PNG auténtico en incremento futuro,
preservando original y registrando derivación. La fecha del directorio no acredita
fecha de ensayo; asociar a informePG05/06, no inventar metadatos de captura.
Las imágenes no prueban por sí solas SQL/entornoAKS: se enlazan con los informes.
No imágenes/PDF propio/vídeo encontrados dentro de fuentes del repo inspeccionadas,
excluyendo .git/node_modules/.venv/dist/.terraform/cachés; no búsqueda indiscriminada
de documentos ajenos del usuario.

## 8. Evidencias pendientes

Catálogo público sanitizado por release con EV→A→archivo→fecha/entorno→commit/digest
y checksum. Recuperar originales si existe otra copia; si no, nuevo ensayo kind de
observabilidad/BG con export durable y capturas. No inventar JSON faltantes desde relato.
Páginas Grafana/Loki/Tempo/Prometheus y entrega de alertas requieren runtime de ensayo
futuro: no están vivas porque haya configuración. Logs/timing del cicloAzure22/11 ya
permiten demostrar IaC/retirada; no recrear Azure solo para screenshotPortal.
La UI móvil original304px es legible a escala adecuada pero mejorar captura consistente
en próxima tanda, no modificar frontend para ello.

## 9. Matriz de screenshots (EV existentes)

A=Playwright propuesto; B=navegador/escritorio; C=registro técnico; D=manual cuando necesario.
“Disponible” se refiere a evidencia, no servicio vivo. Ninguna captura generada aquí.

| ID / requisito | Pantalla o evidencia | Herramienta | Automática/manual | Disponible ahora | Dependencia | Prioridad |
| --- | --- | --- | --- | --- | --- | --- |
| EV-01 A01/50/55 | Inicio/curso/invalidación/victoria/derrota/reinicio desktop+móvil | A Playwright+Edge | Automática tras comprobar lanzamiento |3 capturas históricas; curso/errores pendientes | Runtime PG sintético | P0 |
| EV-02 A02-04/34/44 | Dockerfiles, imagenID/tamaño, healthy/proxy | C scripts/JSON | Automática técnica |Código/informeFIN04 | Docker futuro; no foto terminal necesaria | P1 |
| EV-03 A05-09/45 | IaC/apply, nodos/seguridad, backend | C informes; B Portal opcional | Técnica ya disponible; visual opcional |22/11 técnico, no PortalPNG | Azure solo si se desea visual en próxima sesión | P1 |
| EV-04 A10-15/45 | Ingress/pods/PVC y juego por proxy | C kubectl+HTTP; A UI | Automática |Código/localhistórico; aplicación cloud pendiente | kind o AKS autorizado | P0 |
| EV-05 A16-18/31/36/46 | Actionsjobs, SHA, GHCRdigest, CD | B navegador; C resultados | Automática con sesión; humano si login/MFA |Runhistórico; no screenshot/CIazure | Publicación/activaciónCD y accesoGitHub | P0 |
| EV-06 A20/47 | Blue activo→Green y selectores/versión | A UI + C controller | Automática |Informe local, JSON citado no disponible | Ensayo integrado/captura sincronizada | P0 |
| EV-07 A21/31 | Fallo postpromoción→rollback, datos conservados | A UI + C eventos/SQL | Automática |Informe local; sin screenshot | Mismo ensayo que EV06 | P0 |
| EV-08 A22/30/48 | RequestID/span real Collector→Tempo | A Grafana/Tempo + Cquery | Automática |Config/informe; no PNG | Stackcon datos reales | P0 |
| EV-09 A23/26/27 | Prometheus targetsUP, nodo/contenedor | A Prometheus/Grafana+Cquery | Automática |Config/informe; no PNG | Stack local; endpointAKS pendiente | P0 |
| EV-10 A24/30 | Dashboard8 paneles/unidades/ventana | A Grafana | Automática |ProvisioningJSON; no PNG | Datos/receptor y login demo | P0 |
| EV-11 A25/30 | Logsfrontend/backend/error correlacionados | A GrafanaExplore+CLogQL | Automática |Config/informe; no PNG | Mismo ensayo | P0 |
| EV-12 A28-30 | firing→webhookrecibido→resolved métrica/log | A UI+C receptor/events | Automática |Informe; sin JSON original en ruta | Fallo controlado autorizado desechable | P0 |
| EV-13 A19/49 | CORS/perímetro/Secretrefs/negativos | C tests/documento | Automática técnica |FIN03/07 | No capturar Secret ni datos reales | P1 |
| EV-14 A01/50/51 | Seed/restauración/SQL/reinicio | C run_fin02a/b; A UIpostrestore | Automática |Informes/3UIhistóricas | PG desechable para nueva tanda | P1 |
| EV-15 A05/09/51/52 | Deploy/retiradaCLEAN/reconstrucción | C informes/estado/tiempos | Automática supervisada |Cicloinfra22/11; recreaciónapp pendiente | FuturoAKS con restore y permiso separado | P0 |
| EV-16 A32-54 | PDF/diagramas/índice y release | C PDF/repo; B entrega | Generación futura; entrega humana |Fuentes, no PDFfinal | FIN20 y revisiónpropietario | P0 |
| EV-17 A55-58 | Preguntas/vídeo≤15 min | D grabaciónhumana+Cduración | Manualhumana |No acreditado | Docente/FIN21-22 | P0 |

No Kubernetes Dashboard encontrado; no instalarlo para fotografiar recursos.
Portal no obligatorio como medio si evidencia técnica suficiente; añadir en próxima
ventana solo si aporta valor al mismo ensayo, sin recreación exclusiva para capturas.

## 10. Capacidades de captura automática de Codex

| Capacidad | Nivel comprobado en esta auditoría | Límite |
| --- | --- | --- |
| Playwright del proyecto |No instalado en frontend ni .venv; sin config/testsE2E | No confundir Vitest/jsdom con navegador |
| Playwright de herramientas |1.62.1 y core presentes; require desde Node estándar exitoso | No dependencia nueva del proyecto |
| Runtime Node REPL import |Import falla SyntaxError por exportdefault | Es problema de esa ruta de importación, no ausencia de paquete |
| Chromium |Caché local chromium-1248/headless/ffmpeg presentes | executablePath esperado por paquete no existe; compatibilidad/lanzamiento no probados |
| Edge |msedge.exe presente | No lanzado en auditoría; proponer channel msedge |
| Navegador automatizado |cua.getState funciona: IAB disponible, sin pestañas | No navegar/login/Portal/Grafana aquí |
| EscritorioWindows |@oai/sky importado y list_windows exitoso(5 ventanas) | No control de ventanas ni captura probados; no títulos privados publicados |
| PNG/viewport/fullPage/esperas |API documentada y factible con Playwright | No ejecución de captura/viewport/fullPage verificada; no afirmar PNG producido |
| Guardado de imágenes |3 originales existentes legibles; filesystem autorizado en tarea futura | Única escritura actual es este informe |
| AzurePortal/GitHub |Automatización B probable con sesión y pantalla específica | MFA/CAPTCHA requieren humano; no visitarAzure ahora |
| Grafana |Automatizable con A, cuenta sintética externa y datasourcereal | Servicio no levantado; login/captura no probados ahora |

La enumeración de ventanas demuestra acceso de descubrimiento, no control de Windows
de extremo a extremo. No se inspeccionaron otras aplicaciones o pantallas privadas.

## 11. Estrategia Playwright recomendada (NO implementada)

Incremento acotado futuro: script Node externo o en scripts/evidence, usando Playwright
ya instalado y Edge explícito, sin instalarlo en frontend si no resulta necesario.
Primero smoke de lanzamiento/contexto/capturaPNG con endpoint local autorizado.
Contexto aislado, desktop1440x1000 y móvil390x844, localees-ES/UTC; viewport y fullPage
registrados por separado. Esperar roles/textoestado, respuestaHTTP y condición
SQL/consulta pertinente: no sleeps fijos como criterio de éxito.
Reutilizar seed/fixtures desechables y ejecutor observability; guardar captura cuando
el estado real pase assert, no construir una página que simule victoria o dashboard.

Pasos:ejecutar escenario→assertHTTP/estado/release/query→captura screenshotPNG→validar
cabeceraPNG/dimensiones/legibilidad→manifiesto EV/A/UTC/entorno/commit/digest/rango/
resultado/hash→exportdurable. Fallo produce FAIL/noevidencia, no captura etiquetadaPASS.
No secretos en argv/URL/logs/PNG. AccesoGrafana con contraseña sintética por entorno
privado; no persistir sesión sensible. Revisión humana de cada imagen antes de publicar.
Ajustar la pausa --inspect-seconds del runner a captura coordinada dentro del límite
existente5min; no extender procesos ni modificar limpieza sin necesidad demostrada.
No esperar que las señales sobrevivan al destroy.

Calidad:mismo ancho por familia, texto visible al100%, sin diálogos/erroresinesperados,
origen/local/kind/AKS y release en manifiesto/pie externo, leyendas y ventana reales,
sin IPpersonal/IDsinnecesarios/cuentas, no cuadros de Secret/plan/state completos,
sin datos inventados. Sanitización/recorte derivados documentados; conservar original
privado. Logs/recuentos/testresult adecuados como C, no screenshots de terminal forzados.

## 12. Reutilización de evidencias AKS del22/11

| Aspecto | Evidencia técnica existente | Captura visual | ¿Exige nuevoAKS? |
| --- | --- | --- | --- |
| Terraform y backend |Plan 6 create/hash, applyexit0, state6→0, locking/metadatos y backendconservado | No encontrada | No para acreditar ciclo ya ejecutado |
| Red/identidad/seguridad |Overlay/Sweden, Entra/RBAC, /32, cuentasoff/RunCommandOff; getters sanitizados | NoPortal | No para repetir esos hechos |
| Nodos |kubectl real: 2 Ready/v1.35.9/D4s_v5 | NoPNG | No; tabla/informe ya aportan evidencia |
| Destrucción |applydestroyexit0, group existsfalse ambos, AKSausente, state0 y leasefree | NoPNG | No; no existe ya pantalla de clusteractivo |
| Tiempos |Creación11:37:15→11:42:45; retirada12:01:02→12:07:28Madrid; postflight12:07:42 | Texto suficiente | No |
| Juego/PVC/Ingress/PG/BG/señales en AKS |No ejecutados ese día | Pendientes | Sí, validar todo conjuntamente |
| Recreación/restauraciónappcloud |No ejecutada | Pendiente técnica antes quefoto | Sí, permiso y reserva temporal propios |

No llamar ciclo anterior FIN19completo: acredita retirada de infraestructura, no
reconstrucción de Wordle/PG/observabilidad. Tiempos infra medidos no predicen runtimeapp.
Cargos devengados/backend siguen posibles; coste final no consultado.

## 13. Camino crítico mínimo (mantiene FIN existente)

| Bloque / dependencia | Objetivo/requisito/estado | Trabajo mínimo y evidencia | Entorno | Riesgo |
| --- | --- | --- | --- | --- |
| E1→E2/E3 |FIN01-15, EV01/06-12:funciónlocal histórica | Capturador y un ensayo integrado PG/Ingress/BG/observability; recuperar JSON/PNGs en ubicación durable; no reimplementarapp | Local desechable | LanzamientoEdge, timingalertas/capturas |
| E2 tras revisiónfuentes |FIN04/17 A18/31/32-37:CDparcial | Consolidación selectiva autorizada del trabajo ya probado; identificarrelease/digests/config actual; no gitaddglobal | Local/GitHub futuro | Nuevos archivosCD no están enHEAD |
| E3 en paralelo conE1 |FIN16/17 CDexterno no acreditado | Acordar runnerLinux/salidarestringida, OIDC/environment/reviewers y publicaciónworkflow; verificar guardas y ausencia de IPabierta | Config externa autorizada | Permisos/disponibilidad; no resolver con0.0.0.0/0 |
| E4 trasE1-3 |FIN17/18 A18/20-30/31:cloud pendiente | Una ventana supervisada:commit→digest→deployapp→PG/PVC→UI→promoción/rollback→targets/logs/traza/alertas→exportevidencias→retiradaaprobada | AKS | AdmisiónhostPath/RBAC/cAdvisor/CSI/capacidad y plazo |
| E5 conE4 si cabe, si no aparte |FIN19 A51/52:restorelocalPASS, cloud pendiente | Backup sintético externo→retirada→recreación/restauración→SQL/HTTP y señales→retirada; medirtiempo/remanentes | AKS | No sacrificar limpieza por meter dos ciclos en4 h |
| E6 empieza ya en paralelo |FIN20 A38-53:documentalparcial | Diagramas y memoria con evidencias existentes, completarresultados E4/E5, manualseguido desde cero, PDFrevisado | Local | Inconsistenciahistorica y datosprivados |
| E7 trasE6/docente |FIN21/22 A54-58 | Ensayo, entrega/recibos, preguntasreales, vídeoprofesional≤15 min | Humano/local | Esperadocente sin plazo controlable |

E1 reduce riesgo de cloud; E3 decide si el CD puede demostrarse antes de reservar
ventana. No reemplazar pipeline por despliegue manual solo para cerrarA18.
No proponer nueva plataforma/HA ni authempresarial. No ampliarAzureporcapturas aisladas.

## 14. Estimación de esfuerzo

Estimación profesional, no medición ni compromiso, usando implementaciones existentes:

| Trabajo previo a sesiónAzure final | Implementar/ajustar | Validar | Capturar/archivar | Total efectivo |
| --- | ---: | ---: | ---: | ---: |
| CapturadorEdge y catálogo mínimo |1-1.5h |0.5h |0.5h |2-2.5h |
| Reensayo local integrado único, originalesdurables |0-0.5h |0.5-1h |0.5h |1-2h |
| Revisión/consolidaciónrelease+CDexterno existente |1.5-3h |1-1.5h |0.5h |3-5h |

**Preparación para sesión final:6-10 h efectivas**, redondeadas; E1/E3 parcialmente
paralelizables. No incluye esperas por permisos, disponibilidadrunner o confirmaciones.
Si no puede obtenerse runner/federación/reviewers, el plazoCD queda indeterminado:
no prometer que6-10 h resuelven una dependencia externa.

Ventana finalAzure:reservar4 h con retirada desdeT+160; ensayo de aplicación/observabilidad
puede exceder primer ciclo de infraestructura medido. Si reconstrucción/restore no cabe con margen,
otra ventana acotada60-120min requiere autorización; no asumir cierre en una sola.
No sumar dos veces pruebas/capturas: se ejecutan juntas en E1/E4.
Memoria PDF/diagramas/manual/trazabilidad: **12-18 h efectivas** (redacción8-12,
composición/revisión4-6); puede empezar antes deE4. Vídeo/ensayo2-4 h adicionales
tras preguntas, sin incluir espera docente. Ajustar estimación tras E1, no diez días
por defecto ni promesa de terminarlo todo en una jornada.

## 15. Capítulos de memoria redactables

Índice acorde conp5-6:
1.Portada e índice — redactable ahora, autor/título confirmados por propietario.
2.Descripción/objetivos/alcance y stack — ahora; PostgreSQL directo, no Supabase vigente.
3.Arquitectura y flujos de datos/confianza — ahora; diagramasestadoactual vs objetivo.
4.Docker/Compose/persistencia/migraciones — ahora con PG05/06/FIN02.
5.Kubernetes/Terraform/AKS — infraestructura22/11 redactable; appcloud parcial.
6.CI/CD e imágenes — CI/GHCR ahora; CD Azure depende E3/E4.
7.Blue-Green/rollback — implementación/resultadoslocales ahora; cloud pendiente.
8.Observabilidad/alertas — configs/resultadoslocales ahora; datoscloud/capturas pendientes.
9.Secretos/seguridad — ahora con perímetroprivado y límitesusuario_id explícitos.
10.Requisitosfuncionales/nofuncionales/capturas/código — parcialmente ahora, 3 imágenes;
   esperar E1/E4 para catálogo completo; sin latencia/SLA inventados.
11.Manualdesde cero/backup/restore/retirada/reconstrucción — local+infra ahora;
   terminar tras E5 y sesión independiente.
12.Resultados/conclusiones/incidencias — parcial, reutilizar DNS/probes/MFA/región/
   creación y retirada; costesdefinitivos/reconstrucción pendientes.
13.Mejorasfuturas — ahora, no implementarlas.
14.Anexosseleccionados — tests/runs/inventarioEVsin secretos.
Entrega/recibos, correccionesdocentes y vídeo dependen revisiónexterna.
No redactado PDF en esta iteración, ni memoria completa.

## 16. Riesgos

Pérdida de pruebas enTEMP, artifactsActions7 días, versiónreportadadistinta deldigestactual,
fuentesCDsinversionar, extensiónJPEGerrónea, snapshotsnoasociadosafecha, infraestructura
confundida conapp, UIenmemoria confundida conPG, PSS/RBAC/CSI AKS sinvalidar,
cuota/política/MFA/IP variables y coste sincap. No nuevosrecursos ni remediosautomáticos.
El informeFIN04 cita una publicación782d37 y digestsanteriores; images.lock fija4d56
y otrosdigests: no es fallo demostrado, son releases diferentes que requieren asociación
correcta del dossierfinal. No recuperarvaloresprivados ni reabrirarquitecturapor ello.

## 17. Propuesta de siguiente iteración

**FIN-EVIDENCE-CAPTURE-LOCAL-01**, dentro de FIN20 y soporte FIN18:
autorizar capturador sencillo Playwright+Edge, catálogoEV/metadata y un ensayo local
integrado desechable con export durable, conservando PG05/06. Reutilizar3 originales,
no fabricar pantallas, no instalar dependencias si Edge/runtimeexistente bastan.
En paralelo como decisión del propietario: confirmar vía operativa para CD protegido
ya preparado (runner/OIDC/environment), sin provisionarlo ahora.
Criterio de salida:PNGsauténticos+JSONreales+checksums/commit/digests, señales/rollback
verificados, herramientasdecaptura probadas; entonces consolidaciónautorizada y E4.
No comienza ninguna de esas tareas con este informe.

## 18. Integridad Git y alcance de validación

Inicial:rama codex/pg01-07-consolidation; HEAD4d56cf265cc5f0af8c72c64f2a93373660e8f122; índice vacío.
88 pendientes:9 versionadosmodificados y79 sin seguimiento. Comparación final SHA256alpie.
Archivosversionadosmodificados previos:informeFIN04, planFIN, infra/terraform/{README.md,
backend.hcl.example,main.tf,terraform.tfvars.example,variables.tf},
k8s/observability/{run_observability.py,validation.py}.
No actualizados matriz/plan/dossier ni estadosFIN oficiales.

VALIDADO EN ESTA AUDITORÍA:PDFtexto/hash, presencia/código/configuraciones, recuentosAST,
3imágenesabiertas/formato/dimensiones/checksum, rutasdeJSONvacías, herramientas/paquetes/
cachés/importNode e inventariosUI. **Ninguna validación funcional nueva.**
No tests/builds/renderKustomize/motoresDocker/Kubernetes/Terraform/Azure/serviciosremotos.
No instalación, entorno, limpieza, credenciales, permisos/políticas ni commits/push.
Única escritura autorizada:este informe; sincapturasnuevas.

Cierre UTC 2026-11-22T11:30:10.990679+00:00: 88 pendientes preexistentes idénticos por SHA-256; HEAD inicial/final 4d56cf265cc5f0af8c72c64f2a93373660e8f122; índice vacío. 89 pendientes finales, solo este informe nuevo. git diff --check exit 0. Advertencias LF/CRLF preexistentes en FIN-04, plan FIN y k8s/observability/run_observability.py y validation.py, sin corregir. Sin staging, commits ni push.
