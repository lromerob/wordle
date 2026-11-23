# FIN-AKS-DEPLOYMENT-WINDOW-PREP — 17/11/2026

## 1. Resumen ejecutivo

**PASS documental y de planificación.** Creado un runbook operativo para una persona,
con ventana de cuatro horas, preflight, plan/apply por SHA revisado, validación,
evidencias, coste, incidentes, retirada y comprobación de remanentes.
No demuestra despliegue ni abre permiso de ejecución. Ningún Terraform/Azure/kubectl
ejecutado en esta iteración; solo lectura local y dos documentos nuevos.

## 2. Alcance autorizado

Documentación exclusivamente. Runbook:
docs/operations/FIN-AKS-DEPLOYMENT-RUNBOOK.md.
Todos los comandos L/C/D están marcados NO AUTORIZADOS EN ESTA ITERACIÓN;
las lecturas remotas son futuras y tampoco se ejecutan ahora.
Sin cambios Terraform, scripts, manifiestos, workflows, lock o históricos.

## 3. Referencias revisadas

Informes FIN-AKS:
POST-HARDENING-PLAN, RUN-COMMAND-HARDENING, MFA-WRITE-DELETE-TEST,
MFA-POLICY-VALIDATION, DEPLOYMENT-BLOCKERS, TERRAFORM-PLAN,
DEPLOYMENT-DECISIONS, EPHEMERAL-LIFECYCLE y REMOTE-BACKEND-INITIALIZATION.
Código Terraform real, azure_supervised.py, aks_run.py, aks_recovery.py,
azure-demo.md, overlays aks/aks-full y observability/stack/resources.yaml.
TFG-COMPLETION-PLAN, TFG-COMPLIANCE-MATRIX y TFG-DEFENSE-EVIDENCE.

La matriz y varios apartados de documentación conservan valor de inventario
histórico: referencias a Supabase, ausencia de CI/Ingress/observabilidad o
adaptaciones no implementadas no se toman como estado actual sin contrastar código.
No se reescriben documentos históricos ni criterios de cierre en este incremento.

## 4. Estado de Gate A

**GO**, por evidencia anterior. Sin revalidación remota hoy.

## 5. Estado de Gate B

**GO**, aprobación expresa del propietario en el adjunto de esta iteración.
Sustituye el estado vigente NO-GO anterior sin alterar sus registros históricos.
No equivale a autorizar apply.

## 6. Estado de AKS

**NO-GO**. Ni despliegue ni retirada autorizados por esta documentación.

## 7. Arquitectura confirmada

Inspección local coherente con Terraform 1.9.8/AzureRM 4.50.0 y plan anterior:
seis recursos, swedencentral, Free, 1.35.9, dos D4s_v5, surge1, Ubuntu OS Managed64,
CNI Overlay y CIDR aprobados; Entra/Kubernetes RBAC, cuentas locales off,
API /32 y Run Command false. No nueva validación de herramientas o Azure.
Backend persistente rg-wordle-state/stwordletfgstate7c92d4/tfstate/
wordle/aks-demo.tfstate protegido frente a retirada.

## 8. Dependencias operativas

Antes de ejecutar: fecha/T0, operador disponible, permisos/MFA/IP y cuotas vigentes,
workspace/inputs privados y custodia, plan binario nuevo con autorización específica,
digests recuperables y snapshot del trabajo local. HEAD publicado no sustituye
todos los cambios pendientes.
Para cargas: secretos exclusivamente sintéticos, contexto/kubeconfig nuevo,
capacidad/admisión CSI/hostPath/kubelet y autorización Kubernetes.
Para retirada: autorización propia y decisión de conservación/descarte de datos
sintéticos. Si hay que conservarlos, backup/restauración SQL+HTTP según criterios;
no rebajar esta condición por el reloj. Fijar decisión antes de CREATE.

CD Azure OIDC/runner/reviewers no se presume disponible. Primera ventana manual no
lo sustituye. No activar workflow ni publicar imágenes por extensión.

## 9. Preparación de la ventana

T0 a concretar por propietario; no se inventa fecha/hora.
0–20 min preflight/autorización; 20–80 provisión; 80–120 AKS;
120–160 evidencia/subset opcional; 160–220 retirada; 220–240 contingencia.
**Retirada como máximo T+160**; si la validación termina antes, retirar antes.
Si apply prolonga su ejecución, no ejecutar destroy concurrente: diagnóstico y
decisión antes de consumir reserva. Sin garantía del tiempo de operaciones Azure.

## 10. Presupuesto

Objetivo 5 USD; referencias previas 2,06 USD/4 h y 4,36 USD/8 h.
No precio reconsultado ni garantía de factura/tope automático.
Seguimiento T+20/60/80/120/160/220/240 de recursos/horas y proyección,
separando estimación, devengo estimado y facturación visible con retraso.
Incluye VM/OS/PG, LB/IP/tráfico/IO, surge y backend/retención/backups.
Proyección superior a objetivo o recursos inesperados: STOP pruebas y decisión
de retirada; ocho horas no quedan autorizadas por una estimación.

## 11. Riesgos residuales

Capacidad regional, evaluación de Policy/MFA durante create/delete, expiración,
cambios de IP, admisión de cargas, consumo real, retrasos y limpieza parcial.
Dos nodos: 8 vCPU/32 GiB nominales, menores allocatable.
Inventario previo de observabilidad: requests900m/672MiB y limits4500m/2016MiB,
incluidos dos Node Exporter; excluye app/PG/Ingress/sistema. No medición runtime.
Verificar allocatable/requests/Pressure/OOM/CSI/targets durante ventana;
no prometer suficiencia ni aumentar nodos automáticamente.

## 12. Validaciones previstas

Infraestructura: ARM Succeeded, tier/versión/pool/red/identidad/seguridad exactos;
dos nodos Ready, API accesible con Entra/kubelogin y RBAC.
Aplicación opcional: aks-full, PVC managed-csi8Gi, Services privados,
Ingress/HTTP200 y persistencia real sintética.
verify tiene escrituras; acceptance provoca promoción/fallo post-switch/rollback
y REVOKE/GRANT reversible, exige autorización separada.
Observabilidad: consultas reales, no solo Running; cAdvisor desde kubelet,
Collector/Prometheus/Grafana/Loki/Tempo y alertas firing/resolved.
No se ejecuta ninguna validación runtime, suite o render en esta iteración.

## 13. Evidencias previstas

Runbook contiene matriz de objetivo/momento/captura/criterio:
plan/hash/apply/Portal/AKS/nodos/kubectl/backend, Wordle/Ingress/SQL/HTTP/seguridad,
CI/CD, promoción/rollback, métricas/logs/trazas/dashboard/webhook, retirada y
ausencia ARM/estado. Mapeada con EV-01/03/04/05/15 y FIN pertinentes.
Reconstrucción/restauración normalmente en otra ventana, no inferida del backup.
Cronología UTC, resultados reales sanitizados y limitaciones; sin capturas ficticias,
Secret/DSN/kubeconfig/plan binario o IP doméstica en evidencia pública.

## 14. Procedimiento de retirada

Workspace externo distinto, mismo backend/variables; helper prepare y plan-destroy,
revisión de seis direcciones y dependencias AKS/inventario, SHA plan/inventario y
autorización independiente. execute aplica únicamente plan de destrucción guardado.
Preservar backend y todos sus blobs/versiones, grupo Entra, fuentes y evidencias.
Comprobar estado vacío, ambos RG/AKS ausentes, discos/PV/IP/LB/snapshots sin
remanentes propios, backend disponible y lease libre. No atribuir coste cero a
destroy exit0 ni borrar recursos por prefijo. Detener solo forwards propios.

## 15. Contingencias

Tabla del runbook: apply parcial, capacidad/Policy/RBAC, timeout, lock, API/red,
MFA, Pods/PVC, destroy o backend fallidos. Inventariar, sanitizar y solicitar
decisión acotada; no retry ciego, cambio SKU/región/permisos o force-unlock.

Observación de código: inventory() del helper consulta ambos RG; si uno falta en
un create parcial, puede fallar antes de autorizar destrucción. Se documenta vía
de contingencia supervisada directa con plan-destroy guardado/revisión equivalente
y autorización específica; no parchear scripts ni fingir inventario vacío.
Registrar cualquier residual exacto, estado/dependencia/coste/responsable.
El runbook no autoriza borrar recursos ajenos o no gestionados.

## 16. Matriz GO/NO-GO

Checklist final: contexto/backend/estado/lease, plan/hash, tiempo/presupuesto,
disponibilidad de operador/MFA/retirada, capacidad/digests/secretos para cargas,
inventario/permiso DESTROY y evidencia de ausencia.
Responsable: propietario/operador. GO para solicitar autorización es distinto
de autorización CREATE; NO-GO impide comenzar, STOP impide nuevas acciones y
RECOVERY exige decisión sobre operaciones controladas.

## 17. Limitaciones

Planificación documental completa, no simulación ni prueba operacional.
Los helpers existen pero sus fases Azure no se declaran validadas.
El helper de plan/execute incluye init/reconfigure: deben autorizarse expresamente
en la futura fase. El plan anterior no tiene binario reutilizable.
Plan guardado garantiza correspondencia con las acciones revisadas, no congela
capacidad cloud ni evita fallo parcial. Revisar fingerprint/hash/vigencia.
Sin fecha, credenciales privadas o permiso CREATE/DESTROY generados ahora:
son checkpoints deliberados, no autorizaciones implícitas.
No cambia estado de tareas FIN ni matriz histórica.

## 18. Integridad del repositorio

Preflight: rama codex/pg01-07-consolidation, HEAD
4d56cf265cc5f0af8c72c64f2a93373660e8f122; índice vacío.
71 pendientes previos capturados por SHA-256, más Terraform/lock/caché.
Solo este informe y el runbook nuevos: 73 pendientes finales. Los 71 previos
y Terraform/lock/caché están idénticos por SHA-256; HEAD intacto e índice vacío.
git diff --check exit 0; Markdown sin fences desbalanceados ni whitespace final.
Advertencias LF/CRLF previas: informe FIN-04, plan FIN y observability/
run_observability.py y validation.py. No corregidas.
Sin staging, commits/push, operaciones Terraform/Azure/Kubernetes ni cambios de
Entra/Policy/RBAC/firewall/backend/estado/lock/PG-05/PG-06.

## 19. Próxima acción recomendada

Propietario revisa el runbook, fija T0 y decide alcance de primera ventana,
custodia/datos sintéticos y autorizaciones separadas para preflight/plan privado,
CREATE y retirada. Mantener AKS NO-GO hasta permiso explícito.
No iniciar automáticamente ejecución ni otra iteración.
