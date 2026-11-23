# FIN-AKS-LIVE-DEPLOYMENT-PREFLIGHT — 22/11/2026

## 1. Resumen ejecutivo
**CONDITIONAL GO exclusivamente para solicitar autorización de planificación definitiva.**
No se autoriza ni ejecuta creación. Gate A GO; Gate B GO; AKS NO-GO.
Lecturas reales conformes: identidad/contexto, acceso backend, estado vacío, lease libre,
cuotas, SKU y versión. Incertidumbres antes de apply: MFA de escritura actual, capacidad
física, coste actualizado y retirada de AKS no ensayada.

## 2. Fecha y hora
Inicio del registro de integridad: 2026-11-22T10:22:41.509927+00:00.
Fin y duración del preflight se registran al pie. No se inicia el reloj de despliegue
ni la ventana de cuatro horas. Zona operativa Europe/Madrid; tiempos de registro UTC.

## 3. Alcance autorizado
Lectura local y Azure; propiedades Blob sin exportar contenido, terraform state list
y version; consultas ARM/Graph, cuotas, catálogo, Policy y presupuestos.
Solo este informe nuevo. Sin preflight completo del script ni pruebas funcionales.

## 4. Referencias revisadas
- docs/operations/FIN-AKS-DEPLOYMENT-RUNBOOK.md.
- docs/operations/FIN-AKS-FRIDAY-DEPLOYMENT-CHECKLIST.md (nombre histórico conservado).
- docs/operations/FIN-AKS-EMERGENCY-TEARDOWN.md.
- infra/scripts/Invoke-AksEmergencyTeardown.ps1.
- FIN-AKS-FRIDAY-DEPLOYMENT-READINESS y EMERGENCY-PREFLIGHT-LIVE-RETRY.
- FIN-AKS-POST-HARDENING-PLAN; main.tf, variables.tf, providers.tf y versions.tf.
La salida agregada inicial se truncó; las referencias operativas restantes se
releyeron selectivamente. Una lectura auxiliar tuvo error de codificación local:
se repitió en UTF-8, sin corrección de archivos ni efecto Azure.

## 5. Identidad Azure
Graph signed-in-user coincide exactamente con el humano aprobado b573130a…a831.
Sesión tipo user. No tokens consultados, mostrados o exportados.

## 6. Tenant y suscripción
Coincidencia exacta con referencias aprobadas: tenant aff0390f…1eb9,
suscripción 11306565…1bb5, estado Enabled. Sin account set ni cambio de contexto.

## 7. Estado de autenticación
Account, Graph, ARM y Blob login satisfactorios; sin error de interacción.
Azure CLI 2.86.0. No login ni renovación explícita de sesión.
No se conoce caducidad futura: éxito de GET no acredita escritura o eliminación.

## 8. IPv4 y conectividad
curl.exe -4 directo a api4.ipify.org y checkip.amazonaws.com: misma IPv4 pública/global,
válida para /32, coincidente con la única regla IPv4 de Storage (default Deny).
Dirección completa omitida. Cadena documental POST-HARDENING-PLAN vincula esa regla
con el /32 aprobado anteriormente; no comparación textual con una IP histórica en claro.
No hay API AKS desplegada que consultar. El plan futuro deberá usar el /32 vigente
expresamente aprobado, no ejemplos vacíos. Get-NetRoute IPv4: sin solapamiento observado
de rutas no predeterminadas con 10.10/16, 10.244/16 y 10.20/16.
No garantiza ausencia de cambios futuros de VPN/IP/rutas.

## 9. Backend
rg-wordle-state / stwordletfgstate7c92d4 / tfstate / wordle/aks-demo.tfstate.
Cuenta en swedencentral; RG con metadato location westeurope: son objetos distintos,
no cambio de región del almacenamiento. Blob accesible con --auth-mode login.
Metadatos locales coinciden con coordenadas, tenant/sub y use_azuread_auth=true;
sin claves/SAS/client_secret/OIDC/MSI inesperados en configuración local comprobada.
Inventario Azure relevante: únicamente la cuenta de estado en el RG persistente.

## 10. Estado remoto
Desde infra/terraform: terraform state list, exit 0, stdout vacío, stderr vacío:
**0 recursos gestionados**. No inferidos por tamaño.
resource list/group list filtrados a los grupos Wordle: rg-wordle-academic y
rg-wordle-academic-nodes ausentes y cero recursos en ambos.
No descarga completa/exportación del estado ni state pull.

## 11. Lease e integridad aparente
Antes/después de lecturas: unlocked/available, duration null, sin terraformlockid.
180 bytes; ETag idéntico "0x8DF448850E08ACA"; última modificación
2026-11-17T08:53:57+00:00; metadatos finales vacíos.
Sin adquisición/liberación deliberada de lock ni modificación observada.
Comparación de propiedades, no certificación criptográfica del contenido remoto.

## 12. Configuración Terraform
Terraform 1.9.8 y selección AzureRM 4.50.0 verificadas; provider fijado =4.50.0.
Seis recursos: RG, VNet, subnet, identidad UserAssigned, rol Network Contributor
limitado a subnet y AKS. Providers sin registro automático.
Defaults: swedencentral, Free, 1.35.9, 2 Standard_D4s_v5, Managed OS 64 GiB,
surge 1, Ubuntu, max_pods 30. Azure CNI Overlay, VNet 10.10.0.0/16,
subnet 10.10.0.0/24, pods 10.244.0.0/16, services 10.20.0.0/16,
DNS 10.20.0.10. Entra + Kubernetes RBAC, Azure RBAC false,
local_account_disabled=true y run_command_enabled=false.
API pública con variable obligatoria de un único /32 público y aprobación explícita;
grupo Entra y tenant/sub también son inputs obligatorios. No valores privados nuevos.
No fmt/validate repetidos: evidencia histórica del 17/11, inspección estática actual.
No plan ni validación runtime. Cero procesos Terraform al finalizar consultas locales.

## 13. Cuotas
vm list-usage real, swedencentral:

| Cuota | Límite vCPU | Uso | Libre |
| --- | ---: | ---: | ---: |
| DSv5 | 16 | 0 | 16 |
| Regional cores | 26 | 0 | 26 |

8 vCPU base y 12 con un surge caben en ambas. No solicitud de cuota.

## 14. SKU
Compute skus GET filtrado región: Standard_D4s_v5, standardDSv5Family,
SwedenCentral, restrictions=[]; sin nextLink pendiente.
Publicado sin restricción en respuesta actual; **no reserva de capacidad física**.

## 15. Versión Kubernetes
aks get-versions: 1.35.9 presente como clave patchVersions de 1.35;
no solo referencia de upgrade. Soporte publicado KubernetesOfficial/AKSLongTermSupport.
No creación de clúster de prueba.

## 16. Azure Policy
Assignments atScope devuelve tres, sin paginación pendiente ni exclusiones:
sys.blockwesteurope (deny), sys.mfa-write (Deny), sys.mfa-delete (DenyAction).
Definiciones GET verificadas: bloqueo location westeurope; MFA en identidad humana
mediante claims mfa o acrs p1; delete action protegido. Enforcement Default.
Sweden Central no coincide con la denegación regional observada.
Sin nuevas asignaciones en esta consulta. No auditoría universal de Conditional Access,
exenciones ni políticas fuera de la visibilidad del endpoint consultado.

## 17. MFA
Políticas de escritura/eliminación vigentes. No inspección de JWT.
Prueba histórica de RG vacío del 17/11 y preflight real posterior no prueban admisión
de apply/destroy AKS hoy. Mantener operador para cualquier challenge; detenerse y
pedir intervención si aparece, sin elusión de Policy/RBAC.

## 18. Presupuesto
GET Microsoft.Consumption/budgets de suscripción: value vacío, sin paginación.
No presupuesto/alertas asociados a budgets encontrados en ese ámbito; no prueba
ausencia de toda alerta o presupuesto de otro ámbito.
Modelo histórico ~USD2,06/4h, no cotización actual ni factura. Tarifas no reconsultadas.
USD5 es objetivo aceptado, sin cap automático. VM/discos/LB/IP/tráfico/IO/surge
y backend/versiones/retención pueden generar costes; backend es el único recurso
activo relevante observado. Coste actual y cargos diferidos permanecen inciertos.

## 19. Preparación de retirada
Script, manual autónomo y alternativa manual accesibles localmente.
PowerShell 5.1.26100.10068, Terraform 1.9.8 y CLI 2.86.0 funcionan.
LIVE-RETRY histórico: PASS exit0, inventario0/CLEAN y backend intacto.
No se repite script completo; no -Teardown.
**Destroy real de AKS no validado.** Manual exige revisión de IDs/cascadas,
autorizaciones separadas de plan-destroy y DESTROY, sin fuerza ni huérfanos automáticos.
Retirada debe comenzar como máximo T+160 de la futura ventana autorizada.
Disponibilidad de cuatro horas y operador confirmada por propietario, no automatizada.

## 20. Riesgos residuales
MFA/permisos de operaciones concretas, IP dinámica, capacidad regional,
tiempos de provisión/retirada, cargos diferidos y dependencia de PC/red/operador.
No temporizador cloud ni garantía de coste/plazo. No evidencia AKS runtime actual.
Los GET no acreditan permiso efectivo completo de CREATE/DELETE.
No recursos PG-05/PG-06, Nexo o Supabase utilizados.

## 21. Condiciones GO / NO-GO
CONDITIONAL GO para solicitar planificación: contexto/backend/estado/lease/configuración,
cuotas/SKU/versión y retirada documental conformes.
Antes de apply: plan definitivo privado nuevo y hash revisado, coste actualizado,
sesión/IP/contexto vigentes, permisos/admisión y disponibilidad de retirada.
Cualquier cambio de IP/regla, lock, inventario, identidad, Policy bloqueante,
cuota o disponibilidad invalida la recomendación: STOP/NO-GO, sin autocorrección.

## 22. Recomendación siguiente
Solicitar autorización específica para preparación externa, init del helper y
plan definitivo guardado con lease normal. No ejecutar todavía.
Revisar seis create, cero update/delete/replace, exclusión backend y SHA exacto.
CREATE/apply y retirada requieren decisiones posteriores independientes.

## 23. Integridad Git
Rama codex/pg01-07-consolidation; HEAD 4d56cf265cc5f0af8c72c64f2a93373660e8f122; índice vacío.
83 pendientes iniciales registrados por SHA-256. Únicamente este informe añadido.
Comprobación final y git diff --check se registran al pie.
Sin staging, limpieza, commits ni push; documentación histórica preservada.
No se ejecutaron init/plan/apply/destroy/refresh/force-unlock/state pull/-Teardown.
Sin cambios Azure, Entra, permisos, Policy, firewall, backend o estado remoto.

## 24. Gates finales
**Gate A GO · Gate B GO · AKS NO-GO.**
La recomendación es para planificación, no autorización de despliegue.
Detenerse y esperar instrucciones.

Fin de consultas UTC: 2026-11-22T10:26:08.084598+00:00; duración desde snapshot: 0:03:26.574671.

Integridad final: 83 pendientes preexistentes idénticos por SHA-256; HEAD intacto; índice vacío; 84 pendientes finales. Solo este informe nuevo. git diff --check exit 0. Advertencias LF/CRLF preexistentes en informe FIN-04, plan FIN, k8s/observability/run_observability.py y validation.py; sin correcciones.
