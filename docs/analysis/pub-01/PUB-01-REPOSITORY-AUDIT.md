# PUB-01 — Auditoría previa a publicación

Fecha: 09/11/2026. Solo lectura salvo estos tres informes autorizados. Sin pruebas, contenedores, builds, Kubernetes, Azure, conexiones DB o consultas remotas. No se usa el estado de una página/navegador como evidencia del repositorio.

## Git y alcance observado

- Rama codex/devops-04a1-hardening; HEAD a666b17680781a24889ea774778019995d3fca45, mensaje ci: validate Terraform and document secure AKS access.
- 53 archivos versionados: 13 modificados y 40 sin cambios; 59 nuevos sin seguimiento al iniciar. Índice vacío. Los tres informes PUB-01 son adicionales a ese inventario.
- Hay historia anterior de backend/frontend/Docker/Kubernetes/Terraform/CI y merges; no es el primer commit absoluto del repositorio. Sería la primera consolidación del trabajo PG acumulado.
- Sin cambios de rama, fetch, add, commit, push, reset o clean. No se ha verificado actualidad/divergencia con GitHub; referencias locales no certifican origin/main actualizado.
- git diff --check pasa; avisos LF/CRLF en archivos conocidos son informativos. No equivale a prueba funcional.

El manifiesto compañero enumera cada archivo. Los trece modificados pertenecen a PG-02/03/05/06/07, encima de trabajo ya en HEAD. PG-01 aporta contratos; PG-04 integración; PG-06 perfil PostgreSQL; los informes FIN-01A/B/C, herramientas SQL y plan TFG son anteriores a PG-01 y necesitan selección explícita, no incorporación automática.

## Hallazgos y riesgos para publicación

| Hallazgo | Evidencia | Consecuencia / condición |
|---|---|---|
| Manual raíz obsoleto | README.md sigue afirmando get_supabase, SUPABASE_URL/KEY, escrituras no transaccionales y arranque Compose Supabase | No describe el backend/Compose actuales; actualizar manual autorizado antes de presentar clon limpio como reproducible |
| Plantilla/notas antiguas | backend/.env.example contiene solo placeholders Supabase; SECURITY-NOTES.md sigue describiendo I/O síncrono/ausencia de atomicidad | No hay secreto en la plantilla, pero configuración y riesgos técnicos desactualizados; conservar las limitaciones reales de identidad |
| Dependencias CI locales | Nueve rutas enumeradas en el manifiesto existen pero no están versionadas | Un checkout de HEAD o publicación de solo workflow no ejecutaría correctamente PG-07 |
| Históricos inseguros | supabase/prototype/allow_all.sql concede política abierta y grants; tests/prototype_access.sql y local_backend_smoke.py son del camino Supabase abandonado | No se aplican por CI/Compose/kind actuales; excluir del incremento operativo hasta decisión de archivo histórico y rotulado inequívoco |
| Información personal en evidencias | Siete informes PG-05/06/07-next contienen rutas de usuario/evidencias o referencias específicas al entorno conservado | No son passwords, pero requieren revisión/sanitización para un repositorio público; no modificados en esta auditoría |
| Dependencia local de Windows | run_pg05_compose.py y k8s/postgres/run_pg06.py usan os.environ["LOCALAPPDATA"] y ubicación privada generada | Sin rutas Windows absolutas codificadas, pero esos ejecutores no son directamente portables a Linux sin definir destino equivalente; CI PG-07 no los invoca |
| Imágenes y recursos locales | Scripts construyen y cargan imágenes, generan cluster/proyecto nuevo; no necesitan adoptar PG-05/06 existentes | Los nombres reales de evidencia no deben convertirse en prerrequisitos. Secret/PVC/configuración init se generan, no existen como secretos versionables |
| Versiones móviles | Compose y PG-04 usan postgres:16; Dockerfiles usan tags de base | Los locks fijan paquetes, no garantizan rebuild idéntico por digest. PG-06/07 fijan tag16.15, no todos los digests |
| Plan histórico | tfg-plan-001 se presenta como propuesta, aunque el propietario lo aprobó posteriormente; FIN-02 trata recuperación/datos, FIN-03 seguridad | Mantener trazabilidad histórica y aclarar referencias al publicar; no actualizar estados/backlog desde PUB-01 |

## Secretos: método, hallazgos y límites

Se analizaron en memoria los 112 archivos versionados/candidatos no ignorados con patrones de claves privadas, tokens GitHub, access keys AWS, JWT, URI con credenciales y asignaciones de credenciales. Solo se emitieron rutas/líneas/categorías. No se abrieron backend/.env, kubeconfigs, dumps, estados privados, paquetes ignorados ni archivos externos de credenciales.

| Ruta/línea | Categoría | Evaluación sin valores |
|---|---|---|
| .github/workflows/ci.yml:75 y :98 | Password literal | Mismo valor público exclusivo de CI temporal, autorizado en PG-07; no credencial real ni para despliegue |
| backend/integration/run_pg05_compose.py:89 | Posible literal | Generación aleatoria de passwords fuera del repo; no password fijo encontrado |
| compose.yaml:8 | Password | Sustitución de variable externa con default vacío, no valor incorporado |
| docker/postgres/30-app-role.sh:8 | Password SQL | Referencia psql a variable de entorno, no credencial literal |
| k8s/postgres/postgres.yaml:95 | Posible literal | Shell de probe con referencias de entorno, no secreto versionado |

No se detectó credencial real con estas comprobaciones. Palabra_secreta es dato del juego y no clave de acceso; no se excluyeron archivos enteros por ese nombre. La plantilla docker/postgres/.env.example tiene campos privados vacíos; Terraform usa identificadores nulos de ejemplo y rango documental, no credenciales Azure. El frontend recibe solo URL pública; Docker contexts usan allowlist y no copian .env. No hay claves privadas/dumps/estado Terraform versionados por nombre en el índice actual.

backend/.env existe, está ignorado y NO se inspeccionó: su contenido queda desconocido, no certificado seguro por estar ignorado. .venv/wordle-kind.kubeconfig también existe y está excluido por directorio. git log --all -- backend/.env no devolvió commits en referencias locales; esto no es una auditoría de secretos de todos los blobs, nombres históricos u objetos remotos. No se realizó auditoría completa de historia Git ni de dependencias binarias. No se garantiza ausencia absoluta de secretos por patrones.

27 referencias de entorno/máquina detectadas en nueve rutas: dos ejecutores usan LOCALAPPDATA de forma intencional, y siete informes operativos requieren revisión. No se reproducen rutas personales completas en estos informes.

## GitHub Actions

Un workflow ci.yml; ocho jobs tras PG-07. Triggers PR/manual/push-main conservados. backend-tests instala lock Python3.12 con hashes y exige55/cero skips; incluye guardas DNS/socket/dotenv/psycopg nativo. postgres-integration instala el mismo lock y usa postgres:16.15 con tmpfs/health/puerto loopback dinámico; adapter recibe job.services.postgres.id en env de paso.

El adaptador valida imagen/etiqueta/montajes/puerto y acepta solo esa base/roles. Reutiliza prepare/schema_contracts, baseline original, seed mínimo y once casos PG-04; comprueba DB vacía antes de DDL. Los TRUNCATE de tests quedan limitados a la DB temporal. La caída detiene exclusivamente su servicio al final; el resto de jobs usa runners separados. No se sustituye PostgreSQL por mocks en ese job.

frontend-build mantiene npm ci/build. docker-build necesita offline/integración/frontend; kind-smoke-test depende también de Docker y validación Kustomize, de modo que un fallo PostgreSQL impide el smoke dependiente. kind sigue desplegando **memoria efímera de CI** por autorización expresa del propietario, no el perfil PG-06 persistente ni cloud. Terraform conserva fmt/init-backendfalse/validate, sin operaciones Azure. GHCR está if:false y sin packages:write; su definición histórica no se ejecuta. contents:read y checkout sin persistencia, sin pull_request_target, nuevos tokens o secretos de despliegue.

YAML analizado estáticamente, ocho jobs y referencias locales presentes. No hay actionlint disponible ni ejecución remota en PUB-01. Compatibilidad Linux: Dockerfiles/lock son Linux-amd64, adaptador CI no depende de LOCALAPPDATA y existe evidencia PG-07 de offline Linux; once reales se probaron desde cliente Windows/PG Linux. Falta validar orquestación real services/contextos en Actions, instalación limpia del lock Ubuntu, once casos desde runner Linux, estados de jobs/condiciones y logs. No afirmar pipeline remoto verde.

## Reproducibilidad de un clon

| Operación | HEAD publicado actualmente / árbol local propuesto | Preparación y dependencia |
|---|---|---|
| Instalar backend/frontend | HEAD conserva backend Supabase antiguo; árbol local tiene requisitos/lock PostgreSQL y package-lock frontend | Python3.12/Linux-amd64 para lock; entorno nuevo, npm ci. No requiere .venv ni node_modules del propietario |
| 55 offline | No disponibles como conjunto actual en HEAD; existen completas en árbol local | Incluir modificaciones y dos tests nuevos; wrapper CI bloquea conexiones y exige cero skips |
| PG temporal / once reales | Scripts/SQL/fixture ausentes de HEAD, presentes localmente | Publicar selección coherente; run_pg04 crea su DB/contenedor; CI usa services y adaptador PG-07 |
| Builds | Dockerfiles ya en HEAD y sin cambio; nuevo código/lock debe acompañar | Build descarga bases/paquetes, no depende de imágenes locales guardadas. No se hizo build en PUB-01 |
| Compose persistente | Cambios PG-05 y seis archivos nuevos necesarios | Generar credenciales nuevas, proyecto/volumen nuevo; usar plantilla/manual PG-05, no README antiguo ni compose.env privado |
| kind PostgreSQL | Perfil PG-06 nuevo no versionado; memoria ya en HEAD | start crea cluster/kubeconfig/Secret/init ConfigMap y carga imágenes; requiere Docker/kind/kubectl compatibles y LOCALAPPDATA en el ejecutor actual |

Los mecanismos existen, pero no se probó aquí un clon limpio ni se ejecutaron suites; la evidencia local PG-07 se conserva como histórica (55+11/builds), no como nueva ejecución PUB-01. Los informes operativos son parte del manual propuesto y requieren revisión de privacidad antes de incorporarlos.

## Resultado

READY WITH CONDITIONS, explicado en PUBLICATION-DECISION. Ningún secreto real identificado entre candidatos, pero selección incompleta/documentación incoherente impiden una autorización incondicional ahora. Solo se crean tres informes; FIN-01 sigue pendiente.
