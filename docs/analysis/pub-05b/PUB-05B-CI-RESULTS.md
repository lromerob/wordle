# PUB-05B — Resultados remotos CI

**CI VERIFIED**. Fuente: API pública REST de GitHub, consultada en 2026-11-09T21:29:37+01:00. Sin gh instalado, sin instalar herramientas o consultar tokens.

- Run: 42692713269, intento 1, evento push.
- Rama: codex/pg01-07-consolidation; SHA: b330ae70caf08ac789786376ca5de0305ea4471f.
- URL: https://github.com/lromerob/wordle/actions/runs/42692713269
- Creado: 2026-11-09T20:24:50Z; actualizado al finalizar: 2026-11-09T20:27:32Z.
- Estado final observado: completed / success.

## Los ocho jobs

| Job real | Conclusión | Duración API | ID |
|---|---|---|---|
| Tests / isolated backend | success | 19 s | 129416382262 |
| Integration / real PostgreSQL 16 | success | 33 s | 129416382587 |
| Infrastructure / Kustomize rendering | success | 6 s | 129416382590 |
| Infrastructure / Terraform validation (no Azure) | success | 10 s | 129416382849 |
| Build / frontend | success | 8 s | 129416382877 |
| Build / Docker images (no push) | success | 28 s | 129416716429 |
| Integration / ephemeral kind smoke test | success | 91 s | 129416997049 |
| Publish / GHCR production images | skipped | No ejecutado | 129417861653 |

Duraciones calculadas con started_at/completed_at, no suma de pasos ni tiempo de CPU. GHCR omitido intencionadamente por if:false; no es un control obligatorio fallido. Los otros siete jobs y sus dependencias finalizaron correctamente.

## Evidencia por pasos

- Tests / isolated backend: Run actions/checkout@v4 → success; Run actions/setup-python@v5 → success; Install existing locked backend dependencies → success; Run unittest discovery with external access blocked → success
- Integration / real PostgreSQL 16: Initialize containers → success; Run actions/checkout@v4 → success; Run actions/setup-python@v5 → success; Install existing locked backend dependencies → success; Initialize empty database and run eleven real PG-04 tests → success; Stop containers → success
- Infrastructure / Kustomize rendering: Run actions/checkout@v4 → success; Require Kubernetes files in checkout → success; Run azure/setup-kubectl@v4 → success; Render manifests without a cluster → success
- Infrastructure / Terraform validation (no Azure): Run actions/checkout@v4 → success; Run hashicorp/setup-terraform@v3 → success; Check Terraform formatting → success; Initialize providers without remote state or Azure credentials → success; Validate Terraform configuration → success
- Build / frontend: Run actions/checkout@v4 → success; Run actions/setup-node@v4 → success; Install existing frontend dependencies → success; Build frontend → success
- Build / Docker images (no push): Run actions/checkout@v4 → success; Build backend production runtime → success; Build frontend runtime → success
- Integration / ephemeral kind smoke test: Set isolated kubeconfig path → success; Run actions/checkout@v4 → success; Run azure/setup-kubectl@v4 → success; Run actions/setup-python@v5 → success; Install kind 0.33.0 with release checksum → success; Build memory-only backend and frontend images → success; Create ephemeral Kubernetes cluster → success; Load local images into kind → success; Deploy existing memory manifests and wait for readiness → success; HTTP smoke test through frontend proxy → success; Delete only this runner's ephemeral cluster → success

## Alcance de lo confirmado

- Offline: instalación lock y paso de discovery exitosos. El código exacto de ese SHA exige result.testsRun == 55, cero omitidos y wasSuccessful; el paso exitoso confirma el cumplimiento de esas guardas.
- PostgreSQL: inicialización del servicio, instalación y adaptador PG-07 exitosos. Servicio postgres:16.15; adaptador exige once tests, cero omitidos y éxito (run_pg07_ci.py:82), bootstrap del esquema vacío y fixture, y caída controlada antes de terminar. Resultado inferido de las guardas del código ejecutado y estado del paso, no de una transcripción del resumen unittest.
- Frontend: npm ci y build exitosos. No se ejecuta una suite frontend independiente en este workflow.
- Docker: pasos de construcción runtime backend/frontend exitosos; construir no equivale a publicar.
- Kustomize: comprobación de archivos versionados y render exitosos, sin demostrar por sí solos un despliegue PostgreSQL en Kubernetes.
- kind: construcción memoria, creación, carga, despliegue/readiness, smoke HTTP y limpieza del clúster del runner exitosos según pasos API. El smoke comprueba frontend, /api/health, creación, ocultación de respuesta, intento inválido y victoria. Es memoria efímera, no AKS ni PostgreSQL persistente en Kubernetes.
- Terraform: fmt, init -backend=false y validate exitosos; sin apply, destroy o acceso a infraestructura Azure.

## Limitaciones e incidencias

El endpoint de descarga de logs del job offline devolvió HTTP403 sin autenticación; no se intentaron alternativas de credenciales ni se afirma haber leído logs crudos. Estados, pasos y tiempos sí se consultaron por API pública. No se confirmaron advertencias internas de logs; no se presentan ausencias de advertencias como hecho. No hay fallo de job que diagnosticar.

Publicación GHCR skipped; ningún paso activo de publicación se ejecutó. Sin despliegue Azure. Recursos efímeros del runner gestionados por CI; no hubo operaciones sobre recursos locales PG-05/06. No se ejecutó ni relanzó ninguna prueba/build local durante PUB-05B.
