# TFG-DEFENSE-EVIDENCE

Fecha: 08/11/2026. Plan documental propuesto, no captura técnica ni entrega realizada. Requisitos normativos: Procedimiento PF - DevOps, pp. 5-7. [Matriz completa](TFG-COMPLIANCE-MATRIX.md), [plan FIN-01..22](TFG-COMPLETION-PLAN.md).

## Reglas para no sobrevalorar evidencia

Una captura de manifiesto demuestra configuración, no que el pod arrancó. Un pod Ready demuestra un probe, no persistencia. Una run verde con MemoryDB no demuestra Supabase. Un dashboard instalado no demuestra telemetría. Una regla firing no demuestra notificación entregada. Un job fallido/cleanup no demuestra rollback. Un relato README no equivale a logs originales de una ejecución identificada.

Para cada evidencia futura registrar: ID, fecha/hora UTC, entorno (local/kind/AKS), modo (memoria/PostgreSQL local/Supabase), commit, SHA/digests de imágenes, versión Kubernetes, namespace, comando o run ID, resultado esperado/obtenido y vínculo a requisitos. No incluir valores de secretos, estado/plan Terraform, kubeconfig, cabeceras de autorización ni datos personales. Mantener originales privados cuando haga falta y publicar solo copia sanitizada claramente identificada.

No hay una carpeta de capturas/runs/diagramas académicos versionados en el corte inspeccionado. README, k8s/README e infra/terraform/README aportan relatos históricos aprovechables con su fecha y limitaciones. No reutilizarlos como ejecución Azure nueva. Este documento no convierte evidencias pendientes en existentes.

## Dossier propuesto

Preparar después de aprobación una estructura de evidencias por release, por ejemplo docs/evidence/<release>/, sin crearla en esta tarea. Metadatos y capturas sanitizadas en Git si procede; vídeos/logs voluminosos con retención externa suficiente y enlaces estables. No depender de artifacts de Actions que caducan: kind-diagnostics actuales retienen solo 7 días y son principalmente de fallo.

Manifiesto sugerido: requisito -> archivo/captura -> commit/run/digest -> modo -> resultado -> capítulo PDF. Mantener un índice de checksums de entregables públicos y referencias privadas para respaldos; no publicar el contenido ni secretos de copias de estado.

## Evidencias que capturar durante la implementación

| ID propuesto | Requisitos | Evidencia verificable | Capturar en | Estado actual |
|---|---|---|---|---|
| EV-01 | A01/A50/A55 | Juego completo: creación, inválida sin consumir intento, repetidas, victoria, derrota al sexto, rechazo del séptimo y reinicio | FIN-02 y FIN-18; distinguir memoria de Supabase | Tests y relatos locales; integración real pendiente. |
| EV-02 | A02-A04/A34/A44 | Dockerfiles propios, etapas, usuario, tamaños, healthchecks, Compose healthy y API vía proxy | FIN-04; preservar salidas sanitizadas existentes si están disponibles | Código presente; resultados actuales no comprobados. |
| EV-03 | A05-A09/A45 | Config IaC y lock; validación; plan aprobado privado; recursos creados y parámetros cloud sanitizados; backend remoto y bloqueo sin secretos | FIN-16/17 | Código y validación local histórica; recursos cloud no demostrados. |
| EV-04 | A10-A15/A45 | Deployments/Services/Ingress Controller/Ingress/ConfigMap/Secret referenciado, probes, requests/limits y tráfico real por Ingress | FIN-05/06/07/18 | Perfil local parcial; Ingress y Secrets pendientes. |
| EV-05 | A16-A18/A31/A36/A46 | Run por PR con tests, build, imágenes, kind y Terraform; merge/main -> GHCR SHA/digest -> CD AKS identificado | FIN-04 y FIN-18 | Workflow de siete jobs presente; no se inspeccionaron runs ni paquetes. |
| EV-06 | A20/A47 | Blue sirve mientras Green arranca; candidata validada; selector/ruta antes/después; peticiones con versión y tiempos | FIN-08/18 | Pendiente. |
| EV-07 | A21/A31 | Fallo intencionado de candidata y fallo post-promoción; rollback automático, petición final a Blue, logs del mecanismo y conservación de datos | FIN-09/18 | Pendiente. |
| EV-08 | A22/A30/A48 | Un request/trace ID, span de intento y métricas recogidas/exportadas por Collector; destino consultable y configuración | FIN-10/18 | Pendiente. |
| EV-09 | A23/A26/A27 | Prometheus targets UP; métricas de aplicación, contenedor cAdvisor y nodo Node Exporter con nombres/labels reconocibles | FIN-11/18 | Pendiente. |
| EV-10 | A24/A30 | Dashboard personalizado con unidades, rango temporal, latencia/errores y estado de nodos/contenedores; provisioning/JSON | FIN-13/18 | Pendiente. |
| EV-11 | A25/A30 | Consulta centralizada Loki de frontend/backend, error y correlación con request/trace cuando corresponda | FIN-12/18 | Pendiente. |
| EV-12 | A28/A29/A30 | Umbral/suceso crítico -> firing -> notificación al receptor autorizado -> recuperación/resolved; tanto métrica como log | FIN-14/18 | Pendiente. |
| EV-13 | A19/A49 | Matriz de identidad/permisos, pruebas negativas, valores solo en backend/Secret, logs sin credenciales, límites de exposición | FIN-03/07/18 | Código de exclusiones y límites documentados; runtime pendiente. |
| EV-14 | A01/A50/A51 | Migración a BD vacía, semilla idempotente, reinicio con datos conservados y restauración de respaldo probada | FIN-01/02/19 | Sin migraciones/restauración encontrada. |
| EV-15 | A05/A09/A51/A52 | Secuencia deploy -> verificación -> exportación -> retirada autorizada -> recursos remanentes -> reconstrucción con tiempos | FIN-19 | Pendiente; no acreditarlo solo con terraform validate. |
| EV-16 | A32-A54 | Release fuente, enlace repo, PDF final con todos los apartados y manual seguido desde cero | FIN-20 | Código y manuales parciales; memoria/entrega pendientes. |
| EV-17 | A55-A58 | Preguntas reales del docente, guion de tres respuestas, vídeo profesional y duración <=15 min | FIN-21/22 | Pendiente y dependiente del docente. |

cAdvisor puede estar integrado en kubelet; demostrar su scrape y métricas no exige desplegar un segundo cAdvisor privilegiado. Node Exporter sí debe estar identificado y recogido. No confundir métricas del runner o del host Windows con las del clúster AKS.

## Cómo evitar repetir despliegues costosos

Antes de la sesión cloud: lista EV-01..EV-17 con capturas esperadas, almacenamiento de evidencias preparado, parámetros de versión fijados, escenarios de fallo ensayados en kind, receptor de alertas autorizado y permisos de lectura listos.

En una misma ventana Azure autorizada:

1. Capturar infraestructura/estado y versión inicial antes de cambios.
2. Probar persistencia y funcionalidad de aplicación con datos sintéticos.
3. Ejecutar promoción Blue-Green y fallos previstos; registrar rollback y continuidad.
4. Capturar métricas, traza y logs correlacionados del mismo periodo; mostrar alertas/notificaciones y su recuperación.
5. Exportar dashboards, consultas, logs y evidencias antes de perder PVC/retención efímera.
6. Verificar copias y después ejecutar retirada solo si está autorizada. Recoger lista de recursos remanentes y revisión de coste posterior.
7. Recrear una vez para medir recuperación y validar el manual; no repetir por una captura olvidada.

Las pantallas de recursos no deben mostrar claves, tokens, direcciones personales, IDs innecesarios o configuraciones privadas. Capturar nombre lógico, estado y métricas suficientes. No usar terraform show/state pull ni kubectl get secret -o yaml como evidencia pública.

## Esqueleto de memoria final PDF

| Apartado del PDF propio | Requisito / material |
|---|---|
| Portada e índice | A39/A40: título propio y nombre/apellidos del autor, índice legible. |
| Descripción, objetivos y stack | A41/A42: problema, alcance académico y versiones reales, sin funciones futuras presentadas como existentes. |
| Arquitectura y datos | A43: diagramas de infraestructura, flujo navegador-/api-Supabase, CI/CD y persistencia; límites de confianza. |
| Implementación Docker | A44 con EV-02; explicar optimización, modo memoria y runtime de producción. |
| Implementación Kubernetes/Terraform | A45 con EV-03/04; distinguir kind de AKS y plan de aplicación efectiva. |
| CI/CD | A46 con EV-05; triggers, gates, permisos, imágenes por digest, promoción y diagnóstico. |
| Blue-Green y rollback | A47 y A20/A21 con EV-06/07; datos compatibles, fallo y recuperación automáticos. |
| Monitoreo/observabilidad | A48 con EV-08..12; Collector, exporters, Prometheus, Grafana, Loki y entrega de alertas. |
| Secretos/seguridad | A49 con EV-13; modelos de identidad, RLS y limitaciones honestas. |
| Requisitos funcionales/no funcionales | A50 con EV-01/14; tabla de criterios, capturas y ejemplos breves de código real; métricas medidas sin SLA inventado. |
| Manual desde cero | A51 con EV-14/15; prerequisitos, variables por nombre, secretos fuera de Git, despliegue/verificación/retirada y recuperación. |
| Resultados/conclusiones/dificultades | A52: resultados medidos, incidentes y resolución; DNS Nginx/probes sirven como antecedentes con contexto local. |
| Mejoras futuras | A53: prioridades y límites restantes; no hay obligación de desarrollar funciones nuevas de Wordle. |
| Anexos, si aplica | Selección de tests/logs sanitizados; no volcar todo ni ocultar la evidencia esencial solo en enlaces caducados. |

Diagramas a preparar: arquitectura Azure y dependencias externas; flujo de datos/identidad; secuencia de CI/CD/Blue-Green/rollback; canal de métricas/trazas/logs y alertas; ciclo de reconstrucción y preservación externa. No crear diagramas hipotéticos sin distinguir estado actual y objetivo.

## Defensa oral y vídeo

El docente revisa informe y aplicación, puede pedir cambios y plantea tres preguntas. No se conoce aún su contenido. Preparar explicación oral de decisiones y límites, pero el guion final debe responder a esas preguntas reales. Un walkthrough genérico no las sustituye.

Propuesta de reparto dentro del límite: breve contexto/versiones, respuesta 1, respuesta 2, respuesta 3 y cierre; ajustar los tiempos al contenido para que el archivo total sea <=15 minutos. Comprobar audio, legibilidad de terminal/dashboards y duración del archivo final; no confiar solo en el cronómetro de grabación. No atribuir al PDF una videollamada o duración de cada respuesta que no exige.

Ensayar con anterioridad, mantener demo activa el día anterior en una ventana aprobada, disponer de vídeo/capturas de Azure y fallback local claramente etiquetado. Si falla internet, no presentar kind como si fuera AKS ni declarar una ejecución nueva inexistente. Conservar evidencias permite responder a preguntas sin recrear cloud para cada toma.

## Criterio de cierre

Cada A01-A58 debe tener evidencia suficiente y revisada según su alcance; actualizar matriz solo después de verificarla. Los requisitos de entrega/plataforma/docente se cierran con confirmación real, no con archivos locales. Estos cuatro documentos son planificación, no la memoria final PDF ni los anexos ejecutados. Esperar aprobación antes de abrir tareas técnicas o modificar el backlog oficial.
