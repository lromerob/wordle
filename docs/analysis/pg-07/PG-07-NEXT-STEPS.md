# PG-07 — Revisión y pasos posteriores, sin ejecución automática

> PUB-02 (09/11/2026): rutas personales sustituidas por `%LOCALAPPDATA%` y/o `<evidencias-privadas>` cuando existían. Las evidencias siguen fuera de Git; los nombres/UID de recursos de prueba se conservan como trazabilidad, no como requisitos para otro clon. Resultados, fechas, versiones y conteos originales no se actualizan.

Fecha: 09/11/2026. Esperar revisión/autorización; sin commit/push, workflow remoto o tareas FIN posteriores. FIN-01 pendiente.

## Para verificar en GitHub

1. Revisar el diff PG-07: workflow, adaptador y tres informes. Comprobar también el conjunto anterior PG-02/06 aún local, sin descartarlo ni publicarlo automáticamente. El pipeline necesita app/repository.py, lock actualizado, suites offline/real, run_pg04.py, baseline SQL/catalog tests y seed PG-05. Publicar solo el workflow dejaría rutas ausentes o backend incompatible. Revisar por separado los archivos Kubernetes pendientes y no incorporarlos silenciosamente.
2. Tras autorización explícita de commit/push del conjunto coherente, usar una rama/PR de revisión y comprobar política de Actions/forks. No activar pull_request_target ni añadir secretos Azure/Supabase. Esta fase no creó PR ni ejecutó workflows remotos.
3. En el run de GitHub comprobar 55 offline y 11 reales, cero omitidas, health del servicio, bootstrap y caída final, dos builds sin push, render Kustomize, smoke **memoria** kind y Terraform. Todos deben terminar correctamente; publish-ghcr debe aparecer skipped también para push a main/manual. Guardar enlace/SHA/run/tiempos como evidencia académica tras su ejecución real.
4. Revisar logs sin exportar contraseñas/Config.Env/kubeconfig; no añadir artefactos con valores privados. Si un test, bootstrap o build falla, el job debe fallar, sin continue-on-error ni recortar casos. Los recuentos55/11 son intencionales: si se amplía la suite, actualizar expectativas tras revisión, no ocultar omisiones.
5. No reactivar GHCR cambiando solo if: la publicación está pausada y se retiró packages:write. Una reactivación futura requiere autorización/revisión de condición, dependencias y permisos mínimos; no es parte de PG-07.

## Recursos locales y conservación

Servicio/red temporal PG-07 retirados; no volumen persistente creado. Se conservan dos imágenes locales v1-pg07-ci; no eliminarlas mediante prune global. No se modificó el clúster wordle-pg06-00f26f1f ni PVC data-postgres-0, ni el volumen wordle-pg05-7325afa8cc_postgres_data, sus imágenes o backup privado. No leer/copiar compose.env ni kubeconfig al repo.

## Dependencias FIN-01 y FIN-02

PG-07 automatiza pruebas contra una base **nueva**, no reconstruye datos Supabase ni cierra FIN-01. Quedan revisión del esquema reproducible/fixtures aprobadas, estrategia de migraciones futuras y evidencia remota; no se actualiza el backlog oficial.

Para el trabajo posterior relacionado con identidad, claves, RLS y permisos: arquitectura objetivo ya es PostgreSQL directo, sin dependencia operativa Supabase. El rol app con grants no verifica identidad del jugador; usuario_id sigue declarado por el cliente. No presentar las comprobaciones de propietario como autenticación efectiva ni crear RLS/políticas Supabase o un sistema de auth desde esta fase. Confirmar el alcance vigente de FIN-02 con el plan aprobado antes de implementar.

El CI temporal no valida secretos cloud, AKS, almacenamiento durable, restauración completa, Blue-Green, Ingress o observabilidad. No iniciar esos trabajos ni declarar FIN-01 completo por tener pruebas locales verdes.
