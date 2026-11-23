# Wordle — Checklist del viernes 20/11/2026

Preparada el 17/11/2026. **Documento operativo; no autoriza ejecutar comandos.**
Gate A GO · Gate B GO · **AKS NO-GO**.
PASS documental significa preparación, no autorización de despliegue.

Responsable/operador: __________. Fecha efectiva: __________.
T0 local / zona: __________. T0 UTC: __________.
Inicio máximo previsto de retirada T0+160 min: __________.
Fin objetivo T0+240 min: __________. Carpeta privada de evidencia: __________.
Alcance de primera ventana acordado: infraestructura / otro explícito: __________.
Todos los campos de resultado deben contener referencias sanitizadas; no tokens,
contraseñas, DSN, kubeconfig, planes privados ni IPv4 doméstica completa.

## Fuentes locales que deben estar accesibles sin chat

- [Runbook operativo](FIN-AKS-DEPLOYMENT-RUNBOOK.md), pasos y comandos existentes.
- [Manual de emergencia y alternativa manual](FIN-AKS-EMERGENCY-TEARDOWN.md).
- Script: ../../infra/scripts/Invoke-AksEmergencyTeardown.ps1.
- [Preflight real corregido PASS](../analysis/fin-aks-emergency-preflight-live-retry/FIN-AKS-EMERGENCY-PREFLIGHT-LIVE-RETRY-REPORT.md).
- [Plan post-hardening](../analysis/fin-aks-post-hardening-plan/FIN-AKS-POST-HARDENING-PLAN-REPORT.md).
- [SKU/cuotas/políticas/costes históricos](../analysis/fin-aks-deployment-blockers/FIN-AKS-DEPLOYMENT-BLOCKERS-REPORT.md).
- [Prueba MFA RG vacío](../analysis/fin-aks-mfa-write-delete-test/FIN-AKS-MFA-WRITE-DELETE-TEST-REPORT.md).

El manual contiene notas históricas que dicen “preflight pendiente”; el informe
LIVE-RETRY posterior acredita el PASS del 17/11. No extenderlo a destroy real.
No corregir históricos ni activar workflows por interpretar esta checklist.

## Fase 0 — Condiciones de inicio (comprobar el viernes)

- [ ] Ventana continua de cuatro horas y propietario disponible hasta retirada.
- [ ] Cuota semanal/disponibilidad de Codex comprobada personalmente por el usuario;
      no se presume restablecida. No almacenar datos de cuenta aquí.
- [ ] Manual/script accesibles sin IA; operador puede seguirlos aunque Codex se agote.
- [ ] Equipo encendido, alimentación y conexión doméstica estable, sin VPN inesperada.
- [ ] Sesión Azure humana autorizada, tenant y suscripción coincidentes y Enabled.
- [ ] Contexto MFA revisado: lecturas exitosas no prueban admisión write/delete.
      Si se requiere reautenticación, solicitar intervención autorizada del propietario.
- [ ] IPv4 actual comprobada y cotejada con /32 expresamente aprobado, sin anotarla aquí.
- [ ] Backend accesible y lease libre; inventario actual comprobable.
- [ ] Cuotas regional/familia suficientes para 8 vCPU base y 12 con surge; SKU/versión disponibles.
- [ ] Objetivo USD 5 y cuatro horas aceptados, con margen de retirada y cargos diferidos.
- [ ] Política de conservación/restauración o descarte de datos sintéticos acordada
      antes de crear; si solo infraestructura, registrar “sin datos de aplicación”.
- [ ] Responsable disponible para autorizar retirada separada incluso ante fallo parcial.
- [ ] Inputs/custodia privados externos preparados, sin secretos en Git.
- [ ] Permiso explícito para consultas preflight del día; no heredarlo de la iteración previa.

Resultado fase 0: GO para iniciar consultas / NO-GO: __________.
Condición pendiente y responsable: __________.
No crear si la retirada controlada no está operativamente preparada.

## Fase 1 — Preflight vigente, con autorización de lectura

| Comprobación | Tipo | Resultado/evidencia del viernes |
| --- | --- | --- |
| Terraform 1.9.8 / AzureRM 4.50.0, lock y fuentes | Local, sin init | __________ |
| CLI/kubectl/kubelogin/Python existentes | Local; no instalación automática | __________ |
| Humano, tenant/suscripción/grupo/permisos | Azure lectura | __________ |
| IPv4/rutas/CIDR sin conflicto y API /32 aprobado | Red/lecturas; no cambiar firewall | __________ |
| Backend exacto y key accesible, lease available/unlocked | Azure lectura de propiedades | __________ |
| Preflight autónomo e inventario esperado | state list de lectura dentro del script | __________ |
| Regiones/versiones/Compute SKU y restricciones | Azure lectura | __________ |
| DSv5/total regional: consumo/límite y margen surge | Azure lectura | __________ |
| Policies heredadas/efectos/exenciones y cambios | Azure lectura | __________ |
| RG app/nodos sin colisión y sin Terraform concurrente | Local/Azure lectura | __________ |
| Imágenes por digest y snapshot de cambios locales si habrá app | Local/consulta de registro autorizada | __________ |

- [ ] No estado completo, tokens ni credenciales exportados.
- [ ] Preflight exit 0 y consulta real de inventario, no solo “proceso terminado”.
- [ ] Para primera creación, estado 0 y RG destino ausentes; si no, detenerse/revisar.
- [ ] Bloqueos o problemas de autenticación se documentan sin force-unlock/login automático.

**Preflight es lectura cloud**, aunque genera log local y puede gestionar internamente
credenciales para las consultas. **Plan no es solo lectura técnica del backend**:
adquiere/libera lease y metadatos normales; init también puede escribir estado.
Autorizar esas acciones específicamente en fase 2; nunca llamarlas un simple preflight.

Resultado fase 1: __________. Defectos/incidencias: __________.

## Fase 2 — Plan definitivo privado (autorización independiente)

- [ ] Propietario autoriza preparación externa + init del helper + plan guardado
      con lease normal. Referencia/hora de autorización: __________.
- [ ] Seguir runbook y azure_supervised.py prepare/plan; directorio nuevo externo.
      Revisar acciones internas del helper: plan hace init; no usarlo como lectura.
- [ ] Variables exactas de ventana, backend aprobado y workspace default comprobados.
- [ ] Terraform fmt/validate correctos; sin modificación de infraestructura para forzar éxito.
- [ ] Plan binario nuevo guardado privadamente; no usar el plan histórico sin -out.
- [ ] SHA-256 calculado y concordante con recibo; hash revisado: __________.
- [ ] Seis create, cero update/delete/replace y ninguna dirección inesperada:
      RG, VNet, subnet, MI, rol subnet, AKS.
- [ ] swedencentral / Free / 1.35.9 / dos D4s_v5 / surge1 / Overlay/rangos aprobados.
- [ ] Entra/RBAC, cuentas locales off, API /32 aprobado y run_command_enabled=false.
- [ ] Rol limitado a subnet; backend persistente completamente fuera del plan.
- [ ] Coste/proyección actualizados y aceptados; plan y configuración sin drift.
- [ ] Recibo sanitizado, plan/variables no publicados ni añadidos como artifacts públicos.

Vigencia propuesta según runbook: misma ventana, máximo 30 min desde revisión;
si cambia IP/configuración/estado/contexto o caduca revisión, detenerse y solicitar
nuevo plan/revisión. El binario no congela capacidad Azure.
Resultado: APROBABLE / RECHAZADO: __________. Motivo: __________.

## Fase 3 — Autorización específica de despliegue

- [ ] Propietario revisó plan definitivo y SHA exacto, inventario, coste, tiempo y riesgos.
- [ ] Autorización CREATE/terraform apply específica y posterior al plan:
      referencia __________; hora __________; hash __________; responsable __________.
- [ ] Se confirma disponibilidad de retirada y autorizaciones separadas.
- [ ] Solo entonces decidir AKS GO para esa ejecución concreta; no hacerlo desde esta checklist.
- [ ] Sin autorización específica: **AKS NO-GO, no apply**.

Gate B GO nunca sustituye este permiso. No reutilizar una autorización de otro plan.
No permiso implícito para cargas Kubernetes, fallo controlado, destroy o CD Azure.

## Fase 4 — Aprovisionamiento y validación prioritaria

**Solo tras autorización fase 3; no ejecutado al preparar esta checklist.**

- [ ] Aplicar exactamente el binario revisado con el helper y confirmaciones existentes.
- [ ] Supervisar operación; registrar inicio/fin/exit y recursos realmente creados.
- [ ] Si timeout/fallo, consultar operación/estado real, no repetir apply a ciegas.
- [ ] Verificar recursos y estado Terraform coherentes; backend/lease al finalizar.
- [ ] AKS Succeeded, Free/versión/red/identidad/Run Command false efectivos.
- [ ] Dos nodos SKU correcto, Ready; sistema/CNI/CSI sin errores críticos.
- [ ] Acceso Entra/kubelogin/kubectl, RBAC y restricción API efectivos; no --admin.
- [ ] Revisar tiempo, recursos activos/proyección de coste antes de cualquier prueba adicional.

Si hay permiso específico y margen, subset Wordle: __________.
- [ ] Desplegar app solo si fue autorizado; digests, secretos sintéticos, PVC y capacidad revisados.
- [ ] Evidencia Wordle solo si HTTP/SQL reales funcionan; no convertir Pods Running en juego válido.
- [ ] No afirmar Blue-Green/rollback/observabilidad AKS por su presencia local o pruebas kind.
- [ ] Acceptance/fallos reversibles requieren permiso propio y no deben comprometer T+160.

Resultado infraestructura: __________. Resultado app (o NO EJECUTADA): __________.

## Fase 5 — Evidencias mínimas y realistas

| Evidencia | Resultado que acredita | Ruta privada/referencia sanitaria |
| --- | --- | --- |
| Plan/SHA + apply y cronología | Acciones aprobadas y resultado real | __________ |
| Portal/listado Azure Wordle | Recursos y parámetros efectivos | __________ |
| AKS + nodos Ready | Infraestructura operativa | __________ |
| Lecturas kubectl/sistema/seguridad | Acceso Entra/RBAC y estado | __________ |
| Backend/lease pre/post | Estado operativo, sin secretos | __________ |
| Wordle/Ingress/HTTP/SQL, solo si desplegado | Aplicación realmente operativa | __________ / NO EJECUTADO |
| Destroy y comprobaciones ARM/estado | Retirada/ausencia observable | __________ |

- [ ] Recoger primero infraestructura; exportar antes de retirar.
- [ ] Distinguir evidencias existentes de CI/kind/GHCR y pruebas nuevas en AKS.
- [ ] Blue-Green, rollback, observabilidad, CD y reconstrucción no probados en
      esta ventana permanecen pendientes de evidencia real, sin cierres automáticos.
- [ ] No secretos/logs crudos/IP doméstica completa/planes binarios en material público.

## Fase 6 — Retirada separadamente autorizada

- [ ] Iniciar como máximo T+160 o antes si finalizó la validación; reservar limpieza.
- [ ] Exportar evidencia y resolver datos sintéticos conforme a decisión previa.
- [ ] Propietario autoriza plan-destroy/lease y revisión del inventario actual.
- [ ] Preflight de emergencia actual revisado: identidad, backend, estado, lease y recursos.
- [ ] Usar procedimiento elegido del runbook o script de emergencia, no ambos simultáneamente.
- [ ] Revisar binario de destrucción, hash e IDs/cascadas; solo recursos propios registrados.
- [ ] Autorización DESTROY independiente y explícita:
      referencia __________; hora __________; hash __________; responsable __________.
- [ ] Confirmaciones exactas del mecanismo; no Force, prefijos, state rm o desbloqueo automático.
- [ ] Backend excluido: rg-wordle-state / stwordletfgstate7c92d4 / tfstate /
      wordle/aks-demo.tfstate, incluidas versiones.
- [ ] Si falla el helper o la IA: seguir manual local alternativo; no cambiar arquitectura ni permisos.
- [ ] Huérfanos/ajenos se registran por ID y requieren autorización específica, no borrado automático.

La destrucción real de AKS no ha sido probada todavía. Ejecución autónoma validada
del preflight no garantiza éxito de destroy con recursos.

## Fase 7 — Cierre

- [ ] Operación terminada; estado consultable y vacío.
- [ ] AKS y ambos RG efímeros ausentes, inventario propio de discos/PV/snapshots/IP/LB/red revisado.
- [ ] Recursos residuales exactos registrados; si existen, NO declarar CLEAN.
- [ ] Backend/contenedor/key preservados, accesibles y lease libre; sin modificaciones inesperadas.
- [ ] Evidencias sanitizadas y logs conservados fuera de Git.
- [ ] Costes activos inesperados investigados; separar backend/retención y cargos ya devengados.
- [ ] Incidencias, tiempos y revisión posterior Cost Management con retraso documentados.
- [ ] Terminar únicamente forwards/procesos propios; PG-05/PG-06 y recursos ajenos intactos.

Resultado: CLEAN / PARTIAL CLEANUP / VERIFICATION FAILED: __________.
Fin real UTC: __________. Responsable/seguimiento: __________.
No usar “CLEAN” por exit0 de destroy sin verificación Azure.

## Hitos y presupuesto

| Hito objetivo | Decisión y registro |
| --- | --- |
| T0 | Inicio autorizado de ventana, no permiso implícito CREATE: __________ |
| T+30 | Preflight y plan revisados: __________ |
| T+60 | Provisión terminada o incidencia identificada: __________ |
| T+120 | Validaciones/evidencias prioritarias: __________ |
| T+160 | Inicio máximo previsto de retirada: __________ |
| T+240 | Retirada/cierre o escalamiento de residual: __________ |

Son objetivos, no tiempos garantizados. El runbook anterior reservaba hasta T+80
para provisión: T+60 es revisión temprana/objetivo, no razón para lanzar otro apply.
Si tarda más, recortar pruebas y mantener reserva, no alargar automáticamente.
Si apply está en curso al umbral, no lanzar destroy concurrente: diagnosticar y
obtener decisión humana. No se puede garantizar un plazo Azure ante avería.

Cuatro horas; objetivo USD 5. Modelo histórico ~USD 2,06/4 h, no precio confirmado,
tope o alerta automática. Control T+30/60/120/160/240: recursos-hora, nodos/surge,
discos, LB/IP/tráfico/IO y Storage. Registrar proyección __________ y fuente/fecha
__________. Cost Management puede mostrar cargos con retraso.
No cambiar SKU/región, crear budgets ni ampliar duración sin aprobación nueva.

## Decisiones ante incidentes

| Incidente / señal | Acción segura y parada | Evidencia | Permiso adicional |
| --- | --- | --- | --- |
| Autenticación/MFA: challenge/AADSTS | STOP; humano renueva solo identidad aprobada si autorizado | Código/categoría sanitaria | Reautenticación si no cubierta |
| IP cambió/VPN | No reutilizar /32 antiguo ni abrir firewall/API | Coincidencia sí/no, sin IP aquí | Cambio de acceso/inputs y nuevo plan |
| Backend inaccesible | STOP, diagnosticar red/servicio; no init “reparador” | Error/fecha/key sanitizado | Reparación separada |
| Lease bloqueado | Identificar dueño/operación; esperar, no force-unlock | Estado/proceso/hora | Cualquier intervención sobre lock |
| Plan inesperado | Rechazar CREATE; no -target/replaces improvisados | Direcciones/acciones | Nuevo alcance/corrección |
| Azure Policy/RBAC | No modificar política/rol para continuar | Código/política/acción | Resolución expresa |
| Capacidad/SKU | No cambiar región/tamaño automáticamente | Error/región/tiempo | Cambio arquitectónico |
| Apply parcial/timeout | Inventariar estado/ARM; no repetir ni destruir concurrentemente | IDs propios/estado/coste | Continuar o retirar explícitamente |
| AKS no operativo | Logs/eventos sanitizados, limitar pruebas | Condiciones/nodos | Cualquier modificación nueva |
| Conectividad perdida | Recuperar red; consultar operación real, no asumir rollback | Hora/contexto | Cambios red/acceso |
| Codex agotado/no disponible | Parar ampliaciones; manual/script local con revisión humana | Paso/tiempo/autorizaciones | DESTROY sigue separado; no permiso por emergencia |
| Destroy fallido | Registrar recursos residuales/coste, no reintento ciego | Estado/IDs/lease | Nuevo plan/recuperación aprobada |
| Huérfanos/recursos ajenos | No eliminar automáticamente | ID/tipo/propiedad/coste | Autorización exacta |
| Coste/proyección >USD5 | STOP pruebas; priorizar retirada aprobada | Modelo/activos/tiempo | Extensión/gasto extra si se propone |
| Reserva de limpieza amenazada | No nuevas pruebas largas; escalar al propietario | Tiempos/operación activa | Nueva decisión, sin prolongación implícita |

## Decisión final de readiness del día

- [ ] GO para solicitar permiso de plan privado (lecturas/lease diferenciados).
- [ ] GO para solicitar CREATE tras SHA revisado; autorización recibida: __________.
- [ ] NO-GO por condición crítica: __________.
- [ ] STOP/RECOVERY durante ejecución: __________.

Ninguna casilla está completada anticipadamente. Este documento no es una
autorización ni crea una automatización de expiración de recursos.
