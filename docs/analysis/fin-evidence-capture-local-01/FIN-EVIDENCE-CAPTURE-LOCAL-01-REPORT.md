# FIN-EVIDENCE-CAPTURE-LOCAL-01 — 22/11/2026

## 1. Resumen ejecutivo

**PASS local.** Mecanismo Playwright/Edge implementado y ejecutado. Ensayo de referencia:
`20261122-capture-07`, clúster propio `wordle-fin1015-53676067`, retirado.
Sus 22 capturas reales y resultados SQL/HTTP/Kubernetes/señales permanecen disponibles
después de la limpieza. No es una validación AKS ni una nueva validación CI remota.

Dossier: [manifest.json](../../evidence/local/20261122-capture-07/manifest.json).
Reproducción: [scripts/evidence/README.md](../../../scripts/evidence/README.md).
Se conservan seis ensayos de diagnóstico, con sus fallos, sin sobrescribirlos.

## 2. Preflight y autorizaciones utilizadas

Repositorio Wordle del Escritorio, rama `codex/pg01-07-consolidation`,
HEAD inicial/final `4d56cf265cc5f0af8c72c64f2a93373660e8f122`, índice vacío.
Inicialmente: nueve archivos versionados modificados y 80 sin seguimiento (89 pendientes).
Se registraron sus hashes antes de implementar.

Se leyó FIN-EVIDENCE-READINESS-01 y la trazabilidad existente; no se reinterpretaron
validaciones históricas como implementaciones ausentes. Docker Desktop estaba detenido:
se inició normalmente, sin cambiar configuración. Capacidad disponible: 22 CPU y
aproximadamente 16 GiB para Docker Linux. Puertos loopback efímeros asignados por los
ejecutores, sin tocar el frontend/servicios previos. Cada prueba utilizó recursos propios;
el clúster preexistente PG-06 quedó excluido. No operaciones Azure, Terraform remoto,
GitHub Actions, GHCR ni Supabase. Ninguna instalación global o dependencia nueva.

## 3. Herramientas verificadas

| Herramienta | Versión observada |
| --- | --- |
| Playwright del runtime existente | 1.62.1 |
| Microsoft Edge, canal msedge | 158.0.4370.33 |
| Python del entorno existente | 3.12.14 |
| Node | 24.18.0 |
| Docker Engine Linux | 29.9.2 |
| kind | 0.33.0 |
| kubectl / Kustomize | 1.36.1 / 5.8.1 |
| Kubernetes del ensayo | 1.35.0 |
| PostgreSQL real | 16.15 |

## 4. Playwright + Edge

Smoke real sobre página HTTP loopback controlada: PNG auténtico 1440×1000, firma,
hash, dimensiones y apertura comprobados. Contexto y navegador cerrados.
Salida original en `20261122-capture-01/results/tooling/`, referenciada desde el dossier final.
También se probó el rechazo de sobrescritura, conservando el hash de la captura existente.

Capturas de servicios: desktop 1440×1000, móvil 390×844, es-ES y UTC.
Contextos aislados; peticiones de navegador limitadas a hosts locales. Solo se inicializa
un identificador sintético en el almacenamiento habitual del frontend. No se interceptan
respuestas para simular la API ni se modifica la aplicación. Credencial sintética de
Grafana transmitida únicamente por entorno/stdin, sin exportar perfil o storageState.

## 5. Escenarios ejecutados

| Escenario | Resultado real |
| --- | --- |
| Wordle desktop/móvil | Creación, partida activa, palabra inválida HTTP 400 sin escritura SQL ni consumo de intento, victoria, derrota al sexto y reinicio: PASS |
| Entrada y colores | Teclado físico/virtual; cinco aciertos verdes y respuestas reales representadas: PASS |
| Kubernetes/Ingress | Pods y contenedores Ready, Services, Ingress/Traefik, respuesta HTTP y referencias de imágenes exportadas mediante campos permitidos: PASS |
| Persistencia | Reemplazo del pod PostgreSQL del ensayo, snapshot SQL idéntico y partida recuperada vía HTTP/UI: PASS |
| Promoción | Blue estable → Green candidata validada → selector Green y tráfico real: PASS |
| Rechazo previo | Blue defectuosa rechazada antes de promoción; selector estable conservado: PASS, no se etiqueta como rollback |
| Rollback real | Blue promocionada, fallo funcional público 503 con health Ready, recuperación automática de Green y datos conservados: PASS |
| Señales | OTel/Tempo, seis targets UP, métricas de aplicación/cAdvisor/Node Exporter, Loki y ocho paneles Grafana cargados: PASS |
| Alertas | WordleCriticalLog y WordleUnavailable: dos notificaciones firing y dos resolved recibidas por el webhook local: PASS |
| Restauración independiente | FIN-02B reutilizado sobre dos PostgreSQL nuevos: pg_dump custom, pg_restore, igualdad de datos/esquema/secuencia y comprobaciones HTTP reales: PASS |

Restauración ejecutada separadamente en el ensayo 01: 5 palabras, 3 partidas, 8 intentos,
1 estadística antes del HTTP; respaldo de 7098 bytes, hashes de datos iguales, origen sin
alterar y ocho comprobaciones HTTP documentadas. No se reutilizaron PG-05/PG-06.

En el ensayo 07 se muestrearon **1161 peticiones y 107 respuestas fallidas/timeouts**
durante los fallos controlados y las pruebas de alertas. En promoción inicial no hubo
fallos muestreados; en fallo/rollback sí los hubo. Ventana observada de recuperación
del endpoint de partida: 5,187 s; durante los fallos de observabilidad, 27,359 s.
No se afirma cero downtime ni un SLA. Las muestras y ventanas completas están conservadas.

## 6. Capturas generadas

Ensayo de referencia: **22 PNG**, todos abiertos e inspeccionados:
12 Wordle, 2 Grafana, 4 Prometheus, 3 Loki y 1 Tempo.
Los dos paneles inferiores de Grafana tienen datos visibles en la captura definitiva.
Los viewport muestran una selección legible de series/logs; el JSON conserva el detalle.

Inventario global: **90 capturas PNG nuevas** (89 de servicios, incluyendo diagnósticos,
y un smoke de herramientas), más tres PNG derivados históricos: 93 PNG decodificados.
Los diagnósticos fallidos no cuentan como evidencias satisfactorias del ensayo final.

## 7. Tres capturas históricas recuperadas

`pg05-ui-win.png`, `pg05-ui-loss.png` y `pg06-ui-win.png` siguen siendo JPEG originales
con los tres hashes del informe previo intactos. Se preservaron copias byte a byte con
extensión .jpg y se crearon derivados PNG diferenciados. Procedencia, hashes, dimensiones,
entorno PG-05/PG-06 y referencias constan en `20261122-capture-01/historical/provenance.json`.
Fecha original no acreditada: null; no se infiere del nombre del directorio.
No sustituyen las capturas nuevas.

## 8. JSON/logs originales y mecanismo construido

Originales durables fuera de Git:
`%LOCALAPPDATA%/WordleTFG/evidence/<run-id>/integrated/`.
Se conservan events, traffic, summary y observability cuando el ensayo los produjo.
El manifiesto identifica originales y derivados sanitizados, con sus hashes separados.
Se exportan antes de perder el entorno; la verificación final se realizó después de limpiarlo.

Nuevos: `scripts/evidence/{capture.cjs,hook.py,run_local.py,run_persistence.py,finalize.py,README.md}`.
Se reutilizan los ejecutores FIN-02B y FIN-10/15; no se duplican despliegue ni restauración.
Los dos ejecutores existentes modificados son
`k8s/observability/run_observability.py` y `k8s/observability/validation.py`:
hooks opcionales y corrección focalizada de una aserción redundante de muestreo.
La detección independiente del 503 y las comprobaciones reales de rollback se mantienen.

Manifiestos, revisión visual, JSON funcionales/Kubernetes y checksums quedan en cada dossier.
No se exportan Secrets, ConfigMaps completos, kubeconfig, estado Terraform, DSN o contraseñas.
Análisis automático focalizado de 87 fuentes/JSON: sin hallazgos; revisión visual sin
credenciales visibles. No equivale a una certificación universal de ausencia de secretos.
Los hashes de código se identifican como calculados al finalizar, no como una instantánea
histórica de los primeros intentos. El HEAD solo no reproduce los cambios sin commit.

## 9. Matriz EV/A de esta ejecución

| EV | Requisitos vinculados | Evidencia local |
| --- | --- | --- |
| EV-01 | A01/A50/A55 | UI real + HTTP/SQL, desktop y móvil |
| EV-04 | A10/A11/A12/A15 | Metadatos Kubernetes permitidos + Ingress HTTP |
| EV-06 | A20/A47 | Eventos, selectores y tráfico Blue → Green |
| EV-07 | A21/A31 | Rechazo y rollback posterior diferenciados, snapshots |
| EV-08 | A22/A30/A48 | TraceID, span real POST /game/intento y exportación OTel |
| EV-09 | A23/A26/A27 | Targets UP y vectores Prometheus reales |
| EV-10 | A24/A30 | Dashboard existente, ocho paneles con datos |
| EV-11 | A25/A30 | Consultas Loki de backend/frontend/despliegue, errores y trazas |
| EV-12 | A28/A29/A30 | Respuestas reales del receptor firing/resolved |
| EV-14 | A01/A50/A51 | Reinicio persistente + restauración SQL/HTTP independiente |

La vinculación aporta evidencia; no declara completados todos esos requisitos académicos,
la evaluación docente A55 ni su equivalente Azure. EV-06/07/12 incluyen JSON técnico,
no necesitan una captura de terminal. El manifiesto distingue imagen/runtime imageID
local conocido de un digest de registro no verificado.

## 10. PASS/FAIL/BLOCKED conservados

| Ensayo | Resultado y causa |
| --- | --- |
| 01 | FAIL del hook: argumento kubectl duplicado. Smoke y restauración independientes PASS |
| 02 | FAIL de captura: sincronización de entrada tras inválida/tecla Ñ. Corregido en el capturador |
| 03 | FAIL técnico: muestreador periódico no captó exactamente un 503 ya observado por la prueba independiente; se conservan muestras y comprobación del fallo real |
| 04 | PASS técnico; FAIL de captura Prometheus por espera networkidle incompatible con polling |
| 05 | PASS técnico; captura inferior Grafana FAIL visual por carga incompleta, anotada expresamente |
| 06 | PASS técnico; FAIL de captura funcional por codificación de selectores introducida al guardar el capturador; corregida a UTF-8 |
| 07 | PASS técnico y de las cuatro fases de captura, cero fallos pendientes de captura |

Además: cuatro pruebas offline focalizadas de telemetría aprobadas, cero omitidas;
sintaxis Python y Node correcta; inventarios/checksums/JSON válidos en siete dossiers;
93 PNG decodificados; fuentes nuevas revisadas por whitespace; git diff --check correcto.
No se repitieron las suites completas de aplicación ni se declaró un nuevo CI remoto.

## 11. Limitaciones

Blue y Green usan el mismo código con releases de configuración; no dos binarios funcionales
distintos. La recuperación final es Green, no Blue. Las señales son locales/efímeras,
no dimensionamiento ni validación AKS. La correlación exportada usa TraceID/span;
no se acredita un Request ID independiente que el ejecutor no registra.
Se preservan datos completos de fallos controlados, no una promesa de disponibilidad.

## 12. Riesgos para la futura sesión AKS

El navegador admite puertos loopback y consultas existentes. El hook rechaza contextos
distintos del kind propio: hace falta un adaptador específico, con autorización/contexto
AKS comprobados y sin limpieza de clúster remoto. No debe eliminarse esa protección.
Antes de otra ventana cloud: acceso privado/RBAC, CSI/persistencia, cuotas/capacidad,
exporters y receptor de alertas, puertos y exportación durable. Nada se verificó contra Azure hoy.

## 13. Requisitos todavía pendientes

Permanecen los pendientes acreditados en FIN-EVIDENCE-READINESS-01:
recorrido CD protegido y aplicación/señales/restauración en AKS, reconstrucción cloud
cuando esté autorizada, memoria y defensa. No se reabren componentes ya probados localmente.
Esta tarea no valida de nuevo EV-03/EV-05 remotos ni cierra FIN-17/18/19 por extensión.

## 14. Siguiente incremento propuesto

Revisar y aceptar este dossier. Después, continuar el cierre de prerrequisitos del CD
protegido ya existente dentro de FIN-17, con consolidación/operaciones remotas solo
cuando el propietario las autorice. No se inicia en esta ejecución.

## 15. Integridad Git

87 de los 89 pendientes iniciales permanecen idénticos por SHA-256.
Solo los dos ejecutores de captura/prueba indicados cambian entre los pendientes previos;
se conservaron sus modificaciones anteriores. Los doce informes históricos, los demás
pendientes y los originales de las tres imágenes permanecen intactos.
Nuevos archivos: seis utilidades/documentación de captura, siete dossiers y este informe.
No cambios de aplicación, infraestructura cloud, CI ni plan académico.
Estado final: 9 archivos versionados modificados (preexistentes), 276 sin seguimiento.
Índice vacío, misma rama y HEAD; git diff --check devuelve 0.
Advertencias CRLF de documentos previamente modificados, sin normalización.
No staging, commit ni push.

## 16. Limpieza

Los siete clústeres de ensayo se retiraron mediante sus ejecutores; quedan cero contenedores,
redes o procesos Node/Python/kubectl propios de estos ensayos. El único kind restante es
`wordle-pg06-00f26f1f`, preexistente y preservado.
La prueba FIN-02B retiró su backend, dos contenedores, red y dump temporal.
Los contextos Edge y port-forwards propios se cerraron.
PG-05/PG-06 no fueron objetivo de comandos de modificación.
Docker Desktop se deja iniciado; se conservan cachés/imágenes compartidas, sin prune global.
Los siete inventarios y artefactos son accesibles tras la limpieza.
