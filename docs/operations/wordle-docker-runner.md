# Wordle — Runner Docker y almacén Windows supervisado

FIN-17-PRIVATE-STORE-02: **PASS local con fixtures sintéticos**. El almacén definitivo
no está aprobado ni creado. Runner no registrado; CD/AKS continúa **NO-GO** hasta
completar configuración y autorizaciones externas. Los informes anteriores se
conservan como evidencia histórica; este procedimiento sustituye su bloqueo local.

## Modelo de confianza

El operador controla Windows y Docker Desktop y ejecuta código revisado. PowerShell
comprueba el almacén antes del arranque, verifica el Compose efectivo y emite un
recibo temporal fuera del almacén, montado en solo lectura en /run/wordle-host.
Linux comprueba ese recibo y la identidad/estructura del bind /wordle-private.
No es autenticación criptográfica ni protección frente a un administrador Windows,
Docker o un contenedor comprometido. No aceptar workflows/código no confiables.
Una variable aislada o un JSON autocreado dentro del store no autoriza Windows.

Docker Desktop presenta el bind Windows como 0777; ese modo emulado no acredita los
permisos NTFS. **POSIX es el modelo predeterminado y sigue rechazando group/other**.
Windows solo se selecciona explícitamente mediante el lanzador, sin fallback por 0777.

## Componentes

Ubuntu 24.04 fijado por digest, Linux amd64, UID/GID 10001, Tini, cap_drop ALL,
no-new-privileges, sin puertos, socket/CLI Docker ni privileged. Herramientas ya
verificadas: Git 2.43.0, Python 3.12.3, Node 24.18.0, Terraform 1.9.8, Azure CLI
2.86.0, kubectl 1.35.3, kubelogin 0.2.22, runner 2.338.2, Playwright 1.62.1 y Chromium.
Los checksums/repositorios oficiales siguen en install_tools.py y Dockerfile.

La imagen nueva es wordle-actions-runner:fin17-private-store-02. Se conserva la
anterior fin17-local. Dockerfile copia el contrato real scripts/private_store.py
mediante el contexto adicional store_contract, sin duplicar su implementación.
El contexto principal mantiene su allowlist; no se montan .env, perfiles Azure
humanos o el checkout completo para las pruebas. No hay dependencias nuevas.

Desde la raíz Wordle, PowerShell 7:

```powershell
docker build --build-context store_contract=./scripts -t wordle-actions-runner:fin17-private-store-02 -f docker/runner/Dockerfile docker/runner
.venv/Scripts/python.exe -B -m unittest discover -s docker/runner -p 'test_*.py' -v
./docker/runner/Test-WordleSupervisedStore.ps1 -RunDocker
.venv/Scripts/python.exe -B docker/runner/validate_persistence.py --run-local-validation
```

El self-test crea directorios NTFS temporales sintéticos, fija ACL al crearlos y los
elimina; no cambia permisos de rutas existentes. Incluye un fixture intencionalmente
permisivo para probar su rechazo. Todo contenedor de prueba tiene network none y
se elimina. validate-hold es solo diagnóstico, sin listener, y se comprueba SIGTERM.
La prueba de persistencia escribe desde un contenedor, compara SHA-256 en Windows,
lo elimina y verifica bytes/hash desde otro. No prueba fallo del disco ni backups.

## Preflight Windows: política local conservadora

Test-WordlePrivateStore.ps1 verifica ruta absoluta, disco fijo NTFS, existencia,
independencia del checkout y ausencia de UNC/reparse points en ruta y descendientes.
Inspecciona ACL de root y todos sus objetos sin abrir sus contenidos; lee únicamente
el marker contractual. Exige owner igual al usuario Windows actual, DACL canónica
no nula y FullControl directo al usuario sobre cada objeto.

Se aceptan ACE Allow únicamente para el usuario actual, SYSTEM (S-1-5-18) y
Administrators (S-1-5-32-544). La herencia por sí sola no es un defecto: cada ACE se
evalúa por identidad y derechos. Otros actores, incluso con solo lectura, y ACL
con Deny, ACE especiales/no interpretables, owner diferente o acceso insuficiente
se rechazan. Es un subconjunto deliberadamente conservador, no AccessCheck completo.
No se amplía automáticamente por grupos corporativos ni se ejecuta Set-Acl.
Si una ruta definitiva no cumple, el propietario debe revisar su política aparte.

Antes de cada lanzamiento se realiza el preflight, se renderiza/verifica Compose
y se repite el preflight. Se comprueban fuente y destino de ambos binds, UUID,
modelo, comando, usuario y restricciones de exposición. Se congela el JSON verificado
para evitar que una segunda interpolación cambie el bind. Los controles temporales
nuevos se crean con ACL restrictiva; ningún ACL existente se modifica.

## Configuración definitiva — pendiente del propietario

Elegir y aprobar una ruta Windows persistente externa, UUID, operadores, custodia,
backup/retención y procedimiento de recuperación. No se propone una ruta real ni
se crea un almacén automáticamente. Mantener la estructura:

```text
.wordle-private-store.json
variables.json
backend.json
plans/
selections/
evidence/
backups/
```

El marker real conserva exactamente format, repository, store_id y
**durable_acknowledged=true**, solo después de aprobación humana del almacenamiento
y respaldo. Un marker no demuestra por sí mismo durabilidad, cifrado o restauración.
Variables/backend y los demás inputs siguen sujetos a R1/R2/R4/R6/R8; el preflight
no los abre ni sustituye los gates de release, identidad, plan o evidencia.

Preparar fuera del repo una copia secret-free de runner.env.example con solamente
la ruta Windows aprobada y el UUID. El lanzador exige además esos mismos valores
como argumentos y rechaza un bind o UUID diferente, incluidas sustituciones por el
entorno del proceso. No editar Compose para saltarse el procedimiento.

```powershell
# FUTURO: completar solo después de aprobar ruta, UUID y procedimiento de respaldo.
$cfg = '<archivo externo runner.env sin credenciales>'
$store = '<directorio Windows existente y aprobado>'
$id = '<UUID aprobado>'
$backup = '<referencia al procedimiento de respaldo aprobado>'
./docker/runner/Test-WordlePrivateStore.ps1 -StorePath $store -StoreId $id -StorageApproved -BackupProcedureReference $backup
./docker/runner/Invoke-WordleRunner.ps1 -Action Validate -ConfigurationFile $cfg -StorePath $store -StoreId $id -StorageApproved -BackupProcedureReference $backup
```

El helper devuelve PASS/exit 0 o BLOCKED/exit 2. Validate inicia solo diagnóstico
sin red, registro o listener y elimina su contenedor al terminar. Build construye
la imagen, no aprueba ni arranca un almacén. Stop conserva la comprobación de labels
sobre el nombre de sesión propio; detener un runner no retira AKS.

## Validación Linux y vigencia

El lanzador selecciona WORDLE_STORE_MODEL=windows-supervised. private_store.py exige
ruta /wordle-private, bind dedicado y un mount separado **ro** en /run/wordle-host;
lee approval.json desde esa ruta fija, nunca desde una variable configurable.
Comprueba esquema del recibo, repo, emisor/política, UUID, ruta, hash del marker,
fingerprint ACL, sesión y validez temporal de seis horas como máximo. Mantiene
marker real exacto, aprobación de durabilidad y cuatro directorios obligatorios,
sin symlinks. Solo omite los bits POSIX emulados en este modelo explícito.

La correspondencia con la ruta Windows y la revisión ACL las garantiza el lanzador
bajo el modelo de confianza del operador; Linux no calcula permisos NTFS ni verifica
criptográficamente el fingerprint. La validez temporal no es monitorización continua.
Cada nueva activación requiere otra revisión/recibo; cambios durante una sesión
exigen detenerla y repetir el control. No se reutilizan recibos como aprobación
permanente. La limpieza retira únicamente controles y contenedores propios.

Para tests existe windows-supervised-test: exige marker con
**durable_acknowledged=false** y synthetic_fixture=true, y recibo fixture_only=true.
Solo el self-test lo utiliza; no es un almacén real aprobado. Host y entrypoint
rechazan este modelo para registro y listener, incluso con el flag de autorización.

## Registro futuro — requiere autorización separada

No ejecutado ni autorizado por esta iteración. Antes: verificar GitHub environment,
reviewers, rama/SHA/CI, versión admitida, OIDC/RBAC, red y presupuesto conforme a los
gates existentes. CI continúa hospedado; labels no autorizan código por sí solas.

Solo después de una autorización nueva del propietario:

```powershell
# NO ejecutar durante la preparación. No proporciona ni solicita tokens ahora.
./docker/runner/Invoke-WordleRunner.ps1 -Action Activate -ConfigurationFile $cfg -StorePath $store -StoreId $id -StorageApproved -BackupProcedureReference $backup -AuthorizeRegistrationAndListener
```

Activate requiere todos los controles reales, rechaza fixtures y solo entonces
pide el token efímero por Read-Host -MaskInput. Lo entrega por stdin, nunca en args,
configuración, imagen o logs. config.sh usa ACTIONS_RUNNER_INPUT_TOKEN solo en el
hijo. Repo fijo lromerob/wordle, --ephemeral, un job por sesión, sin auto-update.
Esta acción futura usa bridge con salida; no publica puertos. El flag evita errores
operativos, no autentica al propietario. No invocar activate/run/register directamente
con Docker para omitir el procedimiento. No guardar un runner usado con docker commit.

La sesión futura se llama wordle-actions-runner-session. Stop verifica labels antes
de detenerla. Si se interrumpe un registro efímero, verificar/remover su entrada
GitHub solo con autorización; detener Docker no garantiza baja remota.

## Retirada humana y recuperación

infra/scripts/Invoke-AksEmergencyTeardown.ps1 sigue íntegro y se ejecuta desde Windows,
con identidad humana y herramientas propias, sin depender de Docker/Actions.
TargetFile, WorkDirectory y VariablesFile deben ser externos y aprobados, coherentes
con el mismo backend; no copiar caché .terraform o planes Linux al workspace humano.
No montar sesión/token Azure humano en el runner OIDC.

Las rutas humanas reales, disponibilidad de sus inputs y backups siguen NOT VERIFIED.
No se inventan ni se buscan fuera de las referencias aprobadas. El propietario debe
confirmarlas antes de CD. El kit R1 incluye los archivos del procedimiento vigente
para poder reconstruir el runner; no contiene inputs privados ni herramientas.
El validador legado validate_local.py se conserva en las fuentes Git completas,
no se incorpora al kit operativo: es un diagnóstico anterior, no una dependencia
del arranque supervisado. Restaurar evidencia/backups desde la custodia aprobada,
verificar hashes y volver a ejecutar preflight, nunca reutilizar una aprobación vieja.

**GO local** para los tests descritos. **NO-GO de registro/CD/AKS** hasta aprobación
real de almacén, recuperación humana y controles externos. No se realizaron operaciones
Azure/GitHub, publicación de imágenes ni cambios de configuración global.
