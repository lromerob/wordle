# PG-06 — Resultados de validación

> PUB-02 (09/11/2026): rutas personales sustituidas por `%LOCALAPPDATA%` y/o `<evidencias-privadas>` cuando existían. Las evidencias siguen fuera de Git; los nombres/UID de recursos de prueba se conservan como trazabilidad, no como requisitos para otro clon. Resultados, fechas, versiones y conteos originales no se actualizan.

Fecha: 09/11/2026. Ejecución local real en Windows → Docker Desktop → kind. Sin Supabase/Azure ni credenciales del proyecto. No se declara FIN-01 completo.

## Resultados ejecutados

| Prueba | Resultado observado |
|---|---|
| Herramientas/inventario | Docker 29.9.2 responde; kind 0.33.0; kubectl 1.36.1/Kustomize 5.8.1. Ningún clúster kind preexistente. |
| Clúster exclusivo | wordle-pg06-00f26f1f, un nodo Ready Kubernetes 1.35.0, kubeconfig privada y contexto explícitos; configuración global no utilizada. |
| Build/carga | Backend runtime y frontend construidos con Dockerfiles existentes. Imágenes de aplicación y PG16.15 cargadas desde archivo linux/amd64, sin publicar. |
| Namespace/bootstrap | wordle-pg06 nuevo, Secret efímero nuevo, ConfigMap init inmutable desde fuentes PG-05; no archivos de passwords en Git. |
| PostgreSQL inicial | StatefulSet 1/1 Ready, PVC 2Gi Bound, cinco palabras, catálogo schema_contracts.sql aprobado; cuatro tablas, columnas/tipos/defaults/restricciones/índices del baseline. Rol app no superusuario. |
| Aplicación | Backend/frontend 1/1 Running/Ready; cero reinicios de contenedor antes/después de pruebas. |
| Red Windows | GET / HTTP200 y GET /api/health HTTP200 en 127.0.0.1:18086. Proxy Nginx /api retira prefijo correctamente. |
| API real | Creación; GET activo oculta solución; AB y ZZZZZ HTTP400; victoria de un intento, derrota de seis, intento posterior HTTP400; stats/ranking HTTP200; valores SQL persistidos. |
| Navegador real | React inicia partida; intento incompleto muestra error; teclado físico CASAS muestra feedback gris/verde; teclado virtual GATOS gana en dos. Captura guardada. Derrota comprobada por API, no repetida en navegador. |
| Readiness DB | PostgreSQL usa TCP/app/consulta, no solo socket temporal de init; backend exec positivo con DB real, negativo con PGHOST=127.0.0.1 cerrado; /health sigue 200. No se simuló caída larga ni se observó Ready=False durante esa caída. |
| Recreación PostgreSQL | Se eliminó solo postgres-0 propio; nuevo UID, mismo PVC/PV y snapshot completo idéntico de las cuatro tablas. Logs: Skipping initialization; no baseline/seed/rol reaplicados. |
| Reinicio aplicación | rollout restart backend/frontend; snapshot completo idéntico; reconexión de port-forward y verify HTTP confirma IDs/estado/intentos/stats coincidentes con SQL. |
| Exposición | Tres Services ClusterIP; sin LoadBalancer/NodePort/Ingress/hostPort; solo frontend tiene túnel loopback. |
| Recursos | Requests/limits explícitos; una réplica por componente, pool web 0–4 más probe transitoria. CRI working sets ~22MiB DB/~17MiB frontend/~45MiB backend; no carga. Metrics API no disponible; no se instaló observabilidad. |
| Logs | Revisados sin volcar contenido privado: cero Traceback/deadlock detected/referencias Supabase. Avisos iniciales de probes recuperados sin reinicios. |
| Regresión offline | **55 pruebas, todas aprobadas, cero omitidas, 1.774 s**. DNS/sockets externos/dotenv/conexión nativa psycopg bloqueados. |
| Integración PG-04 | **11 pruebas reales, todas aprobadas, cero omitidas, 2.365 s**; además outage real de PG → HTTP500 sanitizado, /health200 y pool cerrado. Contenedor wordle-pg04-3bdb9952816a/tmpfs/red propios eliminados. |
| Kustomize | Perfiles memoria y PostgreSQL renderizan; validación server-side dry-run de los diez recursos del overlay exitosa en clúster real. Secret/init ConfigMap son bootstrap adicional y no están incluidos en esos diez. |
| Sintaxis/Git/secretos | Nuevos Python compile() sin bytecode; patrones automáticos acotados sin hallazgos; .gitignore probado para kubeconfig/estado local; git diff --check correcto. Avisos CRLF informativos, no errores de whitespace. |
| Preservación | Hashes de archivos anteriores: solo .gitignore cambió; SQL/app/perfil memoria/Compose/PG-05 y documentos previos idénticos. Volumen/imágenes/backup PG-05 presentes; dump 7924 bytes, no abierto. Índice vacío; sin commits/push. |

## Identificadores y evidencia de persistencia

Partidas API:

- Victoria: 3ce05698-9388-41c9-b0e5-28aa9ef4d525.
- Derrota: fcd9d718-ff05-4978-9d3c-352955c73daf.

Incluyendo UI: **5 palabras, 3 partidas, 9 intentos, 3 estadísticas** antes/después de sustituir PostgreSQL y de reiniciar la aplicación. Se compararon todas las filas/valores ordenadas por id en memoria; no se publican snapshots completos ni datos privados.

- Pod PostgreSQL anterior: d4b5e665-bcbc-42b9-8d55-0c6d051967ef.
- Pod PostgreSQL recreado: 0eb2a8ce-642e-4fc0-8d67-61f5ce5c84d8.
- PVC UID conservado: d3052f65-80f4-4758-8e42-4b80fbd24a6a.
- PV conservado: pvc-d3052f65-80f4-4758-8e42-4b80fbd24a6a.

Captura de victoria real, fuera del repositorio:
<evidencias-privadas>/pg06-ui-win.png.

## Incidencias y límites de la evidencia

1. kind load docker-image falló dos veces por digest ausente al importar --all-platforms desde Docker 29. Sin inicialización DB todavía. La exportación linux/amd64 + kind load image-archive funcionó; archivo temporal retirado. No se borraron recursos para recuperarse.
2. Durante preparación se corrigió el parser del ejecutor nuevo: kubectl -o json devuelve una secuencia de objetos en dry-run por lotes, no necesariamente un List. La comprobación auxiliar inicial detectó JSON extra; el despliegue real utilizó el parser corregido. También se separó correctamente la comprobación HTTP de Compose para usar solo el port-forward Kubernetes.
3. Primer arranque: pg_isready sin respuesta, backend connection refused y frontend readiness502 transitorios; recuperación automática, sin reinicios. No se ejecutó una inicialización SQL fallida ni se borró PVC.
4. El port-forward se reconectó al sustituir el pod frontend; el túnel no es un endpoint persistente ni un Ingress.
5. No se verifican caída del nodo, destrucción del clúster, restauración de backup Kubernetes, HA, egress bloqueado por CNI, autenticación real, diccionario completo ni Azure. No presentar /health como prueba de DB.
6. El perfil memoria se preserva byte a byte y renderiza; no se creó un segundo despliegue memoria en esta fase. La regresión offline valida sus dobles; no equivale a arrancar ese perfil en otro namespace.
7. La comprobación de secretos usa patrones, no una garantía absoluta. Los valores efímeros se generan/consumen sin mostrarlos; no se leyeron archivos privados existentes. El runtime construido no tiene SDK Supabase; no hubo conexiones reales a ese servicio. No se hizo captura de paquetes para prometer aislamiento general.

Se conserva el entorno PG-06 para revisión. El procedimiento y los recursos están en el informe de implementación. FIN-01 pendiente; PG-07 no iniciado.
