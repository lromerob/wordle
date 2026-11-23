# PUB-05A — Habilitación de CI en ramas codex

Fecha: 09/11/2026. Incremento exclusivamente local; sin push. FIN-01 pendiente.

## Estado inicial

Rama codex/pg01-07-consolidation. HEAD inicial f5f9ad6b4aac895c9ab9ca48a09e3334d8ed985f. Índice vacío y archivos versionados sin modificaciones. Cuatro informes PUB-04/PUB-05 sin seguimiento, preservados y excluidos. Lecturas: workflow vigente, tres informes PG-07 y decisión/resultados PUB-05. No se encontraron AGENTS.md en las rutas inspeccionadas.

## Cambio y validación

Solo .github/workflows/ci.yml: push.branches pasa de [main] a main y 'codex/**'. Se conservan pull_request y workflow_dispatch preexistentes; no se añade un disparador manual nuevo.

- YAML parseado correctamente con PyYAML BaseLoader existente.
- Comparación estructural completa: al restaurar únicamente push.branches, ambos documentos son idénticos. Los ocho jobs, steps, needs, permisos, variables, versiones y concurrency permanecen intactos.
- Comparación binaria: una única sustitución localizada, conservando el resto de bytes y finales de línea del archivo de trabajo.
- main y codex/** incluidos; la rama de trabajo cumple el patrón codex/**.
- git diff --check y git diff --cached --check correctos; diff completo y staged inspeccionados.
- Índice revisado: exclusivamente el workflow; blob preparado igual al contenido esperado normalizado LF.
- actionlint: no disponible en PATH; no instalado. Parseo YAML y comparación estructural no sustituyen la validación remota de Actions.
- 124 archivos previos ajenos al workflow preservados byte a byte, incluidos los informes locales.

## Commit y verificación posterior

SHA final: d48ebf27c583a215bc2daf321bce2822e08b08e8

Padre: f5f9ad6b4aac895c9ab9ca48a09e3334d8ed985f

Mensaje: ci: enable workflow on codex branches

Rama: codex/pg01-07-consolidation

Exactamente un nuevo commit, que modifica solo .github/workflows/ci.yml. El padre es el commit de consolidación PUB-04; ambos están en HEAD. Índice vacío, archivos versionados sin modificaciones. Los cuatro informes previos siguen sin seguimiento; este informe añade un quinto, también fuera del commit.

### Diff del commit

```diff
diff --git a/.github/workflows/ci.yml b/.github/workflows/ci.yml
index 5a425d0..8284d1a 100644
--- a/.github/workflows/ci.yml
+++ b/.github/workflows/ci.yml
@@ -4,7 +4,9 @@ on:
   pull_request:
   workflow_dispatch:
   push:
-    branches: [main]
+    branches:
+      - main
+      - 'codex/**'

 permissions:
   contents: read
```

## Restricciones y siguiente paso

Sin push, fetch, PR, tags, amend, integración ni cambios de rama/configuración. Sin pruebas funcionales, builds, contenedores o despliegues. No se consultaron secretos ni se tocaron PostgreSQL, Docker, Kubernetes, Terraform, Azure o recursos PG-05/06. GHCR sigue deshabilitado.

Próximo paso: solicitar autorización de publicación controlada del nuevo HEAD; revalidar el destino remoto y su divergencia antes de push y observar la ejecución real para ese SHA. No hay evidencia nueva de CI remoto ni se declara CI VERIFIED. No continuar automáticamente.
