# FIN-AKS-DEPLOYMENT-DECISIONS — 16/11/2026

## 1. Resumen ejecutivo

**PASS de preparación operativa local.** IPv4 contrastada en dos fuentes, también
por conexión directa sin proxy. /32 preparado como ejemplo local, sin default.
Sin solapamientos observados en redes/rutas locales con los tres rangos aprobados.
Helpers reconciliados y runbook actualizado: 4 horas, objetivo 5 USD, backend conservado.
Gate A GO por evidencia anterior; Gate B y AKS NO-GO.
No autorización de Terraform ni despliegue por extensión.

## 2. Alcance autorizado

Consultas públicas HTTPS y lecturas locales de interfaces/rutas; cambios acotados
en helpers, validaciones y documentación. Sin llamadas Azure/Graph ni cambios de
red, secretos, Storage/firewall, cuotas o recursos. Sin staging/commits/push.
Revisión selectiva de los informes GATE-B-READINESS, ENTRA-PREP,
BACKEND-LEASE-VALIDATION y SWEDEN-CONFIG y configuración infra/terraform.
Ningún informe histórico modificado.

## 3. Estado inicial

AKS: swedencentral, Free, 1.35.9, dos Standard_D4s_v5, surge string "1",
CNI Overlay, Entra/Kubernetes RBAC y cuentas locales deshabilitadas.
Tenant/grupo aprobados presentes; API obligatorio, sin default, ejemplos []/false.
Índice vacío; 60 archivos pendientes preexistentes protegidos por SHA-256.
Cuatro referencias West Europe en azure_preflight.py y un fallback en
azure_supervised.py eran de AKS, no de la ubicación histórica del RG de backend.

## 4. IPv4 pública observada

HTTPS sin credenciales ni datos de proyecto. Fuentes independientes coincidentes:

| Fuente | Primera consulta UTC | Contraste directo UTC |
| --- | --- | --- |
| https://api4.ipify.org | 2026-11-16T18:27:13.1372094Z | 2026-11-16T18:28:26.3552497Z |
| https://checkip.amazonaws.com | 2026-11-16T18:27:13.2649332Z | 2026-11-16T18:28:26.6457738Z |

Primera consulta Invoke-RestMethod; contraste curl.exe -4 --noproxy '*' con timeout.
Los cuatro resultados coinciden; IPv4 global comprobada con ipaddress.
La dirección figura solo en el ejemplo del apartado 5, no en defaults ni respuesta final.
Reverificar inmediatamente antes de plan/aplicar y de administrar AKS.
No garantiza permanencia de IP, ausencia de NAT/CGNAT ni conectividad futura.

## 5. Configuración propuesta del /32

Ejemplo local observado en esta sesión; no aplicado ni archivo de configuración creado:

    {
      "api_authorized_cidrs": ["90.173.246.175/32"],
      "api_access_approved": true
    }

Los ejemplos genéricos siguen []/false. El runbook muestra cómo preparar el valor
en memoria tras revalidar dos fuentes, con guardado comentado y confirmación humana.
No se leyó ni reutilizó la regla IP de Storage.

Terraform conserva entradas obligatorias, no nulas, sin default; cardinalidad
reforzada a un CIDR. Rechaza vacío, placeholders, rangos amplios, loopback y bloques
de documentación. El helper exige además dirección global pública, sufijo /32 y
booleano true explícito. Su clasificación pública es más estricta que el filtro
léxico HCL; no se presenta este último como validación completa de routabilidad.
La aprobación humana y titularidad no se prueban con un booleano.
Microsoft documenta accesos propios API/salida añadidos por AKS; el /32 corresponde
a la administración externa, no a eliminar accesos internos del servicio:
[Microsoft API authorized ranges](https://learn.microsoft.com/en-us/azure/aks/api-server-authorized-ip-ranges).

## 6. Comprobación de redes externas

Fecha de lectura: 2026-11-16T18:27:17.8917126Z. Get-NetRoute IPv4, Get-NetIPInterface IPv4,
Get-NetIPAddress IPv4 y Get-NetAdapter -IncludeHidden: 26 rutas,
8 interfaces IP.
Ruta predeterminada por Wi-Fi; adaptador VPN identificado desconectado.
Contraste HTTPS directo coincidente. No se documentan SSID/MAC/IP privadas innecesarias.

| Rango | Redes/interfaces locales | Rutas no predeterminadas |
| --- | --- | --- |
| 10.10.0.0/16 | Sin conflicto observado | Sin conflicto observado |
| 10.244.0.0/16 | Sin conflicto observado | Sin conflicto observado |
| 10.20.0.0/16 | Sin conflicto observado | Sin conflicto observado |

ipaddress no encontró intersecciones. 0.0.0.0/0 es salida predeterminada, no conflicto.
La contención subnet 10.10.0.0/24 en VNet es intencional.
Solo se observa este equipo: no se inspeccionó router, redes de terceros o Azure.
La conexión doméstica sin VPN es la condición aprobada, no un hecho demostrable
solo con las rutas. Futuras VPN/redes: no verificables; repetir revisión al cambiar
conexión. Sin modificaciones de interfaces/rutas/DNS ni conexión a otra red.

## 7. Helpers operativos revisados

azure_supervised.py inspeccionado sin ejecutar prepare/operate/plan/execute:
terraform_defaults lee literales location/node_vm_size/node_count de variables.tf;
fallback de región coherente; validate_inputs exige un /32 público aprobado.
azure_preflight.py usa esos defaults en resultado, función y CLI; desaparecen las
cuatro referencias AKS obsoletas. Overrides explícitos conservados.
azure_dispatch.py y procedimientos existentes revisados; workflows sin cambios.
West Europe histórico, errores regionales y RG real del backend conservados.
No sustitución global.

Campos del preflight como lease no probado/presupuesto no confirmado describen
lo que ese helper acredita por sí mismo; no sustituyen informes anteriores ni
decisiones del propietario. No se añadió aprobación automática de gasto o gates.

## 8. Cambios realizados

Seis archivos editados:
- scripts/azure_preflight.py: defaults de Terraform.
- scripts/azure_supervised.py: lectura de defaults y guardas /32.
- scripts/test_azure_readiness.py: fixture sintáctica y regresiones focalizadas.
- infra/terraform/variables.tf: exactamente un CIDR.
- infra/terraform/README.md: reconciliación de helpers.
- docs/operations/azure-demo.md: runbook y decisiones vigentes.

Además se crea este informe. La dirección pública de la fixture no es un input
aprobado ni una configuración de despliegue. No se cambian ejemplos/backend,
lock, esquema, aplicación, pipelines o informes históricos.

## 9. Presupuesto y ventana

Decisión aprobada: 4 horas totales, objetivo 5 USD; retirar al terminar la validación,
aunque quede ventana; conservar backend. No límite automático ni presupuesto Azure creado.

Revisión aritmética de supuestos históricos Gate B, 16/11/2026, USD Linux Consumption,
730 h/mes; no cotización nueva:
- VM: 2 × 0,204 × 4 = 1,632 USD.
- OS supuesto P6 64 GiB: 2 × 11,2272 × 4/730 = 0,12304 USD.
- PG SSD 8 GiB: 0,60 × 4/730 = 0,00329 USD.
- Una IP salida: 0,005 × 4 = 0,020 USD.
Subtotal 1,77833 USD. Surge una hora: aproximadamente 0,21938 USD VM+OS adicionales.

No cuantificados ni cero: Load Balancer/reglas/datos, egreso, IO, operaciones Storage,
estado/versiones/retención, backups/evidencias, tiempos adicionales y remanentes.
Observabilidad propia consume nodos/red/disco; no Log Analytics premium añadido.
SKU real de discos requiere plan/inventario. Free no elimina recursos facturables:
[Microsoft tiers AKS](https://learn.microsoft.com/en-us/azure/aks/free-standard-pricing-tiers).
Completar y aceptar estimación total antes de CREATE; no garantía bajo 5 USD.
Backend/retenciones pueden seguir facturando tras retirar AKS.

## 10. Condiciones de parada

Coste superior al objetivo o partidas desconocidas no aceptables; recursos imprevistos;
SKU/servicios nuevos; ampliar ventana; seguridad incumplida; cuota/capacidad insuficiente;
IP distinta/discrepante; VPN/conflicto nuevo; contexto erróneo o backend inaccesible.
Sin ampliar red, cambiar suscripción/SKU ni elevar permisos para forzar éxito.
Con recursos creados, solo retirada previamente autorizada; si falla, informar
inmediatamente del coste y pedir resolución acotada. No abandono ni borrado general.

## 11. Runbook del ciclo de vida

Actualización de docs/operations/azure-demo.md, sin otro ejecutor.
DEPLOY: identidad/tenant/suscripción Enabled, región/versión/SKU/cuotas,
IPv4/rutas revalidadas, acceso al backend, coste completo y ventana;
validación/init/plan por autorización separada, revisión de plan/hash,
aprobación independiente antes de apply; margen/retirada previstos antes de crear.
VALIDATE: nodos Ready, Entra/kubelogin/RBAC, networking, Wordle/PVC/Services ClusterIP,
HTTP frontend y /api/health y datos sintéticos. Fallos/rollback solo autorizados.
EVIDENCE: configuración/commit/digests/versiones, tiempos, nodos/Pods/PVC,
SQL/HTTP, capturas, incidencias y costes sanitizados; nunca secretos/kubeconfig/DSN.
DESTROY: workspace externo nuevo, mismo backend, plan-destroy e inventario,
hashes y aprobación independiente; execute DESTROY del plan guardado.
Excluir rg-wordle-state, stwordletfgstate7c92d4, tfstate, estado/blobs/versiones.
No az group delete ni limpieza automática. Revisión posterior de discos/snapshots,
LB/IP, grupo de nodos y cargos diferidos. PG-05/PG-06 siempre excluidos.
Nada de este ciclo ejecutado hoy.

## 12. Validaciones locales

Python AST de los tres scripts. Ocho tests focalizados de validación/preflight
offline, cero omitidos, con subprocess.run/Popen, socket.connect y DNS bloqueados.
No prepare/operate ni operaciones de infraestructura.
Casos negativos: vacío, abierto, cero, documentación, privado, loopback, IPv6,
placeholder, nulo, sin /32, amplio, múltiples; aprobación false/nula/texto/entero/
ausente rechazada. Caso sintáctico válido y defaults/overrides/backend independiente.
Ejemplo PowerShell parseado con System.Management.Automation, no ejecutado.
HCL: revisión textual/léxica, referencias y ejemplos JSON. Sin parser HCL completo;
sin fmt/validate o instalación. No se afirma validación real del proveedor.
Red y contraste de IPv4 satisfactorios según límites anteriores.
git diff --check, revisión focalizada de credenciales y preservación por hashes:
PASS al cierre; índice vacío, HEAD intacto y 54 pendientes ajenos conservados por SHA-256. Sin suites de aplicación ni CLI de despliegue.

## 13. Riesgos y limitaciones

Sin prueba real de Terraform/ARM/AKS. IP/rutas solo representan equipo y momento.
VPN futura, otras redes y Policy heredada no cubiertas. Sin coste total confirmado,
capacidad garantizada ni nueva prueba del backend. Booleano no verifica identidad.
El informe contiene /32 observado; sanitizarlo antes de eventual publicación pública
no autorizada. Hoy no se prepara para commit ni se publica.

## 14. Decisiones pendientes

Escenario, presupuesto objetivo y ventana aprobados; revalidar salida/red en el
momento de uso y completar/aceptar total antes de CREATE. Preparar suscripción e
inputs privados explícitos. Autorizar separadamente validación Terraform/init/plan,
revisar plan real, CREATE/retirada y cargas. No se presume autorización remota.

## 15. Estado de Gate A

GO mantenido por bootstrap y lease previos. Backend, firewall, permisos, retención
y blobs intactos, sin consulta remota en esta iteración.

## 16. Estado de Gate B

NO-GO. AKS NO-GO. Preparación local avanzada; faltan comprobaciones vigentes,
coste completo previo a CREATE y autorizaciones operativas independientes.

## 17. Recomendación de siguiente iteración

Revisar el resultado y autorizar fase acotada de validación Terraform, y después
init/plan, con inputs privados y contexto /32 revalidados. Apply y retirada exigen
sus confirmaciones independientes. No se inicia nada automáticamente.
No terraform init, plan, apply ni destroy ejecutados; no AKS creado ni Azure/Entra
modificados; sin staging, commits, push o cambios del historial Git.
