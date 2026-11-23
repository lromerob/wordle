# FIN-17-DOCKER-RUNNER-01 — 22/11/2026

## 1. Resumen ejecutivo

**PARTIAL.** Imagen Linux x64 construida y runtime validado; todas las herramientas
requeridas y Chromium funcionan sin registro ni acceso cloud. Bloqueo concreto:
el bind Windows devuelve modo 0777 y no supera el contrato POSIX del store privado.
Se conserva el rechazo estricto; no se ha cambiado R1/R2/R4/R6/R8 para sortearlo.
No hay runner registrado ni CD operativo. AKS/CD permanece NO-GO.

## 2. Arquitectura implementada

Un servicio wordle-actions-runner en Docker Desktop Linux; Ubuntu 24.04 fijado por
digest, runner oficial 2.338.2, UID/GID 10001, Tini, capabilities eliminadas y
no-new-privileges. Sin privileged, socket/CLI/daemon Docker, DinD, puertos o SSH.
La validación usa network none; el uso futuro requiere únicamente salida autorizada.
El CI hospedado y workflow CD existentes no se modifican.

## 3. Archivos creados y modificados

Únicamente 12 archivos nuevos; ningún archivo previo modificado:

- docker/runner/Dockerfile
- docker/runner/.dockerignore
- docker/runner/.gitignore
- docker/runner/compose.yaml
- docker/runner/runner.env.example
- docker/runner/install_tools.py
- docker/runner/entrypoint.py
- docker/runner/Invoke-WordleRunner.ps1
- docker/runner/test_runner.py
- docker/runner/validate_local.py
- docs/operations/wordle-docker-runner.md
- Este informe.

La whitelist de contexto de build permite solo Dockerfile, installer y entrypoint;
no se envían el checkout completo, .env, tests ni configuraciones privadas.

## 4. Imagen y herramientas

Imagen local: wordle-actions-runner:fin17-local.
ID inmutable observado: sha256:92c225acb3b2adfe517834376ffa5317be0aebe5f80d3d42585587cec3ed8ff9.

Tamaño lógico Docker: 3500610119 bytes (~3.26 GiB).

| Herramienta | Versión comprobada en el contenedor |
|---|---|
| Git | 2.43.0 |
| Python | 3.12.3, alias python disponible |
| Node | 24.18.0 |
| Terraform | 1.9.8 linux_amd64, solo version |
| Azure CLI | 2.86.0, solo version |
| kubectl | 1.35.3; Kustomize 5.7.1, solo cliente |
| kubelogin | 0.2.22 |
| Actions Runner | 2.338.2, solo --version |
| Playwright | 1.62.1 |
| Chromium headless shell | 151.0.7922.34, build Playwright 1234 |

Fuentes oficiales: Ubuntu/Docker Library, Microsoft APT con key fingerprint y firma;
[runner/checksums](https://github.com/actions/runner/releases/tag/v2.338.2),
[kubelogin/checksum](https://github.com/Azure/kubelogin/releases/tag/v0.2.22),
[Terraform/SHA256SUMS](https://releases.hashicorp.com/terraform/1.9.8/),
[Node/SHASUMS256](https://nodejs.org/dist/v24.18.0/),
[kubectl/checksum](https://dl.k8s.io/release/v1.35.3/bin/linux/amd64/kubectl.sha256),
npm oficial y CDN oficial Playwright. Cada archivo de herramientas verificadas se
rechaza si no coincide con el hash oficial. npm verifica integrity; el browser usa
el instalador oficial de Playwright. No se afirma verificación de firma independiente
del browser. Ubuntu aplica paquetes de seguridad del repositorio firmado: rebuild
no garantiza identidad binaria pese a fijar base y herramientas principales.

El tamaño se redujo ~0.88 GiB evitando duplicar archivos del runner al cambiar
propietario en otra capa. Azure CLI y runtimes del runner/browser son componentes
necesarios; no se instalaron Docker, frontend/backend ni herramientas de producción extra.

## 5. Compatibilidad con GitHub Actions

Registro futuro limitado por URL fija a https://github.com/lromerob/wordle y etiqueta
wordle-azure; etiquetas predeterminadas self-hosted/Linux/X64 satisfacen el YAML.
Checkout previsto en /home/runner/_work, usuario 10001. Python y herramientas en PATH,
capturador configurado con rutas Linux /opt/wordle-browser. Helpers CD actuales usan
biblioteca estándar Python, no requieren instalar dependencias de la aplicación.

Default validate no lee token ni registra/escucha. activate requiere autorización
REGISTER_RUN explícita y token efímero por stdin; no argumento, build arg ni archivo.
config.sh recibe ACTIONS_RUNNER_INPUT_TOKEN solo como entorno de su proceso hijo; salida
suprimida y token eliminado de ese diccionario tras terminar. Se prepara --ephemeral
(un job por registro) y --disableupdate. run/remove mantienen autorización explícita.
No se ejecutó ninguna de esas operaciones. Pruebas de registro usan subprocess
simulado y un literal sintético, nunca un token de GitHub.

Labels no son barrera de autorización: verificar políticas y ausencia de PRs
no confiables antes de activar. CI sigue en ubuntu-latest. No se modificaron
CI, OIDC, reviewers, gate, selección de release o retirada. Registro/admisión
real, environment/runner y ejecución de workflow: NOT RUN.

## 6. Almacenamiento privado

Compose requiere WORDLE_PRIVATE_HOST_DIR existente, absoluto y externo, mediante
configuración privada futura, y monta /wordle-private sin creación automática.
No se eligió ni creó un almacén real fuera del repo ni se inventaron IDs aprobados.
El environment protegido deberá usar /wordle-private como ruta Linux y el store UUID
aprobado. Planes, selections, evidencia y backups sobreviven solo si ese bind real
está custodiado; el filesystem de la imagen/contenedor no es el almacén durable.

Prueba real sobre directorio temporal propio dentro del repo (no apto como store
definitivo): lectura/escritura y retorno del archivo sintético al host satisfactorios.
Root y marker se presentan 0777 desde Linux. require_store rechaza la falta de
almacén y el marker físico false/no aprobado. Para aislar la comprobación POSIX,
solo se simuló en memoria la deserialización del marker: stat sobre el bind real
provocó el rechazo por permisos group/other. No se escribió un marker aprobado ni
se modificó private_store.py. No se atribuye durabilidad física al ensayo.

Solución mínima documentada, PENDIENTE DE DECISIÓN: compatibilidad explícita con ACL
Windows verificadas, limitada al directorio aprobado, o proporcionar un bind ya
existente que conserve semántica POSIX y supere el contrato sin cambios. La primera
opción exige aprobar el cambio de contrato antes de implementarlo. No se instala
WSL/distro ni se propone privileged, chmod 777, marker falso, almacenamiento efímero
o relajar silenciosamente las comprobaciones. Este bloqueo impide activar CD hoy.

## 7. Seguridad

Inspección real: USER 10001:10001, Privileged=false, CapDrop=ALL, sin PortBindings
ni socket Docker, no Docker CLI, registrado=false. Variables de imagen sin tokens,
client secrets, contraseñas o claves. Contexto restringido y ejemplos sin secretos.
El contenedor de validación no montó repo completo, perfil Azure, kubeconfig ni .env.
No se extrajeron credenciales de otros proyectos ni se usó identidad Azure real.
Docker no se presenta como aislamiento fuerte de código malicioso. Apagar fuera
de sesiones y no convertir un contenedor registrado en imagen mediante docker commit.

## 8. Retirada humana

Invoke-AksEmergencyTeardown.ps1, sus tests y runbook permanecen idénticos. Recuperación
Windows con humano y herramientas propias, independiente de Docker/Actions. Inputs
JSON pueden referirse al mismo backend aprobado sin copiar sesión/token humano al
runner. Mantener TargetFile y workspace Windows separados del cache/proveedores/plan
Linux. No se ejecutó el script ni se generó plan. No prueba operativa de retirada.

## 9. Pruebas realizadas

- Docker Desktop 29.9.2, Linux x86_64; Compose v5.6.1. Contenedor PG-06 existente
  fafa5f0b92b8 identificado y preservado, sin exec/start/stop sobre él.
- Build real de imagen, incluidos hashes de herramientas y paquetes oficiales.
- Diez unitarias focalizadas, cero fallos/errores/omitidas: modo por defecto,
  autorización, rechazo root/acciones desconocidas, URL/etiquetas, stdin sin token
  en argv, checksum corrupto, whitelist y restricciones Compose. Registro siempre mock.
- AST Python de cuatro archivos y parser PowerShell del helper correctos.
- docker compose config: un servicio, bind explícito, create_host_path=false,
  sin privileged/puertos y validate por defecto. Ausencia de ruta provoca rechazo.
- Contenedor real de validación, sin red y sin registro: ocho herramientas, UID,
  arquitectura, permisos/montajes, ausencia de Docker CLI/socket y credenciales.
- Lectura/escritura sintética del bind y rechazo estricto descrito en §6.
- Motor Playwright existente, con Chromium del runner y página sintética loopback:
  PNG auténtico 1440x1000, firma/hash comprobados. No prueba funcional Wordle/AKS.
  SHA-256 del PNG diagnóstico temporal: e8d95cc9c71bef868da6fa4a5aeb53ca4f18a1af98a213272301511d8d559005.
- Parada limpia con código 0; eliminación del contenedor y fixture propios.
  Identificador de la validación final: 6b92e4ae37cd.
- Revisión de patrones sensibles en fuentes nuevas y git diff --check.

La primera prueba detectó que el fixture aplanado calculaba ROOT=/; se corrigió
únicamente su estructura para preservar el cálculo original del helper. La nueva
prueba pasó y detectó el problema real de modos Windows. Ningún script previo se
cambió para hacer pasar la validación. La fuente oficial confirmó el prefijo ACTIONS_RUNNER_INPUT_TOKEN; se corrigió antes de entregar y una regresión comprueba el canal exacto. La imagen final se reconstruyó y validó después de esa corrección, sin registro.

## 10. Resultados

PASS: build, herramientas, runtime, Chromium, aislamiento de validación, parada y
limpieza de contenedores/fixtures. PASS del rechazo seguro ante store ausente o no
aprobado. Incompatibilidad real del bind POSIX: confirmada, no resuelta por bypass.
NOT RUN: registro, tokens, listener, workflows, OIDC real, Terraform remoto, AKS.
**Resultado conjunto PARTIAL**, no runner operativo para CD.

## 11. Limitaciones

Imagen grande (~3.26 GiB) por runtimes requeridos; estado del runner y credenciales
futuras viven en el contenedor, no se publican. Un registro efímero interrumpido puede
quedar offline en GitHub; parada local no garantiza baja remota. El runbook indica
verificar/remover desde GitHub con autorización. No se solicitan tokens en esta fase.
Registro compatible con la versión aceptada por GitHub deberá confirmarse en ventana
posterior; no actualización automática ni instalación global. Internet de ejecución,
IP de salida /32 y acceso Azure/Storage/GHCR no se probaron. Las únicas conexiones
externas fueron documentación y descargas públicas oficiales autorizadas del build.

## 12. Configuraciones pendientes

- Resolver y aceptar la compatibilidad del store Windows sin debilitar silenciosamente
  el contrato; elegir ruta externa, ACL/custodia, UUID/marker y entradas reales.
- Verificar environment, reviewers, branch policy, runner elegible, versión aceptada,
  principal OIDC/roles y red antes de solicitar registro efímero.
- Configurar en el futuro WORDLE_AZURE_PRIVATE_DIR=/wordle-private y store ID en el
  environment, así como las identidades/credenciales sintéticas ya previstas.
- Target/workspace humano Windows y conservación de evidencia/backups aprobados.

No se ha configurado ninguno automáticamente ni se han reutilizado datos personales.

## 13. Criterios GO/NO-GO

GO para repetir validación local sin registro. NO-GO de activación/registro/CD hasta
resolver §6 y verificar prerrequisitos externos. La construcción no autoriza
publicación, recursos Azure, cambio main ni pipeline. FIN-17 permanece pendiente
como ejecución integrada AKS; no se modifica el plan ni estados académicos.

## 14. Próximo incremento

Decidir una solución acotada y verificable de permisos para el bind Windows; después
completar las lecturas externas pendientes. Registro y CD requieren autorización
expresa distinta. No se inicia esa tarea. Reproducción y operaciones futuras en
[runbook](../../operations/wordle-docker-runner.md).

## 15. Integridad Git

Rama codex/pg01-07-consolidation; HEAD
4d56cf265cc5f0af8c72c64f2a93373660e8f122. Índice vacío. Nueve versionados ya
modificados y 301 sin seguimiento al terminar. Los 470 archivos no ignorados previos
conservan sus SHA-256; doce archivos nuevos, ninguno previo modificado/eliminado.
Se conservan doce informes históricos y todos los dossiers. Sin add/commit/push,
fetch o cambio de rama. Sin cambio de workflow, aplicación o configuración global.

Los fixtures temporales propios, incluida la captura diagnóstica, se retiraron;
no se publican como evidencias de aplicación. Ningún contenedor de validación queda
activo. Solo se conserva la imagen final y puede quedar cache de construcción:
no se hizo prune ni se borraron imágenes/volúmenes ajenos. La retirada opcional de
la primera referencia de imagen no se confirmó; no se forzó ninguna eliminación.
No se creó un volumen Docker ni un almacén externo privado.

Sin registro ni token de registro real, workflow, OIDC/RBAC, operación Azure,
Terraform remoto, Kubernetes, publicación GHCR o recurso PG-05/PG-06 modificado.
