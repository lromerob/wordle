# FIN-AKS-BACKEND-BOOTSTRAP — Wordle — 16/11/2026

## 1. Resumen ejecutivo: PARTIAL

Se creó y verificó únicamente **rg-wordle-state**. La única solicitud de creación de **stwordletfgstate7c92d4** fue rechazada por Azure con **RequestDisallowedByAzure**. Se detuvieron todas las operaciones posteriores, sin reintento de creación, cambios de región, permisos o configuración ni eliminación automática. **Gate A NO-GO y AKS NO-GO.**

No existe cuenta/contenedor/backend operativo, no se creó blob de estado y no se ejecutó Terraform. El resultado no se considera PASS por existir el RG.

## 2. Identidad y suscripción verificadas

Contexto activo coincidió con la suscripción `11306565…1bb5` y tenant `aff0390f…1eb9`, Enabled. Principal user de CLI comprobado por Graph con proyección id: operador autorizado `b573130a…a831`, coincidente con la referencia previa. No se cambió contexto/identidad. La IP doméstica no se publica.

## 3. Preflight obligatorio

- Nombre Storage aprobado, check-name nameAvailable=true; no cuenta propia previa autorizada. RG previsto ausente.
- Región verificada westeurope, configuración de creación coincidía con ficha: StorageV2/Standard_LRS/Hot, HTTPS/TLS1.2, anonymous/SharedKey false, endpoint Enabled con defaultAction Deny y bypass None.
- Permisos ARM devueltos permitían resourceGroups/write, storageAccounts/write, blobServices/write, containers/write, managementPolicies/write y roleAssignments/write. No se presentaron como garantía de éxito frente a políticas/deny o condiciones del servicio.
- Consulta de asignaciones Policy al ámbito de suscripción, con herencia consultada mediante disable-scope-strict-match: cero asignaciones devueltas. **No demuestra inexistencia de restricciones de plataforma, región/oferta o controles no visibles.** La creación posteriormente fue denegada.
- IPv4 pública vigente detectada y validada como globalIPv4, sin publicar su valor. Ruta doméstica declarada por el propietario; señales locales: cero VPNWindows conectadas, WinInetProxyEnabled=false y variablesproxy ausentes. Esto no es prueba exhaustiva de ausencia de todo softwareVPN/ruta intermedia, pero no se observó discrepancia con lo autorizado.
- Inmediatamente antes de escribir se revalidó contexto/operador, ausenciaRG, disponibilidad de nombre eIPv4. No se usó otra cuenta o suscripción.

## 4. Recursos creados y operaciones

| Operación | Resultado | Verificación |
|---|---|---|
| Crear rg-wordle-state/westeurope | Succeeded | group show, región ytagscoincidentes |
| Crear stwordletfgstate7c92d4 | Denegada: RequestDisallowedByAzure | storage account show posterior: ResourceNotFound |
| Configurar firewall | NO EJECUTADA | Se detuvo antes |
| Protección/versioning/lifecycle | NO EJECUTADA | Se detuvo antes |
| Crear tfstate privado | NO EJECUTADA | Cuenta inexistente |
| Asignar rol Blob | NO EJECUTADA | Sin cuenta/contenedor |

RG tiene tags exactamente: project=wordle, purpose=terraform-state, environment=tfg, lifecycle=temporary. Lectura posterior de provisioningState: Succeeded. `az resource list -g rg-wordle-state` devuelve **cero recursos**. El RG se conserva; no se borra bajo esta autorización.

Comandos de escritura intentados, con suscripción explícita y output none:

```text
az group create --name rg-wordle-state --location westeurope --tags project=wordle purpose=terraform-state environment=tfg lifecycle=temporary --subscription <confirmada> --only-show-errors -o none
az storage account create --name stwordletfgstate7c92d4 --resource-group rg-wordle-state --location westeurope --kind StorageV2 --sku Standard_LRS --access-tier Hot --https-only true --min-tls-version TLS1_2 --allow-blob-public-access false --allow-shared-key-access false --public-network-access Enabled --default-action Deny --bypass None --tags project=wordle purpose=terraform-state environment=tfg lifecycle=temporary --subscription <confirmada> --only-show-errors -o none
```

El segundo comando devolvió error y no se repitió. Solo el primero produjo recurso creado. No hubo otras escrituras Azure.

## 5. Configuración de seguridad

Seguridad Storage aprobada se envió como parámetros de creación, **no quedó aplicada/verificada**, porque la cuenta no existe. No se declara HTTPS/TLS/firewall/Entra de backend operativo. No se habilitaron claves, SAS o redes abiertas para resolver el fallo. Tags/ubicación del RG sí verificados.

## 6. Reglas de red

No se creó regla de red; IP observada solo se mantuvo en memoria para futura reglaindividual. No se configuró /32 en Storage ni APIAKS. Se detuvo antes de network-rule add. No se crearon VPN/NAT/VNet/firewall ni otros componentes; no se usó AllowAll.

## 7. Permisos asignados

**Ninguno.** No se alcanzó la fase de Storage Blob Data Contributor al operador/scopedecontenedor; no se añadieron usuarios/grupos/identidades o roles en otros ámbitos. No se amplía ningún privilegio por el error de creación.

## 8. Protección y retención

No se activaron soft delete, versioning o lifecycle: cuenta ausente. No se creó contenedor o blob de estado ni blob de prueba. La política propuesta de versionesprevias7d, sin acción sobre estadoactual, permanece pendiente. No hay estado que inicializar o migrar; no se ejecutó init/plan/apply/destroy ni prueba de lease/escritura.

## 9. Verificaciones posteriores y diagnóstico de lectura

Tras el error, solo se realizaron lecturas de contexto, group show, resource list del RG, storage account show y ActivityLog fallido del RG (última1h). Resultados: RG correcto y vacío; cuenta ResourceNotFound; lista de eventos fallidos devuelta vacía en ese momento. No se confunde ausencia de log con ausencia de fallo; el código de rechazo fue capturado de la respuesta CLI de creación. Puede existir latencia o un ámbito de evento distinto; **causa detallada no determinada**.

No se atribuye el error a falta de cuota, a Azure for Students (oferta documentada es PayAsYouGo), a un permiso concreto o región prohibida sin evidencia suficiente. No se modifican parámetros para probar hipótesis. Posibles restricciones de plataforma/política necesitan diagnóstico de lectura o intervención del propietario, no nuevas pruebas de creación.

## 10. Recursos residuales y coste esperado

Único remanente nuevo confirmado: RG vacío. El Resource Group no genera cargo propio; no se observan cuentaStorage, discos, IP, LB, nodos o recursos facturables creados por este intento. **No se aplica la estimación de capacidad/operacionesBlob del backend, al no existirlo.** Esto no es un análisis de cargos ajenos de la suscripción ni garantía de que CostManagement ya haya reflejado eventos.

No se elimina el RG automáticamente. Tras resolver el rechazo, una nueva autorización debe decidir reutilizar expresamente este RG creado en la iteración o retirarlo; el script de preparación rechaza RGpreexistente y no debe saltarse esa guarda sin aprobación puntual. No aplicar el bootstrap completo desde cero a ciegas.

## 11. Incidencia y recuperación propuesta

Incidencia confirmada: **RequestDisallowedByAzure al crear Storage Account**, después de crearRG. Estado parcialmente creado registrado y operaciones detenidas como se pidió. No hay incidente de secretos o exposición de datos observado, porque no se creó cuenta ni estado.

Próximo diagnóstico acotado: consultar ActivityLog/operación exacta en el ámbito autorizado y restricciones de región/oferta/Policy de Storage, sin nuevascreaciones y sin abrir ticket automáticamente. Si Azure exige soporte o cambiarregión/configuración, presentar evidencia y solicitar autorización nueva. No inferir de ceroPolicyassignments que se puede eludir la restricción. Si no se desea continuar, proponer eliminación puntual del RGvacío tras permiso explícito; no se hace hoy.

## 12. Gate A final

**NO-GO: backend no operativo.** PASS solo para RG y preflight identificado; cuenta denegada, sin contenedor/RBAC/red/retención/accesoEntra. No se intentó validar Blob mediante escritura porque no hay cuenta; no se considera lectura a ARM equivalente a acceso al estado.

AKS sigue NO-GO y no se inicia GateB. Terraform/código/configuración locales sin cambios; todos los archivos pendientes previos conservados por SHA-256. Sin staging/commits/push ni publicación/despliegues.

## 13. Próxima acción recomendada

Autorizar un **diagnóstico exclusivamente de lectura del rechazo de Azure Storage** y revisión del error con el propietario. Mantener región/ficha aprobadas, sin repetir creación ni modificar este RG hasta decidir recuperación. No iniciar otro bootstrap o limpieza automáticamente. El procedimiento general de análisis de denegaciones está documentado en [Azure Policy troubleshooting](https://learn.microsoft.com/en-us/azure/azure-resource-manager/troubleshooting/error-policy-requestdisallowedbypolicy); su existencia no identifica la causa concreta de este código.

Único archivo local creado por esta iteración: este informe. Solo recursoAzure creado: rg-wordle-state aprobado. Sin cuentaStorage, permisos o recursos adicionales; no se cambió identidad/suscripción ni se accedió a secretos/estados ajenos.
