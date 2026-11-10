# FIN-03C — CORS restringido y perímetro de demo

Fecha: 10/11/2026. **FIN-03C PASS**. No se cierra FIN-03 automáticamente ni se inicia la siguiente tarea.

## Preflight y alcance

Rama codex/pg01-07-consolidation, HEAD bb35711a07d19f8944d52c1d5dfa1c9c2a31755b. Índice vacío, sin cambios versionados iniciales y14 informes sin seguimiento. Leídos FIN-03A/B, plan, FastAPI/frontend, Compose, Kubernetes pertinentes y workflow. Los doce informes históricos y ambos informes FIN-03A/B se preservan.

Archivos imprescindibles:

- Modificado backend/app/main.py: lectura/validación de allowlist y CORSMiddleware.
- Modificado backend/.env.example: ejemplo no sensible de la variable.
- Nuevo backend/cors_tests/test_cors.py: nueve casos focalizados.
- Nuevo este informe.

Sin cambio de modelos/routers/evaluador, persistencia, SQL, frontend, Docker, Compose, Kubernetes, Terraform o GitHub Actions. No se instala ninguna dependencia.

## Política anterior y nueva

Anterior: allow_origins/methods/headers con comodines. Nueva:

- Orígenes exactos por defecto: http://localhost:5173 y http://127.0.0.1:5173, usados por Vite en desarrollo nativo.
- WORDLE_CORS_ORIGINS permite sustituir la lista completa por orígenes HTTP(S) separados por coma; espacios exteriores eliminados, duplicados eliminados. Una cadena vacía configura lista vacía: sin permiso cross-origin.
- Se rechazan comodines, esquemas ajenos a HTTP(S), null, paths/barra final, query, fragmentos, userinfo y puertos inválidos mediante fallo de configuración antes de servir. No se configura allow_origin_regex.
- Métodos permitidos para preflight: GET y POST. Headers solicitados configurados: Content-Type; Starlette añade las cabeceras CORS safelisted estándar (Accept, Accept-Language, Content-Language y Content-Type), no autorización arbitraria. No Authorization ni cookies de sesión; allow_credentials=False explícito.
- OPTIONS se procesa como preflight por el middleware; no requiere añadir OPTIONS a la lista de métodos objetivo GET/POST. Restricción CORS no cambia los métodos reales de las rutas ni deniega peticiones directas sin Origin.

Nginx sirve frontend y /api en el mismo origen; no necesita agregar cada puerto loopback del proxy a CORS. Una respuesta same-origin no necesita Access-Control-Allow-Origin para que el frontend lea la respuesta. No se cambia Compose/Kubernetes para transmitir la variable: los valores por defecto cubren desarrollo Vite y el despliegue proxy usa same-origin. Un futuro cross-origin personalizado en Compose/Kubernetes requerirá transmitir explícitamente la variable mediante cambio mínimo autorizado: exportarla solo en el shell del host no la añade a sus environment/env declarados.

## Ajuste para demo

Para backend nativo, definir la variable en el proceso que lo arranca **antes del import de app.main** y reiniciar ese proceso tras cambiarla. El backend no carga automáticamente .env; backend/.env.example es plantilla, no credencial ni mecanismo de carga.

Ejemplo PowerShell, solo terminal de desarrollo:

```powershell
$env:WORDLE_CORS_ORIGINS = 'http://localhost:5173,http://127.0.0.1:5173'
python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --workers 1
```

Usar el lanzador/loop compatible con psycopg en Windows si se ejecuta con PostgreSQL real; FIN-02B ya documenta SelectorEventLoop. El ejemplo muestra la configuración CORS, no autoriza arrancar una base existente. Para otra URL, introducir solo su origen exacto scheme://host[:port], sin barra/path; cambiar host o puerto Vite requiere ajustar allowlist explícitamente. No usar credenciales ni tokens como orígenes. El valor vacío deshabilita acceso cross-origin, no peticiones same-origin o clientes directos.

## Pruebas ejecutadas y reproducibilidad

1. Wrapper exacto del job backend-tests existente, extraído sin editar workflow: **55 offline aprobadas, cero omitidas,1.233s**, con DNS/sockets externos/dotenv/libpq bloqueados.
2. Suite nueva unittest con el mismo bloqueo global: **9 aprobadas, cero omitidas,0.038s**. Usa get_repository sustituible y MemoryDB existente; no prueba SQL ni se presenta como PostgreSQL real.
3. run_pg04.py --run-disposable-postgres: **11 pruebas PostgreSQL16.15 aprobadas, cero omitidas,1.096s**; rollback/locks/tipos/contratos. Outage real adicional:500 genérico,/health200,pool cerrado; limpieza de contenedor wordle-pg04-7d604562fdff y red propia confirmada. No se tocaron PG-05/06.
4. HTTP TCP real en subproceso Uvicorn loopback con MemoryDB existente, libpq/DNS/conexiones externas bloqueados. WORDLE_CORS_ORIGINS solo http://127.0.0.1:5173 para demostrar sustitución por entorno, no acumulación de defaults. Sin PostgreSQL ni passwords en ese subproceso. Backend temporal detenido al terminar.

La suite nueva está fuera de backend/tests porque el workflow actual exige exactamente55 casos. Se conserva el comportamiento de CI y se documenta esta limitación: **los nueve casos CORS no se ejecutan automáticamente en ese job**; integrarlos en CI y actualizar su recuento requiere una tarea posterior autorizada, no alterar Actions aquí.

Comandos de regresión desde raíz, entorno existente y lista por defecto para la suite CORS:

```powershell
$env:WORDLE_CORS_ORIGINS = 'http://localhost:5173,http://127.0.0.1:5173'
python -B -m unittest discover -s backend/cors_tests -v
python -B -m unittest discover -s backend/tests -v
python -B backend/integration/run_pg04.py --run-disposable-postgres
```

El discovery simple de unitarias no equivale por sí mismo al wrapper de aislamiento global usado en esta validación; los fixtures HTTP bloquean DB, y la validación ejecutada añadió además las guardas globales durante imports. El runner real crea su propio PG autorizado y no acepta un DSN arbitrario. No sumar la suite en memoria y la real como casos únicos equivalentes.

| Caso | Resultado observado |
|---|---|
| GET permitido por defecto, localhost y127.0.0.1:5173 |200, ACAO exacto y Vary:Origin, sin Access-Control-Allow-Credentials |
| GET de origen no permitido |200 sin ACAO: **no concede permiso de lectura al navegador**, tampoco garantiza que no se procese la petición |
| OPTIONS permitido POST/content-type |200, ACAO exacto, métodos GET/POST y Content-Type admitidos |
| OPTIONS origen no permitido |400 sin ACAO |
| OPTIONS DELETE o header x-unneeded |400; no se autoriza ese método/header, aunque el origen válido pueda reflejarse en la respuesta de error |
| Sin Origin |/health200 sin ACAO; contrato intacto |
| Flujo de juego con Origin permitido |Creación200 y victoria200 con cabeceras correctas; probado en suite y por TCP |
| Override por entorno |TCP:127.0.0.1:5173 admitido; localhost:5173 deja de estar permitido al no figurar en la lista configurada |
| Lista vacía y configuración inválida |Parser devuelve[] para vacío y rechaza valores inválidos/comodines mediante ValueError; validado por unitarias |
| Regresiones |55 offline y11 reales sin fallos ni omisiones |

No se automatizó un navegador físico: se verificaron respuestas/preflight por TestClient y HTTP TCP real. La aplicación del bloqueo de lectura al navegador es la semántica CORS, no una prueba de autenticación o filtrado de red. No se reconstruyó Compose/kind en FIN-03C; su topología no cambió y conserva evidencia FIN-03B. El smoke TCP CORS usa memoria, mientras la suite11 sí usa el motor real.

## Perímetro y riesgos residuales

Uso permitido como propuesta: demo privada y supervisada, host/clúster propios, navegador de operador confiable, DB de datos exclusivamente sintéticos, sin usuarios reales ni passwords personales. Frontend local, backend solo dentro del perímetro y PostgreSQL sin exposición pública. No abrir túneles públicos/puertos0.0.0.0 ni interpretar publicación de código como autorización de despliegue. No apto para producción por este cambio.

**Persisten** lectura cruzada de partidas/estadísticas, suplantación mediante usuario_id y ausencia de autenticación/autorización robustas. FIN-03B las demostró y no se intentan ocultar con CORS. Un cliente no navegador o una petición sin Origin puede seguir usando la API dentro del perímetro; una petición simple puede producir efectos aunque el navegador no permita leer su respuesta. No se promete protección CSRF por limitar ACAO. El rol PostgreSQL app tampoco identifica al jugador.

Los logs pueden contener IDs sintéticos; no se añaden credenciales o valores sensibles a logs. Se preserva la regla de no exportar logs crudos/Secrets/config expandida y de no usar datos personales. Esta tarea no implementa redacción global de logs, seguridad de producción, rate limiting o RLS por usuario.

## Recomendación de cierre y estado

La brecha CORS de FIN-03B queda corregida y validada en el alcance descrito. **Se recomienda revisar FIN-03 para cierre únicamente con aceptación expresa del responsable del perímetro de operador único y de los riesgos multiusuario.** No se cambia su estado ni se afirma que el requisito de negativos de acceso ajeno demuestre denegación inexistente. Si se exige privacidad entre jugadores, el cierre requiere otro alcance autorizado.

No se realizan commits/push/PR, publicación GHCR, Azure/Supabase, cambios a CI/esquema ni a PG-05/06. Fuera de los dos archivos versionados de CORS/plantilla, archivos previos y14 informes sin seguimiento preservados. Nuevos test/informe locales sin seguimiento; índice vacío. Sintaxis y git diff --check correctos; cambios limitados a configuración, pruebas y documentación CORS.
