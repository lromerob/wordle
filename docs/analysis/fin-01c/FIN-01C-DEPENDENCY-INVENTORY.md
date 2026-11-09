# FIN-01C - Inventario de dependencias Supabase

Fecha: 08/11/2026. Análisis, no autorización de migración. Corte local: codex/devops-04a1-hardening, HEAD a666b17680781a24889ea774778019995d3fca45, con docs/ y supabase/ anteriores sin versionar. No se hizo fetch ni se afirma que sea el main remoto actual. Se preservan todos los archivos previos. No se consultaron secretos, Supabase ni Azure; no se arrancaron servicios, instalaron paquetes o ejecutaron pruebas/migraciones.

## Evidencia y límites

Las referencias de líneas se verificaron por lectura/AST. Se inspeccionaron fuentes, configuración y lock, excluyendo .env, estado Terraform, kubeconfig, caches y dependencias instaladas. El único import del paquete supabase de producción está en database.py; los routers importan get_supabase. No se encontraron consumidores de Supabase en frontend/src. Los relatos de FIN-01B acreditan validación SQL histórica, no integración del backend actual por conexión directa.

## 1. Código y endpoints

| Archivo / función | Operación actual y endpoint | Cambio necesario si se aprueba |
|---|---|---|
| [database.py:6-18](../../../backend/app/database.py) get_supabase | Importa create_client, dotenv y variables; crea cliente lazy con lru_cache | Sustituir fábrica por gestión de conexiones/pool psycopg y dependencia FastAPI; conservar configuración sin secretos y definir cierre del pool. |
| [game.py:3,38](../../../backend/app/routers/game.py) nueva_partida | POST /game/nueva: SELECT palabras, random.choice en Python, INSERT partida, retorno data[0][id] | SQL parametrizado y RETURNING id; mantener selección/evaluación y respuesta. |
| game.py:57 registrar_intento | POST /game/intento: leer partida, validar propietario/estado/límite/diccionario, INSERT intento, UPDATE partida y estadísticas | Lecturas/escrituras directas bajo una transacción; serializar por partida y acordar manejo de conflictos. Mantener reglas/estados HTTP existentes. |
| game.py:117 estado_partida | GET /game/{partida_id}: SELECT * de partida y SELECT intentos ORDER BY numero | Resultados dict con serialización equivalente; mantener filtrado de solución en partida activa. |
| game.py:131 _actualizar_estadisticas | SELECT/INSERT/UPDATE estadisticas dentro de finalizar partida | SQL con actualización coherente del promedio/rachas, usando la misma conexión/transacción del intento. Revisar primera fila concurrente con UNIQUE usuario_id. |
| [stats.py:8](../../../backend/app/routers/stats.py) obtener_estadisticas | GET /stats/{usuario_id}: SELECT *; ceros si no hay fila; porcentaje en Python | SQL parametrizado y dict; conservar ceros/porcentaje y campos existentes. |
| stats.py:30 ranking_global | GET /stats/ranking/global: proyección de cuatro columnas, ORDER BY partidas_ganadas DESC LIMIT 10 | SQL equivalente; no añadir desempate/orden de NULL que altere resultados sin acuerdo. |
| [main.py](../../../backend/app/main.py) app/health | /health no utiliza DB; incluye routers | Integrar ciclo de vida del pool sin redefinir silenciosamente /health como chequeo DB. Elegir comportamiento de arranque con DB no disponible. |
| game.py:13 IntentoPeticion | Modelo HTTP Pydantic, no ORM; tres str | Mantener contrato externo; no introducir UUID SQL en respuesta como formato distinto. |
| game.py:19 evaluar_intento | Lógica pura, dos pasadas para repetidas | Ningún cambio requerido por PostgreSQL. |

Son cinco endpoints de datos afectados; /health solo por posible ciclo de vida de conexión. No hay llamadas RPC, joins, Auth, Storage, Realtime o funciones remotas. No se detecta función de Wordle que requiera un producto exclusivo de Supabase. El cliente es síncrono dentro de handlers async; no trasladar ese bloqueo a psycopg síncrono sin una estrategia explícita.

## 2. Dependencias Python

[requirements.txt](../../../backend/requirements.txt) declara supabase==2.4.6. [requirements.lock](../../../backend/requirements.lock) fija los componentes de su familia:

| Componente | Versión observada | Impacto |
|---|---|---|
| supabase | 2.4.6 | Retirar del runtime tras aprobar y completar reemplazo. |
| postgrest | 0.16.11 | Desaparece el transporte Data API usado para tablas; no es un driver PostgreSQL. |
| gotrue | 2.12.4 | Dependencia transitiva del SDK; no hay uso Auth en la aplicación. |
| realtime | 1.0.6 | Transitiva, sin consumidor funcional identificado. |
| storage3 | 0.7.7 | Transitiva, sin llamadas Storage identificadas. |
| supafunc | 0.4.7 | Transitiva, sin llamadas de funciones identificadas. |

No borrar indiscriminadamente sus dependencias compartidas (HTTPX, anyio, Pydantic u otras). HTTPX==0.27.0 se declara y usa en TestClient; FastAPI/Uvicorn siguen siendo necesarios. Revisar python-dotenv: hoy se importa en la fábrica, podría mantenerse solo para configuración local si se decide. Regenerar el lock con el procedimiento existente para Linux/Python 3.12, nunca editar hashes manualmente. El target Docker instala wheels con --require-hashes/--only-binary: confirmar disponibilidad de la distribución psycopg elegida y libpq si procede. No se elige una versión nueva sin comprobarla durante la implementación.

## 3. Variables y credenciales, sin leer valores

| Referencia | Estado actual | Sustitución propuesta |
|---|---|---|
| database.py; Compose; tests CI; manifiesto backend; memory_server | SUPABASE_URL, SUPABASE_KEY | Host/puerto/nombre/usuario/password PostgreSQL con nombres por acordar, por ejemplo PGHOST/PGPORT/PGDATABASE/PGUSER y password externo. No asumir que basta renombrar la URL del servicio REST. |
| [frontend/src/api.js](../../../frontend/src/api.js); Dockerfile frontend | VITE_API_BASE_URL público, /api en build Docker | Sin cambio si se conservan HTTP y proxy. Nunca poner credenciales DB en VITE_. |
| Configuración privada/plantillas | No se inspeccionaron .env ni valores secretos | Documentar nombres nuevos y retirar referencias antiguas solo en la implementación aprobada; evitar DSN con contraseña en logs/errores. |
| supabase/prototype/allow_all.sql | Roles/políticas propios del prototipo | Mantener como evidencia histórica; no aplicarlos automáticamente a PostgreSQL directo ni recrear roles anon/authenticated/service_role sin necesidad. |

La identidad usuario_id sigue siendo texto controlado por el cliente; la migración no introduce login ni seguridad de usuario nueva. Cambiar de conexión no demuestra autorización efectiva. Para este análisis solo se propone usuario técnico DB con permisos de operación necesarios, secretos externos y Service interno.

## 4. Pruebas y utilidades

| Archivo/componente | Acoplamiento actual | Adaptación propuesta |
|---|---|---|
| [test_backend.py](../../../backend/tests/test_backend.py) EvaluationTests | Evaluador extraído por AST y cache_info de get_supabase | Preservar casos de letras; adaptar prueba del lifecycle/dependencia. No eliminar la garantía de no conectar externamente al importar. |
| test_backend.py MemoryDB/MemoryQuery, HandlerTests | Simulan API table/select/eq/insert/update; seis tests de handler vía AST | No representan cursor/driver ni catálogo. Adaptar dobles al acceso de dominio mínimo o tests HTTP; no crear un clon general del SDK como arquitectura nueva. |
| test_backend.py EndpointTests | Doce tests HTTP, override get_supabase y parche de factory | Cambiar override a nueva dependencia. Mantener casos y estados HTTP; añadir integración real PG para SQL, no solo mocks de cursor. |
| [test_stabilization.py](../../../backend/tests/test_stabilization.py) | Seis tests reutilizan setup/guess de EndpointTests | Adaptar fixture común; conservar sus regresiones. |
| [memory_server.py](../../../backend/docker/memory_server.py) | Importa fixture MemoryDB, bloquea imports supabase, dotenv y sockets externos | Mantener modo puramente en memoria si es útil, adaptando interfaz; añadir otro perfil con PG real. Su bloqueo actual impide conectar a una DB en otro contenedor. |
| [supabase/tests](../../../supabase/README.md) schema_contracts/backend_operations | SQL contra PG ya validado en FIN-01B | Reutilizar sin alterar baseline; no sustituye pruebas del backend por driver. |
| supabase/tests/prototype_access.sql | Espera roles/políticas legacy | Separar de aceptación PG directo; no interpretar fallo por roles ausentes como error de las tablas. |
| supabase/tests/local_backend_smoke.py | HTTP con opt-in local; documentación presupone Supabase local | Contratos HTTP reutilizables para driver directo; documentar nuevo runtime y extender a derrota/repetidas/persistencia. No basta renombrar su resultado. |
| supabase/tools/prepare_dictionary.py y test_dictionary_preparation.py | Generador SQL estándar; cinco tests offline | Reutilizables; fuente real del diccionario sigue pendiente. |
| [frontend/src/App.test.jsx](../../../frontend/src/App.test.jsx) | Doce casos con fetch simulado | No dependen de SDK Supabase; conservar si se mantiene API. No acreditan driver/PG real. |

Ninguna de estas suites se ejecutó en FIN-01C. Conteos son inventario de código y evidencia histórica, no nuevos resultados.

## 5. Contenedores, Kubernetes y CI

| Archivo | Dependencia actual | Cambio necesario |
|---|---|---|
| [backend/Dockerfile](../../../backend/Dockerfile) | Instala lock del SDK y define memory-test con harness | Actualizar lock/driver y posible libpq; preservar runtime non-root. Planear cómo poner SQL en Job/servicio de migración sin ejecutar migraciones en cada web worker. |
| [backend/.dockerignore](../../../backend/.dockerignore) | Contexto allowlist solo app/lock/fixture/harness; SQL supabase/ está fuera de backend/ | No asumir que la imagen contiene migraciones. Diseñar entrega explícita de SQL al migrador; no ampliar contexto incluyendo secretos. |
| [frontend/Dockerfile](../../../frontend/Dockerfile), nginx.conf, frontend/.dockerignore | Proxy backend:8000 y build /api | No precisan cambio funcional; verificar regresión HTTP. |
| [compose.yaml](../../../compose.yaml) | Dos servicios, backend inyecta variables Supabase | Añadir PG con volumen, salud, credenciales privadas y migrador/seed one-shot; nueva conexión backend. |
| [compose.test.yaml](../../../compose.test.yaml) | memory-test, dos redes, sin persistencia | Conservar test memoria o perfilar integración PG temporal; no usar la misma base/volumen de desarrollo. |
| [k8s/local/backend.yaml](../../../k8s/local/backend.yaml) | Comando memory_server y variables Supabase vacías | Perfil de integración separado; backend driver, DB Service/Secret; no conectar un memory harness bloqueado a PG. |
| [frontend.yaml](../../../k8s/local/frontend.yaml), [nginx.conf](../../../k8s/local/nginx.conf) | ClusterIP y proxy al Service backend | Conservar; promoción Blue/Green debe mantener resolución/ruta lógica. |
| [kustomization.yaml](../../../k8s/local/kustomization.yaml), namespace.yaml | Solo app/config Nginx, entorno local-memory-test | Añadir recurso de datos separado en perfil nuevo; no incluir DB/PVC en la conmutación de colores ni borrado de namespace app. |
| [ci.yml](../../../.github/workflows/ci.yml) backend-tests | Vacía variables Supabase y bloquea sockets/DNS | Mantener unit tests offline; integración PG debe ser job/entorno separado con red solo local autorizada. |
| ci.yml docker-build/frontend-build | Build de imágenes y Vite | Regenerar dependencias backend; frontend permanece igual. |
| ci.yml kind-smoke-test | Construye/carga imágenes memory-test, aplica perfil memoria y realiza HTTP | Conservar evidencia de memoria mientras se añade una puerta de integración PG; después adaptar/deprecar explícitamente, sin afirmar que kind memoria demuestra persistencia. |
| ci.yml kubernetes-validation | Render Kustomize local | Renderizar también perfil PG/AKS cuando exista, sin conectar a cloud. |
| ci.yml publish-ghcr | Publica runtime backend/frontend por SHA tras cinco jobs | Driver nuevo entra en runtime; no necesita publicar imagen PostgreSQL personalizada. Decidir gate de integración antes de publicar/promover; no existe CD/BG actual que se pueda dar por conservado. |
| ci.yml terraform-validation | Valida IaC sin DB ni credenciales | Sin dependencia de SDK; futuro sizing/storage revisados, no retirar este check. |
| [infra/terraform/main.tf](../../../infra/terraform/main.tf) | AKS con pool y red, sin DB gestionada | No crear Azure Database ni ACR. PVC/CSI consume disco y memoria del clúster; revisar sizing y costes, sin cambios imprescindibles de IaC por el driver en sí. |

## 6. Documentación y rutas históricas

README principal, k8s/README, infra/terraform/README y SECURITY-NOTES describen Supabase o ausencia de persistencia; se actualizarían solo después de aprobar/implementar. Los informes [FIN-01A](../fin-01a/FIN-01A-SCHEMA-ASSESSMENT.md), [FIN-01B](../fin-01b/FIN-01B-RECONSTRUCTION-REVIEW.md) y [validación PG](../fin-01b/FIN-01B-POSTGRES-VALIDATION.md) deben conservar procedencia histórica, no reescribirse como si ya usaran psycopg.

La carpeta supabase/ contiene SQL PostgreSQL reutilizable. Mantener su ubicación durante la primera implementación reduce riesgo; una futura reubicación neutral exige actualizar rutas/hashes/documentación, sin duplicar baseline ni reejecutarla sobre una DB existente. El nombre de carpeta no obliga a utilizar el servicio.

Los cuatro análisis TFG-PLAN-001 y el análisis Azure describen la arquitectura antigua. FIN-01C solo propone revisiones del plan; no modifica estados, dependencias o backlog.
