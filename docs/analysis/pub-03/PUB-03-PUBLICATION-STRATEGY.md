# PUB-03 — Estrategia propuesta de publicación

Fecha: 09/11/2026. **READY FOR COMMIT**: se puede solicitar autorización para preparar y crear el commit. No se ha ejecutado la estrategia ni se autoriza commit/push por este documento. FIN-01 pendiente.

## Estado real y rama recomendada

Fetch autorizado correcto: origin/main es 86cbf8936dc04abc39b8bee26c37767328db13df (merge PR#5), un commit por delante de HEAD a666b17680781a24889ea774778019995d3fca45. HEAD es ancestro; no hay commits locales exclusivos ni divergencia lateral. Ambos árboles son cf8c64542e1e1a79dd581415d41c22161141a89a: **archivos base idénticos**, pese a que main avanzó en historial.

Recomiendo una rama nueva **codex/pg01-07-consolidation desde origin/main actualizado**, llevando los cambios sin commit al mismo árbol base, únicamente después de autorización explícita. La rama codex/devops-04a1-hardening queda preservada en su commit original, ya integrado en main. La propuesta no requiere merge, rebase, stash, reset o force push. La rama nueva no existe localmente; su posible existencia remota se debe verificar en la fase de publicación autorizada (PUB-03 solo permite fetch main).

Los81 archivos actuales coinciden exactamente con PUB-02, regulares y no ignorados:16 modificados/65 nuevos. No se ha perdido trabajo. Los tres informes PUB-03 son archivos adicionales autorizados para esta auditoría: no se incorporan automáticamente a esos81. Propuesta por defecto: commit de81 rutas; si el propietario aprueba incluir también los informes PUB-03, revisar una lista explícita de84 antes del add. No generar un add global ni incorporar archivos fuera de esa selección.

## Alternativas y por qué no se ejecutan ahora

| Alternativa | Evaluación |
|---|---|
| Commit/push sobre codex/devops-04a1-hardening | Técnicamente viable: no hay diferencias de base ni conflicto detectado. Mantiene el nombre de una tarea ya fusionada y una base de historial un merge por detrás; menos clara para revisar PG-01/07 |
| Nueva rama desde origin/main, conservando cambios | Recomendada: conserva ref anterior y comienza exactamente en main; árboles idénticos permiten trasladar el estado sin integración de contenidos. Revalidar antes de cambiar rama |
| Merge/rebase para actualizar la rama vieja | Innecesario para el contenido actual; introduciría cambios de historial/pasos adicionales sin beneficio demostrado |
| Clon/worktree o stash para trasladar trabajo | No necesarios aquí; añadirían gestión de65 archivos sin seguimiento y riesgo de omitirlos. Valorar solo si el estado cambia, con autorización distinta |

No se garantiza que una operación futura sea inocua si main/archivos cambian. Si hay novedad, rama remota ocupada, error o conflicto, detenerse: no forzar checkout ni usar reset/clean/stash para continuar.

## Secuencia exacta propuesta, NO ejecutada

Desde la raíz del repositorio en PowerShell. Requiere autorización nueva que incluya creación/cambio de rama y preparación del índice; commit y push deben estar expresamente autorizados. safe.directory se limita a cada invocación. Las comprobaciones paran si el estado observado dejó de ser el de PUB-03.

### 1. Revalidar y abrir la rama de publicación

```powershell
$repoGitPath = (Get-Location).Path.Replace('\', '/')
function Invoke-WordleGit {
    & git -c "safe.directory=$repoGitPath" @args
    if ($LASTEXITCODE -ne 0) { throw 'Git falló: detenerse sin integración ni recuperación automática.' }
}
if ((Invoke-WordleGit branch --show-current) -ne 'codex/devops-04a1-hardening') { throw 'La rama cambió; revisar.' }
if ((Invoke-WordleGit rev-parse HEAD) -ne 'a666b17680781a24889ea774778019995d3fca45') { throw 'HEAD cambió; revisar.' }
Invoke-WordleGit diff --cached --quiet
# Verificar de nuevo origin, sin imprimir credenciales, antes de conectar.
Invoke-WordleGit fetch origin main
if ((Invoke-WordleGit rev-parse origin/main) -ne '86cbf8936dc04abc39b8bee26c37767328db13df') { throw 'main cambió: reevaluar sin seguir.' }
Invoke-WordleGit diff --quiet HEAD origin/main
Invoke-WordleGit switch -c codex/pg01-07-consolidation origin/main
Invoke-WordleGit status --short --untracked-files=all
```

Capturar y comparar hashes de los81 archivos antes/después de switch, además de comprobar el índice vacío y la selección. Si Git rechaza la operación o cambia un hash, detenerse sin forzar. No se realizó switch ni creó una rama en PUB-03. Los demás archivos/secretos locales quedan fuera del conjunto y no se borran. Un backup privado, si se desea, requiere su propia acción autorizada; no se publica.

### 2. Preparar únicamente la lista aprobada de81

```powershell
$publicationPaths = @(Select-String -Path 'docs/analysis/pub-02/PUB-02-PUBLICATION-MANIFEST.md' -Pattern '^\| `([^`]+)` \| (?:Modificado, ya versionado|Nuevo, sin seguimiento) \|' | ForEach-Object { $_.Matches[0].Groups[1].Value })
if ($publicationPaths.Count -ne 81 -or (@($publicationPaths | Sort-Object -Unique)).Count -ne 81) { throw 'Manifiesto inesperado.' }
foreach ($publicationPath in $publicationPaths) {
    if (-not (Test-Path -LiteralPath $publicationPath -PathType Leaf)) { throw 'Falta un archivo aprobado.' }
}
# Revisar previamente tipo/ignorados/riesgos y correspondencia con el estado actual.
$addArguments = @('add', '--') + $publicationPaths
Invoke-WordleGit @addArguments
Invoke-WordleGit diff --cached --check
$prepared = @(Invoke-WordleGit diff --cached --name-only)
if (@(Compare-Object ($publicationPaths | Sort-Object) ($prepared | Sort-Object)).Count -ne 0) { throw 'Índice distinto del manifiesto.' }
Invoke-WordleGit diff --cached --stat
```

DETENERSE aquí para inspeccionar el índice real y ejecutar análisis de secretos sin mostrar valores antes del commit. No basta reutilizar un informe anterior. La revisión debe distinguir los seis indicadores justificados de CI/variables/generación aleatoria de cualquier hallazgo nuevo, y analizar los blobs preparados, no solo el working tree. El contenido histórico Supabase se publica solo como archivo con su nota, nunca como init activo. No hay un script de escaneo dedicado en el repositorio: usar una comprobación inline/revisión autorizada, sin inventar un comando existente ni volcar secretos.

Si se autorizan los tres informes PUB-03, sustituir esta lista por otra explícita de84 y revisar los tres adicionalmente; no basta cambiar el número81 sin enumerarlos. Ninguno está staged ahora.

### 3. Commit solo después de revisión/autorización

Mensaje propuesto, no creado:

```powershell
Invoke-WordleGit commit -m 'feat: migrate Wordle to PostgreSQL and consolidate local DevOps validation'
Invoke-WordleGit show --stat --oneline HEAD
Invoke-WordleGit status --short --untracked-files=all
```

La rama antigua debe seguir en a666b17680781a24889ea774778019995d3fca45. Revisar que el commit tenga exactamente la lista aprobada. Si se eligen81, los tres informes PUB-03 seguirán sin seguimiento por decisión explícita: no confundirlo con pérdida de trabajo ni exigir clean. Los archivos privados/ignorados siguen locales. No hay commit en PUB-03.

### 4. Push exclusivamente a la rama nueva, con autorización

Verificar antes el destino efectivo de push sin revelar valores privados y comprobar que el nombre remoto esté libre. La consulta siguiente es una operación remota FUTURA que no se realizó ni está autorizada para ejecutarse en PUB-03:

```powershell
$existingRemoteBranch = @(Invoke-WordleGit ls-remote --heads origin refs/heads/codex/pg01-07-consolidation)
if ($existingRemoteBranch.Count -ne 0) { throw 'Rama remota existente: revisar antes de publicar.' }
if ((Invoke-WordleGit branch --show-current) -ne 'codex/pg01-07-consolidation') { throw 'Rama incorrecta.' }
Invoke-WordleGit push --set-upstream origin HEAD:refs/heads/codex/pg01-07-consolidation
```

No push a main, force ni force-with-lease. Si falla autenticación o Git solicita interacción inesperada, detenerse y no cambiar configuración para conseguir acceso. Verificar después que el SHA remoto coincida con el commit mediante una consulta autorizada. No ejecutar ninguna publicación GHCR, Azure o despliegue por este paso.

## Autorizaciones necesarias y comprobaciones posteriores

1. Aprobar rama recomendada y conjunto81 o84, con hashes/contenidos actuales.
2. Autorizar creación/cambio de rama y add; después revisión del índice/secretos y autorización del commit, con su mensaje/lista exactos.
3. Autorizar push/consulta del destino y cualquier PR o ejecución manual posterior. Nada de esto se hizo en PUB-03.
4. Crear el PR manualmente hacia main cuando se autorice. Comparación propuesta: https://github.com/lromerob/wordle/compare/main...codex/pg01-07-consolidation?expand=1. No se abrió ni creó.

El workflow actual escucha pull_request, workflow_dispatch y push solo a main. **Un push a esta rama por sí solo no activa CI por evento push**: usar el PR o un dispatch autorizado para verificarla. Conservar el run/SHA/enlace y55 offline/once reales/cero omitidas, frontend/Docker, Kustomize, kind memoria efímero autorizado y Terraform. GHCR debe quedar skipped. No hacer merge para provocar una ejecución sin revisión.

No se afirma validación remota de GitHub, ni se repiten pruebas funcionales o builds en esta auditoría. Se mantienen límites de identidad, fixture de cinco palabras, tags de imágenes móviles, backup independiente y almacenamiento local. Publicar fuentes no equivale a autorizar exposición pública o cloud.

## Cierre

Se resuelve la condición PUB-02 de contraste con main actualizado mediante el fetch y la igualdad de árboles; la elección final de la propuesta corresponde al propietario. **READY FOR COMMIT** significa que hay una estrategia concreta y verificable para solicitar autorización, no que el índice esté preparado o que se haya publicado. Solo se crean tres informes PUB-03; todos los archivos anteriores deben permanecer idénticos. FIN-01 sigue pendiente. Detenerse para revisión.
