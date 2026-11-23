# FIN-AKS-LIVE-DEPLOYMENT-PLAN — 22/11/2026

## 1. Resumen ejecutivo
**PASS de planificación.** Un único plan real, exit 0: **6 create · 0 change · 0 destroy · 0 replace**.
Plan privado conservado; configuración crítica conforme; backend excluido; lease final libre.
Esto no autoriza apply. Gate A GO; Gate B GO; AKS NO-GO.

## 2. Alcance autorizado
Lecturas necesarias, fmt/validate, un plan -out con bloqueo normal, show legible/JSON
procesado localmente, SHA-256 y este informe. Sin init, apply, destroy o cambios de configuración.
Referencias: runbook, checklist Friday (nombre histórico), manual de emergencia,
LIVE-DEPLOYMENT-PREFLIGHT y POST-HARDENING-PLAN; configuración infra/terraform.
No auditoría completa ni repetición de cuotas/Policy del preflight inmediato.

## 3. Fecha y hora
Registro inicial de Git: 2026-11-22T10:28:55.290565+00:00.
Consultas: 2026-11-22T10:29:57.360143+00:00 a 2026-11-22T10:30:43.650213+00:00.
Plan: 2026-11-22T10:30:11.676260+00:00 a 2026-11-22T10:30:34.302071+00:00 UTC (22,63 segundos).
Zona operativa Europe/Madrid. No se inicia reloj de despliegue; no apply autorizado.

## 4. Identidad y contexto
Account show y Graph signed-in-user coinciden exactamente: humano b573130a…a831,
tenant aff0390f…1eb9, suscripción 11306565…1bb5, user/Enabled.
Sin login, cambio de contexto ni tokens mostrados. IPv4 de dos fuentes HTTPS coincide
con única regla /32 del backend vinculada a aprobación histórica; valor omitido.
Grupo Entra aprobado f35832fa…8ccc, sin grupos añadidos.

## 5. Versiones y validación
Terraform 1.9.8, AzureRM 4.50.0 comprobados.
terraform fmt -check -recursive: exit 0.
terraform validate -no-color: exit 0.
Sin init/upgrade/descargas. Sin overrides ARM_/TF_VAR_/TF_CLI_ARGS/TF_LOG/TF_DATA_DIR/
TF_WORKSPACE preexistentes. Variables aprobadas solo en entorno del subproceso:
tenant, suscripción, grupo, API /32 y aprobación. Resto defaults existentes.
No archivos de variables creados o modificados.

## 6. Backend
rg-wordle-state / stwordletfgstate7c92d4 / tfstate / wordle/aks-demo.tfstate.
Backend local azurerm coincide con coordenadas, tenant/sub y use_azuread_auth=true;
sin claves/SAS/client_secret/certificado/OIDC/MSI inesperados.
Acceso Blob --auth-mode login satisfactorio. No exportación de estado completo.

## 7. Estado inicial
terraform state list: exit 0, salida vacía, cero recursos.
84 pendientes Git, índice vacío, HEAD 4d56cf265cc5f0af8c72c64f2a93373660e8f122.
Configuración y pendientes del preflight preservados por comparación de huellas disponible.

## 8. Lease inicial
unlocked/available; duration null; sin terraformlockid.
Blob 180 bytes; ETag "0x8DF448850E08ACA";
lastModified 2026-11-17T08:53:57+00:00.

## 9. Comando utilizado
Desde infra/terraform, binario de usuario Terraform 1.9.8:
`terraform plan -input=false -no-color -lock=true -lock-timeout=60s -out="<carpeta privada>/wordle-aks.tfplan"`
**Una única invocación real.** Sin target/replace/destroy/auto-approve ni bypass de refresh/lock.
Stdout/stderr capturados en memoria, no publicados como logs crudos.

## 10. Ubicación privada
%LOCALAPPDATA%/WordleTFG/plans/20261122-f63b7de5c1cc47d0bade22325acd0bbf/wordle-aks.tfplan
Representación legible: misma carpeta, review.txt; ambas conservadas, fuera de Git y OneDrive.
Plan 9179 bytes. ACL heredada revisada: sin Allow a Everyone, Authenticated Users
o Builtin Users; no permisos modificados. No se certifica cifrado del disco.
JSON completo procesado en memoria, no guardado ni publicado.
Una revisión show auxiliar desde raíz falló por contexto local; repetida correctamente
desde infra/terraform. No se repitió plan ni se cambió configuración.

## 11. SHA-256 completo
`6217fbe2952eef657649e2b55e3d6949b56b393c2e54c39aad6009dfade85ff3`
Hash recomprobado después de show: idéntico.

## 12. Resumen de operaciones
6 create, 0 change, 0 destroy, 0 replace; plan complete=true, errored=false,
applyable=true (campo técnico, no autorización humana).

## 13. Inventario previsto
| Dirección | Recurso |
| --- | --- |
| azurerm_resource_group.wordle | rg-wordle-academic |
| azurerm_virtual_network.wordle | vnet-wordle-academic |
| azurerm_subnet.aks | snet-aks |
| azurerm_user_assigned_identity.aks | id-wordle-aks |
| azurerm_role_assignment.aks_network | Network Contributor sobre subnet |
| azurerm_kubernetes_cluster.wordle | aks-wordle-academic |
RG de nodos esperado rg-wordle-academic-nodes: dependencia administrada AKS,
no séptimo recurso Terraform. No recursos adicionales en resource_changes.

## 14. Comparación histórica
Mismo inventario y operaciones que POST-HARDENING-PLAN: 6/0/0/0.
Mismos parámetros críticos y Run Command false. Comparación semántica de campos
e inventario; no equivalencia binaria con plan histórico sin archivo -out.
Cuotas/Policy/SKU del preflight inmediato no se presentan como pruebas de apply.

## 15. Validación AKS
swedencentral, Free, Kubernetes 1.35.9; 2 Standard_D4s_v5, surge 1.
Managed OS 64 GiB/Ubuntu, max_pods30 según configuración existente.
run_command_enabled=false; local_account_disabled=true; Kubernetes RBAC true.
Todos los checks críticos del plan satisfactorios.

## 16. Validación de red
VNet 10.10.0.0/16, subnet 10.10.0.0/24, Azure CNI Overlay;
pods10.244.0.0/16, services10.20.0.0/16, DNS10.20.0.10.
API autorizado exclusivamente al /32 actual aprobado, comprobado en memoria.
API pública restringida, no clúster privado. Standard LB/salida loadBalancer existentes.
No nueva ampliación de acceso. Datos domésticos omitidos.

## 17. Validación de identidad
UserAssigned, Entra tenant/grupo aprobados; azure_rbac_enabled=false.
Referencias del plan configurado: rol.scope → azurerm_subnet.aks.id;
rol.principal_id → azurerm_user_assigned_identity.aks.principal_id.
Sin identidades adicionales; Network Contributor limitado a subnet, no suscripción.
Variables del JSON coinciden con las 19 declaradas, sin inputs inesperados.

## 18. Protección del backend
Cambios limitados a las seis direcciones aprobadas. Ningún RG de backend,
Storage Account, contenedor o state key como recurso a crear/modificar/eliminar.
Backend persistente excluido de infraestructura efímera.

## 19. Riesgos e incertidumbres
IDs/FQDN/kubeconfig/identidad kubelet/tenant-principal MI/rol y valores runtime son
known after apply normales; no credenciales extraídas. Bloques computed no prueban
servicios opcionales habilitados ni NetworkPolicy efectiva.
Capacidad física, admisión MFA/RBAC/Policy de CREATE/DELETE, duración y coste real
solo podrán acreditarse posteriormente. Plan no prueba nodos Ready ni retirada.
Modelo histórico ~USD2,06/4h, objetivo USD5 sin cap; no precio actualizado.
Destrucción real AKS no ensayada. Antes de crear, preservar reserva de retirada T+160.

## 20. Lease y estado final
Blob accesible; unlocked/available, duration null, sin bloqueo persistente.
180 bytes, ETag "0x8DF4883A43B453E"; lastModified 2026-11-22T10:30:34+00:00.
Cambio de metadatos temporalmente asociado al plan y locking autorizado; no evidencia
de alteración indebida por ese hecho. No comparación de contenido completo.
state list final exit0: cero recursos. ARM posterior: cero grupos/recursos en ambos
RG efímeros. Sin creación/eliminación de infraestructura.

## 21. Integridad del repositorio
Verificación final por SHA-256 al pie: pendientes previos y todos los archivos bajo
infra/terraform, incluyendo lock/proveedor/metadatos/caché, deben conservarse.
Plan externo no aparece entre candidatos versionables. Sin staging/commit/push.
Advertencias LF/CRLF existentes no se corrigen.

## 22. Recomendación para apply
Plan técnicamente conforme para revisión humana. **Apply NO AUTORIZADO / AKS NO-GO.**
Revisar SHA e inventario exactos y vigencia antes de cualquier decisión.
Runbook propone máximo30min y misma ventana; invalidar por drift/IP/contexto/cambios.
No ejecutar automáticamente ni reutilizar tras cambios sin nueva autorización.

## 23. Autorizaciones pendientes
CREATE/apply específico del hash, tiempo/coste/retirada; cargas Kubernetes y credenciales
si se desean, por separado; plan-destroy y DESTROY separados. No se conceden aquí.
No init, apply, destroy, refresh, force-unlock, state pull ni -Teardown ejecutados.
Sin cambios Terraform, Azure/Entra/Policy/RBAC/firewall; únicamente operaciones técnicas
normales de bloqueo/metadatos autorizadas, sin modificación deliberada del estado remoto.
Sin commits ni push.

## 24. Gates
**Gate A GO · Gate B GO · AKS NO-GO.**
PASS de planificación no autoriza despliegue. Detenerse y esperar aprobación expresa.

Integridad final: 84 pendientes previos y 15 archivos Terraform protegidos idénticos por SHA-256; HEAD intacto; índice vacío. 85 pendientes finales, solo este informe nuevo. git diff --check exit0. Advertencias LF/CRLF preexistentes en informe FIN-04, plan FIN y k8s/observability/run_observability.py y validation.py, sin corrección. Plan privado externo ausente de candidatos Git.
