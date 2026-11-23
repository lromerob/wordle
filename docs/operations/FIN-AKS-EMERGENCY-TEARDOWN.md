# Wordle — Retirada de emergencia sin IA

Preparado el 17/11/2026. **No se ha ejecutado contra Azure.**
Gate A GO; Gate B GO; AKS NO-GO. Disponer del script no autoriza desplegar ni destruir.
La retirada real exige autorización expresa del propietario y revisión del alcance.
Este manual funciona sin ChatGPT, Codex ni historial: conservarlo localmente junto
con el repositorio y los inputs privados de cada ventana.

## 1. Objetivo y cuándo utilizarlo

Retirar únicamente infraestructura Wordle registrada en el backend aprobado:
rg-wordle-academic, aks-wordle-academic y dependencias de red/identidad/pool.
Sirve tras despliegue completo o parcial. No elimina huérfanos automáticamente.
Nunca usar para Nexo, PG-05/PG-06 ni recursos ajenos.

## 2. Requisitos y autorización

Internet, equipo encendido, PowerShell Windows 5.1 o compatible, Azure CLI instalada
con sesión humana autorizada, Terraform 1.9.8 y AzureRM 4.50.0 ya instalados.
Usar una copia de trabajo **externa y privada**, ya inicializada con el backend
Entra/CLI aprobado; no hay init automático. Identificadores de instalación y UUID
del operador humano se proporcionan en `-TargetFile`, copia externa de
`infra/terraform/emergency-target.example.json`. El script exige coincidencia exacta;
no selecciona automáticamente la sesión actual como autoridad. Consultar
[contrato vigente de custodia y retirada](release-gates.md#human-emergency-recovery-independent-of-cd).

Conservar fuera del repo variables JSON revisadas de la ventana (incluido /32 vigente,
grupo Entra y aprobación), credenciales sintéticas y evidencia/backup que deban salvarse.
Antes de destruir, resolver la conservación/restauración o descarte autorizado de datos.
La frase escrita confirma permiso del propietario: no sustituye esa decisión.
No necesita Python, Pester ni una IA. No tiene -Force ni modo no interactivo.

## 3. Abrir PowerShell y localizar el script

Inicio de Windows → escribir PowerShell → abrir terminal normal, sin administrador.
Utilizar el workspace aprobado C:/WordleTFG/repo. Desde la raíz, o desde cualquier carpeta,
usar la ruta completa al script. No cambiar PATH/configuración global.

Ejemplos FUTUROS, **NO AUTORIZADOS EN ESTA ITERACIÓN**:
    $WordleScript = (Resolve-Path './infra/scripts/Invoke-AksEmergencyTeardown.ps1').Path
    # Desde la raíz del checkout; definir rutas privadas reales fuera del repositorio.
    $PrivateTarget = '<ruta privada externa>/emergency-target.json'
    $PrivateWork = '<ruta privada externa>/terraform-emergency'

Si su carpeta está en otra ubicación, cambiar solo la ruta local al repositorio correcto.
Terraform predeterminado: %LOCALAPPDATA%/WordleTFG/tools/terraform-1.9.8/terraform.exe.
Puede indicarse -TerraformPath con el binario revisado; versión se valida.
Si las políticas impiden ejecutar scripts: no cambiar política de usuario/sistema.
Tras revisar el archivo, el propietario puede usar una excepción de proceso:
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File $WordleScript -Preflight -TargetFile $PrivateTarget -WorkDirectory $PrivateWork
Si Group Policy impide esa excepción, detenerse y solicitar intervención al responsable;
no desactivar controles del sistema.

## 4. Preflight — solo lectura cloud

FUTURO, requiere acceso de lectura autorizado; no ejecutado aquí:
    & $WordleScript -Preflight -TargetFile $PrivateTarget -WorkDirectory $PrivateWork

Sin switches también utiliza preflight. No llamar -Teardown por probar.
Comprueba herramientas/versiones, tenant/suscripción/operador, backend exacto,
RG/cuenta/contenedor/blob, lease libre, inventario Terraform y recursos de ambos RG.
Muestra nombres e IDs para revisión local; no tokens ni valores de variables.
No plan, apply, init ni escritura cloud. Sí crea un log local sanitizado.
Estado vacío: no genera plan; distingue CLEAN frente a recursos residuales.
Preflight OK con estado no vacío significa que puede revisar un plan, no que todos
los recursos sean seguros de destruir. No hay autorización implícita.

## 5. Revisar y ejecutar retirada

FUTURO, **DESTRUCTIVO — NO AUTORIZADO EN ESTA ITERACIÓN**:
    & $WordleScript -Teardown -TargetFile $PrivateTarget -WorkDirectory $PrivateWork -VariablesFile '<ruta privada externa>/variables.json'

No sustituir el marcador por un archivo del repo con placeholders.
Primero repite verificaciones. Exige PLAN WORDLE AKS antes de generar el plan
-destroy guardado y su lease normal. No modifica infraestructura en esta etapa.
Plan protegido por directorio único de usuario fuera de Git; show -json se procesa
en memoria y no se guarda como estado/evidencia. El plan puede contener secretos:
no copiarlo, publicarlo ni abrir una transcripción de consola.

Después muestra:
- Tenant y suscripción exactos.
- Direcciones/IDs de recursos que se eliminarían.
- Inventario de dependencias/cascada de ambos RG y cantidad Terraform.
- SHA-256 del plan y advertencia irreversible.
- Confirmación de que backend está excluido.

Revisar cada ID. RG administrado de nodos debe pertenecer al AKS exacto (managedBy);
revisar también todos sus recursos, no asumir exclusividad por nombre.
Si hay un recurso ajeno, CANCELAR, aunque el grupo esté marcado como administrado.
Si todo coincide con autorización, escribir exactamente:
    DESTRUIR WORDLE AKS

Enter, texto vacío, minúsculas o otra frase no sirven. Nunca pegar automáticamente
la frase desde una automatización. Confirmación válida máximo diez minutos.
Antes de apply comprueba de nuevo identidad, hash, ficheros, estado, ETag del blob,
inventario y concurrencia. Terraform aplica el mismo binario con bloqueo normal;
rechaza planes obsoletos adicionalmente. No se hace destroy con replanteamiento implícito.
Sin -auto-approve, init, force-unlock, state rm, borrado de grupos por CLI o prefijos.

No ejecutar dos terminales de retirada. No reintentar automáticamente tras error.
El archivo binario se elimina en finally, conservando solo logs sanitizados;
interrupción brusca/apagado puede dejar el archivo: custodiarlo como sensible y
eliminar solo ese plan de la sesión cuando no haya operación activa.
Borrado en SSD no garantiza sobreescritura forense: usar disco de usuario cifrado
y acceso privado. No copia pública/OneDrive del directorio de planes.

## 6. Estados finales y evidencias

CLEAN: estado vacío, RG de app/nodos ausentes, AKS no listado, recursos antes
observados ausentes y backend/key/contenedor/cuenta/RG accesibles, lease libre.
Solo alcance observable revisado; no auditoría universal de todos los discos Azure.
PARTIAL CLEANUP: quedan recursos/estado; no iniciar otra destrucción ciega.
VERIFICATION FAILED: fallo impide concluir; incluso si apply terminó, no declarar limpio.
Exit 0: preflight conforme o CLEAN; exit 2: limpieza parcial; exit 1: fallo seguro.

Logs: %LOCALAPPDATA%/WordleTFG/emergency/<sesión>/audit.jsonl.
Fecha, modo, fases, direcciones Terraform, hash, aceptación y resultados sanitizados.
No estado completo, variables, credenciales, tokens ni errores crudos.
Guardar recibos/capturas sanitizados fuera de Git; no añadir logs ni planes al commit.
El backend/retenciones y backups pueden seguir generando costes; revisar cargos
diferidos. Ausencia de cargo visible hoy no prueba coste cero.

## 7. Incidentes: actuar sin IA

| Problema | Acción humana |
| --- | --- |
| MFA/sesión caducada | Detenerse. Revisar el error de autenticación en una consola privada. Si está autorizado renovar la misma identidad: az login --tenant <tenant aprobado>; completar personalmente MFA. Verificar account show y ad signed-in-user show antes de repetir preflight. No códigos en chat, otra cuenta ni cambios RBAC. |
| Suscripción/tenant incorrectos | No account set automático. Abrir sesión/contexto correcto mediante decisión del propietario y repetir preflight. |
| Acceso Storage/red fallido | Revisar conexión doméstica, IPv4/VPN y servicio. No abrir firewall/API ni cambiar backend para salir del paso. |
| Lock | Identificar proceso/operación dueña; esperar y consultar propiedades. Nunca force-unlock sin diagnóstico y autorización específica. |
| Apply/destroy fallido | Conservar log, inspeccionar state list y recursos exactos. Puede haber retirada parcial. Nuevo plan/revisión/confirmación, no repetir el viejo binario. |
| Huérfano/ajeno | Registrar ID, ubicación, tipo, dependencia y coste potencial; no borrar automáticamente ni importar/state rm. Solicitar autorización específica. |
| Error ocultado | El log evita detalles sensibles. Diagnosticar en terminal privada con consultas acotadas del procedimiento manual, no --debug global ni transcripción con secretos. |
| Script cancelado/PC apagado | Recuperar sesión/conectividad, averiguar operación real; no asumir rollback. Revisar plan residual privado sin ejecutarlo. |
| Cambio de estado/configuración/ETag | Autorización invalidada: no aplicar; repetir preflight y generar nuevo plan tras revisión. |

El script no renueva sesión ni elude Azure Policy. RBAC suficiente no garantiza MFA.
No utilizar Run Command (deshabilitado), --admin ni 0.0.0.0/0 como recuperación.

## 8. Procedimiento manual alternativo sin script ni IA

Todos los comandos siguientes son FUTUROS; plan/lease/apply **NO AUTORIZADOS EN ESTA
ITERACIÓN**. No ejecutar como bloque completo. Leer cada paso y comprobar exit code.
No requiere el helper Python.

1. Definir $Repo, $Tf, $Subscription y $Private manualmente:
   raíz Wordle correcta, Terraform 1.9.8, suscripción aprobada arriba y carpeta privada
   nueva fuera de Git/OneDrive para plan/inputs/evidencia. Abrir terminal sin
   TF_CLI_ARGS*, TF_LOG*, TF_DATA_DIR, TF_WORKSPACE, TF_VAR_* ni ARM_* inesperados.
   No cambiar variables de autenticación por rutina.
2. Lecturas: az account show; az ad signed-in-user show. Comparar IDs con sección 2,
   user/Enabled. Revisar procesos Terraform; si hay uno activo, parar.
3. En $Repo/infra/terraform: leer solo configuración backend local de
   .terraform/terraform.tfstate (no estado remoto): tipo azurerm, tenant/subscription
   aprobados, use_azuread_auth=true y coordenadas exactas siguientes:
   rg-wordle-state / stwordletfgstate7c92d4 / tfstate / wordle/aks-demo.tfstate.
   Rechazar claves/SAS/OIDC/MSI/credenciales inesperadas; no imprimir contenido.
   Contrastar también versions.tf/backend.hcl.example. No ejecutar init.
4. Consultar RG/cuenta/container/Blob mediante CLI, --subscription explícita,
   --auth-mode login para Blob/container. Backend debe existir, key accesible y
   lease unlocked/available sin terraformlockid. No state pull ni force-unlock.
   Ejemplo lectura:
       az storage blob show --account-name stwordletfgstate7c92d4 --container-name tfstate --name wordle/aks-demo.tfstate --auth-mode login --subscription $Subscription --query "{lease:properties.lease,bytes:properties.contentLength,etag:properties.etag}"
5. Local/versiones y lectura de estado:
       & $Tf version -json
       & $Tf state list
   Exigir 1.9.8/4.50.0. Solo seis direcciones permitidas:
   azurerm_resource_group.wordle, azurerm_virtual_network.wordle, azurerm_subnet.aks,
   azurerm_user_assigned_identity.aks, azurerm_role_assignment.aks_network,
   azurerm_kubernetes_cluster.wordle. Subconjunto permitido para create parcial.
   Si estado vacío, NO plan/apply: comprobar RG/recursos residuales y backend.
6. Inventario de lectura con az group list, az resource list y az aks list,
   --subscription $Subscription. Revisar únicamente IDs del RG app/nodos y recursos
   antes registrados. RG nodos managedBy debe ser AKS Wordle exacto.
   Cualquier recurso de app fuera del estado es huérfano: detenerse. En nodos,
   revisar dependencias administradas y cualquier recurso ajeno; no eliminarlos
   por asumir que un nombre/tag es prueba de propiedad.
7. Revisar variables.json externo de la ventana (nombres/IDs/backend correctos,
   no secretos). Guardar huellas SHA-256 de .tf, lock, inputs y metadatos backend.
   Registrar inventario/IDs y direcciones del estado en privado.
8. Local validate y, SOLO con autorización para plan de retirada y lease:
       & $Tf validate -no-color
       & $Tf plan -destroy -input=false -no-color -lock-timeout=60s "-var-file=$Private/variables.json" "-out=$Private/destroy.tfplan"
   Comprobar exit 0. No flags de bypass. No apply si plan falla.
9. Revisar privadamente plan sin exportarlo públicamente:
       & $Tf show -no-color "$Private/destroy.tfplan"
       Get-FileHash -LiteralPath "$Private/destroy.tfplan" -Algorithm SHA256
   El texto puede contener datos sensibles: no transcribir/grabar ni compartir.
   Solo delete (o no-op) de las direcciones registradas; ningún create/update/replace.
   IDs exactos bajo /subscriptions/<aprobada>/resourceGroups/rg-wordle-academic,
   nombres vnet-wordle-academic/snet-aks/id-wordle-aks/aks-wordle-academic;
   rol con scope exacto de subnet. Ningún recurso Storage/backend ni otro RG.
   Revisar también cascada de RG y todos los recursos dependientes.
10. Autorización expresa del propietario con SHA-256, inventario y frase escrita
    DESTRUIR WORDLE AKS. Revalidar contexto/lease/ETag, estado, inventario y hashes;
    si cambió algo o han pasado más de diez minutos, invalidar y revisar otro plan.
    Concurrencia desconocida: no continuar. Solo entonces, **DESTRUCTIVO**:
        & $Tf apply -input=false -lock-timeout=60s "$Private/destroy.tfplan"
    Aplica exclusivamente ese binario, no terraform destroy con un nuevo cálculo.
    No borrar por CLI, no -force, no state rm/import y no reintento sin diagnóstico.
11. Tras terminar, lecturas: state list exit0 vacío; group exists=false para
    rg-wordle-academic y rg-wordle-academic-nodes; AKS listado ausente; comprobar
    IDs previos de VNet/subnet/MI/rol/AKS/VMSS/discos/PV/snapshots/LB/IP.
    Consultar recursos por sus IDs/inventario, no borrar por prefijo.
    Si algo existe o no se puede consultar: PARTIAL CLEANUP/VERIFICATION FAILED.
12. Repetir propiedades del backend, RG/cuenta/contenedor/key y lease libre.
    Conservar evidencias sanitizadas, revisar costes diferidos. Eliminar únicamente
    el plan privado propio cuando no haya operación activa; nunca el estado/versions.
    Si se requieren acciones fuera del estado, obtener otra autorización exacta.

Este proceso manual conserva los mismos límites, pero los controles son humanos:
una lectura o hash ignorado no ofrece seguridad. Si no puede revisar cada punto,
no ejecutar destrucción y acudir al responsable Azure autorizado.

## 9. Limitaciones y protección adicional futura

No es un temporizador cloud: no funciona con PC apagado/sin Internet, sesión MFA
inservible, permisos denegados, estado corrupto o servicios Azure indisponibles.
CLEAN se limita al inventario observable del despliegue; no garantiza ausencia de
cargos devengados ni recursos desconocidos creados fuera de su alcance.
No detecta semánticamente todo recurso ajeno infiltrado en un RG administrado:
la revisión humana del inventario es obligatoria antes de destruir un padre.
No garantía de borrado forense de planes ni de ejecución después de cancelación brusca.
No renombra/borra recursos ni usa datos PG-05/PG-06.

Una automatización Azure futura independiente del PC podría reducir riesgo de
abandono, pero exige identidad, permisos, coste, protección del estado y autorización
propios. No implementada ni activada; no confiar en ella para esta ventana.

## 10. Pruebas offline (no hacen una retirada)

    powershell.exe -NoProfile -ExecutionPolicy Bypass -File '<repo>/infra/scripts/Test-AksEmergencyTeardown.ps1'

Mocks reemplazan toda la frontera Native sin fallback. No invocan Azure ni Terraform.
28 escenarios, incluidos planes completo/parcial y confirmación correcta simulada.
No confundir esos resultados con una destrucción cloud real.

## Correccion local del descubrimiento Azure CLI — 17/11/2026

El wrapper ahora se llama Invoke-WordleAzureCli. La busqueda selecciona solo
aplicaciones externas az/az.cmd y exige una ruta absoluta existente; funciones
o alias llamados Az/az no se utilizan como ejecutable. Si falta la aplicacion,
comprobar la instalacion y PATH de esa terminal; no cambiar identidad ni ejecutar
logins por un error local de descubrimiento. Esta correccion pasa pruebas offline;
queda pendiente repetir el preflight real con autorizacion independiente.

## 9. Preparación local tras migración — 23/11/2026

FIN-17-AKS-RECOVERY-01: PARTIAL; recuperación humana NOT READY y remota NOT VERIFIED.
No ejecutar los comandos cloud de esta guía durante esta iteración.

- Script vigente: C:/WordleTFG/repo/infra/scripts/Invoke-AksEmergencyTeardown.ps1.
- Fuentes Terraform históricas: C:/WordleTFG/repo/infra/terraform.
- WorkDirectory humano: NO RESUELTO; C:/WordleTFG/recovery/workspace existe vacío.
  El contrato exige copia externa con fuentes/lock revisados y backend inicializado
  para la identidad humana; no acepta el directorio Terraform dentro del repo.
- TargetFile: NO RESUELTO. C:/WordleTFG/recovery/inputs/target.json NO existe.
- VariablesFile: NO RESUELTO. C:/WordleTFG/recovery/inputs/variables.json NO existe.
  Estos nombres son referencias documentadas, no inputs reales ni archivos creados.
- Backend identificado localmente en infra/terraform/backend.hcl.example y
  .terraform/terraform.tfstate; coincidencia de RG/cuenta/contenedor/key comprobada.
  AzureRM azurerm, Entra, key wordle/aks-demo.tfstate. No se verificó acceso remoto.
- Región histórica swedencentral; suscripción/tenant deben contrastarse con los
  identificadores aprobados, no adoptar automáticamente la sesión activa.
- fmt y validate locales exit 0; sintaxis PowerShell válida. Ningún init/plan/cloud.

Para una futura emergencia, cuando existan los tres parámetros REALES aprobados:
1. Revisar autorización de lectura y retirada, identidad humana y suscripción.
2. Comparar backend con objetivo y confirmar que es independiente del RG efímero.
3. Ejecutar sólo entonces el -Preflight de sección 4: incluye consultas Azure.
4. Revisar inventario/lease/estado actuales. Estado vacío no autoriza borrar huérfanos.
5. Sólo con autorización separada invocar -Teardown de sección 5, con VariablesFile.
   PLAN WORDLE AKS y DESTRUIR WORDLE AKS son confirmaciones humanas, no automatizarlas.
6. Verificar CLEAN, backend conservado, ausencias de recursos y costes diferidos.
No sustituir los parámetros por ejemplos con placeholders ni reutilizar caché OIDC.

## 10. Inputs materializados — 23/11/2026, FIN-17-AKS-RECOVERY-02

Esta sección actualiza el estado de la sección 9, conservada como historial.
Resultado PARTIAL; recuperación NOT READY y remoto NOT VERIFIED.

Rutas definitivas existentes:
- TargetFile: C:/WordleTFG/recovery/inputs/target.json.
  Trece campos reales verificados; operador/grupo derivados de FIN-AKS-ENTRA-PREP
  y tenant contrastado con metadatos locales de backend.
- VariablesFile: C:/WordleTFG/recovery/inputs/variables.json.
  Diecisiete variables verificables; NO contiene api_authorized_cidrs ni
  api_access_approved. No es aún un archivo de variables operativo completo.
- WorkDirectory: C:/WordleTFG/recovery/workspace.
  Cinco .tf, lock y backend.hcl.example, copia exacta SHA-256 de fuentes vigentes.
  Sin .terraform, estado, credenciales ni inicialización remota.

Los JSON nuevos tienen ACL restringidas a propietario/SYSTEM/Administrators.
No se modificaron las ACL del almacén aprobado.

Antes de cualquier ejecución real:
1. Revalidar grupo/operador humano e identidad de suscripción/tenant con autorización.
2. Obtener y aprobar el CIDR de acceso API correspondiente a esa ventana.
   No copiar el /32 histórico ni el del firewall Storage sin contrastarlo.
   Incorporar los dos campos pendientes sólo tras decisión explícita; no inferir
   api_access_approved=true de una aprobación de despliegue antigua.
3. Revisar deriva de fuentes y conservar lock; regenerar copia externa si cambia
   infraestructura. Comparar hashes y revisar inputs, nunca copiar .terraform.
4. Inicializar backend humano en el workspace externo únicamente con autorización
   separada. Referenciar backend.hcl.example y los IDs del TargetFile; usar Entra/CLI
   humana, no caché OIDC. init no se ejecutó en esta preparación.
5. Después seguir -Preflight y -Teardown de secciones 4/5 bajo autorizaciones.
   Nunca invocar ahora: falta configuración completa y backend humano inicializado.

Comandos futuros documentados, NO ejecutados:
    $PrivateTarget = 'C:/WordleTFG/recovery/inputs/target.json'
    $PrivateVariables = 'C:/WordleTFG/recovery/inputs/variables.json'
    $PrivateWork = 'C:/WordleTFG/recovery/workspace'
    $WordleScript = 'C:/WordleTFG/repo/infra/scripts/Invoke-AksEmergencyTeardown.ps1'
    # Sólo después de resolver las condiciones previas y autorizar lectura Azure:
    & $WordleScript -Preflight -TargetFile $PrivateTarget -WorkDirectory $PrivateWork
    # Sólo con autorización independiente de retirada y confirmaciones humanas:
    & $WordleScript -Teardown -TargetFile $PrivateTarget -WorkDirectory $PrivateWork -VariablesFile $PrivateVariables

La configuración histórica no acredita estado Azure actual. El backend identificado
permanece independiente de los RG efímeros; verificarlo de nuevo antes de actuar.
