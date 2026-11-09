# PUB-02 — Decisión de publicación

Fecha: 09/11/2026. **READY WITH CONDITIONS**. La consolidación documental local está resuelta; queda una condición concreta de publicación de PUB-01, no un bloqueo causado por falta de ejecución remota de CI.

## Resuelto efectivamente

- README/notas/plantilla corresponden a PostgreSQL16/psycopg async y variables del código; no describen Supabase como runtime vigente.
- Siete informes revisados/saneados, con evidencia técnica intacta demostrada por comparación exacta de texto tras sustituciones permitidas.
- Nueve dependencias necesarias presentes, revisadas, no ignoradas y enumeradas para futura inclusión; no se inventó ni añadió contenido privado. Siguen sin seguimiento e índice vacío, conforme a la restricción.
- Material histórico preservado y separado conceptualmente por documentación: allow_all y smoke Supabase no entran en init/CI. Se propone incluirlos expresamente solo para trazabilidad, junto a su nota; ninguna ejecución autorizada.
- Manifiesto exacto del conjunto futuro y exclusiones concretas; análisis acotado sin credenciales reales detectadas, sin garantizar todos los blobs históricos o archivos privados no abiertos.
- Código, contratos, SQL, ejecutores, pruebas, Dockerfiles, Compose, Kubernetes, Terraform y workflow no cambiaron en PUB-02. No procede repetir suites por cambios únicamente documentales/de plantilla.

## Condición pendiente antes de autorizar publicación

**Contrastar con origin/main realmente actualizado y acordar la rama de publicación preservando todo el trabajo.** Seguimos en codex/devops-04a1-hardening, HEAD a666b17680781a24889ea774778019995d3fca45. Las referencias locales dan origin/main...HEAD = 0/1, pero no se hizo fetch ni se consultó GitHub, y no puede asumirse que correspondan al main actual.

PUB-01 ya exigía esa comprobación. No se la marca resuelta por documentarla, ni se cambia de rama para simular una consolidación completa. Una tarea autorizada de preparación Git debe actualizar refs, comprobar diferencias y elegir una rama apropiada sin perder cambios; después revisar el índice real/listado/secretos/whitespace antes de commit/push. PUB-02 prohíbe prepararlo y no autoriza publicar. No se ha confirmado divergencia inesperada, solo falta de verificación actual.

## Verificación posterior, no bloqueo por sí sola

GitHub Actions real sigue pendiente hasta un push autorizado. No se clasifica BLOCKED por esa ausencia. Será necesario registrar SHA/run/enlace y siete jobs activos correctos (offline, PostgreSQL, frontend, Docker, Kustomize, kind memoria y Terraform), con publicador GHCR skipped. actionlint no está instalado: análisis YAML no certifica todas las reglas del servidor GitHub.

Se mantienen riesgos académicos conocidos de identidad cliente/CORS, fixture mínima, tags móviles, almacenamiento local y restore independiente. Publicar fuentes no habilita exponer la API, Azure, Blue-Green, observabilidad o nuevos sistemas de autenticación. FIN-01 continúa pendiente.

## Resultado y límite

Quedan once archivos existentes modificados documentalmente y tres informes PUB-02 nuevos; todo el trabajo previo fuera de ese alcance preservado. Sin add, commits, push, reset, clean, cambio de rama, instalaciones, pruebas, contenedores, despliegues ni operaciones sobre recursos PG-05/06. Esperar revisión de esta propuesta y autorización de la fase Git; no continuar automáticamente.
