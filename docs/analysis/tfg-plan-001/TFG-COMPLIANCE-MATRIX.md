# TFG-COMPLIANCE-MATRIX

Análisis propuesto, no implementación ni modificación del backlog oficial. Fecha: 08/11/2026.

## Fuente y corte de evidencia

Fuente normativa principal: «Procedimiento PF - DevOps», PDF aportado por el usuario, 7 páginas físicas; SHA256 `e092aa234334b6cdb5187aeab4be7ee83d4fde92a6ff3698e5c40e3540185ea3`. Se leyó todo el texto y se revisó visualmente cada página (la primera es portada). Las páginas citadas son las del archivo, no una numeración inventada. No se copia el PDF a Git.

Corte local: rama `codex/devops-04a1-hardening`, commit `a666b17680781a24889ea774778019995d3fca45`. Árbol inicialmente limpio. No se hizo fetch, no se consultaron runs/paquetes GitHub ni Azure/Supabase. La referencia local no acredita que sea el main remoto actual. No se ejecutaron pruebas o infraestructura para este análisis.

## Interpretación académica

- El escenario dice Blue-Green «y/o» rollback (p. 3), pero el desarrollo exige ambos explícitamente (p. 4) y la memoria incluye Blue-Green (p. 6). Se consideran obligatorios ambos, sin eliminar la ambigüedad del resumen.
- «Como OpenTelemetry, Prometheus...» en el escenario se concreta en la lista «incluya» de p. 4: Collector, Prometheus, Grafana, Loki, cAdvisor, Node Exporter, alertas y notificaciones. No son meras sugerencias en el desarrollo.
- «Ingress Controllers» está expresamente en p. 3: port-forward no sustituye su implementación. Distinguir controlador de recurso Ingress.
- EKS o AKS son alternativas; se elige AKS y no se exige implementar AWS. GitHub Actions u otra herramienta y Docker Hub o GHCR son alternativas, no obligaciones acumulativas.
- Compose dice «si es necesario»: aplica porque el proyecto tiene dos servicios. Anexos dicen «si aplica»: se proponen por la utilidad de logs/pruebas, sin convertirlos en requisito obligatorio adicional.
- Modularización no exige número de módulos: un módulo raíz pequeño y organizado es suficiente para esta escala. No se propone sobreingeniería.
- El PDF no exige Supabase, React, FastAPI, una nueva autenticación concreta, Bicep, Key Vault, un backend de trazas específico ni un SLA numérico. Esquema/semillas/seguridad efectiva son tareas de habilitación del Wordle elegido, no requisitos tecnológicos inventados.
- El vídeo responde a tres preguntas del docente, con profesionalidad y duración máxima de 15 minutos. No se inventa una defensa síncrona obligatoria ni fecha de entrega. El ensayo oral es preparación recomendada.

## Clasificación

Técnicos: A02-A04, A16-A18, A20-A21. Infraestructura: A05-A15. Seguridad: A03, A15, A19, A49. Observabilidad: A22-A30. Funcionales/no funcionales: A01, A20-A21, A30-A31, A50, A55. Documentales: A32-A53. Entrega/defensa: A54-A58. Las categorías pueden solaparse; no se suman entre sí.

Estados: CUMPLIDO = artefacto implementado con evidencia suficiente para el alcance exacto de la fila; PARCIAL = código incompleto o validación insuficiente; PENDIENTE = sin implementación/evidencia verificable; NO APLICA = solo con justificación del PDF. Que un YAML exista puede satisfacer su definición declarativa, pero no acredita despliegue, integración o automatización funcional.

## Método y resultado

Se atomizan 58 obligaciones verificables. Las repeticiones del escenario y requisitos adicionales se consolidan con la tarea correspondiente, salvo entregables documentales distintos. Cada fila pesa uno; no es ponderación oficial, nota ni porcentaje de horas de proyecto. Una fila PARCIAL no suma medio cumplimiento. Se excluyen del denominador opciones tecnológicas y anexos condicionales.

- CUMPLIDO: 14/58 = 24.14 %.
- PARCIAL: 21/58 = 36.21 %.
- PENDIENTE: 23/58 = 39.66 %.
- NO APLICA: 0/58 = 0.00 %.

No hay exclusiones NO APLICA en las 58 filas. Los porcentajes están redondeados a dos decimales.

## Matriz

| ID | Requisito académico | Evidencia en repositorio | Estado | Brecha | Acción necesaria | Prioridad |
|---|---|---|---|---|---|---|
| A01 | Aplicación web funcional y configurada (pp. 2, 6) | E10/E11/E12/E13: UI, API y pruebas aisladas | PARCIAL | Integración con persistencia real no verificada | FIN-01/02/03/18 | P0 |
| A02 | Dockerfile personalizado e imágenes personalizadas (pp. 2, 3, 5) | E01/E02: imágenes propias backend/frontend | CUMPLIDO | Sin brecha de definición de imágenes; ejecución cloud se evalúa aparte | Preservar digests y evidencias FIN-04 | P1 |
| A03 | Optimizar las imágenes para que sean ligeras y seguras; todas las imágenes (pp. 3, 5) | E01/E02: multietapa, runtime sin herramientas de build, non-root; E03: read-only/cap_drop | CUMPLIDO | Optimización comprobable en código; no se afirma certificación ni ausencia de vulnerabilidades | Registrar tamaño y controles FIN-04 | P1 |
| A04 | Docker Compose para desarrollo multicontenedor, si es necesario (pp. 3, 5) | E03: Compose y override de pruebas para dos servicios | CUMPLIDO | La condición aplica al proyecto y está implementada | Conservar comprobaciones existentes FIN-04 | P1 |
| A05 | Terraform para aprovisionar infraestructura en la nube: EKS o AKS (p. 3) | E07/E08/E18: configuración AzureRM y validación local documentada | PARCIAL | No hay aprovisionamiento Azure demostrado | FIN-16/17/19 | P0 |
| A06 | Definir recursos de red: VPC, subredes, balanceadores, etc. (p. 3) | E07: VNet/subred y Standard LB de salida administrado por AKS | PARCIAL | Declaración preparada; red real y exposición de aplicación no probadas | FIN-06/16/18 | P0 |
| A07 | Clúster Kubernetes y nodos de trabajo de forma declarativa (p. 3) | E07/E09: AKS, pool, SKU y cantidad parametrizados | CUMPLIDO | La definición está implementada; creación efectiva cubierta por A05 | Validar materialización FIN-17 | P1 |
| A08 | Buenas prácticas de modularización Terraform (p. 3) | E07/E08/E09: módulo raíz pequeño, archivos por responsabilidad, variables y outputs | CUMPLIDO | El PDF no exige módulos hijos; no introducirlos solo para contar módulos | Mantener módulo raíz documentado FIN-16 | P2 |
| A09 | Estado remoto Terraform (p. 3) | E08/E18: backend azurerm parcial y ejemplo | PARCIAL | Storage externo y bloqueo/recuperación no verificados | FIN-16/19 | P0 |
| A10 | Manifiestos declarativos Deployments (p. 3) | E04: backend y frontend con selectores y probes | CUMPLIDO | Recurso YAML presente; perfil AKS evaluado aparte | FIN-05 | P1 |
| A11 | Manifiestos declarativos Services (p. 3) | E04: dos ClusterIP con selectores y puertos | CUMPLIDO | Definición presente; acceso cloud no demostrado | FIN-05/06 | P1 |
| A12 | Manifiestos declarativos Ingress Controllers (p. 3) | E04/E17: acceso mediante port-forward; no controlador | PENDIENTE | No hay Ingress Controller ni recurso Ingress de aplicación | FIN-06 | P0 |
| A13 | Manifiestos declarativos ConfigMaps (pp. 3-4) | E05: configMapGenerator de Nginx montado por frontend | CUMPLIDO | Generación declarativa válida como ConfigMap; no exige archivo independiente | Conservar patrón FIN-05 | P1 |
| A14 | Manifiestos declarativos Secrets (p. 4) | E04: variables Supabase vacías en perfil memoria, sin Secret | PENDIENTE | No hay referencia/creación segura del Secret de runtime | FIN-07 | P0 |
| A15 | Manifiestos Kubernetes declarativos y mejores prácticas (p. 5) | E04/E05: non-root, límites, probes, seccomp, sin token de ServiceAccount | PARCIAL | Faltan perfil cloud, exposición y secretos; aislamiento no demostrado | FIN-05/06/07/18 | P1 |
| A16 | Pipeline que automatice la compilación de pruebas (p. 4) | E06/E12/E13: unittest y build Vite; frontend tests existen | PARCIAL | Sin runs verificadas en esta auditoría; CI no ejecuta Vitest | FIN-04 | P0 |
| A17 | Construcción de imagen Docker y envío a Docker Hub o GHCR (p. 4) | E06: docker-build y publish-ghcr por SHA completo | PARCIAL | Workflow implementado; ejecución, paquetes y digests no comprobados | FIN-04 | P0 |
| A18 | Pipeline que automatice el despliegue en Kubernetes (p. 4) | E06: kind-smoke-test despliega memoria en runner | PARCIAL | No hay despliegue automatizado al entorno Azure objetivo | FIN-17/18 | P0 |
| A19 | Manejo seguro de credenciales y secretos durante todo el proceso (pp. 2, 4-5) | E06: GITHUB_TOKEN/permisos limitados; E15: límites conocidos | PARCIAL | No se ha verificado inyección runtime, RLS, control de acceso ni e2e | FIN-03/07/16/18 | P0 |
| A20 | Blue-Green deployment para minimizar inactividad (p. 4) | E04: backend Recreate; sin Blue y Green ni promoción | PENDIENTE | No existen versiones simultáneas ni conmutación verificada | FIN-08 | P0 |
| A21 | Rollback automático si falla la nueva versión (p. 4) | E06: diagnósticos/cleanup de kind; no rollback de aplicación | PENDIENTE | Fallo del pipeline no restaura la versión de servicio | FIN-09 | P0 |
| A22 | OpenTelemetry Collector: métricas y trazas (p. 4) | Sin Collector, instrumentación ni configuración OTLP encontrada | PENDIENTE | No hay señales ni backend de trazas acordado | FIN-10 | P0 |
| A23 | Prometheus: servidor de métricas y recogida de exporters (p. 4) | Sin configuración ni despliegue encontrado | PENDIENTE | No hay scrape/targets/reglas verificables | FIN-11 | P0 |
| A24 | Grafana: métricas y dashboards personalizados (p. 4) | Sin dashboards ni provisioning encontrado | PENDIENTE | No hay datasource ni paneles de Wordle/cluster | FIN-13 | P0 |
| A25 | Loki: gestión centralizada de logs (p. 4) | Nginx/Uvicorn emiten logs; no Loki ni agente | PENDIENTE | Logs de contenedor no equivalen a centralización | FIN-12 | P0 |
| A26 | cAdvisor: métricas del clúster (p. 4) | Sin configuración de scrape/validación de kubelet-cAdvisor | PENDIENTE | No se demuestra recogida de métricas de contenedores | FIN-11 | P0 |
| A27 | Node Exporter: métricas del clúster (p. 4) | Sin DaemonSet/chart/targets encontrado | PENDIENTE | No se demuestra recogida de métricas de nodos | FIN-11 | P0 |
| A28 | Alertas basadas en métricas y logs críticos (p. 4) | Sin reglas de alerta encontradas | PENDIENTE | No hay disparo ni recuperación reproducible | FIN-14 | P0 |
| A29 | Notificaciones de alertas críticas (p. 4) | Sin receptor/canal de notificación encontrado | PENDIENTE | Canal y entrega real no definidos | FIN-14 | P0 |
| A30 | Observabilidad correctamente integrada e información relevante de sistemas/aplicaciones (pp. 2, 5) | E04: probes y logs; sin integración observabilidad | PENDIENTE | Faltan correlación, métricas/trazas/logs y demostración conjunta | FIN-10/11/12/13/14/15/18 | P0 |
| A31 | Pipeline funcional y automatización completa (p. 5) | E06: CI/kind/publicación definidos, Terraform solo valida | PARCIAL | Sin CD Azure, promoción, rollback ni evidencias reales de runs | FIN-04/17/18/19 | P0 |
| A32 | Entrega de enlace al repositorio (p. 5) | Repositorio asociado lromerob/wordle; commits locales y tracking origin | CUMPLIDO | Existe enlace identificable; su envío por plataforma cubierto por A54 | Incluir enlace y commit de entrega FIN-20 | P1 |
| A33 | Repositorio con código de aplicación (p. 5) | E10/E11: frontend y backend versionados | CUMPLIDO | Sin brecha de presencia; funcionamiento cubierto por A01 | FIN-20 | P1 |
| A34 | Repositorio con Dockerfile y Docker Compose (p. 5) | E01/E02/E03: archivos versionados | CUMPLIDO | Sin brecha de presencia | FIN-20 | P1 |
| A35 | Repositorio con manifiestos Kubernetes .yaml (p. 5) | E04/E05: archivos versionados | CUMPLIDO | Presencia cumplida; recursos ausentes se evalúan en A12/A14 | FIN-20 | P1 |
| A36 | Repositorio con configuración GitHub Actions u otra herramienta (p. 5) | E06: workflow versionado | CUMPLIDO | Presencia cumplida; resultados se evalúan aparte | FIN-20 | P1 |
| A37 | Repositorio con scripts adicionales utilizados (p. 5) | E14 y scripts inline E06 versionados | CUMPLIDO | Scripts actuales presentes; los futuros deben entregarse también | FIN-20 | P1 |
| A38 | Documentación del proyecto en PDF (p. 5) | E16/E17/E18 son Markdown; no memoria final encontrada | PENDIENTE | No existe PDF académico del proyecto | FIN-20 | P0 |
| A39 | Portada: título y nombre y apellidos del autor (p. 5) | Sin memoria final; la portada del enunciado no cuenta | PENDIENTE | Falta portada de la memoria propia | FIN-20 | P1 |
| A40 | Índice de contenidos (p. 5) | Sin memoria final | PENDIENTE | Falta índice académico | FIN-20 | P1 |
| A41 | Descripción general y objetivos (p. 5) | E16/E18: descripción técnica y alcance parcial | PARCIAL | No hay capítulo académico consolidado ni objetivos trazados | FIN-20 | P1 |
| A42 | Stack tecnológico y herramientas utilizadas (p. 5) | E16/E18: herramientas documentadas | PARCIAL | Falta consolidación en memoria y versiones de la entrega | FIN-20 | P1 |
| A43 | Arquitectura con diagramas de infraestructura/flujo de datos y explicación (p. 6) | E18 describe arquitectura en prosa; no diagramas versionados encontrados | PENDIENTE | Faltan diagramas actuales/objetivo y flujo de datos | FIN-20 | P1 |
| A44 | Implementación detallada: contenerización Docker (p. 6) | E16: instrucciones y decisiones de contenedores | PARCIAL | Hay material técnico, no capítulo final con evidencias | FIN-04/20 | P1 |
| A45 | Implementación detallada: orquestación Kubernetes (p. 6) | E17: procedimiento y validación local documentada | PARCIAL | Faltan integración cloud y capítulo final | FIN-18/20 | P1 |
| A46 | Implementación detallada: configuración CI/CD (p. 6) | E06/E16: CI definido y descripción parcial | PARCIAL | Sin CD completo ni capítulo con ejecuciones verificadas | FIN-04/18/20 | P1 |
| A47 | Implementación detallada: Blue-Green Deployment (p. 6) | Sin implementación ni capítulo | PENDIENTE | Falta implementación y explicación demostrada | FIN-08/09/20 | P0 |
| A48 | Implementación detallada: monitoreo y observabilidad (p. 6) | Sin stack ni capítulo | PENDIENTE | Falta implementación y explicación demostrada | FIN-10/11/12/13/14/15/20 | P0 |
| A49 | Implementación detallada: secretos y seguridad (p. 6) | E15/E18: límites y diseño de seguridad | PARCIAL | No se acredita manejo seguro del runtime completo | FIN-03/07/18/20 | P1 |
| A50 | Requisitos funcionales/no funcionales, capturas y ejemplos de código de funcionamiento (p. 6) | E10/E12/E13/E15: comportamiento y pruebas; sin capturas versionadas | PARCIAL | Falta catálogo con criterios y evidencias integradas; no inventar SLA | FIN-03/04/18/20 | P0 |
| A51 | Manual detallado: replicar entorno y desplegar desde cero (p. 6) | E16/E17/E18: manuales parciales locales e IaC | PARCIAL | No cubre esquema, secretos, AKS y retirada probados | FIN-01/02/17/19/20 | P0 |
| A52 | Conclusiones, dificultades y resolución (p. 6) | E17/E18: incidencias y limitaciones documentadas | PARCIAL | Faltan resultados finales y conclusiones académicas | FIN-19/20 | P1 |
| A53 | Propuestas de mejora y posibles funcionalidades futuras (p. 6) | E15/E18: pendientes técnicos | PARCIAL | Falta capítulo de mejoras priorizadas; no exige implementarlas | FIN-20 | P2 |
| A54 | Entrega por plataforma Tokio School de enlace y documentación (p. 5) | No se ha accedido a plataforma ni hay recibo | PENDIENTE | Entrega externa no comprobada | FIN-20 | P0 |
| A55 | Revisión docente de informe y aplicación configurada; prueba de funcionalidad y cambios solicitados (p. 6) | Sin evaluación/aceptación docente verificable | PARCIAL | Base funcional local; falta sistema integrado listo para evaluación y revisión docente | FIN-18/20/21 | P0 |
| A56 | Responder en vídeo las tres preguntas planteadas por el docente (p. 6) | No hay preguntas recibidas ni vídeo en evidencia local | PENDIENTE | Dependencia externa de revisión docente | FIN-22 | P0 |
| A57 | Vídeo grabado con profesionalidad como defensa del proyecto (pp. 6-7) | Sin vídeo/guion verificable | PENDIENTE | Preparar guion, audio/imagen legibles y ensayo | FIN-21/22 | P1 |
| A58 | Vídeo con longitud no mayor de 15 minutos (p. 7) | Sin vídeo verificable | PENDIENTE | Medir duración del archivo final | FIN-22 | P0 |

## Catálogo de evidencia concreta

Cada referencia E apunta a archivos inspeccionados; las referencias a pruebas indican existencia de código, no ejecución actual.

| Código | Archivos y comprobación |
|---|---|
| E01 | [backend/Dockerfile](../../../backend/Dockerfile): Python 3.12, lock con hashes, usuario 10001, targets runtime/memory-test y healthcheck. |
| E02 | [frontend/Dockerfile](../../../frontend/Dockerfile), [frontend/.dockerignore](../../../frontend/.dockerignore): Node build, npm ci, Nginx non-root, /api; sin node_modules del host. |
| E03 | [compose.yaml](../../../compose.yaml), [compose.test.yaml](../../../compose.test.yaml): dos servicios, healthchecks, backend sin puertos host, dos redes en test. |
| E04 | [backend.yaml](../../../k8s/local/backend.yaml), [frontend.yaml](../../../k8s/local/frontend.yaml), [namespace.yaml](../../../k8s/local/namespace.yaml): recursos y seguridad locales, sin Ingress/Secret/PVC. |
| E05 | [kustomization.yaml](../../../k8s/local/kustomization.yaml), [nginx.conf](../../../k8s/local/nginx.conf): ConfigMap generado y proxy backend:8000. |
| E06 | [ci.yml](../../../.github/workflows/ci.yml): siete jobs, pruebas, build, render, kind, GHCR y Terraform. No se han verificado runs externas. |
| E07 | [main.tf](../../../infra/terraform/main.tf): seis recursos; AKS Free con identidad/subred, RBAC y restricción API. |
| E08 | [versions.tf](../../../infra/terraform/versions.tf), [.terraform.lock.hcl](../../../infra/terraform/.terraform.lock.hcl), [providers.tf](../../../infra/terraform/providers.tf), [.gitignore](../../../infra/terraform/.gitignore): AzureRM 4.50.0, backend parcial, lock y exclusiones. |
| E09 | [variables.tf](../../../infra/terraform/variables.tf), [outputs.tf](../../../infra/terraform/outputs.tf), [backend.hcl.example](../../../infra/terraform/backend.hcl.example): parametrización sin credenciales reales. |
| E10 | [App.jsx](../../../frontend/src/App.jsx), [api.js](../../../frontend/src/api.js), [package.json](../../../frontend/package.json): React/Vite, identidad local no autenticada y contratos API. |
| E11 | [main.py](../../../backend/app/main.py), [game.py](../../../backend/app/routers/game.py), [stats.py](../../../backend/app/routers/stats.py), [database.py](../../../backend/app/database.py): API, Supabase lazy, estadísticas y validación. |
| E12 | [test_backend.py](../../../backend/tests/test_backend.py), [test_stabilization.py](../../../backend/tests/test_stabilization.py): 20+6 métodos de prueba encontrados por AST, sin ejecutarlos. |
| E13 | [App.test.jsx](../../../frontend/src/App.test.jsx): 12 casos de Vitest con fetch simulado; CI actual hace build, no npm test. |
| E14 | [memory_server.py](../../../backend/docker/memory_server.py): MemoryDB de prueba, bloquea Supabase/env/red externa; no persistencia real. |
| E15 | [SECURITY-NOTES.md](../../../backend/SECURITY-NOTES.md): usuario_id suplantable, consultas sin autorización verificable y escrituras no atómicas. |
| E16 | [README.md](../../../README.md): procedimientos y relatos de pruebas Docker/frontend/backend. Relato no equivale a logs originales revalidados. |
| E17 | [k8s/README.md](../../../k8s/README.md): pruebas históricas en kind, DNS Nginx, probes transitorias y límites NetworkPolicy. |
| E18 | [infra/terraform/README.md](../../../infra/terraform/README.md): validación local histórica fmt/init/validate y diseño de acceso/red/costes; no despliegue Azure. |

## Evidencia no verificada y límites de inspección

No se hallaron memoria académica propia, diagramas, capturas versionadas, scripts SQL/migraciones, backlog oficial, resultados de runs CI, manifiestos de observabilidad ni workflows Azure. No se consultó un backlog en una herramienta externa: su existencia/estado es desconocido y no se modifica. No se inspeccionaron secretos, backend local, estado Terraform, kubeconfig ni archivos ignorados sensibles. No se afirma ausencia universal de recursos en Azure, sino ausencia de evidencia inspeccionada que los demuestre.

Los nuevos documentos de análisis no convierten automáticamente requisitos en CUMPLIDO: son propuestas, no memoria final ni ejecución técnica. Los resultados académicos siguen pendientes de evaluación docente.

Ver [brechas](TFG-GAP-ANALYSIS.md), [plan propuesto](TFG-COMPLETION-PLAN.md) y [evidencias](TFG-DEFENSE-EVIDENCE.md).
