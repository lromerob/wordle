# FIN-AKS-LIVE-DEPLOYMENT-APPLY — 22/11/2026

## 1. Resumen ejecutivo
**PASS.** Un único apply del binario/hash autorizado terminó exit0.
Seis recursos Terraform creados; AKS Succeeded; dos nodos Ready verificados mediante
API Kubernetes/Entra. Backend accesible y lease libre.
No Wordle/observabilidad/Blue-Green desplegados; no retirada ejecutada.
La infraestructura sigue activa y puede generar costes.

## 2. Autorización
Adjunto FIN-AKS-LIVE-DEPLOYMENT-APPLY del propietario: un apply del plan exacto,
lecturas previas/posteriores, comprobación de nodos e informe.
Sin nuevo plan/init/destroy, cambios de configuración o correcciones automáticas.

## 3. Plan aprobado
%LOCALAPPDATA%/WordleTFG/plans/20261122-f63b7de5c1cc47d0bade22325acd0bbf/wordle-aks.tfplan.
6 create, 0 change, 0 destroy, 0 replace. Las seis direcciones aprobadas coinciden
exactamente con resource_changes revisado antes de apply.

## 4. SHA-256 verificado
`6217fbe2952eef657649e2b55e3d6949b56b393c2e54c39aad6009dfade85ff3`
Recomprobado al inicio e inmediatamente antes de apply; coincidencia exacta.
Archivo y review.txt conservados fuera de Git/OneDrive; no contenido completo publicado.

## 5. Vigencia del plan
Plan iniciado 2026-11-22T10:30:11.676260+00:00; finalizado 10:30:34.302071 UTC.
Apply comenzó con antigüedad conservadora de 423.637322 segundos desde inicio
del plan, inferior a 1800 segundos. Verificación al ejecutar, no solo al autorizar.
Configuración protegida idéntica por hash a snapshot de planificación.

## 6. Identidad y suscripción
Account/Graph: humano aprobado b573130a…a831; tenant aff0390f…1eb9;
suscripción 11306565…1bb5, user/Enabled. Sin login ni cambio de contexto.
IPv4 pública de dos fuentes coincidente con firewall y variable /32 del plan;
dirección omitida. Conectividad ARM/Blob comprobada.

## 7. Backend inicial
rg-wordle-state / stwordletfgstate7c92d4 / tfstate / wordle/aks-demo.tfstate.
Metadatos locales inicializados coinciden con coordenadas/tenant/sub/use_azuread_auth.
Blob accesible, 180 bytes, lease unlocked/available,
sin terraformlockid. ETag "0x8DF4883A43B453E".
state list exit0, cero recursos antes de apply.
Herramientas 1.9.8/AzureRM4.50.0 comprobadas, sin init.

## 8. Hora T0
**2026-11-22T10:37:15.313582+00:00 UTC = 11:37:15.313582 Europe/Madrid.**
Inicio del reloj operativo inmediatamente antes de lanzar apply.
T+30:12:07:15; T+60:12:37:15; T+120:13:37:15;
**inicio máximo previsto de retirada T+160:14:17:15; cierre T+240:15:37:15 Madrid.**
No retirada automática ni autorización implícita.

## 9. Comando ejecutado
Desde infra/terraform, Terraform1.9.8:
`terraform apply -input=false -no-color "<ruta absoluta privada>/wordle-aks.tfplan"`
Un único proceso. Sin auto-approve/target/replace ni apply sin binario.
Salida cruda capturada en memoria; solo fases/tiempos sanitizados publicados.

## 10. Resultado del apply
Exit **0**; fin 2026-11-22T10:42:45.231527+00:00.
Duración desde T0: aproximadamente **5 min30 s**.
Sin categorías de error MFA/Policy/cuota/capacidad detectadas ni errores Terraform.
No reintento, cancelación o proceso Terraform concurrente lanzado.

## 11. Recursos creados
| Dirección | Creación completada UTC |
| --- | --- |
| azurerm_resource_group.wordle | 2026-11-22T10:37:43.270622+00:00 |
| azurerm_user_assigned_identity.aks | 2026-11-22T10:37:46.925253+00:00 |
| azurerm_virtual_network.wordle | 2026-11-22T10:37:52.557131+00:00 |
| azurerm_subnet.aks | 2026-11-22T10:37:59.153025+00:00 |
| azurerm_role_assignment.aks_network | 2026-11-22T10:38:24.954761+00:00 |
| azurerm_kubernetes_cluster.wordle | 2026-11-22T10:42:44.238776+00:00 |

Lectura ARM confirma VNet, identidad y AKS en rg-wordle-academic, Sweden Central.
Subnet/rol acreditados por apply y state list, no una lectura ARM independiente de cada hijo.
rg-wordle-academic-nodes contiene dependencias AKS: VMSS, NSG, identidad agentpool,
Standard LB y una IP pública de salida. Estas dependencias están autorizadas por el
aprovisionamiento AKS; no son despliegues manuales adicionales.

## 12. Estado AKS
ARM: Succeeded, Free, Kubernetes1.35.9, Sweden Central.
Pool System:2 Standard_D4s_v5, Succeeded, versión1.35.9, maxSurge1.
Cuentas locales deshabilitadas, KubernetesRBAC true, Run Command deshabilitado.
Entra managed, grupo/tenant aprobados exactos, AzureRBAC false, UserAssigned.
API una única /32; antes de apply coincide exactamente con el plan e IPv4 actual.
Red efectiva: azure/overlay, pods10.244/16, services10.20/16, DNS10.20.0.10,
salida loadBalancer y LBstandard. No prueba de NetworkPolicy.

## 13. Estado de nodos
Consulta real kubectl get nodes -o json: exit0.
**Dos nodos Ready=true, v1.35.9, Standard_D4s_v5, pool system.**
Acceso Entra mediante kubeconfig nuevo externo y kubelogin azurecli, sin --admin,
login interactivo, cambios RBAC ni workloads.
Archivo privado: misma carpeta del plan, aks-readonly.kubeconfig.
No se modificó kubeconfig predeterminado. PATH solo del subproceso para kubelogin.
No pruebas exhaustivas de sistema/CNI/CSI, aplicación o observabilidad.

## 14. Estado Terraform
state list posterior exit0, seis direcciones exactas:
- azurerm_kubernetes_cluster.wordle
- azurerm_resource_group.wordle
- azurerm_role_assignment.aks_network
- azurerm_subnet.aks
- azurerm_user_assigned_identity.aks
- azurerm_virtual_network.wordle
Sin state pull, show del estado completo, import o manipulación del inventario.

## 15. Estado del backend
Blob final accesible, 26927 bytes;
ETag "0x8DF488557E63A6E"; lastModified 2026-11-22T10:42:45+00:00.
Crecimiento esperado por estado de seis recursos tras apply. Actualizaciones normales
de estado/locking autorizadas; sin cambio de coordenadas/firewall/Storage/configuración.
Backend no incluido en recursos creados/destruidos.

## 16. Lease final
unlocked/available, duration null, sin terraformlockid.
No force-unlock ni manipulación manual de lease.

## 17. Tiempo consumido
Apply ~5min30s; comprobaciones adicionales posteriores dentro de la ventana.
El reloj sigue activo mientras permanezcan recursos; no termina al emitir informe.
No ampliar automáticamente240min. Retirada requiere autorización independiente y
debe comenzar antes de14:17:15Madrid; priorizarla si no se desean más verificaciones.

## 18. Riesgos residuales
Recursos activos: nodos/discosOS, LB/IP/red y backend/retenciones pueden facturar.
USD5 es objetivo, sin cap automático; coste actual no consultado ni garantizado.
Sesión/MFA/IP/red pueden cambiar antes de retirada. Destroy real no ensayado.
No cargas de aplicación o datos PostgreSQL creados en este clúster.
No afirmación de cierre completo del TFG, CD/Wordle/observabilidad/rollback en Azure.

## 19. Evidencias
Hash, T0, eventos de creación y exit observados en proceso real.
ARM resource list/aks list/aks show, state list, Blob show y kubectl get nodes.
Sin tokens, credenciales, kubeconfig, plan completo o IP personal en informe.
Credenciales de usuario solicitadas mediante get-credentials solo para comprobación
autorizada; custodiadas localmente fuera del repositorio.
No identidad/permiso creado manualmente fuera de la identidad/rol del plan.

## 20. Incidencias
Sin error de apply. Consulta auxiliar de parámetros ARM tuvo error local de nombre
de campo (authorizedIpRanges frente a variante de mayúsculas); corregida únicamente
la consulta de lectura, sin cambios de configuración ni segundo apply.
Descubrimiento local inicial de herramientas encontró LOCALAPPDATA de sandbox distinto;
se consultó ruta de usuario autorizada. Ninguna instalación o cambio global.

## 21. Operaciones pendientes
Decisión humana de retirada: autorización específica de plan-destroy y destrucción
tras revisar estado/inventario actuales y exclusión del backend.
Otras validaciones/cargas AKS requieren alcance nuevo; no se inician automáticamente.
No coste cero ni limpieza afirmada. Recursos permanecen activos.

## 22. Integridad Git
Rama codex/pg01-07-consolidation, HEAD 4d56cf265cc5f0af8c72c64f2a93373660e8f122.
85 pendientes iniciales capturados por hash; índice vacío.
Solo este informe nuevo; comprobación final registrada al pie.
Metadatos/proveedor/configuración locales Terraform deben conservarse; el estado remoto
sí se actualizó legítimamente por apply. No backend local sensible impreso.
Sin staging/commits/push ni limpieza de históricos.

## 23. Recomendación siguiente
Revisar este resultado y decidir retirada controlada con permisos separados.
Si se conserva temporalmente AKS para otra comprobación, autorizarla explícitamente
sin comprometer T+160. No aplicar de nuevo el plan ya consumido.
No plan adicional, init, destroy, force-unlock, import, state pull o -Teardown.
Sin cambios de archivos Terraform, variables, providers, firewall o Policy/Entra.
La identidad y rol previstos se crearon por Terraform autorizado; no RBAC manual.

## 24. Gates
**Gate A GO · Gate B GO · AKS aprovisionamiento PASS / GO técnico acreditado.**
Dos nodos Ready no equivalen a validación completa Wordle/TFG en Azure.
No permiso implícito de cargas adicionales ni destrucción.
Detenerse y esperar instrucciones del propietario.

Verificación final 2026-11-22T10:45:13.233368+00:00: 85 pendientes y 15 archivos Terraform locales protegidos idénticos por SHA-256; HEAD intacto; índice vacío; 86 pendientes finales, solo este informe nuevo. git diff --check exit0. Advertencias LF/CRLF previas en informe FIN-04, plan FIN y k8s/observability/run_observability.py y validation.py, sin corregir.
