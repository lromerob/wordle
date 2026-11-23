# FIN-17-GIT-CONSOLIDATION-02 — 23/11/2026

## 1. Estado e inventario
PASS — SELECTION READY, condicionado a sanitización antes del staging.
Inicial: nueve modificados, 319 sin seguimiento, índice vacío; mismo HEAD
4d56cf265cc5f0af8c72c64f2a93373660e8f122 y rama codex/pg01-07-consolidation.
Comparación con inventario anterior: ningún archivo previo cambió; único añadido
era FIN-17-GIT-CONSOLIDATION-01-REPORT.md. Se reutilizan decisiones A/B previas.

## 2. Cinco informes
Todos B, seleccionados CONDICIONALMENTE, sin editar en esta iteración.
Sustituciones exactas por línea y nota editorial incluidas en cada entrada del
manifiesto; source_sha256 impide aplicarlas sobre un archivo distinto.
| Informe | Líneas actuales | Propuesta |
|---|---|---|
| FIN-17-AKS-RECOVERY-01 | 63, 82 | Ruta documental con <USER_HOME>; comando con Join-Path LOCALAPPDATA |
| FIN-17-AKS-RECOVERY-03 | 45 | $Tf mediante Join-Path LOCALAPPDATA |
| FIN-17-AKS-RECOVERY-04 | 39 | Invocación Terraform con Join-Path LOCALAPPDATA, argumentos intactos |
| FIN-17-PRIVATE-STORE-03 | 46, 48 | <USER_HOME> manteniendo sufijos/versions de Terraform y kubelogin |
| FIN-17-WORKSPACE-MIGRATION-01 | 14 | <LEGACY_REPO_ROOT>, definido como origen histórico OneDrive/Escritorio |
No cambiar rutas aprobadas C:/WordleTFG, UUID, resultados, fechas ni hashes.
Añadir nota editorial de normalización histórica; no presentar un placeholder
como ruta realmente observada o sustituir origen histórico por workspace vigente.
No se requiere decisión adicional para clasificarlos; aplicar cambios aún exige
autorización del siguiente incremento.

## 3. Doce históricos
| Ruta | Decisión | Motivo / equivalente |
|---|:---:|---|
| docs/analysis/fin-01r/FIN-01R-CLOSURE-DECISION.md | C | Recomendación condicional sustituida por ratificación/cierre definitivo. Relacionado/definitivo: docs/analysis/fin-01s/FIN-01S-CLOSURE-RECOMMENDATION.md |
| docs/analysis/fin-01r/FIN-01R-REMAINING-GAPS.md | C | Pendientes previos ya resueltos por ratificación del baseline. Relacionado/definitivo: docs/analysis/fin-01s/FIN-01S-ARCHITECTURE-DECISION.md |
| docs/analysis/fin-01s/FIN-01S-BASELINE-REVIEW.md | B | Diccionario de tipos, restricciones y compatibilidad del baseline. Relacionado/definitivo: docs/analysis/fin-01s/FIN-01S-ARCHITECTURE-DECISION.md |
| docs/analysis/pub-04/PUB-04-COMMIT-REPORT.md | C | SHA anterior a corrección de identidad; inventario redundante para publicación. Relacionado/definitivo: docs/analysis/pub-05c/PUB-05C-IDENTITY-REPORT.md |
| docs/analysis/pub-05/PUB-05-CI-RESULTS.md | C | CI no ejecutada; resultados definitivos posteriores disponibles. Relacionado/definitivo: docs/analysis/pub-05b/PUB-05B-CI-RESULTS.md |
| docs/analysis/pub-05/PUB-05-DECISION.md | B | Causa del bloqueo por triggers y decisión que conduce a PUB-05A. Relacionado/definitivo: docs/analysis/pub-05a/PUB-05A-CI-TRIGGER-REPORT.md |
| docs/analysis/pub-05/PUB-05-PUSH-REPORT.md | C | Push no realizado; repetición de la decisión de bloqueo. Relacionado/definitivo: docs/analysis/pub-05/PUB-05-DECISION.md |
| docs/analysis/pub-05a/PUB-05A-CI-TRIGGER-REPORT.md | B | Resolución concreta de triggers y validación del cambio CI. Relacionado/definitivo: docs/analysis/pub-05b/PUB-05B-CI-RESULTS.md |
| docs/analysis/pub-05b/PUB-05B-CI-RESULTS.md | B | Ejecución real por SHA/run, siete jobs y GHCR omitido.  |
| docs/analysis/pub-05b/PUB-05B-DECISION.md | C | Resumen repetido de resultados y publicación definitivos. Relacionado/definitivo: docs/analysis/pub-05b/PUB-05B-CI-RESULTS.md |
| docs/analysis/pub-05b/PUB-05B-PUSH-REPORT.md | B | Evidencia del push autorizado y SHA remoto.  |
| docs/analysis/pub-05c/PUB-05C-IDENTITY-REPORT.md | B | Preservación de árboles/mensajes y corrección de autoría; email ya parcial.  |

Resultado: seis B y seis C; C significa no incorporar, no borrar.
PUB-05C conserva trazabilidad de corrección de identidad y árboles; el correo
está parcialmente oculto. Identidad Git autorizada no se convierte en secreto.

## 4. Los 126 archivos intermedios
Son 65 PNG y 61 archivos auxiliares (JSON, manifests, checksums y resúmenes),
no 126 imágenes. Seleccionados 0; no seleccionados 126.
| Paquete | Archivos | PNG | Motivo / equivalente final |
|---|---:|---:|---|
| capture-02 | 13 | 4 | Estados iniciales/entrada inválida y diagnóstico; cubiertos por capture-07 |
| capture-03 | 19 | 10 | Victoria, derrota, reinicio y vistas móviles; cubiertos por capture-07 |
| capture-04 | 27 | 13 | Promoción/rollback y señales; dossier final completo en capture-07 |
| capture-05 | 36 | 22 | Grafana, Prometheus, Loki, Tempo y juego; repetición del dossier final |
| capture-06 | 31 | 16 | Ensayo diagnóstico con fallo de captura; resolución final documentada por capture-07 |
Se preservan físicamente todos los ensayos. No se imponen cupos por hito.
B anteriores capture-01 (20 archivos) y capture-07 (43) se mantienen completos:
proveniencia histórica, persistencia/restauración, UI, blue-green/promoción/rollback,
señales y alertas. Los tres references de capture-07 necesitan capture-01.
No hay captura AKS o CI remoto en estos paquetes: no atribuirles esa evidencia.
CI remoto y retirada Azure se acreditan mediante los informes correspondientes.
Búsqueda focalizada: no hay enlaces Markdown activos hacia los seis documentos C
ni hacia capture-02..06. Las rutas en el inventario anterior son menciones históricas
de archivos locales excluidos, no enlaces de ejecución. El informe de captura cita
capture-07 y capture-01; su afirmación de conservar ensayos sigue siendo cierta
localmente. No es necesario cambiar resultados, imágenes o checksums.

## 5. Dependencias CI/CD
52/52 rutas REQUIRED sin versionar están seleccionadas A; listado exacto en
critical_dependencies.paths del manifiesto. Sin diferencias respecto al inventario.
Se mantienen workflows/helpers, Docker/build context adicional scripts, pruebas,
plantillas Terraform, overlays y documentación operativa como unidades coherentes.
Dependencias ya versionadas se conservan. No se ejecutaron tests ni workflows.
Inputs de runner/backend/variables/kubeconfig/planes siguen externos. Recuperación
humana no sustituye inputs CD; no incluir almacenes para completar un checkout.

## 6. Selección definitiva
Inventario actual: 319 sin seguimiento + nueve modificados.
Esta iteración añade dos salidas. El manifiesto contiene 330 entradas exactas:
**A=61, B=137, C=132, D=0** (incluye nueve modificados y las dos salidas).
Sólo sin seguimiento al finalizar: **A=54, B=135, C=132, D=0**, total 321.
De los 143 D anteriores: cinco pasan a B condicional, seis históricos a B,
seis históricos a C y 126 archivos intermedios a C. Ninguno queda sin clasificar.
source_sha256 registra candidatos previos; el propio manifiesto no puede contener
su hash autorreferente. Dos salidas nuevas se identifican expresamente.
C siempre selected=false y proposed_commit=null; los condicionales bloquean staging
hasta completar pre_staging_actions y actualizar/verificar hashes.

## 7. .gitignore propuesto, NO aplicado
Append exacto en gitignore_proposal.append_lines:
~~~
.terraform/
*.tfplan
/private/
/recovery/
/backups/
/.wordle-private-store.json
/target.json
/variables.json
/backend.json
*.7z
*.7z.[0-9]*
*.dump
*.backup
~~~
Conservar exclusiones actuales de estados, secretos, cachés/temporales y excepciones
de plantillas/lock. No ignorar SQL, documentación, evidencias o JSON completos.
.gitignore es una modificación FUTURA separada del inventario de 330; se propone
para commit 1 sólo tras autorización, no se declara modificado ahora.

## 8. Tres commits
Listas exactas disponibles en commits[].paths; ninguna operación Git ejecutada.
- Commit 1 — Código e infraestructura: 22 archivos seleccionados.
- Commit 2 — Runner y operaciones: 39 archivos seleccionados.
- Commit 3 — Documentación y evidencia: 137 archivos seleccionados.

Orden 1→2→3. Commit1: fuentes Terraform/overlays/observabilidad y scripts/evidence.
Commit2: workflow, módulos operativos/gates, Docker runner, retirada y runbooks;
depende de las fuentes de commit1. No publicar el workflow sin sus dependencias.
Commit3: informes y paquetes finales; depende de sanitizar los cinco documentos.
C excluidos de TODOS. Añadir .gitignore al commit1 sólo tras su edición autorizada.
Validación mínima futura: nombres/diff preparados y secretos, diff --cached --check;
sintaxis y pruebas focalizadas de módulos tocados, render/fmt según cambios. No
repetir demos completas. Evidencias: verificar hashes/proveniencia y enlaces.

## 9. Decisiones pendientes
Ninguna ambigüedad de selección D. Queda autorizar ejecución de sanitizaciones,
reglas .gitignore y staging selectivo. No se concede permiso de commit/push/CD.
Los informes de selección son decisiones posteriores que sustituyen la
clasificación D anterior, no reescritura de evidencias.

## 10. Git final
Misma rama/HEAD, índice vacío; nueve modificados y 321 sin seguimiento.
Únicas salidas: este informe y GIT-SELECTION-MANIFEST.json.
Todos los archivos anteriores conservados; nada eliminado, movido o renombrado.

## 11. OneDrive
Intacto. Almacén, recuperación humana, respaldos y configuración global sin cambios.

## 12. Resultado
PASS — SELECTION READY. Selección preparada, NO versionada.
No staging, commit, push, Azure, Terraform, registro, CD, instalaciones ni pruebas.

## 13. Próximo paso mínimo
Autorizar un incremento para las cinco sanitizaciones propuestas, .gitignore y
staging por manifiesto con verificación de hashes; no ejecutarlo automáticamente.
