# Wordle — Runbook de primera ventana AKS

Fecha: 17/11/2026. **Preparado, NO ejecutado.**
Gate A GO; **Gate B GO ratificado por el propietario en FIN-AKS-DEPLOYMENT-WINDOW-PREP**;
AKS NO-GO. Esta decisión posterior no reescribe gates históricos.

## 1. Objetivo y alcance

Operación por una sola persona sobre Wordle, en una ventana de cuatro horas.
Primera prioridad: crear AKS, validar infraestructura, recoger evidencia y retirarlo.
Wordle/Blue-Green/observabilidad son fases opcionales de esta ventana, con autorización
propia y tiempo suficiente. No convertir infraestructura Ready en cumplimiento del TFG.
No usar Nexo, PG-05/PG-06, Supabase ni datos reales.

**Todos los comandos son futuros. No ejecutar este documento como un script.**
R = lectura (solo tras autorización de consultas); L = escritura local privada;
C = creación/modificación; D = destrucción.
**Todo L/C/D: NO AUTORIZADO EN ESTA ITERACIÓN.**
Los planes escriben archivos privados y lease/metadatos: requieren autorización aunque
no creen infraestructura. Dry-run server de Kubernetes también contacta admisión;
no confundir con una mera lectura local.

## 2. Arquitectura y fuentes

infra/terraform: seis recursos (RG/VNet/subnet/MI/rol subnet/AKS), Terraform 1.9.8,
AzureRM 4.50.0. swedencentral, Free, Kubernetes 1.35.9, dos Standard_D4s_v5,
surge "1", Ubuntu OS Managed 64 GiB. VNet 10.10.0.0/16, subnet 10.10.0.0/24,
pods 10.244.0.0/16, Services 10.20.0.0/16, DNS 10.20.0.10.
Entra + Kubernetes RBAC, Azure RBAC false, cuentas locales off,
API pública limitada al /32 aprobado, Run Command false.

Conservar siempre backend: rg-wordle-state / stwordletfgstate7c92d4 /
tfstate / wordle/aks-demo.tfstate. No pertenece al módulo desechable.
Targets: rg-wordle-academic, rg-wordle-academic-nodes, aks-wordle-academic.

Usar k8s/aks-full para ensayo integrado: observability → blue-green → demo-kind,
imágenes por digest y PostgreSQL único compartido, PVC managed-csi 8 GiB.
No sustituir por k8s/aks: es otro perfil, con referencias de imágenes diferentes.
Servicios de demo privados ClusterIP; Traefik con port-forward loopback.

Referencias: los nueve informes FIN-AKS indicados en el informe de preparación,
docs/operations/azure-demo.md, TFG-COMPLETION-PLAN, TFG-COMPLIANCE-MATRIX y
TFG-DEFENSE-EVIDENCE. Matriz/plan de defensa conservan descripciones históricas;
contrastar con informes fechados y evidencia runtime, sin declarar cierres nuevos.

## 3. Autorizaciones y preparación local

Antes de fijar fecha, propietario/operador debe estar disponible para MFA y retirada.
Registrar inicio real T0, límite T0+240 min, zona horaria y equivalentes UTC.
No reservar horas absolutas ficticias. Preparar custodia privada fuera de Git/OneDrive
compartido para variables, credenciales sintéticas, kubeconfig, planes y evidencias.

Definir en futura sesión PowerShell: $Repo (raíz Wordle), $Private (directorio privado
externo), $Work (nuevo workspace de creación vacío), $DestroyWork (otro nuevo vacío),
$Subscription (ID aprobado), $Kubeconfig (archivo nuevo), $Context='wordle-azure-supervised'.
Usar .venv/Scripts/python.exe como $Py; ruta de usuario existente Terraform como $Tf,
y kubelogin v0.2.22. PATH, si necesario para helpers, solo en esa sesión.
No modificar configuración global ni instalar automáticamente herramientas.

Preparar variables.json/backend.json externos según ejemplos reales y revisar valores:
IDs aprobados, mismos nombres/backend, versión/región/SKU/nodos, grupo y /32 vigente.
Los ejemplos []/false y suscripción placeholder NO son ejecutables.
Credenciales de demo: tres sintéticas distintas >=32 caracteres, inyectadas
mediante mecanismo privado sin historial/echo, nunca secretos personales.

Autorizaciones independientes con objetivo, hora, alcance y responsable:
1. Preflight remoto + preparación/init/plan privado guardado.
2. CREATE del SHA-256 exacto revisado y presupuesto.
3. Credenciales y cargas Kubernetes; verify escribe datos sintéticos.
4. Acceptance provoca fallo, tráfico y REVOKE/GRANT reversible: autorización aparte.
5. Plan de retirada y DESTROY exacto, incluso en caso de create parcial.

Acordar antes de CREATE que el responsable estará disponible para autorizar retirada;
el runbook no concede permiso automático de destruir.
No arrancar si esa disponibilidad no está asegurada.

## 4. Preflight futuro — checklist ejecutable

No ejecutado ahora. Cualquier fallo crítico impide solicitar CREATE.

| Control | Tipo / mecanismo previsto | Éxito y evidencia | Si falla |
| --- | --- | --- | --- |
| Identidad | R: az account show; az ad signed-in-user show | IDs exactos de informes, user, Enabled; registro sanitizado | STOP, no account set automático |
| Permisos/MFA | R: permisos efectivos ARM y grupo Entra; políticas heredadas atScope | RG/red/MI/rol/AKS y permisos Blob; evidencia MFA contextual reciente | No inferir MFA de GET; reauth solo autorizada |
| IP | R: dos fuentes IPv4 HTTPS de informes y rutas locales | Misma global /32 expresamente aprobada; sin VPN inesperada | STOP si cambió; no abrir API/Storage |
| CIDR | R/local: revisar rutas y rangos declarados | Sin conflicto conocido; confirmación del propietario | No cambiar rangos automáticamente |
| Backend | R: metadatos locales y propiedades Blob login | Coordenadas exactas, key accesible, unlocked/available y sin lock metadata | STOP; no force-unlock |
| Estado | R: terraform state list, con acceso autorizado | Cero recursos en primera creación | Si no vacío, revisar alcance antes de seguir |
| Herramientas | Local: versiones, lock y proveedor existente | 1.9.8/4.50.0, hashes preservados | No upgrade/init improvisado |
| Validación | Local: terraform fmt -check -recursive; terraform validate -no-color | Exit 0, sin diagnósticos nuevos | STOP; corrección requiere otro alcance |
| Región/versión | R: az aks get-versions --location swedencentral --subscription $Subscription | 1.35.9 disponible | STOP |
| SKU/cuotas | R: Compute SKU filtrado región y vm list-usage | D4s_v5 sin restricción, 8 vCPU base/12 con surge disponibles; cuota DSv5 y regional | STOP; catálogo no reserva capacidad |
| Políticas | R: assignments atScope + definiciones/exenciones | Cambios respecto a antecedentes identificados | STOP si nueva denegación |
| Colisiones | R: group exists para ambos RG destino y aks show si procede | Grupos ausentes para primera ejecución | No reutilizar ni borrar recursos preexistentes |
| Concurrencia | Local procesos Terraform + R despliegues Wordle/lease | Sin operación paralela conocida | Esperar/diagnosticar, no romper locks |
| Fuentes/imágenes | Local hashes + consulta pull autorizada | Snapshot del trabajo pendiente y digests de images.lock.json recuperables | No reconstruir/publicar imágenes por extensión |
| Operación | Confirmación humana | 4 h disponibles, objetivo 5 USD, retiro/evidencia definidos | NO-GO |

Para Blob, usar solo propiedades (no descargar estado completo):
```powershell
# R — FUTURO, no ejecutado ahora
az storage blob show --account-name stwordletfgstate7c92d4 --container-name tfstate --name wordle/aks-demo.tfstate --auth-mode login --subscription $Subscription --query "{lease:properties.lease,bytes:properties.contentLength}"
```
Sanitizar salidas antes de publicarlas. No ejecutar az account get-access-token para
mostrar tokens, --debug, state pull o consultas de Secret.
Al preparar workspace, confirmar backend default/key exactos y exclusión del RG estado.

## 5. Secuencia de despliegue — C/L NO AUTORIZADOS EN ESTA ITERACIÓN

Ruta preferida: helper existente scripts/azure_supervised.py, con workspace externo.
El helper plan hace init y guarda approved.tfplan; execute hace init -reconfigure
y apply del binario. **Estas acciones internas deben figurar en la autorización futura.**
No es una continuación automática del último plan sin -out.

```powershell
# L — NO AUTORIZADO EN ESTA ITERACIÓN
& $Py -B scripts/azure_supervised.py prepare --workdir $Work --variables "$Private/variables.json" --backend "$Private/backend.json"
# L/lease — NO AUTORIZADO EN ESTA ITERACIÓN
& $Py -B scripts/azure_supervised.py plan --workdir $Work --confirm "PLAN rg-wordle-academic/aks-wordle-academic"
```
Comprobar $LASTEXITCODE tras cada comando y detenerse si no es cero.
Revisar privadamente review.txt/review.json y approved.tfplan:
6 create, 0 update/delete/replace, parámetros de sección 2, Run Command false,
rol limitado a subnet, ningún recurso backend. El helper admite updates en general:
**el operador debe imponer este criterio más estricto de primera creación.**

Calcular SHA-256 de approved.tfplan con Get-FileHash; cotejar receipt/fingerprint.
La autorización debe citar SHA, inventario/variables, plazo y presupuesto; aprobar
antes de ejecutar, nunca solo el texto genérico CREATE.
Vigencia propuesta: misma ventana y máximo 30 minutos desde revisión; invalidar por
cambio de IP, configuración, identidad, políticas relevantes o estado/drift.
Plan guardado no congela capacidad/servicios Azure. No reutilizar tras fallo/drift.

```powershell
# C — NO AUTORIZADO EN ESTA ITERACIÓN
& $Py -B scripts/azure_supervised.py execute --workdir $Work --confirm "EXECUTE rg-wordle-academic/aks-wordle-academic" --approve-intent "CREATE rg-wordle-academic/aks-wordle-academic" --budget-approved --plan-sha256 "<SHA256_APROBADO>"
```
Usar el valor real revisado, no el marcador. execute verifica hash/fingerprint/backend.
Custodiar binario/JSON/review como sensibles, fuera de artifacts públicos; no contienen
necesariamente solo lo marcado sensitive. Tras ejecución y evidencia mínima, eliminar
las copias privadas cuando el propietario autorice su limpieza. Borrado normal en SSD
no acredita sobreescritura segura: usar almacenamiento cifrado y control de acceso.
Conservar recibo/hash sanitizado; no borrar estado, backups o pruebas por extensión.

No reintentar apply por timeout; consultar operación real y estado antes de decidir.
No Ctrl-C repetido, cambio de SKU/región, -target o -lock=false.

## 6. Validaciones de AKS y Wordle

### AKS — R salvo obtención local de kubeconfig

L/C futuro, **NO AUTORIZADO EN ESTA ITERACIÓN**:
```powershell
$aksArgs = @('--variables', "$Private/variables.json", '--kubeconfig', $Kubeconfig, '--context', $Context)
& $Py -B scripts/aks_run.py credentials @aksArgs --evidence "$Private/evidence/credentials" --confirm "CREDENTIALS rg-wordle-academic/aks-wordle-academic"
```
credentials usa get-credentials + kubelogin azurecli, no --admin. Archivo nuevo,
sin sobrescribir kubeconfig por defecto. No realizar login interactivo sin permiso.

```powershell
# R — FUTUROS, requieren clúster ya autorizado
az aks show --subscription $Subscription --resource-group rg-wordle-academic --name aks-wordle-academic --query "{state:provisioningState,version:kubernetesVersion,tier:sku.tier,pool:agentPoolProfiles,network:networkProfile,entra:aadProfile,rbac:enableRbac,localOff:disableLocalAccounts,api:apiServerAccessProfile,identity:identity}"
$K = @('--kubeconfig', $Kubeconfig, '--context', $Context)
kubectl @K get nodes -o wide
kubectl @K wait --for=condition=Ready nodes --all --timeout=300s
kubectl @K get pods -n kube-system
kubectl @K get events -A --sort-by=.lastTimestamp
kubectl @K auth can-i get nodes
kubectl @K auth can-i create deployments -n wordle-demo
```

| Comprobación | Esperado / evidencia | Fallo y acción |
| --- | --- | --- |
| ARM AKS | Succeeded, versión 1.35.9, Free, dos D4s_v5, MI y red correctas | Registrar campo discordante; STOP cargas |
| Seguridad | Entra/grupo exactos, RBAC true, localOff true, api.disableRunCommand=true, /32 exacto | STOP; no corregir remotamente sin permiso |
| Nodos | 2 Ready, kubelet/OS/SKU coherentes | Eventos/condiciones; no escalar para ocultar fallo |
| Sistema/red | CoreDNS/CNI/CSI sin errores persistentes | Logs sanitizados y diagnóstico de red/admission |
| Autorización | Kubectl lectura y permisos de operación necesarios | No --admin ni roles adicionales automáticos |
| Capacidad | Allocatable/requests suficientes, sin Pressure/Pending/OOM | Limitar ensayo; retirada si no cabe |

### Aplicación — fases opcionales autorizadas por separado

k8s/aks-full, scripts/aks_run.py, aks_recovery.py y promotion.py existen; el despliegue
real AKS y la portabilidad/admisión siguen sin probar. No ejecutar runner kind en AKS.
Los apartados antiguos de azure-demo.md que describen adaptaciones pendientes son
históricos: el ejecutor integrado ya existe, pero su existencia no acredita runtime.

C **NO AUTORIZADO EN ESTA ITERACIÓN**:
```powershell
& $Py -B scripts/aks_run.py deploy @aksArgs --evidence "$Private/evidence/deploy" --confirm "DEPLOY rg-wordle-academic/aks-wordle-academic" --ack-costs
& $Py -B scripts/aks_run.py verify @aksArgs --evidence "$Private/evidence/verify" --confirm "VERIFY rg-wordle-academic/aks-wordle-academic"
# Solo con autorización de promoción/fallo reversible, Blue inicialmente activo:
& $Py -B scripts/aks_run.py acceptance @aksArgs --evidence "$Private/evidence/acceptance" --confirm "ACCEPTANCE rg-wordle-academic/aks-wordle-academic"
```
verify crea partida/intento SQL/HTTP; no es lectura. deploy crea Secret/namespace/PVC
y cargas. acceptance cambia tráfico, provoca 503 y usa REVOKE/GRANT reversible.
No repetir acceptance con Green inicialmente activo ni forzar selector para hacerlo pasar.

Esperar StatefulSet/postgres y Deployments activos con timeout; PVC único Bound
managed-csi/8Gi; backend/PG sin Service público. Green empieza escalado a cero.
Forward loopback a service/ingress 18080:8080, namespace wordle-demo:
```powershell
# L/túnel — NO AUTORIZADO EN ESTA ITERACIÓN; mantener proceso propio identificable
kubectl @K -n wordle-demo port-forward --address 127.0.0.1 service/ingress 18080:8080
# R, en otra consola con el forward autorizado activo
curl.exe --noproxy "*" --fail --silent --show-error -H "Host: wordle.test" http://127.0.0.1:18080/
curl.exe --noproxy "*" --fail --silent --show-error -H "Host: wordle.test" http://127.0.0.1:18080/api/health
```
Esperado: 200 frontend y salud, release header coherente, imágenes runtime por digest,
entradas inválidas sin escritura, partida/estadísticas persistidas y secreto oculto.
Flujo completo victoria/derrota/seis intentos se documenta si se ejecuta realmente;
verify integrado no sustituye automáticamente cada caso EV-01 de defensa.

Observabilidad: Collector, Prometheus, Grafana, Loki, Tempo, Node Exporter,
cAdvisor vía kubelet, Alertmanager/receptor. Dos nodos ofrecen nominalmente
8 vCPU/32 GiB, **no allocatable**. Stack según inventario previo:
requests 900m/672 MiB, limits 4500m/2016 MiB con dos Node Exporter;
no incluye Wordle, PG, Traefik o sistema. Los requests bajos no prueban suficiencia.
Revisar todos los recursos renderizados antes de cargas y durante ensayo:
kubectl describe nodes, get pods -A, eventos, PVC/volúmenes y condiciones;
kubectl top nodes/pods solo si metrics API disponible, no instalarla por extensión.
Comprobar targets UP, CPU/RAM/disco, OOM/evictions, ingesta/logs/trazas/dashboards
y firing/resolved real del webhook. Sin métricas inventadas ni nuevo pool.
No afirmar NetworkPolicy efectiva sin evidencia en AKS.

## 7. Evidencias para defensa

Guardar fuera de Git: ID de ensayo, UTC, paso, esperado, observado, exit code,
ruta sanitizada, PASS/FAIL/NO EJECUTADO y limitaciones. No logs crudos, Secret,
kubeconfig, plan binario, JWT, DSN o IP doméstica en material público.

| Evidencia | Objetivo / referencia | Momento / captura | Criterio y disponibilidad |
| --- | --- | --- | --- |
| Plan/hash/apply | EV-03, A05-A09 | Antes/después CREATE, salidas sanitizadas | 6 create; apply éxito y valores efectivos; primera ventana |
| Portal/AKS/nodos/kubectl | EV-03/04 | Provisionado; tabla/captura campos sin IDs sensibles | 2 Ready, seguridad/red correctas; primera ventana |
| Backend | EV-03/15 | Pre/post; propiedades sin contenido | Accesible y lease libre; primera ventana |
| Wordle/Ingress/SQL/HTTP | EV-01/04 | Tras cargas; recibos y UI | Tráfico real proxy, PG compartido; opcional si autorizado |
| Seguridad | EV-04 y FIN-03 | Pre/post cargas | Sin exposición backend/PG; riesgos de usuario_id explícitos |
| CI/CD | EV-05 | Reusar runs y digests reales; registrar qué es local/remoto | CI/GHCR previos no acreditan CD Azure |
| Blue-Green/rollback | Plan FIN-08/09 | acceptance autorizada, estado/selectores/HTTP | Promoción y rollback posterior al fallo, no solo rechazo |
| Prometheus/Node/cAdvisor | FIN-10/11/15 | Consultas/targets con hora | Datos y salud reales, no solo Pods Running |
| Grafana/Loki/OTel/Tempo | FIN-12/13/15 | Dashboard/log/trace correlacionado | Datos reales y trace_id; exportar antes de retirar |
| Alertas | FIN-14/15 | Firing/resolved + recibo webhook | Notificación recibida; no prometer aviso externo humano |
| Destroy/ausencia | EV-15, FIN-19 | Tras retirada y facturación diferida | Inventario/estado/ARM coherentes, remanentes identificados |
| Reconstrucción/restauración | EV-15 | Otra ventana salvo tiempo explícitamente reservado | SQL+HTTP reales; backup no es restauración |

No cerrar FIN-17/18/19 por este documento ni por la primera validación AKS.
CI/CD Azure con OIDC/runner/reviewers sigue pendiente; no activarlo en esta ventana
manual sin otro alcance. Mantener política GHCR vigente, sin publicar nuevas imágenes.

## 8. Tiempo y control económico

Inicio absoluto: PENDIENTE de fijar por propietario. T0 incluye preflight, no solo HTTP.

| Intervalo | Actividad | Punto de decisión |
| --- | --- | --- |
| T+0–20 | Preflight, plan privado vigente y autorización | Si no cabe revisión, no empezar CREATE |
| T+20–80 | Aprovisionamiento supervisado | Si sigue en curso, priorizar diagnóstico y retirada |
| T+80–120 | AKS y capacidad | Cargas opcionales solo si sobra tiempo |
| T+120–160 | Evidencia / subset de demo autorizado | Parar pruebas a T+160 como máximo |
| T+160–220 | Retirada y comprobación | Reserva dedicada 60 min |
| T+220–240 | Contingencia de limpieza | No nuevas pruebas ni despliegues |

Fases pueden finalizar antes; retirar entonces. No garantías de tiempos Azure.
No iniciar acceptance/reconstrucción si su timeout potencial compromete retirada.
Si apply sigue en curso a T+80, no lanzar destroy concurrente: consultar estado;
abortar nuevas cargas y solicitar decisión. La reserva no garantiza completar
una operación Azure atascada; escalar antes de vencer ventana.

Objetivo 5 USD; modelo previo 2,06 USD/4 h y 4,36 USD/8 h, **no cotización nueva,
tope automático ni autorización de ocho horas**.
Revisiones T+20/60/80/120/160/220/240: VM/OS/discos PVC, IP/LB, tráfico/IO,
Storage/retención, surge, tiempos parciales, recursos activos e incidencias.
Registrar estimación actualizada y proyección al fin, separada de coste devengado
estimado y cargo visible Cost Management (puede llegar con retraso).
Sin presupuestos/alertas Azure nuevos. No asumir datos vacíos de facturación como cero.
Si proyección >5 USD, recurso inesperado o retraso amenaza reserva: STOP pruebas,
notificar y solicitar/usar únicamente autorización de retirada correspondiente.
Costes posteriores de backend/backups/retención son explícitos, no "cero absoluto".

## 9. Puntos de parada

NO-GO antes de CREATE: IP/identidad/backend equivocado, estado inesperado,
grupo ajeno, cuota/versión/policy incierta crítica, plan distinto, hash vencido,
sin responsable de retirada/MFA/presupuesto.
STOP durante ejecución: capacidad/policy/permisos, costes no aceptados, leak de
credencial, recursos ajenos o timeout ambiguo. Conservar evidencia, no retry ciego.
No cambiar región, SKU, roles, firewall o métodos MFA automáticamente.
Reautenticación solo del humano autorizado y con autorización de intervención;
nunca códigos en chat, otra identidad o evasión de políticas.

## 10. Incidentes y recuperación

| Incidente | Diagnóstico acotado | Recuperación / límite |
| --- | --- | --- |
| Apply parcial/fallido | Exit, operación ARM, state list y recursos de ambos RG; comprobar lease | No repetir apply ni eliminar manualmente; nuevo plan/decisión de continuar o retirar |
| Capacidad/Policy/RBAC | Código y política/acción exacta sanitizados | No cambiar arquitectura ni permisos; retirar parcial con autorización |
| Timeout | Proceso/operación real, recursos/estado | No asumir fallo ni ejecutar operaciones concurrentes |
| Bloqueo estado | Proceso dueño y propiedades Blob | Esperar/diagnosticar; nunca force-unlock por rutina |
| API inaccesible | IP actual, VPN/rutas, DNS/TCP443/FQDN, kubelogin/grupo | No Run Command (off), --admin ni API abierto; reparación exige permiso |
| MFA | Identificar challenge frente a RBAC/Policy | Usuario completa flujo aprobado; no tokens/códigos guardados |
| Pods/PVC/observabilidad | Eventos, describe y logs sanitizados | No escalar nodos automáticamente; capturar fallo y reducir alcance/retirar |
| Destroy parcial | State list + IDs ARM exactos + costes | Nuevo plan/permiso de recuperación; no state rm/import ni borrar por prefijo |
| Fallo de backend | Acceso/red/lease/servicio | No borrar blob ni migrar estado; recuperar vía responsable autorizado |

Scripts pueden ocultar errores sensibles: inspeccionar diagnósticos privadamente,
conservar solo código/categoría sanitizados. No activar logs debug globales.
Si falta RG de nodos tras create parcial, inventory() del helper puede fallar:
no parchear el script durante la ventana ni fabricar inventario vacío. Solicitar
procedimiento supervisado directo de plan-destroy guardado sobre el estado correcto,
con revisión equivalente de IDs, antes de ejecutar; autorización específica.
Si la retirada no se completa, informar IDs residuales, ubicación, estado, dependencia,
coste horario estimado, responsable y próxima acción. No declarar limpieza ni coste cero.

## 11. Destrucción — D/L NO AUTORIZADOS EN ESTA ITERACIÓN

Requiere autorización independiente antes de ejecutar. Identificar inventario actual,
estado y recursos ajenos; congelar cargas/operaciones concurrentes.
Exportar evidencia emptyDir y datos sintéticos según política aprobada.
Si hay datos que conservar, usar backup existente:
```powershell
# C/L (pausa y reanudación de app, dump privado) — NO AUTORIZADO EN ESTA ITERACIÓN
& $Py -B scripts/aks_run.py backup @aksArgs --evidence "$Private/evidence/backup" --directory "$Private/backups/run1" --confirm "BACKUP rg-wordle-academic/aks-wordle-academic"
```
El helper quiesce y reanuda. Sin restore real SQL/HTTP no declarar backup restaurable.
Si restauración no cabe, otra ventana; no prolongar recursos por datos académicos
sin nueva decisión. Conservar la exigencia histórica de restauración verificada
o pedir decisión explícita de descartar datos exclusivamente sintéticos antes de
autorizar destrucción; no inventar esa aprobación ni eliminar evidencia.

Crear otro workspace vacío con variables/backend iguales:
```powershell
# L/lease — NO AUTORIZADO EN ESTA ITERACIÓN
& $Py -B scripts/azure_supervised.py prepare --workdir $DestroyWork --variables "$Private/variables.json" --backend "$Private/backend.json"
& $Py -B scripts/azure_supervised.py plan-destroy --workdir $DestroyWork --confirm "PLAN-DESTROY rg-wordle-academic/aks-wordle-academic"
```
Revisar review.txt/review.json/inventory.json: solo seis direcciones conocidas y
dependencias propias; cero create/update/replace inesperados, ambos RG dedicados,
sin recursos ajenos. Calcular/revisar hash plan e inventario; revalidar identidad,
suscripción, MFA, backend correcto y exclusión del RG estado. La lista de seis
no enumera individualmente todos los recursos administrados de AKS: revisarlos también.

```powershell
# D — NO AUTORIZADO EN ESTA ITERACIÓN
& $Py -B scripts/azure_supervised.py execute --workdir $DestroyWork --confirm "EXECUTE rg-wordle-academic/aks-wordle-academic" --approve-intent "DESTROY rg-wordle-academic/aks-wordle-academic" --plan-sha256 "<SHA256_PLAN_DESTRUCCION_APROBADO>" --inventory-sha256 "<SHA256_INVENTARIO_APROBADO>"
```
Se materializa un plan -destroy mediante apply del binario revisado, en vez de
terraform destroy con replanteamiento implícito. No fuerza ni confirmaciones masivas.
Nunca az group delete por prefijo, borrar RG nodos aparte, Secret/estado para forzar,
o recursos ajenos al inventario. Nuevos remanentes requieren autorización concreta.

## 12. Verificación final — R futuro

```powershell
az group exists --name rg-wordle-academic --subscription $Subscription
az group exists --name rg-wordle-academic-nodes --subscription $Subscription
# Desde workspace del mismo backend y con autorización de lectura:
# & $Tf state list
az storage blob show --account-name stwordletfgstate7c92d4 --container-name tfstate --name wordle/aks-demo.tfstate --auth-mode login --subscription $Subscription --query "{lease:properties.lease,bytes:properties.contentLength}"
```
Esperado RG=false/false; AKS GET not found; state list exit0 vacío; backend accesible
lease available/unlocked sin lock metadata. Revisar listado ARM privado de IDs de
ambos RG y dependencias registradas: VMSS, discos OS/PG/PV, snapshots, IP, LB y red.
Detectar huérfanos mediante el inventario de IDs antes de destroy, no solo nombres/tags.
GET404 de cada ID esperado a desaparecer o ausencia demostrada; un listado vacío
con error no vale. No borrar remanentes automáticamente.
Empty state y destroy exit0 no prueban ausencia de discos/IP externos al estado.
Backend/grupo Entra/credenciales sintéticas privadas/backups/evidencias conservados;
Cost Management se revisa después con autorización de lectura. Documentar costes
pendientes y persistentes, sin prometer facturación final cero.
Terminar solo forwards propios identificados; no procesos ni recursos PG-05/PG-06.

## 13. Checklist GO/NO-GO operativo

Responsable único: propietario/operador, con disponibilidad confirmada.

| Condición / evidencia | Estado requerido | Si falla |
| --- | --- | --- |
| Gate A y B ratificados, AKS permiso CREATE exacto | GO para solicitar/recibir autorización, no ejecutar por inferencia | NO-GO |
| Contexto/IP/MFA/backend/lease/estado actuales | Todos conformes | NO-GO |
| Plan guardado/hash/fingerprint/coste revisados | 6 create, hardening false, sin drift | NO-GO |
| Tiempo y responsable de retirada | T+160 reservado; aprobación de retirada disponible | NO-GO |
| Secretos/digests/capacidad para cargas | Verificados antes de deploy | STOP solo cargas; priorizar infraestructura/limpieza |
| Operación o coste anómalo | Sin contradicción crítica | STOP y RECOVERY autorizada |
| Inventario/plan-destroy/hash + permiso | Alcance propio y backend protegido | No borrar; resolver con propietario |
| Ausencia ARM/estado y lease libre | Limpieza acreditada | RECOVERY, registrar residual/coste |
| Evidencia sanitaria exportada | Sin secretos, resultados reales | No declarar cumplimiento |

**GO es recomendación/preparación; autorización CREATE/DESTROY siempre explícita.**

## Retirada de emergencia sin IA

Antes de abrir AKS GO, revisar [el manual autonomo](FIN-AKS-EMERGENCY-TEARDOWN.md)
y el script infra/scripts/Invoke-AksEmergencyTeardown.ps1. Preflight por defecto;
retirada solo con plan revisado y confirmacion expresa. Mecanismo preparado, no
autorizacion de ejecutar ni temporizador cloud.
