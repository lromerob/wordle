# FIN-10 a FIN-15 — Observabilidad integrada

10/11/2026. Rama `codex/pg01-07-consolidation`; HEAD preservado `774405e6b92c33b438509832c6722605fee7d289`. **Resultados PASS exclusivamente locales**; no acredita AKS ni una ejecución remota CI.

| Tarea | Resultado y evidencia real |
|---|---|
| FIN-10 | **PASS local**. Adaptador ASGI opcional → OTLP/JSON → Collector → Tempo/Prometheus/Loki. Span real `POST /game/intento`, HTTP 200, release Green; trace ID `4b4b75b116530f771329ed08c9a1ea77`. Error intencionado `GET /game/{partida_id}`, HTTP 500, STATUS_CODE_ERROR; trace ID `61990041ce3138a747a88712478fe18f`. Siete series del contador HTTP y siete de duración exportadas. |
| FIN-11 | **PASS local**. Seis targets UP: Prometheus, Collector, dos backends reales, Node Exporter y kubelet-cAdvisor. Doce series de memoria de contenedores Wordle; MemTotal del nodo 16465416192 bytes. cAdvisor procede del kubelet real, sin DaemonSet cAdvisor privilegiado. |
| FIN-12 | **PASS local**. Consulta Loki devolvió 347 logs backend y 490 frontend en la muestra inicial; agentes filelog de Collector leen solo el archivo operativo compartido de Nginx. También 32 eventos de despliegue, incluyendo selector y rollback, consultados en Loki. Error 500 consultado después. |
| FIN-13 | **PASS local**. Dashboard `wordle-demo` de ocho paneles y datasources Prometheus/Loki/Tempo provisionados desde cero. Grafana API confirma el dashboard; consultas a métricas y logs mediante su proxy devuelven datos. Links de trace_id desde logs a Tempo; sin configuración manual ni captura visual de navegador. |
| FIN-14 | **PASS local**. Prometheus evalúa WordleUnavailable y Loki ruler WordleCriticalLog. Alertmanager entregó POST HTTP reales firing y resolved a un receptor independiente de demo; emparejamiento por alertname y startsAt. No es solo evaluación de reglas. El receptor es externo a los motores de alertas y permanece dentro del clúster privado: no se afirma envío a correo, Slack o servicio corporativo. |
| FIN-15 | **PASS local**. Promoción, rechazo de candidata y rollback real ejecutados con el stack completo; eventos visibles en Loki, métricas por release y spans de operaciones. Fallo de permisos DB reversible, recuperación, datos idénticos, medidas CPU/memoria/disco y ausencia de OOM en contenedores inspeccionados. Capacidad/endpoint AKS definitivos siguen pendientes de FIN-18. |

## Implementación

Overlay separado `k8s/observability`, reutilizando Blue-Green/PostgreSQL/Traefik existentes. Sin modificar esos archivos, la aplicación ni dependencias/lock. El adaptador `telemetry_app.py` se monta por ConfigMap y arranca con python -m uvicorn solo en este perfil; conserva rutas/cuerpos/status del juego y añade X-Trace-Id y /metrics operativo. Exporta spans HTTP de servidor, contador acumulativo y duración de la última observación por ruta/método/status, con cola acotada y sin SDK ni dependencias nuevas. No es histograma ni p95 ni trazado SQL automático. /metrics distingue proceso vivo y acceso de lectura a PostgreSQL.

Collector recibe OTLP y exporta trazas a Tempo, métricas al exporter Prometheus y logs a Loki mediante su endpoint OTLP nativo. Frontend registra únicamente nivel, servicio/release, clase de ruta, método, status y trace ID; un sidecar Collector filelog lee ese archivo compartido, sin montar logs del host. Backend no exporta URL, query, headers, body, usuario_id, ID de partida, DSN, excepción SQL o solución del juego. El ejecutor exporta a Loki eventos sanitizados de promoción/rollback. Los spans/ejemplos reales y respuestas de consultas se conservaron en los JSON de evidencia; no aparecen palabra_secreta ni Authorization en esos artefactos.

Versiones fijadas y descargadas: Collector contrib 0.165.0, Prometheus 3.16.0, Alertmanager 0.35.0, Node Exporter 1.12.1, Grafana 13.3.0, Loki 3.6.20 y Tempo 2.10.10 monolítico. Tempo es el único destino adicional necesario para consultar trazas. Sin Helm, operadores, Promtail ni SaaS.

## Ejecución y alertas comprobadas

Ejecución final `wordle-fin1015-d8e779e3`, Kubernetes 1.35.0, 13:52:00–13:58:07 UTC, exit 0. Blue → Green, candidata Blue no sana rechazada, promoción posterior a Blue, fallo funcional 503 y rollback automático a Green. Las conmutaciones aparecen en Loki, no solo en el fichero del ejecutor. Partida ganada y mismo PostgreSQL/PVC compartido preservados.

Después se esperó estado normal de alertas y se revocó temporalmente SELECT en partidas **solo al rol app de la DB nueva desechable**. Un POST real devolvió 500 y el muestreo capturó también lecturas 500; ambas clases de alerta se activaron. La concesión SELECT se restauró mediante finally, se recuperaron targets y lectura de la victoria y se comprobó la igualdad del dataset. No hubo migración ni modificación de PG-05/PG-06.

Entregas registradas por el receptor HTTP (UTC):

- WordleCriticalLog firing: 13:57:17; resolved: 13:57:52. Mismo startsAt 13:57:12.076.
- WordleUnavailable firing: 13:57:19; resolved: 13:57:29. Mismo startsAt 13:57:14.283.

Disponibilidad usa scrape y readiness de dependencia; la alerta de log cuenta ERROR en ventana 20s con for 5s. Evaluación/scrape 5s, group_wait 0s, group_interval 5s y repeat_interval 1h limitan ruido. Es una regla acelerada para ensayo, no un umbral de producción.

El muestreo integrado registró 1023 peticiones y 110 fallos durante los escenarios de avería; las diez últimas fueron 200/Green. No se afirma cero downtime. El dato de fallo/recuperación y sus ventanas están en traffic.json y summary.json.

## Capacidad, almacenamiento y permisos

Aplicación + observabilidad: 1.3 CPU y 1248MiB solicitados; kube-system sumó 0.95 CPU/290MiB. Muestra final real de carga pequeña: 0.1749 cores y 939802624 bytes de working set (~896.3MiB) de Wordle/observabilidad; no es pico ni estrés. Nodo kind: 22 CPU y 16079508Ki de memoria asignable. No se observó OOMKilled en los estados inspeccionados. El filesystem subyacente compartido de Docker Desktop mostró 22.55GB usados y ~1003.55GB disponibles; no se atribuye todo ese uso al stack. PostgreSQL de ensayo ocupó 7986199 bytes.

Prometheus: retención 1h/128MB. Loki: retención configurada 24h; Tempo: 30m. Datos de observabilidad en emptyDir acotados (1Gi por volumen data, tmp 64Mi; logs frontend comparten tmp de 32Mi). Grafana se reprovisiona por ConfigMap y su cuenta demo usa Secret sintético externo. No se probó el envejecimiento completo de esas ventanas: todos los datos de señales desaparecen al eliminar el clúster. JSON sanitizados del host sí se conservan. No es backup/HA de observabilidad.

Prometheus usa ServiceAccount con lectura de nodos y GET nodes/proxy/nodes/metrics, y descubrimiento de Pods solo en el namespace de observabilidad. El proxy kubelet requiere un permiso de alcance mayor que una única ruta /metrics: revisarlo en AKS. Node Exporter no es privileged, no usa hostNetwork/hostPID, monta /proc y /sys read-only, sin montar rootfs. El namespace observability admite hostPath mediante excepción PodSecurity; los contenedores siguen non-root, filesystem read-only y capacidades eliminadas. No se presenta esa excepción como aislamiento de producción. Los demás procesos no montan token de ServiceAccount. Services ClusterIP; accesos al host únicamente por port-forward 127.0.0.1.

Propuesta AKS: mantener inicialmente los dos D4s_v5 y discos OS 64Gi ya parametrizados en Terraform, más PVC PostgreSQL del perfil AKS y dimensionamiento explícito de señales si se requiere retención durable. Las reservas locales caben numéricamente en ese diseño, pero AKS tiene reservas/add-ons, un exporter por nodo y límites distintos: medir allí antes de reducir tamaño o prometer capacidad. Coste futuro = horas de dos VM + dos discos OS + disco PG/señales si se añaden + IP/Load Balancer/salida + estado remoto. Free no elimina esos cargos. Sin cotización regional ni presupuesto aprobado no se da un importe cerrado ni se crea ningún recurso.

## Reproducción e inspección

Con Docker, kind, kubectl y Python existentes, desde la raíz:

```powershell
.venv\Scripts\python.exe -B k8s/observability/run_observability.py --run-disposable-kind
```

El comando completa pruebas y limpieza automática. Evidencias finales reales: `%TEMP%/wordle-fin1015-evidence-6gsrj2ag/{events.json,traffic.json,summary.json,observability.json}`. Incluyen spans, métricas, eventos consultados en Loki, estado de paneles, recursos y notificaciones; no kubeconfig ni contraseñas. Un directorio alternativo vacío, fuera del repo, puede indicarse con --evidence-dir.

Para explorar Grafana antes de la limpieza, introducir una contraseña sintética nueva de al menos 32 caracteres en WORDLE_GRAFANA_DEMO_PASSWORD usando entrada oculta/entorno protegido y añadir --inspect-seconds 120 (máximo 300). El ejecutor muestra solo URL loopback y usuario demo; no muestra la contraseña. Esa pausa y forward se ejercitaron durante un segundo en la ejecución final. Al terminar retira el forward y su clúster. No usar contraseñas personales/producción ni literales en el historial del shell.

Pruebas focalizadas offline: `.venv\Scripts\python.exe -B k8s/observability/test_telemetry.py` (cuatro casos, todos aprobados). No se repitieron las 87 pruebas de Wordle: lógica y código de aplicación intactos. Render Kustomize de 63 objetos y referencias/requests<=limits correctos; validador real del Collector, imports en imagen, dry-run server, HTTP/SQL y consultas reales aprobados; git diff --check correcto.

## Archivos y límites

Nuevos únicamente bajo `k8s/observability/` (overlay, patches, adaptador, agentes, configs Nginx, stack con RBAC/servicios/reglas/provisioning/dashboard y ejecutor/validación/pruebas), este informe y una adición fechada al plan FIN. Los doce informes históricos, la modificación FIN-04 y todo FIN-05/06/07/08/09 conservan sus bytes previos.

Durante la implementación se corrigieron reservas mayores que limits, la ruta de importación de Uvicorn y un escape de LogQL; los intentos anteriores se limpiaron y no se cuentan como aceptación. La última ejecución anterior es íntegramente satisfactoria, desde cero y sin intervención en sus fallos/recuperaciones automáticas.

Solo sigue el clúster preexistente wordle-pg06-00f26f1f; todos los clústeres/forwards propios se retiraron, imágenes/cachés locales permanecen. Sin Azure, Terraform apply, GHCR, cambios CI, commit o push. FIN-04/05 conservan sus pendientes y FIN-16 no se inicia. Deben repetirse endpoints gestionados, capacidad y controles de red en FIN-18; un canal de notificación fuera del clúster requeriría autorización y configuración separadas. No se afirma entrega a personas ni a servicios externos. El adaptador OTLP es deliberadamente acotado, de entrega best-effort; no garantiza colas persistentes, retries o telemetría sin pérdidas bajo carga.

Referencias técnicas: [OTLP/JSON](https://opentelemetry.io/docs/specs/otlp/), [ingestión OTLP nativa en Loki](https://grafana.com/docs/loki/latest/send-data/otel/native_otlp_vs_loki_exporter/), [configuración Tempo](https://grafana.com/docs/tempo/latest/configuration/).
