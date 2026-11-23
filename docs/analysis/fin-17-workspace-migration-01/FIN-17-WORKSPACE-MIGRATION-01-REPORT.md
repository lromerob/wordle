# FIN-17-WORKSPACE-MIGRATION-01 — 23/11/2026

## 1. Resumen ejecutivo

**PASS.** Copia completa y no destructiva a C:\WordleTFG\repo. El origen permanece
intacto y disponible. Se preservan historia, índice, referencias, trabajo pendiente,
archivos ignorados, documentación y evidencias. Se corrigen exclusivamente rutas
de 19 archivos generados de .venv en la copia nueva, conforme a la autorización de
la fase 9. No se reinstalan paquetes ni se modifica código/evidencias históricos.
La migración no autoriza registro del runner, CD o Azure; continúan **NO-GO**.

## 2. Ruta de origen verificada

<LEGACY_REPO_ROOT> (repositorio histórico Wordle bajo OneDrive/Escritorio del usuario).
Directorio real con .git interno, no un checkout alternativo. La raíz tiene etiqueta
Cloud Files 0x9000e01a (OneDrive), sin bit Name Surrogate; no es junction/symlink que
redirija a otro proyecto. No hay reparse points dentro del árbol ni archivos
Offline/Recall pendientes de descarga; todos los bytes se leyeron localmente.
El destino es una carpeta normal, sin reparse tag; no se traslada la integración
OneDrive. [Referencia Microsoft](https://learn.microsoft.com/en-us/windows/win32/fileio/reparse-point-tags).

## 3. Ruta de destino

`C:\WordleTFG\repo`. C:\WordleTFG no existía en preflight: se creó nuevo con repo,
private, recovery y backups. No se adopta ni sobrescribe un proyecto preexistente.
Origen y destino son independientes, ninguno contiene al otro. No se cambia el
workspace abierto de IDE/Codex ni la configuración global de herramientas.

## 4. Inventario previo

- 9,927 archivos regulares; 1,479 subdirectorios; 450,785,323 bytes (~430 MiB).
- 464 archivos de .git; 16 referencias Git.
- 181 archivos versionados, nueve con cambios locales; índice vacío.
- 308 archivos sin seguimiento y 8,974 ignorados, incluidos entorno y dependencias.
- 315 archivos bajo docs/; 96 imágenes/PDF por extensión. Se conservan sin alterar
  los informes históricos y evidencias; no se valida de nuevo su contenido académico.
- Atributos ocultos relevantes preservados, incluido .git. Sin enlaces internos.

Preflight: consulta de procesos completada con acceso de lectura ampliado tras un
error CIM del sandbox. Ningún proceso ajeno referenciaba el origen, sin listeners
en 5173/8000/8080 ni proceso OneDrive observado. No se detuvo/modificó ningún proceso.
Espacio libre inicial: 736660938752 bytes, suficiente. La estabilidad se comprobó
además releyendo inventarios y hashes antes y después, no solo por procesos.

## 5. Procedimiento de copia

Robocopy a destino recién creado:

```text
/E /COPY:DAT /DCOPY:DAT /XJ /SL /R:0 /W:0 /XC /XN /XO /NP /NFL /NDL /NJH /NJS
```

Sin /MIR, purga, borrados, clone, /COPYALL o /SEC. /XC /XN /XO evita reemplazar
archivos ya existentes. Código Robocopy **1**: copia correcta, inferior al umbral
8 de error. Se preservan datos, atributos y timestamps; ACL del destino heredadas
normalmente de su ubicación local, sin copiar ACL OneDrive ni alterar permisos
existentes. No se siguen enlaces externos. Manifest/log técnicos fuera del repo,
retirados al finalizar; no se incorporan archivos privados al informe.

## 6. Resultado de integridad

Primera copia: **9.927/9.927 tamaños y SHA-256 iguales**, inventario de directorios
completo, cero discrepancias de timestamps de archivos y atributos ocultos.
Lectura posterior confirma que todos los archivos del origen conservan su hash.

Tras las correcciones funcionales autorizadas: **9.908 archivos idénticos** y
**19 excepciones generadas explícitas** (sección 10); sus hashes nuevos se verifican
contra la generación controlada. Ninguna diferencia sin explicación ni pérdida.
El único archivo adicional es este informe y su nuevo directorio de documentación.
No se eliminan archivos copiados, ignorados o evidencias.

Huella agregada del inventario original (rutas relativas, tamaños y SHA-256):
`8da5e89ba299815321a3febaf85dada26ca7e5d17289ed0773819d3d1f60684a`.
Huella agregada de .git, idéntica en ambas copias:
`f5ffcbb21bf0aab2a67cde32165b9dfce2f01bb4c4469e6310b782afa1940e8f`.

## 7. Comparación Git

Ambos árboles: codex/pg01-07-consolidation, HEAD
4d56cf265cc5f0af8c72c64f2a93373660e8f122; 16 referencias idénticas, índice vacío,
nueve cambios versionados y los mismos 308 sin seguimiento antes de este informe.
Origen continúa con 308; destino queda con **309**, exclusivamente por este informe.
Los 19 archivos corregidos son ignorados: no alteran el estado de trabajo versionado.

464 archivos .git y configuración local byte a byte iguales, sin exponer valores.
No core.worktree, hooksPath o fsmonitor local anclados a la ruta anterior.
`git fsck --full --strict`: exit 0; sin reescritura o limpieza de objetos.
Git se invocó con --no-optional-locks, GIT_OPTIONAL_LOCKS=0, GIT_NO_LAZY_FETCH=1,
fsmonitor deshabilitado solo por comando y safe.directory limitado por comando.
Sin operaciones remotas, refresh explícito de índice o cambios de configuración.

## 8. Comprobaciones funcionales

Desde el destino:
- Python 3.12.14 resuelve sys.prefix en C:\WordleTFG\repo\.venv.
- Activación PowerShell en proceso de prueba: prefijo nuevo correcto; sin PATH global.
- uvicorn --version correcto, sin arrancar aplicación; Vite 8.3.4 --version correcto.
- AST de 11 scripts Python operativos y parser de cinco PowerShell correctos.
- ROOT relativo, Dockerfile, contextos de build, runbooks/manifiestos e informes localizados.
- Compose base: backend/frontend/PostgreSQL; overlay test: backend/frontend;
  runner: un servicio, contextos docker/runner y scripts resueltos en el destino.
- Renderizado con --env-file temporal vacío y --no-env-resolution, solo placeholders
  sintéticos en memoria. No se leen .env reales ni se crean credenciales utilizables.
- Herramientas en PATH: Git 2.56.1, Docker CLI/Compose 5.6.1, Node 24.18.0/npm,
  Azure CLI, kubectl y kind. Solo se consultan versiones locales de Git, Node y
  Compose; Azure CLI/kubectl/kind se localizan sin invocarlos.
- Terraform/kubelogin no están en PATH en esta sesión: sus rutas externas operativas
  no se han revalidado ni reconfigurado; no se buscan instalaciones por el disco.

Sin suites de aplicación/Kubernetes/observabilidad, builds, contenedores o comandos
Terraform. No se comprueba autenticación Azure ni un despliegue real.

## 9. Referencias absolutas detectadas

| Referencia | Clasificación | Tratamiento |
|---|---|---|
| 17 ejecutables y dos activadores .venv/Scripts | Funcional, requería cambio | Regenerados/reubicados solo en copia |
| .venv/pyvenv.cfg, clave command | Histórica generada de creación | Conservada, no se utiliza para resolver el entorno |
| Home/base Python en caché de herramientas del usuario | Externa existente y válida | Conservada; mismo equipo, no portabilidad a otro equipo |
| Código/documentación operativa no ignorada | Sin referencias antiguas encontradas antes del informe | Rutas relativas funcionan; sin cambios |
| Metadatos npm/Vite revisados | Sin referencia antigua detectada | Conservados |
| Workspace abierto en IDE/Codex y rutas externas de herramientas | Externa, decisión del propietario | Abrir la carpeta nueva manualmente; no cambiar ajustes globales |
| Origen citado en este informe | Documental/histórica | Mantener como trazabilidad |

La búsqueda fue acotada al repositorio y metadatos generados conocidos; se excluyeron
.git, .env privados, estados/planes y configuraciones sensibles de inspección textual.
No se inspeccionaron valores de secretos. La copia/hash trata archivos como bytes.
No se reescriben informes históricos para sustituir rutas.

## 10. Cambios realizados en la copia nueva

Se corrigen únicamente .venv/Scripts/activate y activate.bat y estos 17 launchers:

dotenv.exe, email_validator.exe, httpx.exe, idna.exe, markdown-it.exe, pip-compile.exe, pip-sync.exe, pip.exe, pip3.12.exe, pip3.exe, pygmentize.exe, pyproject-build.exe, typer.exe, uvicorn.exe, watchfiles.exe, websockets.exe, wheel.exe.

Se utilizó el ScriptMaker de pip/distlib ya instalado, en staging técnico temporal,
para regenerar launchers Windows con el nuevo Python. ZIP CRC válido y __main__.py
exactamente idéntico en cada entrypoint; sin editar binarios a mano, reinstalar
paquetes o cambiar versiones. Los activadores solo sustituyen la ruta. Todos los
outputs se verificaron antes de escribir en la copia. Esta es la excepción de
hash autorizada por la fase 9; los archivos originales siguen intactos.

Único documento creado: este informe. Sin cambios de aplicación, infraestructura,
workflow, README, informes anteriores o configuración Git. [Python documenta que
los entornos venv no son portables sin tratar sus rutas](https://docs.python.org/3.12/library/venv.html#how-venvs-work).
El resultado conserva el mismo intérprete base externo y no pretende ser un paquete
portable a otro equipo.

## 11. Directorios complementarios

C:\WordleTFG\private, recovery y backups existen y permanecen **vacíos**.
Sin marker, UUID definitivo, variables/backend reales, planes, secretos o respaldo
aprobado. No se modifican ACL existentes. Un backup en C: no protege frente a fallo
del mismo disco. La aprobación/configuración privada pertenece a otro incremento.

## 12. Riesgos y limitaciones

La copia no sustituye backup externo. El origen queda conservado; no trabajar en
ambos árboles simultáneamente para evitar divergencias. Lecturas de filesystem
pueden actualizar LastAccess gestionado por Windows; no se escribe contenido,
LastWrite o configuración del origen. No se cambia/desactiva OneDrive.
Las comprobaciones de procesos son puntuales, complementadas por hashes completos.
Las rutas externas Terraform/kubelogin y la preparación real de CD no se acreditan
por trasladar el repo. Mantener revisión de los 19 launchers si se reconstruye .venv.

## 13. Reversibilidad

Volver al origen no requiere restauración: está intacto, con su .venv original y
Git pendiente conservado. No se mueve/baja otra aplicación ni se elimina nada del
origen. El propietario decide cuándo dejar de utilizar la carpeta anterior.

## 14. Criterios GO/NO-GO

**PASS / GO para trabajar localmente en C:\WordleTFG\repo**: integridad y Git
preservados, correcciones funcionales explícitas verificadas, documentación/evidencia
conservadas, comprobaciones focalizadas correctas y directorios vacíos preparados.
Sin staging/commit/push, runner, workflows, Docker resources, Terraform remoto,
Azure, cambios de permisos existentes o configuraciones globales.
**CD/AKS NO-GO**: este traslado no aprueba almacén privado, recuperación ni despliegue.

## 15. Próximo incremento

Abrir manualmente C:\WordleTFG\repo en IDE/Codex y continuar la aprobación del
almacén definitivo/rutas de retirada humana en una iteración separada. No crear
marker/credenciales ni registrar runner como continuación automática. No borrar
el origen; conservarlo hasta una decisión explícita del propietario.

> Rutas personales normalizadas editorialmente para publicación. Resultados, fechas, hashes y entorno histórico no cambian. <USER_HOME> designa el directorio personal original; variables PowerShell se resuelven para el usuario que reproduce. <LEGACY_REPO_ROOT> identifica el origen histórico, no el workspace vigente.
