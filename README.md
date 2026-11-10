# Wordle — TFG DevOps

Aplicación académica: React/Vite servido por Nginx → `/api` → FastAPI →
**PostgreSQL 16 con psycopg 3 async**. Una base compartida por la aplicación;
Supabase ya no es una dependencia operativa. El nombre `supabase/` se conserva
para no romper la ruta de la migración estructural validada.

PG-01 a PG-07 tienen evidencia local y [CI remoto verificado](https://github.com/lromerob/wordle/actions/runs/42692713269)
para el commit `b330ae70caf08ac789786376ca5de0305ea4471f`.
FIN-01 está **Completado**, aprobado por el responsable el 10/11/2026;
[registro de cierre](docs/analysis/tfg-plan-001/TFG-COMPLETION-PLAN.md).
FIN-02 permanece pendiente. AKS es un objetivo posterior, no un despliegue
validado. No están implementados Blue-Green, rollback automático, Ingress
definitivo ni observabilidad completa.

## Requisitos e instalación

Python 3.12, Node 24 (frontend requiere >=22.12), Docker en modo Linux y Compose
con soporte `!reset` para el perfil memoria (validado con Compose5.6.1).
kind/kubectl solo son necesarios para Kubernetes local. Ejecutar desde la raíz.
No reutilizar credenciales, datos, clústeres o volúmenes privados del autor.

Linux x86_64, entorno aislado y dependencias transitivas bloqueadas:

```sh
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install --only-binary=:all: --require-hashes -r backend/requirements.lock
```

Windows PowerShell, entorno de desarrollo (requirements.txt fija dependencias
directas; la reproducibilidad transitiva Linux se valida con el lock y Docker):

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
```

En los comandos `python` siguientes usar el intérprete del entorno aislado.
No se requiere instalar un cliente ni SDK Supabase. Las imágenes base usan tags
móviles; el lock de paquetes no garantiza imágenes idénticas por digest.

## Pruebas offline y PostgreSQL real

```sh
python -B -m unittest discover -s backend/tests -v
```

Referencia actual: **55 pruebas, cero omitidas**. Los HTTP tests sustituyen
`get_repository` por dobles en memoria; no requieren DB ni credenciales. El paso
backend-tests de [ci.yml](.github/workflows/ci.yml) añade bloqueo global de DNS,
sockets externos, dotenv y conexiones nativas psycopg durante imports/ejecución;
falla si faltan casos, se omiten o fallan. No aceptar tests omitidos por falta de
dependencias como validación completa.

Integración opt-in, con Docker y un PostgreSQL **nuevo y desechable**:

```sh
python -B backend/integration/run_pg04.py --run-disposable-postgres
```

El ejecutor no acepta una DSN arbitraria: crea contenedor/red propios, PostgreSQL
16 en tmpfs, puerto loopback dinámico y credenciales aleatorias. Exige DB vacía,
aplica baseline/catálogo y ejecuta **11 pruebas reales** con fixtures propias,
rollback y locks concurrentes; al final comprueba caída real y limpia solo sus
recursos. No toca Compose persistente ni kind. El tag local `postgres:16` puede
cambiar de minor; PG-07 usa `postgres:16.15`. Véase [PG-04](docs/analysis/pg-04/PG-04-TEST-RESULTS.md).

## Ejecución persistente con Docker Compose

Ruta recomendada en Windows: el ejecutor PG-05 genera un proyecto/volumen nuevos y
dos passwords distintos fuera del repositorio. Requiere `LOCALAPPDATA` (Windows);
no es un ejecutor portable Linux sin adaptar explícitamente el destino privado.

```powershell
.\.venv\Scripts\python.exe -B backend/integration/run_pg05_compose.py start
# Usar la ruta state.json devuelta; no abrir ni publicar compose.env.
$state = 'RUTA_DEVUELTA/state.json'
.\.venv\Scripts\python.exe -B backend/integration/run_pg05_compose.py smoke --state $state
# El ejecutor indica el puerto frontend asignado en 127.0.0.1.
# Al terminar, detener únicamente este proyecto, conservando su volumen:
.\.venv\Scripts\python.exe -B backend/integration/run_pg05_compose.py stop --state $state
```

Para ejecución manual en Linux/Windows, copiar
[docker/postgres/.env.example](docker/postgres/.env.example) a una ubicación
privada externa al repositorio, asignar un nombre de proyecto nuevo y generar dos
contraseñas aleatorias distintas. Comprobar que `<proyecto>_postgres_data` no exista;
si existe, no reutilizarlo sin verificar procedencia/autorización. Desde la raíz,
sustituir los marcadores por la ubicación privada y nombre elegidos:

```text
docker compose --env-file <archivo-privado> --project-name <proyecto-nuevo> config --quiet
docker compose --env-file <archivo-privado> --project-name <proyecto-nuevo> build
docker compose --env-file <archivo-privado> --project-name <proyecto-nuevo> up --detach --wait
docker compose --env-file <archivo-privado> --project-name <proyecto-nuevo> port frontend 8080
docker compose --env-file <archivo-privado> --project-name <proyecto-nuevo> down
```

Solo Nginx publica loopback; backend y PostgreSQL no publican puertos. La imagen
frontend usa `/api`, nunca una URL interna Docker desde el navegador. PostgreSQL
inicializa **solo almacenamiento vacío**: validación, migración
[supabase/migrations/20261108000100_initial_wordle.sql](supabase/migrations/20261108000100_initial_wordle.sql),
fixture de cinco palabras y rol app separado de owner. Ningún worker FastAPI
aplica DDL. Los scripts viven en `docker/postgres/`; los `.sh` mantienen LF.

Cambiar passwords en el archivo no los rota dentro de una DB ya inicializada.
Ante init parcial: conservar datos, diagnosticar y acordar recuperación; nunca
borrar automáticamente el volumen para conseguir un arranque limpio. `down`
conserva el volumen; no usar `down -v` ni prune global como limpieza de pruebas.
Procedimientos y límites: [PG-05](docs/analysis/pg-05/PG-05-IMPLEMENTATION-REPORT.md).

Perfil alternativo sin DB ni persistencia:

```sh
docker compose --env-file docker/postgres/.env.example -f compose.yaml -f compose.test.yaml config --quiet
docker compose --env-file docker/postgres/.env.example -f compose.yaml -f compose.test.yaml up --build --detach --wait
docker compose --env-file docker/postgres/.env.example -f compose.yaml -f compose.test.yaml down
```

No activar el perfil `persistent` en modo memoria. Su solución es CASAS y los
datos desaparecen al reiniciar el backend. Mantener separados proyectos/nombres
si se ejecutan varios perfiles; no sustituir un proyecto persistente por memoria.

En Linux, los ejecutores PG-05/06 pueden recibir un destino privado explícito en
el entorno de ese proceso, sin cambiar el código ni copiar estado Windows:

```sh
LOCALAPPDATA="$HOME/.local/share" python -B backend/integration/run_pg05_compose.py start
# Alternativa kind (crea otro entorno; no ejecutar ambos por obligación):
LOCALAPPDATA="$HOME/.local/share" python -B k8s/postgres/run_pg06.py start
```

El destino lo crea el ejecutor. Esta adaptación de entorno se revisó estáticamente;
los ensayos PG-05/06 registrados se hicieron desde Windows, no se afirma un nuevo
ensayo Linux. No utilizar directorios privados de otro usuario.

## Backend nativo y frontend de desarrollo

[backend/.env.example](backend/.env.example) documenta PGHOST/PGPORT/PGDATABASE/
PGUSER/PGPASSWORD/PGSSLMODE. **El backend no carga `.env` automáticamente.**
Exportar esas variables en la terminal o suministrarlas con el mecanismo explícito
del lanzador; no copiar valores del autor. Usar el rol app de una DB de desarrollo
ya inicializada con fixture. El PostgreSQL de Compose no expone su puerto al host:
para ese modo usar la aplicación Compose completa, no asumir acceso nativo a DB.

Con un PostgreSQL de desarrollo propio accesible y configurado:

```sh
python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --workers 1
```

Frontend, desde otra terminal:

```sh
cd frontend
npm ci
npm run dev
npm test
npm run build
```

Vite usa http://localhost:5173 y por defecto API http://localhost:8000.
`frontend/.env.example` permite configurar VITE_API_BASE_URL: es una URL pública
embebida al construir; nunca incluir passwords/claves en variables VITE_. Las
pruebas frontend simulan fetch; no son pruebas DB. La UI v1.0 tiene seis filas,
teclados físico/virtual, colores del backend, carga/errores y nueva partida;
no reintenta escrituras automáticamente y no reanuda una partida al recargar.

## Kubernetes local con PostgreSQL

Perfil `k8s/postgres/` separado de `k8s/local/` (memoria), con Kustomize, dos
Deployments/Services y PostgreSQL StatefulSet de una réplica con PVC2Gi.
Los Services son internos; acceso por port-forward del frontend. Validado con
kind0.33.0, Kubernetes1.35.0 y kubectl1.36.1; no equivale a AKS/CSI/HA.

Ejecutor Windows existente, siempre para un clúster nuevo exclusivo:

```powershell
.\.venv\Scripts\python.exe -B k8s/postgres/run_pg06.py start
# Guardar la ruta state.json y los nombres devueltos, no abrir kubeconfig.
# En otra terminal, usar esos valores, no los identificadores del autor:
kubectl --kubeconfig <ruta-privada>/kind.kubeconfig --context kind-<cluster-devuelto> -n wordle-pg06 port-forward --address 127.0.0.1 service/frontend 18086:8080
.\.venv\Scripts\python.exe -B k8s/postgres/run_pg06.py smoke --state <state-devuelto> --base-url http://127.0.0.1:18086
```

El ejecutor construye/carga imágenes locales sin registro, genera un Secret nuevo
por stdin y un ConfigMap inmutable de init a partir de los mismos scripts/SQL.
`kubectl apply -k k8s/postgres` **solo no basta**: requiere ese bootstrap.
`LOCALAPPDATA` es necesario para el ejecutor actual; Linux requiere preparar su
destino privado de forma explícita, no copiar el estado de otra máquina.
Readiness backend consulta DB; `/health` solo comprueba proceso. No borrar PVC,
namespace o clúster para solucionar init. Local-path sobrevive al pod, no a
eliminar kind. Manual/evidencia y limpieza autorizada:
[PG-06](docs/analysis/pg-06/PG-06-IMPLEMENTATION-REPORT.md).

## Integración continua y estado de validación

[ci.yml](.github/workflows/ci.yml) se configura para PR, manual y push a `main` y `codex/**`:
55 offline, servicio PostgreSQL16.15/once reales, npm ci/build, builds Docker,
Kustomize memoria, kind memoria efímero y validación Terraform sin Azure.
El job GHCR se conserva **deshabilitado** y sin permiso packages:write.
No hay CD persistente ni publicación de imágenes autorizada por este README.

[PG-07](docs/analysis/pg-07/PG-07-TEST-RESULTS.md) registra 55 offline aprobadas en
Windows/Linux y once reales más outage, así como builds locales con caché válida.
Son resultados locales del 09/11/2026. Posteriormente,
[PUB-05B](docs/analysis/pub-05b/PUB-05B-CI-RESULTS.md) confirmó el run remoto
42692713269 para el commit publicado: siete jobs obligatorios correctos y GHCR
omitido intencionadamente. Los conteos 55/11 se sustentan en las guardas de los
pasos exitosos; no se descargaron logs completos (HTTP403). El smoke kind usa
memoria, no PostgreSQL persistente ni AKS. La rama publicada contiene las fuentes,
el lock y los recursos necesarios para checkout CI; no se afirma su merge a main.

## Seguridad e historia

`usuario_id` es declarado por el cliente: no hay autenticación verificable ni
autorización efectiva de propietario. CORS es abierto y no hay rate limiting.
La aplicación académica no debe presentarse como servicio público seguro.
Transacciones/locks reducen inconsistencias de intentos y stats, pero no prometen
HA ni resolución de un fallo exactamente al COMMIT. Véanse
[notas actuales](backend/SECURITY-NOTES.md) y [contratos](docs/analysis/pg-01/PG-01-HTTP-CONTRACT.md).

[supabase/README.md](supabase/README.md) separa el SQL vigente del material
histórico Supabase. Los scripts de permisos abiertos **no forman parte del
bootstrap actual**. Los informes FIN/plan se conservan como trazabilidad del
momento en que se redactaron; no son instrucciones para reactivar Supabase ni
actualizaciones automáticas del backlog. La hoja TFG-PLAN-001 fue aprobada
posteriormente por el propietario; conserva sus definiciones originales y añade
el registro vigente FIN-01T de cierre de FIN-01.
FIN-02 corresponde a datos/recuperación y FIN-03 a límites de seguridad; esta
nota no cambia el estado ni las dependencias de esas tareas. La auditoría
[PUB-01](docs/analysis/pub-01/PUB-01-REPOSITORY-AUDIT.md) es histórica; el estado de
consolidación más reciente está en [PUB-05B](docs/analysis/pub-05b/PUB-05B-PUSH-REPORT.md), tras la corrección de identidad PUB-05C.

## Registro anterior a la transición PostgreSQL

La versión previa del README registraba validación de contenedores en memoria
con Docker Desktop29.4.1/WSL2, 20 pruebas backend y 12 frontend aprobadas, proxy,
victoria/derrota y corrección de la red interna para acceso Windows. Ese registro
corresponde a la etapa React/Compose anterior a PG-01/07, no a una nueva ejecución
en PUB-02 ni a integración Supabase productiva. El backend actual tiene la
referencia de 55 offline y once reales descrita arriba. La historia Git conserva
las implementaciones previas; los informes por incremento conservan sus límites.
