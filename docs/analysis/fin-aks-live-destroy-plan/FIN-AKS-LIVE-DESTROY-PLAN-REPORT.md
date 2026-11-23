# FIN-AKS-LIVE-DESTROY-PLAN — 22/11/2026

## 1. Resumen ejecutivo
**PASS del plan de retirada.** Un único plan -destroy exit0:
**0 create · 0 change · 6 destroy · 0 replace**.
Inventario ARM coherente con apply, sin recursos adicionales observados; grupo de nodos
managedBy del AKS exacto. Backend excluido y lease final libre.
**No se ejecutó apply ni destroy. Recursos activos, retirada pendiente de autorización.**

## 2. Alcance autorizado
Lecturas, un único terraform plan -destroy -out con bloqueo normal, show,
SHA-256 e informe. Sin init ni cambios de configuración.
Referencias operativas revisadas en esta sesión: runbook, checklist Friday y manual,
script Invoke-AksEmergencyTeardown.ps1, LIVE-DEPLOYMENT-PREFLIGHT/PLAN/APPLY,
configuración infra/terraform. Históricos intactos.
Sin repetir auditorías completas o pruebas de aplicación.

## 3. Fecha y hora
Inicio registro Git 2026-11-22T10:48:03.258653+00:00.
Consultas 2026-11-22T10:49:09.834418+00:00 a 2026-11-22T10:50:13.136537+00:00.
Plan 2026-11-22T10:49:28.465389+00:00 a 2026-11-22T10:50:03.100456+00:00 UTC, duración34,64s.
Revisión complementaria del rol/hash10:50:32UTC; revisión final de IDs posterior.
Hora/tiempo restante exactos de cierre al pie. Europe/Madrid=UTC+1 hoy.

## 4. Tiempo desde T0
T0 original2026-11-22T10:37:15.313582+00:00 (11:37:15Madrid).
Inicio de esta revisión aproximadamente T+11min.
Límite inicio retirada14:17:15Madrid; cierre15:37:15.
Preparar el plan no detiene facturación ni reinicia el reloj.

## 5. Identidad y suscripción
Account/Graph exactos: humano b573130a…a831, tenant aff0390f…1eb9,
suscripción11306565…1bb5, user/Enabled. Sin login/cambio de contexto.
Dos consultas IPv4 HTTPS coinciden; IPv4 global y misma /32 de firewall y API AKS.
Dirección omitida. Sin cambios de acceso.

## 6. Backend
rg-wordle-state / stwordletfgstate7c92d4 / tfstate / wordle/aks-demo.tfstate.
Metadatos locales azurerm/tenant/sub/use_azuread_auth comprobados.
Blob login accesible; coordenadas preservadas. Terraform1.9.8/AzureRM4.50.0.
Sin overrides inesperados ni otro proceso Terraform activo en preflight.

## 7. Estado inicial
Seis direcciones Terraform exactas, state list exit0.
Blob26927bytes, ETag"0x8DF488557E63A6E",
lastModified2026-11-22T10:42:45+00:00; unlocked/available sin lockmetadata.
Configuración idéntica por hash al apply. Manual y script accesibles.

## 8. Inventario ARM
Inventario de ambos grupos coincide exactamente por tipo/nombre/grupo con apply:

| Grupo | Recurso |
| --- | --- |
| rg-wordle-academic | Microsoft.ManagedIdentity/userAssignedIdentities: id-wordle-aks |
| rg-wordle-academic | Microsoft.Network/virtualNetworks: vnet-wordle-academic |
| rg-wordle-academic | Microsoft.ContainerService/managedClusters: aks-wordle-academic |
| rg-wordle-academic-nodes | Microsoft.Network/publicIPAddresses: 79d08f45-0619-4e22-b165-0260bfa88a2e |
| rg-wordle-academic-nodes | Microsoft.Network/loadBalancers: kubernetes |
| rg-wordle-academic-nodes | Microsoft.ManagedIdentity/userAssignedIdentities: aks-wordle-academic-agentpool |
| rg-wordle-academic-nodes | Microsoft.Network/networkSecurityGroups: aks-agentpool-16059026-nsg |
| rg-wordle-academic-nodes | Microsoft.Compute/virtualMachineScaleSets: aks-system-11527481-vmss |

rg-wordle-academic sin managedBy ajeno; rg-wordle-academic-nodes.managedBy coincide
exactamente con ID de aks-wordle-academic. AKS Succeeded.
No titularidad inferida únicamente por pertenencia a grupo; comparación con inventario
del apply y relaciones de propiedad. No recurso adicional o no reconocido observado.

## 9. Inventario Terraform
- azurerm_kubernetes_cluster.wordle
- azurerm_resource_group.wordle
- azurerm_role_assignment.aks_network
- azurerm_subnet.aks
- azurerm_user_assigned_identity.aks
- azurerm_virtual_network.wordle
Seis recursos independientes; dependencias internas AKS no se cuentan como direcciones extra.

## 10. Comando utilizado
Desde infra/terraform, Terraform1.9.8:
`terraform plan -destroy -input=false -no-color -lock=true -lock-timeout=60s -out="<carpeta privada>/wordle-aks-destroy.tfplan"`
Una única invocación real; sin target/replace/refresh=false/lock=false.
Variables aprobadas en entorno del subproceso: tenant/sub, grupoEntra y misma API/32
con aprobación; otros valores defaults existentes. Sin variables/configuración editadas.

## 11. Resultado del plan
Exit0. Archivo no vacío, 24307 bytes.
show legible guardado privadamente en review.txt; show JSON procesado solo en memoria.
Exactamente seis resource_changes con actions=[delete]; ningún create/update/replace.
No segundo plan ni correcciones automáticas.

## 12. Recursos que serán destruidos
RG rg-wordle-academic, VNet vnet-wordle-academic, subnet snet-aks,
MI id-wordle-aks, rol Network Contributor de esa MI en esa subnet y AKS aks-wordle-academic.
IDs comparados con suscripción/RG/nombres exactos; rol ID bajo subnet y scope exacto.
Principal del rol coincide con MI UserAssigned y AKS referencia esa misma MI.
No identidad/red compartida o ajena incluida entre estas seis direcciones.

## 13. Dependencias AKS
Grupo administrado rg-wordle-academic-nodes: VMSS/pool, discosOS dependientes,
NSG, identidad agentpool, LB e IPsalida pueden eliminarse en cascada.
Terraform no enumera individualmente todas estas dependencias; inventario ARM
independiente revisado. No disco independiente adicional listado; no significa que
VMSS carezca de discosOS gestionados. No PostgreSQL/PVC/Wordle desplegado aquí.
No garantía universal sobre recursos ocultos o cambios posteriores de terceros.

## 14. Recursos excluidos
No otros RG, suscripciones, redes/identidades ajenas o recursos de Nexo/PG-05/PG-06.
Backend y sus versiones/retención/firewall/permisos excluidos.
No creación, migración, despliegue de aplicación ni modificación de suscripción.

## 15. Protección del backend
Lista cerrada de seis direcciones y validación de IDs bajo rg-wordle-academic.
Ningún recurso Storage/contenedor/key ni rg-wordle-state en cambios del plan.
No actuación manual sobre blob/lease/retención/versiones o acceso.

## 16. Ruta privada
%LOCALAPPDATA%/WordleTFG/plans/destroy-20261122-501926820ec74b4d85db1a421ddf3094/wordle-aks-destroy.tfplan
Representación legible: misma carpeta/review.txt.
Carpeta nueva fuera de repo y OneDrive; no sobrescribe plan de creación.
ACL sin entradas Allow a Everyone/AuthenticatedUsers/BuiltinUsers; sin permisos cambiados.
Plan y review conservados, sin publicación ni JSON completo almacenado.

## 17. SHA-256
`7faf0be02baae5ce8417b5e268c6d21e98fa2703c88644b017dc8ccc24281da6`
Calculado tras generación y recomprobado tras inspección: idéntico.

## 18. Vigencia
Máximo30min para aprobación e inicio de ejecución posterior.
Referencia conservadora: generación iniciada10:49:28.465389UTC;
**caducidad operativa11:19:28UTC =12:19:28Madrid**.
No basta autorización dentro del plazo: debe comenzar ejecución antes de caducar.
Si cambia inventario/configuración/IP/contexto/estado, invalidar aunque no haya expirado.
Sin regeneración automática.

## 19. Lease final
unlocked/available; durationnull; sin terraformlockid.
Blob accesible26927bytes; ETag"0x8DF48865CE53D32";
lastModified2026-11-22T10:50:03+00:00.
Cambio de metadatos compatible con bloqueo/liberación autorizados; sin modificación
deliberada de contenido o manipulación manual. Sin force-unlock.

## 20. Estado Terraform final
state list exit0, mismas seis direcciones. Inventario ARM posterior idéntico al previo.
No recurso destruido, ningún apply ejecutado en esta iteración.
No se infiere ausencia de destrucción solo del exit del plan: inventario complementario.

## 21. Riesgos residuales e incidencia de revisión
Costes siguen activos, objetivoUSD5 sin cap; no coste real calculado hoy.
Retirada puede requerir MFA y tiempo variable. Sin garantía de destroy por plan correcto.
Una comprobación auxiliar marcó WRONG_ROLE al comparar contra principalId de nivel
superior AKS, que no es la identidad UserAssigned. Se detuvo esa revisión y se aclaró
mediante show del mismo plan: principal_id del rol=principal_id MI, scope=subnet,
AKS.identity_ids contiene MI exacta; todos conformes. Error de comprobación local,
no cambio real de rol ni permiso. No segundo plan, edición o acción Azure para resolverlo.

## 22. Tiempo restante
Cálculo exacto al pie a partir del reloj UTC, T0 y límites originales.
Si se alcanza14:17:15 sin permiso, comunicar/escalar, nunca destroy automático.
La caducidad del plan12:19:28Madrid ocurre antes que el límite de retirada.

## 23. Integridad Git
Rama codex/pg01-07-consolidation; HEAD4d56cf265cc5f0af8c72c64f2a93373660e8f122, índice vacío.
86 pendientes iniciales por hash, más15 archivos protegidos bajo infra/terraform.
Resultado final al pie. Solo informe nuevo dentro del repositorio.
No staging/commits/push, scripts/pruebas/configuración modificados ni limpieza.

## 24. Recomendación
Plan conforme para decisión humana específica de ejecución de retirada.
Revisar hash/ruta/alcance/cascadas y vigencia; revalidar contexto/estado/lease/inventario
antes de ejecutar únicamente el binario aprobado si se autoriza.
No ejecutar ahora: autorización de apply/destroy separada.

## 25. Autorizaciones pendientes y gates
**Retirada pendiente de autorización específica del propietario para este archivo y hash.**
GateA GO; GateB GO; AKS aprovisionado y operativo (sin retirada realizada).
No apply, destroy, init, force-unlock, state pull o -Teardown en esta iteración.
Sin archivosTerraform, variables, permisos, Policy, Entra o firewall modificados.
Solo plan-destroy con locking/metadatos normales autorizados.
Detenerse y esperar instrucciones.

Cierre 2026-11-22T10:51:57.731013+00:00 UTC; Madrid 2026-11-22T11:51:57.731013+01:00. Desde T0: 0:14:42.417431; hasta inicio máximo retirada: 2:25:17.582569; hasta cierre objetivo: 3:45:17.582569.
Integridad final: 86 pendientes y15 archivosTerraform locales protegidos idénticos por SHA-256; HEAD intacto, índice vacío; 87 pendientes finales, solo este informe nuevo. git diff --check exit0. Advertencias LF/CRLF preexistentes en informe FIN-04, planFIN y k8s/observability/run_observability.py y validation.py, sin corregir. Plan externo ausente de candidatosGit.
