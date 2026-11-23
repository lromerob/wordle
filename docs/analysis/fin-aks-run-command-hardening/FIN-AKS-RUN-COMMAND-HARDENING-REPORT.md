# FIN-AKS-RUN-COMMAND-HARDENING — 17/11/2026

## 1. Resumen ejecutivo

**PASS.** run_command_enabled=false añadido explícitamente al único recurso AKS.
Esquema local AzureRM 4.50.0 compatible; fmt y validate exit 0, sin advertencias.
Cinco regresiones offline aprobadas, cero omitidas. Sin dependencia Run Command
detectada en scripts, workflows o manifiestos inspeccionados.
No Azure, backend remoto ni Terraform plan ejecutados. No prueba de despliegue.

## 2. Autorización y alcance

Solo cambio local Run Command, consultas locales de esquema, formato/validate,
pruebas focalizadas e informe. Sin init, plan, apply, destroy, import, refresh,
state, actualización de proveedor o acceso al estado remoto.
Sin operaciones Azure/Entra, autenticación, staging, commits o push.

## 3. Estado inicial

Raíz infra/terraform, rama codex/pg01-07-consolidation, HEAD
4d56cf265cc5f0af8c72c64f2a93373660e8f122 e índice vacío.
69 pendientes preexistentes registrados por SHA-256; main.tf ya tenía cambios
anteriores, preservados. Run Command no figuraba explícitamente.
Arquitectura actual conserva región y demás parámetros mediante variables aprobadas;
no se suministran valores privados ni se ejecuta un plan nuevo.

## 4. Referencias revisadas

DEPLOYMENT-BLOCKERS, TERRAFORM-PLAN, MFA-POLICY-VALIDATION,
MFA-WRITE-DELETE-TEST y PROVIDER-SCHEMA-VALIDATION.
Inspección selectiva de main.tf, versions.tf, lock y scripts operativos.
[Implementación AzureRM v4.50.0](https://github.com/hashicorp/terraform-provider-azurerm/blob/v4.50.0/internal/services/containers/kubernetes_cluster_resource.go):
atributo líneas 1324–1328; actualización 1982–1986; expansión 3026–3029.

## 5. Versiones de herramientas

terraform version -json: exit 0, Terraform 1.9.8 windows_amd64,
provider_selections registry.terraform.io/hashicorp/azurerm=4.50.0.
required_providers fija =4.50.0; ejecutable local disponible.
Sin instalación, init ni descarga de proveedor. No se actualiza por advertencia
terraform_outdated=true de version -json: no es error de validate.

## 6. Esquema AzureRM 4.50.0

terraform providers schema -json: exit 0, stderr vacío.
azurerm_kubernetes_cluster.run_command_enabled: type=bool, optional=true.
El JSON público de esquema no incluye default/ForceNew; se complementa con código
oficial del tag exacto: Default=true y sin ForceNew en este atributo.
La actualización detecta HasChange y actualiza ApiServerAccessProfile.
false se transforma en DisableRunCommand=true también en la creación.
No reemplazo exigido por este atributo según implementación; no garantía global
sobre un plan futuro ni sobre todas las restricciones del servicio.

Para evitar que providers schema cargase el backend remoto del directorio real,
se consultó en un directorio temporal aislado sin configuración remota:
configuración mínima de proveedor, copia del lock y enlaces locales al binario
ya instalado. Sin init ni red; esquema proyectado en memoria.
Directorio temporal eliminado al salir; no copia de estado ni secretos.

## 7. Configuración inicial de Run Command

Atributo omitido en main.tf: default implícito true según versión fijada y plan
histórico. No había dependencia explícita del mecanismo en scripts inspeccionados.

## 8. Modificación aplicada

Solo infra/terraform/main.tf, dentro de azurerm_kubernetes_cluster.wordle:
    run_command_enabled               = false

No variable nueva ni refactorización. Finales de línea originales preservados.
No cambios a región, nombres, Kubernetes, Free, pool, surge, red, identidad,
RBAC, Entra, grupo, API /32, tags, outputs, backend o versiones.

## 9. Diff funcional

Diferencia respecto al archivo inmediatamente anterior a esta iteración:
    local_account_disabled            = true
  + run_command_enabled               = false
    private_cluster_enabled           = false

Exactamente una línea añadida. No se confunde el diff acumulado frente a HEAD
(con trabajo anterior) con este incremento. Se verifica contra snapshot previo.

## 10. Resultado de terraform fmt

Desde infra/terraform: terraform fmt -check -recursive.
Exit 0; stdout y stderr vacíos. No fue necesario escribir formato.

## 11. Resultado de terraform validate

Desde infra/terraform: terraform validate -no-color.
Exit 0: Success! The configuration is valid. Stderr vacío.
CHECKPOINT_DISABLE=1 y TF_IN_AUTOMATION=1 solo en subprocesos.
Validación local con plugin instalado, sin init/configuración del proveedor
contra Azure. No prueba admisión regional, plan ni comportamiento runtime.

Regresiones pertinentes: 5/5, cero omitidas:
defaults región/pool, restricciones de tamaño/cantidad, API /32/aprobación,
backend independiente y rechazo de credenciales/backend o API abiertos.
subprocess.run/Popen y conexiones/resolución de red bloqueados durante esas pruebas.
No se repitieron suites de aplicación ni demostraciones kind.

## 12. Dependencias encontradas

Búsqueda en scripts/, .github/ y k8s/: sin usos de command invoke,
command result, runcommand o run_command previos.
aks_run.py usa az aks get-credentials y kubelogin convert-kubeconfig -l azurecli;
aks_recovery.py construye comandos kubectl.
No dependencia incompatible identificada; no scripts modificados.
La inspección estática no demuestra un despliegue cloud completo.

## 13. Impacto operativo

Se pierde ejecución/diagnóstico mediante AKS Run Command por ARM.
Permanecen kubectl, API Kubernetes, get-credentials y kubelogin, sujetos a red,
allowlist /32, Entra y autorización Kubernetes.
Manifiestos, CI/CD, Ingress, observabilidad y evidencias mantienen sus mecanismos
de API normales. Los jobs kind no dependen de Run Command.
Sin acceso al API, se pierde esa vía alternativa de diagnóstico: preparar
conectividad y recuperación autorizada del /32, sin abrirlo indiscriminadamente.
No cambio de estrategia de creación/destrucción ARM ni de persistencia.

## 14. Impacto de seguridad

Reduce una vía administrativa adicional mediante ARM capaz de ejecutar comandos
en el clúster. No elimina RBAC/Entra ni cambia permisos del operador.
El /32 del API Kubernetes no debe presentarse como equivalente a controlar
todas las operaciones ARM. No se afirma seguridad absoluta por este atributo.

## 15. Riesgos residuales

Credenciales, RBAC, contexto MFA, políticas heredadas, conectividad, capacidad,
coste y retirada siguen requiriendo verificación en la futura operación autorizada.
MFA de RG vacío acreditado no garantiza todos los tipos AKS.
No comprobación runtime de Run Command deshabilitado porque no se despliega.
Un futuro plan debe revisar el efecto junto con los demás cambios pendientes.

## 16. Integridad del repositorio

Único cambio funcional nuevo: una línea en main.tf; único archivo nuevo: este informe.
Otros pendientes, lock, proveedores y caché/metadatos locales conservados por SHA-256.
HEAD intacto e índice vacío. Sin staging, limpieza, commits o push.
git diff --check: exit 0, sin errores de whitespace. Advertencias LF/CRLF
preexistentes: informe FIN-04, plan FIN, observability/run_observability.py y
observability/validation.py. Sin corregirlas. Los otros 68 pendientes previos
están intactos; total final 70 pendientes (69 previos más este informe).
No consulta/modificación de backend o estado remoto.

## 17. Estado Gate A

**GO**, mantenido por evidencia previa, sin operaciones de backend.

## 18. Estado Gate B

**NO-GO**. Validación local no cambia el gate.

## 19. Estado AKS

**NO-GO**. Sin AKS creado ni Azure/Entra/permisos modificados.

## 20. Próxima acción recomendada

FIN-AKS-POST-HARDENING-PLAN, con autorización independiente para lecturas Azure,
verificar estado remoto y ejecutar/revisar un plan vigente.
No iniciar ahora. No init/plan/apply/destroy ejecutados en este incremento.
