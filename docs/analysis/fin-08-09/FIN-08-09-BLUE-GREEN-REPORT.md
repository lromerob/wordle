# FIN-08/09 — Blue-Green y rollback automático

Fecha: 10/11/2026. **FIN-08 PASS local · FIN-09 PASS local**.
Rama `codex/pg01-07-consolidation`, HEAD intacto `774405e6b92c33b438509832c6722605fee7d289`. Sin commit ni push.

## Implementación y reproducción

Nuevo overlay `k8s/blue-green`, derivado de `demo-kind`: frontend/backend Blue y Green, Services internos por color y un único Service activo `frontend`. Nginx de cada color usa su backend correspondiente y añade `X-Wordle-Release: blue|green`. PostgreSQL 16.15 sigue siendo un StatefulSet de una réplica con el mismo PVC; no se duplica ni migra la base.

El controlador `promotion.py` espera la última revisión de ambos Deployments, prueba frontend/salud/lectura funcional de la candidata por su Service interno y conmuta **solo** el selector wordle.slot del Service frontend mediante JSON Patch con test del valor anterior. La comprobación pública atraviesa Traefik/Ingress/Nginx y confirma el color. Si falla después del cambio, restaura automáticamente el selector anterior y verifica HTTP funcional de la versión estable. Las dos parejas siguen desplegadas; no se usa eliminación de Pods como supuesto rollback ni se revierten datos.

Desde la raíz, con Docker, kind, kubectl y Python existentes:

```powershell
.venv\Scripts\python.exe -B k8s/blue-green/run_blue_green.py --run-disposable-kind
```

En otro sistema: `python -B` con el mismo script. Opcional `--evidence-dir <DIRECTORIO_VACIO_FUERA_DEL_REPOSITORIO>`. Crea un clúster aleatorio propio, kubeconfig temporal aislado y secretos sintéticos, construye/carga runtimes locales e importa el controlador existente. Conserva únicamente JSON sanitizados fuera del repo; retira su clúster y port-forwards también ante fallo. Reutiliza `configure_demo_secrets.py` y el helper de comandos FIN-05/06/07 sin modificar esos archivos. No está diseñado para operar una instalación persistente arbitraria.

## Escenarios ejecutados realmente

Ejecución final: clúster `wordle-fin0809-7c8eddf2`, Kubernetes 1.35.0, 10/11/2026, 13:02:13–13:05:41 UTC; exit 0. No hubo intervención manual durante esta ejecución.

1. **A — Promoción correcta**: Blue activo mientras Green partía de cero réplicas. Gates de backend/frontend Green y HTTP funcional aprobados; selector blue → green y cabecera Green observada por Ingress. Partida creada en Blue y ganada desde Green, persistida en el mismo PostgreSQL. Se conservó Blue durante la preparación/promoción.
2. **B1 — Rechazo previo, no rollback**: se configuró readiness de una nueva revisión Blue contra un endpoint inexistente. No completó rollout en el límite de 25s; el controlador la rechazó y mantuvo el selector Green. La revisión anterior Blue podía seguir Ready durante ese rollout: se exige disponibilidad de la revisión nueva, no solo un Pod antiguo sano. Después se restauró automáticamente la candidata.
3. **B2 — Rollback auténtico**: Blue saludable pasó gates y recibió tráfico público (13:05:26 UTC). Después se desplegó en Blue una configuración Nginx que devuelve 503 en /api/game/, manteniendo /api/health sano. Se observó el 503 real, el smoke funcional falló y el controlador cambió blue → green; HTTP público y partida persistida correctos a las 13:05:35 UTC. Motivo registrado: `HTTP gate failed: status=503, release=blue, expected=blue`.

Transiciones reales del Service: **blue → green → blue → green**. El rechazo B1 no produjo conmutación. Detección registrada a 198.813s; selector restaurado a 199.047s y recuperación funcional completa a 202.500s: **3.687s** desde detección hasta verificación.

## Tráfico, estado y persistencia

Muestreo secuencial de /, /api/health y lectura de partida, pausa nominal 250ms entre ciclos y timeout por petición 3s; se conservan timestamps, estado y color, nunca cuerpos de respuesta. **405 peticiones, cuatro fallos**: dos 502, un 503 y un timeout. Todos se iniciaron durante fault-blue. Preparación Green: 80/80 HTTP 200; promoción normal: 6/6 HTTP 200; rechazo previo: 216/216 HTTP 200 sobre Green; rollback-green: 9/9 HTTP 200. La fase de cada muestra corresponde al comienzo de la petición, no a su finalización.

Ventanas observadas por endpoint entre primera muestra fallida y siguiente correcta: frontend 3.391s, salud 0.407s y partida 3.813s. No son SLA ni límites exactos de indisponibilidad; el muestreo no permite afirmar cero interrupciones entre peticiones. Hubo errores transitorios además del 503 provocado: no se ocultan como éxito sin interrupciones.

Tras rollback: selector frontend Green; cinco Deployments disponibles, siete Services ClusterIP, un StatefulSet PostgreSQL y el mismo PVC Bound/UID. Blue defectuoso seguía aislado del tráfico público; Ready no significaba que su funcionalidad de juego fuera correcta. La versión estable Green sí pasó comprobación funcional. Hash idéntico antes/después de los fallos sobre las cuatro tablas completas y la secuencia de palabras: `a2c940f4176ad8d2c0057b275ff3ca14bca14d082eb7165196adc97c1c60daa6`. Se conservó la victoria realizada durante A; rollback de aplicación no significa rollback de escrituras.

## Validaciones, incidencias y evidencia

- Kustomize: 27 objetos, selectores por color y referencias de ConfigMap comprobados, una sola base/PVC y ningún Secret con valores en el render. Dry-run server, despliegues y pruebas HTTP/SQL reales satisfactorios.
- Cuatro comprobaciones focalizadas del controlador: promoción, rechazo sin conmutación, recuperación post-switch y conflicto de selector. Sintaxis Python y rechazo de ejecución sin opt-in comprobados. No se repitieron las 87 pruebas de Wordle ni se modificó su código.
- Primer arranque detenido antes de promocionar por namespace ausente en el overlay: corregido y referencias generadas verificadas. Segundo intento ejecutó promoción y rollback real, pero una aserción del demostrador exigía HTTP503 como motivo y rechazó un timeout válido; se ajustó para admitir fallos de transporte, exigiendo por separado que el 503 provocado se hubiera observado tras promoción. Ambos intentos fallidos limpiaron su propio clúster y conservaron sus JSON. La ejecución final anterior es la evidencia de aceptación completa.
- Evidencia final fuera de Git: `%TEMP%/wordle-fin0809-evidence-i_c5crtb/`: events.json (cronología, gates, motivo y selectores), traffic.json (405 muestras), summary.json (estado y tiempos). Intentos anteriores: carpetas `wordle-fin0809-evidence-onf47xh4` y `wordle-fin0809-evidence-b7t7840l`. Sin kubeconfig, valores de Secret ni logs crudos de Pods en esos artefactos.
- Clústeres temporales y port-forwards retirados. Continúa el clúster preexistente wordle-pg06-00f26f1f; PG-05/PG-06 no se tocaron. Los doce informes históricos y todos los cambios FIN-04/05/06/07 se preservan byte a byte, salvo la adición fechada al plan que conserva su contenido anterior.

## Archivos y límites

Nuevos: `k8s/blue-green/{kustomization.yaml,green.yaml,services.yaml,blue.conf,green.conf,blue-fault.conf,promotion.py,run_blue_green.py}` y este informe. Único archivo anterior actualizado en este incremento: plan FIN, con estados locales demostrados. `git diff --check` correcto; índice vacío.

Ambos colores utilizan el mismo código de aplicación v1, distinguidos como releases de configuración por labels/cabecera; no se introduce una variante visual Green ni se afirma probar compatibilidad entre binarios o esquemas distintos. La configuración defectuosa solo pertenece a este overlay de demostración. La automatización depende del perfil local FIN-05/06/07 todavía sin consolidar: ambos deben revisarse juntos antes de publicar.

Alcance privado, supervisado y sintético; sin autenticación nueva, migraciones, rollback de datos, Argo CD, service mesh o controlador adicional. La recuperación no garantiza cero pérdida de peticiones ni tolerancia a fallos de PostgreSQL. No se valida gestión multioperador más allá del test del selector, alta disponibilidad o cancelación forzosa del proceso. No hubo Azure, GHCR, CI remoto nuevo, commit ni push. FIN-04/05 conservan sus pendientes GHCR y FIN-18 deberá repetir las evidencias en Azure cuando exista autorización. No se inicia otra tarea.
