# PG-02 — Resultados de validación

Fecha: 08/11/2026. Evidencia local Windows/Python 3.12.14, sin PostgreSQL, Supabase ni Azure. Cambios sin commit en la rama indicada en el informe de implementación. No se atribuyen resultados a una imagen o DB no ejecutada.

## Resultados ejecutados

| Comprobación | Resultado real |
|---|---|
| Referencia antes de cambios | 26 pruebas existentes aprobadas, cero omitidas; 1.120 s. |
| Primera ejecución adaptada | 44 pruebas aprobadas, cero omitidas; 1.039 s, en .venv existente. |
| Suite final en entorno limpio sin SDK | **45 pruebas aprobadas, cero omitidas; 1.564 s.** Incluye un caso adicional de UUID en nueva partida. |
| Evaluador/modelo | AST idéntico al HEAD de referencia para evaluar_intento e IntentoPeticion. |
| Cobertura previa | Los mismos 26 métodos originales siguen presentes; ninguna reducción de número de aserciones por método. Se adaptan cache_info/single() a garantías de la nueva interfaz. |
| Sintaxis | compile() en memoria de nueve archivos Python de app/tests/harness, correcto; sin generar bytecode. |
| Dependencias Windows | pip check del .venv existente y uv pip check del entorno nuevo: sin incompatibilidades. Entorno nuevo con 41 distribuciones, sin distribución supabase. |
| Lock | Regeneración uv 0.13.0 mediante comando del README; segunda ejecución idéntica byte a byte; sin hashes manuales. Versiones compartidas del lock conservadas. |
| Wheels Linux | 40 wheels para CPython 3.12/Linux x86_64 descargados desde PyPI; todos los pines y hashes del lock verificados. Metadatos Requires-Dist y extras contrastados con entorno Linux y especificadores: cierre completo satisfecho. |
| Docker | Docker Engine 29.9.2 responde. python:3.12-slim-bookworm NO está en las imágenes locales. No se ejecuta build porque descargar la base de Docker Hub excedería la excepción autorizada (solo PyPI). |
| SQL baseline | SHA256 da743e629094da2b7d126f7889c5d1ca72e63a232844feadea3798254b19b0cb, sin cambios. No se ejecutó migración ni SQL sobre DB. |
| Scope | Hashes de archivos originales: solo nueve archivos backend versionados cambiaron; los anteriores docs/ y supabase/ intactos. Se añaden repositorio SQL, prueba PG-02 y tres documentos. |
| Secretos en candidatos | Comprobación automática acotada de 14 archivos: claves privadas, tokens GitHub, JWT, DSN con contraseña, claves cloud y asignaciones literales de credenciales; cero hallazgos. No se abrieron .env ni archivos de secretos. No equivale a detección exhaustiva. |
| Git diff --check | Correcto. Git avisa de normalización futura LF/CRLF en el lock; sin error de whitespace. |

El entorno nuevo se creó en una carpeta temporal separada mediante uv venv usando Python 3.12.14 e instalación --only-binary desde requirements.txt. Sus transitivas Windows se resuelven para Windows (por ejemplo tzdata); no se afirma que sea una ejecución Linux del lock. El .venv existente se conserva, incluidas sus dependencias antiguas; no se desinstaló el SDK de ese entorno. Los artefactos temporales de validación están fuera del repositorio; no se eliminan recursos/datos existentes.

## Comandos de dependencias

Ejecutado en el .venv aislado, únicamente con PyPI:

```text
python -m pip install --only-binary=:all: --index-url https://pypi.org/simple psycopg[binary]==3.3.8 psycopg-pool==3.3.3
uv pip compile backend/requirements.txt --python-version 3.12 --python-platform x86_64-unknown-linux-gnu --generate-hashes --no-emit-index-url --index-url https://pypi.org/simple --output-file backend/requirements.lock
```

El lock es para Linux. La descarga de verificación usó `pip download --no-deps --only-binary=:all: --require-hashes --platform manylinux_2_28_x86_64 --platform manylinux_2_17_x86_64 --platform manylinux2014_x86_64 --implementation cp --python-version 3.12 --abi cp312 --abi abi3 -r backend/requirements.lock` con destino temporal e índice PyPI. --no-deps evita evaluar marcadores de Windows al descargar todos los paquetes explícitos Linux; el cierre transitivo Linux se verificó separadamente contra METADATA de los 40 wheels, incluyendo extras.

Incidencias de validación, resueltas sin alterar producción: el primer pip download sin --no-deps evaluó un marcador Windows de psycopg y pidió tzdata no incluido en el lock Linux. Era un límite del chequeo cruzado, no un hash ausente del destino Linux; se corrigió el método y se comprobó el cierre Linux. Un precheck con find_spec('supabase') confundió la carpeta SQL supabase/ con un namespace Python; se sustituyó por verificación de distribución instalada. Ninguna de estas comprobaciones fallidas se contabiliza como prueba aprobada de integración.

## Ejecución offline reproducible

Desde la raíz, con el Python del entorno aislado. Equivale a unittest discover -s backend/tests -v, con bloqueos durante discovery, imports y ejecución:

```python
import socket
import unittest
from unittest.mock import patch

original_connect = socket.socket.connect

def offline(sock, address):
    # Windows asyncio puede usar socketpair loopback internamente.
    if isinstance(address, tuple) and address[0] in ("127.0.0.1", "::1"):
        return original_connect(sock, address)
    raise AssertionError("External network forbidden")

with patch("socket.socket.connect", new=offline), patch(
    "socket.socket.connect_ex", side_effect=AssertionError("Network forbidden")
), patch("socket.getaddrinfo", side_effect=AssertionError("DNS forbidden")), patch(
    "dotenv.load_dotenv", side_effect=AssertionError("dotenv forbidden")
), patch("psycopg.AsyncConnection.connect", side_effect=AssertionError("Native PostgreSQL forbidden")):
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.discover("backend/tests")
    )
if not result.wasSuccessful() or result.skipped:
    raise SystemExit(1)
```

El bloqueo de psycopg es esencial: libpq puede abrir sockets sin pasar por socket.connect de Python. Los tests de HTTP sustituyen get_repository; los tests del pool real sustituyen su método de conexión por objetos de protocolo en memoria; el proceso nuevo de import/health tiene también bloqueo nativo. Ninguno intenta alcanzar un servidor PostgreSQL ni requiere PGPASSWORD, SUPABASE_URL o SUPABASE_KEY. No se carga .env.

## Reparto y alcance de las 45 pruebas

- test_backend: 20 previas (dos evaluación/dependencia, seis handlers y doce HTTP).
- test_stabilization: seis previas de alfabeto/Ñ, estados, ausencia y promedio.
- test_postgres_adapter: seis SQL/cursores/UUID/JSONB; seis contratos HTTP; cinco pool/lifecycle; dos import/errores HTTP.

El pool auténtico se prueba con cuatro conexiones simuladas prestadas, una quinta con timeout, devolución/reutilización y cierre. La dependencia se prueba con error y CancelledError; no se afirma rollback real. SQL y parámetros se inspeccionan como argumentos del cursor simulado, no se parsean/ejecutan en PostgreSQL. FastAPI serializa valores nativos sintéticos, no filas recibidas por libpq. El caso de error HTTP usa repositorio/dependencia reales con conexión simulada y verifica 500 genérico sin replay.

## No ejecutado / límites

No se construyó ni ejecutó imagen backend, no se arrancó harness como servidor, no hay test TCP/HTTP contra servicios ni conexión DB, no se ejecutó baseline ni integración SQL del driver. No hay evidencia de autenticación/roles/TLS, atomicidad de intento, carreras de estadísticas, persistencia o rendimiento de PostgreSQL. PG-03/PG-04 deberán cerrar sus respectivos gates con autorización. No se modifica el plan FIN ni se declara FIN-01 terminado.
