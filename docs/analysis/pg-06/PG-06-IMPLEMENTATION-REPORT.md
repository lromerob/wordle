# PG-06 — Kubernetes local con PostgreSQL persistente

> PUB-02 (09/11/2026): rutas personales sustituidas por `%LOCALAPPDATA%` y/o `<evidencias-privadas>` cuando existían. Las evidencias siguen fuera de Git; los nombres/UID de recursos de prueba se conservan como trazabilidad, no como requisitos para otro clon. Resultados, fechas, versiones y conteos originales no se actualizan.

Fecha: 09/11/2026. Preparado para revisión; FIN-01 sigue pendiente. Sin commit/push, Azure, Supabase, cambios de esquema, frontend, contratos o inicio de PG-07.

## Arquitectura y archivos

Navegador Windows → port-forward del Service frontend → Nginx /api → Service backend → FastAPI/psycopg async → Service postgres → StatefulSet de una réplica → PVC data-postgres-0.

Nuevo overlay `k8s/postgres/`, separado de `k8s/local/`:

- kustomization.yaml: reutiliza el perfil local y su frontend/ConfigMap Nginx; transforma namespace e imágenes y añade configuración no sensible PostgreSQL.
- backend-patch.yaml: elimina comando memoria y variables Supabase; usa runtime normal, rol app/Secret y readiness de DB mediante exec.
- postgres.yaml: Service ClusterIP, StatefulSet, PVC Retain de 2 Gi, probes, recursos y contextos de seguridad.
- readiness.py: probe async read-only de las cuatro tablas y diccionario no vacío; error genérico, sin mostrar credenciales. Se monta mediante ConfigMap, no modifica la aplicación ni /health.
- run_pg06.py: ejecutor local opt-in, crea un clúster/nombre exclusivo, construye/carga imágenes, genera Secret por stdin, crea ConfigMap init desde las fuentes PG-05 y aplica los recursos por etapas. Smoke, persistencia y verificación posteriores explícitos. Nunca elimina namespace, clúster, PVC o volumen.

.gitignore añade *.kubeconfig y k8s/postgres/.local/. Tres documentos nuevos en esta carpeta. El perfil de memoria, Compose, SQL, Dockerfiles y todo el trabajo PG-01/05 se mantienen. No se duplican frontend, Nginx ni baseline SQL.

## Versiones y almacenamiento

Docker Engine 29.9.2; kind 0.33.0; kubectl disponible **1.36.1**, Kustomize 5.8.1. No había clústeres kind. Se creó exclusivamente **wordle-pg06-00f26f1f**, Kubernetes **1.35.0**: cliente y servidor difieren una minor compatible. No se asumió que siguiera instalado el kubectl 1.34.1 histórico.

Namespace **wordle-pg06**, Pod Security restricted v1.35. Tres pods, una réplica por componente, tres Services ClusterIP, sin NodePort/LoadBalancer/Ingress/hostPort. Backend y DB no se publican al host. Acceso Windows validado en http://127.0.0.1:18086/ por port-forward.

PostgreSQL **16.15**, imagen oficial local ID sha256:f9a7b9ebf6f56201f949db745e47bc423c0f0f8294bafe991cc10bf74b029657, alias postgres:16.15. UID/GID postgres 999 verificados. Aplicación: wordle-backend:v1-pg06 y wordle-frontend:v1-pg06, imagePullPolicy Never. No publicaciones en registros. El ejecutor exige versión 16.15 y obtiene el tag exacto si falta; los tags de base no equivalen a un pin de digest para siempre.

StorageClass **standard**, provisionador local-path de kind, PVC **data-postgres-0**, RWO 2 Gi, UID **d3052f65-80f4-4758-8e42-4b80fbd24a6a**, PV **pvc-d3052f65-80f4-4758-8e42-4b80fbd24a6a**. Sobrevive al pod, pero reside dentro del nodo Docker: NO sobrevive a borrar el clúster/nodo y no es almacenamiento AKS ni backup. La clase puede tener reclaimPolicy Delete; la política Retain del StatefulSet retiene el claim, no convierte el PV en backup.

## Inicialización y secretos

El ejecutor crea un Secret nuevo wordle-db con dos valores aleatorios distintos (admin-password/app-password), únicamente en memoria y por stdin a kubectl. No copia/abre compose.env PG-05 ni escribe contraseñas en archivos/argumentos/logs. La kubeconfig se guarda fuera del repo en %LOCALAPPDATA%/WordlePG06/<cluster>/kind.kubeconfig; contiene acceso administrador local y no debe publicarse. Kubernetes Secret es almacenamiento de credenciales, no prueba de cifrado en reposo: quien controla Docker/kind o tiene permisos Secret puede recuperarlas. No es un gestor cloud de secretos.

ConfigMap inmutable wordle-postgres-init se genera desde 00-check-config.sh, baseline FIN-01B, 20-demo-words.sql y 30-app-role.sh; normaliza finales de línea LF. No se copia SQL a otra migración. Baseline SHA256 da743e629094da2b7d126f7889c5d1ca72e63a232844feadea3798254b19b0cb intacta. El ConfigMap no contiene passwords. Kustomize por sí solo no genera Secret ni el ConfigMap init: ejecutar el bootstrap documentado antes de apply. Así se mantiene una sola fuente SQL/scripts, sin usar LoadRestrictionsNone.

PGDATA apunta a un subdirectorio del PVC, con fsGroup 999. La imagen oficial inicializa solo PGDATA nuevo: valida roles, crea cuatro tablas, carga **cinco palabras de demostración** y crea wordle_app con USAGE/esquema/secuencia y SELECT/INSERT/UPDATE. wordle_owner inicializa; el backend no recibe su contraseña. No hay migraciones en workers. La fixture no es un diccionario final aprobado.

Si falla el primer init, el ejecutor se detiene antes de desplegar la aplicación y conserva PVC/Secret/ConfigMap. Una inicialización parcial no se repara automáticamente: revisar logs sin publicar secretos, catálogo, PG_VERSION y permisos, y acordar recuperación antes de alterar datos. No borrar PVC ni regenerar el Secret para ocultar el error; cambiar Secret no rota contraseñas ya guardadas en PG.

## Seguridad, probes y capacidad

Se heredan frontend UID 101 y backend UID 10001; PostgreSQL UID 999. Todos non-root, filesystem raíz read-only, capacidades ALL eliminadas, sin privilege escalation, seccomp RuntimeDefault y sin token de ServiceAccount. Directorios temporales/socket usan emptyDir limitados; PGDATA es el único almacenamiento duradero de DB.

Postgres startup/liveness usan pg_isready por TCP, evitando considerar listo el servidor temporal de init (solo socket). Readiness autenticada con rol app consulta palabras. Backend startup/liveness mantienen /health de proceso; readiness exec abre una conexión async con rol app, timeouts acotados y lecturas únicamente. No prueba escrituras ni usa el pool del proceso web, ni sustituye una transacción funcional. La prueba negativa usa PGHOST=127.0.0.1 solo en el proceso exec para obtener fallo; no se afirma haber observado una transición Ready=False por una caída prolongada real de DB. Nginx readiness comprueba proxy /api/health y liveness /healthz.

| Componente | Requests CPU/RAM | Limits CPU/RAM |
|---|---|---|
| Backend | 100m / 128Mi | 500m / 384Mi |
| Frontend | 50m / 32Mi | 250m / 96Mi |
| PostgreSQL | 100m / 128Mi | 500m / 512Mi |

Pool web 0–4, un worker y una réplica; readiness añade como máximo una conexión simultánea transitoria: presupuesto app aproximado 5, más administración. No demuestra dimensionamiento para Blue-Green/observabilidad. Tres working sets puntuales CRI: DB 23,015,424; frontend 17,797,120; backend 46,821,376 bytes. Metrics Server no está disponible; no se instaló. Sin carga ni HA.

El perfil kind estándar no garantiza enforcement de NetworkPolicy/egress. No se suministran credenciales/SDK/URLs Supabase, el destino operativo es el Service PostgreSQL y las pruebas no usan servicios externos. No se afirma aislamiento de red total ni certificación por captura de paquetes. GHCR/cloud/observabilidad/Ingress definitivo quedan fuera.

## Comandos reproducibles

Desde la raíz del repo, Docker Linux, kind, kubectl y .venv existentes; herramientas compatibles con Kubernetes 1.35.0. La creación puede descargar imágenes oficiales/base y dependencias de build; no instala herramientas globales ni publica imágenes.

```powershell
kind get clusters
docker info
kubectl version --client
.\.venv\Scripts\python.exe -B k8s/postgres/run_pg06.py start
# Usar la ruta state.json devuelta; NO abrir kind.kubeconfig o Secrets.
$state = 'RUTA_DEVUELTA/state.json'
# En otra terminal, usar cluster/kubeconfig de ese state (metadata sin passwords):
kubectl --kubeconfig <ruta-privada>/kind.kubeconfig --context kind-<cluster> -n wordle-pg06 port-forward --address 127.0.0.1 service/frontend 18086:8080
.\.venv\Scripts\python.exe -B k8s/postgres/run_pg06.py smoke --state $state --base-url http://127.0.0.1:18086
.\.venv\Scripts\python.exe -B k8s/postgres/run_pg06.py persist --state $state
# Reiniciar port-forward tras sustituir frontend: el túnel estaba unido al pod anterior.
.\.venv\Scripts\python.exe -B k8s/postgres/run_pg06.py verify --state $state --base-url http://127.0.0.1:18086
.\.venv\Scripts\python.exe -B k8s/postgres/run_pg06.py inspect --state $state
kubectl kustomize k8s/local
kubectl kustomize k8s/postgres
kubectl --kubeconfig <ruta-privada>/kind.kubeconfig --context kind-<cluster> apply --dry-run=server -k k8s/postgres
```

start comprueba que su nombre de clúster no exista; deploy rechaza namespace existente. Si falla solo la carga antes de crear namespace, load_images y deploy aceptan el state propio y comprueban etiqueta de clúster antes de continuar. NO usar deploy como reparación de inicialización parcial. Un segundo smoke crea datos adicionales: ejecutar verify para revisión sin nuevos datos. persist sustituye solo postgres-0 y reinicia ambos Deployments; requiere reconectar port-forward al terminar.

kind load docker-image falló al importar un digest ausente de otra plataforma con Docker 29. Se resolvió con `docker image save --platform linux/amd64 --output <archivo-temporal> <tres-imagenes>` seguido de `kind load image-archive --name <cluster> <archivo-temporal>`. El ejecutor usa este camino y elimina solo ese archivo temporal. No cambia configuración de Docker ni elimina imágenes. Adaptar plataforma si el host no es amd64; esta ejecución es Windows/amd64.

## Recursos conservados y limpieza futura

Se conservan clúster **wordle-pg06-00f26f1f**, namespace **wordle-pg06**, PVC **data-postgres-0**, datos 5 palabras/3 partidas/9 intentos/3 estadísticas, Secret, ConfigMaps, Services e imágenes PG-06. Kubeconfig y state.json están fuera del repo en %LOCALAPPDATA%/WordlePG06/wordle-pg06-00f26f1f/. El port-forward de revisión usa 127.0.0.1:18086. No hay borrado automático de recursos persistentes.

Para detener solo el acceso local: Ctrl+C en la terminal de port-forward. No ejecutar delete -k sobre el overlay para limpiar: incluye Namespace y borraría PVC. No eliminar namespace/PVC/nodo/clúster hasta exportar lo necesario y obtener autorización explícita. Una futura eliminación autorizada sería `kind delete cluster --name wordle-pg06-00f26f1f`; destruiría los datos locales. No se ejecutó.

PG-05 se preserva: volumen wordle-pg05-7325afa8cc_postgres_data, ambas imágenes y backup privado pg05-demo.dump de 7924 bytes. Sin prune, sin abrir compose.env ni tocar datos PG-05.
