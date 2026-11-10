# Wordle v1.0 on local kind (memory only)

This directory is exclusively a local test environment. Do not apply these
manifests to shared, cloud or production clusters. No Supabase credentials,
Secret resources, schema changes, Ingress, Blue-Green or observability are used.
The memory backend uses one replica with Recreate: restart or rollout loses all
games. A second backend replica would have independent, inconsistent state.

## Prerequisites and installation

Docker Desktop must be running in Linux-container mode with WSL2 available.
Validated tool versions: kind 0.33.0 and kubectl 1.34.1; cluster node Kubernetes
1.34.0. Check tools before proceeding:

```powershell
docker info
kind version
kubectl version --client
kind get clusters
```

If tools are missing, install them manually according to their official Windows
instructions before deployment; do not change Windows features or WSL settings
as part of deployment. With WinGet already available, explicit user-approved
installation commands are:

```powershell
winget install --id Kubernetes.kind --exact --version 0.33.0
winget install --id Kubernetes.kubectl --exact --version 1.34.1
```

A freshly installed tool may require a new terminal to pick up PATH. Using its
existing absolute executable path also works without modifying system settings.

## Dedicated cluster and images

Run from the repository root. The isolated kubeconfig below is ignored by Git;
never print or publish it. If wordle-dev already exists, inspect its ownership
and resources before reuse: do not replace it or apply over unrelated resources.

```powershell
kind create cluster --name wordle-dev --config k8s/local/kind.yaml --image kindest/node:v1.34.0 --kubeconfig .venv/wordle-kind.kubeconfig --wait 120s
# If a dedicated cluster already exists and is confirmed appropriate:
# kind export kubeconfig --name wordle-dev --kubeconfig .venv/wordle-kind.kubeconfig

docker build --target memory-test -t wordle-backend:v1-kind-memory backend
docker build -t wordle-frontend:v1-kind frontend
kind load docker-image --name wordle-dev wordle-backend:v1-kind-memory wordle-frontend:v1-kind
```

Application images are loaded directly into kind, never pushed to a registry.
Initial creation/build may download the official kind node image, base images
and packages. imagePullPolicy: Never prevents application image registry pulls.
The kubeconfig parent directory must exist; .venv already exists in this project.
For subsequent commands use the explicit kubeconfig AND kind-wordle-dev context,
so the current default context and other clusters are unaffected.

## Deploy and inspect

```powershell
# Namespace must exist before a server dry-run of namespaced resources.
kubectl --kubeconfig .venv/wordle-kind.kubeconfig --context kind-wordle-dev apply -f k8s/local/namespace.yaml
kubectl --kubeconfig .venv/wordle-kind.kubeconfig --context kind-wordle-dev apply --dry-run=server -k k8s/local
kubectl --kubeconfig .venv/wordle-kind.kubeconfig --context kind-wordle-dev apply -k k8s/local
kubectl --kubeconfig .venv/wordle-kind.kubeconfig --context kind-wordle-dev -n wordle-local rollout status deployment/backend --timeout=120s
kubectl --kubeconfig .venv/wordle-kind.kubeconfig --context kind-wordle-dev -n wordle-local rollout status deployment/frontend --timeout=120s
kubectl --kubeconfig .venv/wordle-kind.kubeconfig --context kind-wordle-dev -n wordle-local get pods,services
kubectl --kubeconfig .venv/wordle-kind.kubeconfig --context kind-wordle-dev -n wordle-local logs deployment/backend
kubectl --kubeconfig .venv/wordle-kind.kubeconfig --context kind-wordle-dev -n wordle-local logs deployment/frontend
```

Both Services are ClusterIP only. There are no hostPort, NodePort, externalIPs
or LoadBalancer endpoints. Only frontend receives a local port-forward:

```powershell
kubectl --kubeconfig .venv/wordle-kind.kubeconfig --context kind-wordle-dev -n wordle-local port-forward --address 127.0.0.1 service/frontend 8080:8080
```

Keep that terminal open and use another one for checks:

```powershell
curl.exe http://127.0.0.1:8080/
curl.exe http://127.0.0.1:8080/api/health
$game = Invoke-RestMethod -Method Post 'http://127.0.0.1:8080/api/game/nueva?usuario_id=local-test'
$body = @{partida_id=$game.partida_id; usuario_id='local-test'; palabra='CASAS'} | ConvertTo-Json
Invoke-RestMethod -Method Post 'http://127.0.0.1:8080/api/game/intento' -ContentType 'application/json' -Body $body
```

The deterministic memory solution is CASAS. Valid fixture words include PERRO,
SACAS and AAAAA. Try ZZZZZ for HTTP 400 without consuming an attempt; SACAS tests
mixed green/yellow feedback. CASAS wins; PERRO six times in a new game loses.
A seventh attempt must return HTTP 400. GET /api/game/{id} must hide the solution
while active. Browser uses /api, never a Kubernetes service hostname.

## Configuration and isolation boundaries

Kustomize installs a hashed ConfigMap with the Nginx config. Docker's resolver
127.0.0.11 is omitted: Nginx resolves Service backend through Pod DNS at startup
and proxies to its stable ClusterIP. Recreating the Service or changing the
ConfigMap requires a frontend rollout; restart Pods after updating local images
with the same tags. Services are created before Deployments by Kustomize.

Backend startup explicitly runs the existing memory_server.py. It clears both
Supabase variables and blocks Supabase imports, .env loading and outbound
external connections/DNS in the server process. No credentials are supplied.
Default kind networking does not enforce NetworkPolicy; this iteration relies
on the memory harness and not on a claim of cluster-wide egress isolation.

Pods have non-root IDs (backend 10001, Nginx 101), read-only root filesystems,
RuntimeDefault seccomp, no privilege escalation, no capabilities and no mounted
service account token. Writable /tmp uses a size-limited emptyDir. The namespace
enforces the restricted Pod Security Standard. Startup/liveness/readiness
probes and CPU/memory requests/limits are explicit. Frontend readiness also
checks /api/health; backend probes do not claim real database readiness.

## Cleanup (only resources owned by this local exercise)

Stop the port-forward with Ctrl+C. To remove this application's resources only:

```powershell
kubectl --kubeconfig .venv/wordle-kind.kubeconfig --context kind-wordle-dev delete -k k8s/local
```

This also removes wordle-local: first confirm that nobody has added unrelated
resources there. Do not delete shared namespaces or clusters. Delete the entire
cluster only if you created it for this exercise and it contains no other work:

```powershell
kind delete cluster --name wordle-dev
```

No cleanup command is run automatically. Real Supabase integration and durable
state are deliberately outside the scope of this local deployment.


## Validation recorded

The dedicated wordle-dev cluster was created successfully with the isolated
kubeconfig. Both local images were loaded directly into kind. All six rendered
resources passed server-side dry-run and were applied. Backend and frontend
reached Running and Ready with zero restarts. HTTP checks from Windows through
frontend port-forward passed for the page, static assets, /api/health, game
creation, invalid and short guesses, owner mismatch, mixed letter feedback,
victory, six-attempt defeat, seventh-attempt rejection and a new game.
Active-game retrieval hid the solution. No Secret objects, credentials, external
Services or host ports were present in the namespace.

Transient startup warnings were observed (backend connection refused before
Uvicorn listened, frontend readiness 502 before backend was ready); both
recovered without intervention or restarts. These warnings do not represent
failed final health checks. Supabase integration and production authorization
remain outside this test. Do not interpret the owner-ID consistency check as
verified authentication. The local cluster and application resources are kept
for follow-up; use the scoped cleanup commands only when no longer needed.


## FIN-05/06/07 — Perfil privado con Ingress y PostgreSQL real

`local` conserva la demo en memoria. `postgres` conserva PG-06 sin cambios. El nuevo `aks` deriva del perfil PostgreSQL, elimina la entrada memory, usa runtimes GHCR con tag SHA completo, pull IfNotPresent, readiness SQL y StatefulSet de una réplica con PVC 8Gi managed-csi. `demo-kind` sustituye únicamente imágenes locales y almacenamiento standard/2Gi. Las referencias GHCR no aseguran que los paquetes estén publicados: FIN-04 sigue pendiente de esa evidencia.

Ruta: navegador → Service ingress → Traefik → Ingress host wordle.test → Service frontend/Nginx → /api → Service backend/FastAPI → Service postgres/PVC. Tanto / como /api se encaminan a Nginx; solo Nginx retira el prefijo /api. No se expone FastAPI ni PostgreSQL mediante NodePort o LoadBalancer. Todos los Services son ClusterIP, incluido el controlador.

### Demostración local desechable

Prerrequisitos: Docker, kind, kubectl y Python existentes. No se usa el contexto Kubernetes activo del operador. Desde la raíz:

```sh
python -B k8s/demo-kind/run_demo.py --run-disposable-kind
```

En Windows puede usarse `.venv\Scripts\python.exe`. Crea un nombre aleatorio wordle-fin0507-*, kubeconfig temporal y contexto explícito; construye/carga runtimes locales, usa PostgreSQL 16.15 y Traefik 3.7.17 fijado por digest. Inyecta dos contraseñas sintéticas aleatorias desde el entorno del proceso; no se guardan en archivos ni se muestran. Inicializa una base nueva con el baseline ratificado, cinco palabras y el rol app vigente. Comprueba HTTP a través del controlador, SQL real, recuperación del Secret, nueva conexión backend y persistencia tras recrear el pod PostgreSQL. Al terminar, también ante fallo, detiene su port-forward y elimina solo su clúster; no toca PG-05/PG-06. Conserva imágenes y cachés de Docker para reproducir la prueba. No ejecutar este script para administrar entornos persistentes.

Render sin clúster ni secretos:

```sh
kubectl kustomize k8s/local
kubectl kustomize k8s/aks
kubectl kustomize k8s/demo-kind
```

### Configuración externa e inicialización manual autorizada

Para un entorno NUEVO autorizado: elegir kubeconfig/contexto explícitos, verificar destino y crear el Namespace wordle-demo con las etiquetas del render. Cargar externamente WORDLE_DEMO_ADMIN_PASSWORD y WORDLE_DEMO_APP_PASSWORD (distintas, al menos 32 caracteres) mediante entorno protegido o entrada interactiva oculta; no usar literales en shell, argumentos, archivos Git ni logs. Por ejemplo, una sesión Python puede usar getpass.getpass para poblar os.environ y lanzar el comando siguiente como subproceso; no imprimir el entorno. La demo automática anterior genera esos valores con secrets.token_urlsafe.

```sh
python -B scripts/configure_demo_secrets.py --kubeconfig <ARCHIVO_PRIVADO> --context <CONTEXTO_EXPLICITO> --authorize-private-demo
kubectl --kubeconfig <ARCHIVO_PRIVADO> --context <CONTEXTO_EXPLICITO> apply -k k8s/demo-kind
# Tras disponibilidad de PostgreSQL, backend, frontend e ingress:
kubectl --kubeconfig <ARCHIVO_PRIVADO> --context <CONTEXTO_EXPLICITO> -n wordle-demo port-forward --address 127.0.0.1 service/ingress 18085:8080
curl -H 'Host: wordle.test' http://127.0.0.1:18085/
curl -H 'Host: wordle.test' http://127.0.0.1:18085/api/health
```

Para AKS futuro se usa `-k k8s/aks`, solo tras autorización cloud y revisión de imágenes/discos. Primero inspeccionar colisiones de Namespace/IngressClass/ClusterRole y no adoptar recursos ajenos. La configuración externa crea wordle-db y el ConfigMap inmutable wordle-postgres-init a partir de los cuatro archivos fuente existentes; no duplica SQL ni ejecuta semillas FIN-02A automáticamente. Rechaza sobreescribir un Secret existente. Las credenciales no pertenecen al render Kustomize.

Nombres de configuración: ConfigMap wordle-pg-config (con hash) contiene PGHOST/PORT/DATABASE/USER/SSLMODE y WORDLE_CORS_ORIGINS vacío: mismo origen por Ingress, sin autorización cross-origin. Secret wordle-db: admin-password solo PostgreSQL; app-password PostgreSQL y backend. Frontend no recibe secretos. Las cuentas app/owner conservan grants SQL existentes; no son identidad de jugador. Application ServiceAccounts no montan token; el controlador sí lo necesita.

### Recuperación, permisos y rotación

Conservar la fuente externa de credenciales en almacenamiento protegido fuera de Git y del repositorio, accesible solo al operador; el Secret Kubernetes no es un respaldo. Evitar kubectl get secret -o yaml, shell tracing, dumps de entorno y artefactos con valores. Base64 no cifra. Un administrador de Kubernetes puede leer Secrets. Traefik dispone de lectura de Secrets/Services/Ingress/EndpointSlices únicamente en wordle-demo y descubrimiento de nodos/IngressClass a nivel clúster; el operador que crea la configuración necesita crear Secret/ConfigMap y los recursos del perfil. Ese permiso no se concede a frontend/backend. Aislar la demo en un clúster/namespace dedicado.

Si se pierde solo wordle-db, recuperar **los mismos valores** de la fuente externa, ejecutar configure_demo_secrets.py con --recover-secret-only y reiniciar el Deployment backend. No regenerar contraseñas sobre un PVC existente: los env POSTGRES_* solo inicializan PGDATA vacío. La prueba automática reproduce esta recuperación sin leer ni mostrar valores del Secret. La recreación del Secret no rota contraseñas SQL.

Para rotación futura: ventana privada de mantenimiento, conservar recuperación externa, cambiar las contraseñas de los roles PostgreSQL mediante sesión administrativa y SQL parametrizado sin logs, actualizar la fuente externa y wordle-db con esos mismos valores, reiniciar workloads dependientes y verificar readiness y operación real. No borrar PVC ni confiar en reiniciar PostgreSQL con otro env. Este incremento no automatiza ni afirma haber probado esa rotación. Si se pierde el origen externo de credenciales se requiere recuperación administrativa/backup aprobada; no se obtiene de los manifiestos.

### DNS, TLS y perímetro

wordle.test es un host de ensayo; curl usa Host explícito sin tocar hosts/DNS del sistema. HTTP sobre port-forward loopback es suficiente para la prueba local privada, no para uso público. No hay certificado real, ACME ni cert-manager. Para AKS se conserva Service ClusterIP y port-forward como primera demo; cualquier futuro acceso privado de red debe revisar DNS interno, TLS terminado en Traefik mediante Secret externo y, si se autoriza, LoadBalancer **interno** con alcance de red restringido. No se declara un LB público ni se despliega TLS aquí. El control plane Terraform sigue restringido por CIDR y Entra. No se implementa aislamiento por jugador: solo demo supervisada y datos sintéticos; CORS no autentica.

Fuentes oficiales para la elección del controlador: [provider Kubernetes Ingress de Traefik](https://doc.traefik.io/traefik/reference/install-configuration/providers/kubernetes/kubernetes-ingress/) y [política de releases](https://doc.traefik.io/traefik/deprecation/releases/). La imagen estable disponible al validar fue v3.7.17; v3.7.18 aparecía en GitHub pero aún no existía su tag Docker, por lo que no se seleccionó una referencia no descargable. Solo se incorpora un controlador, sin Helm, operadores ni CRDs adicionales.
