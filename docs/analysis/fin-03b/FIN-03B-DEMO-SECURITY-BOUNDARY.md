# FIN-03B — Perímetro de seguridad de demo y negativos

Fecha: 10/11/2026. **FIN-03B PASS** en el sentido de revisión/perímetro documentado y pruebas locales previstas ejecutadas con resultados explícitos. **No significa que todos los controles de seguridad pasen: se confirman fallos de aislamiento por jugador y CORS abierto. FIN-03 permanece pendiente.** No se implementa FIN-03C.

## 1. Preflight y criterios originales

Rama codex/pg01-07-consolidation, HEAD bb35711a07d19f8944d52c1d5dfa1c9c2a31755b, índice vacío, ningún cambio versionado y trece informes sin seguimiento. Leídos plan FIN, FIN-03A, README, Compose, Kubernetes/FastAPI y workflow; no consultas Azure/Supabase ni a recursos PG-05/06.

`TFG-COMPLETION-PLAN.md:86-94`: decidir identidad/propiedad, RLS/alcance de credencial; probar restricciones/concurrencia; no añadir login nuevo sin aprobación. Aceptación: decisión revisada/firmada, negativos de lectura/escritura ajena, ninguna garantía falsa basada en usuario_id y exposición limitada. Evidencias: ADR/matriz/pruebas sanitizadas. La arquitectura PG directa sustituyó la dependencia operativa Supabase, no creó identidad de jugador. FIN-01/02 completados; sus pruebas de locks/rollback y recuperación no equivalen a autorización.

## 2. Propuesta técnica de perímetro, pendiente de aceptación

Se propone una demostración **privada, supervisada por un operador confiable**, sobre máquina y motor Docker propios, navegador controlado, exclusivamente usuarios/UUID sintéticos, DB de prueba separada y passwords efímeros no personales. Frontend solo loopback; backend y PostgreSQL sin publicación al host; nadie no confiable comparte host, redes/pods, acceso Docker o kubeconfig. No abrir port-forward0.0.0.0, túneles públicos, Ingress o puertos de datos. No presentar esta modalidad como servicio multiusuario o producción.

La configuración actual permite montar ese perímetro de red en Compose: probado realmente en un proyecto nuevo. Kubernetes declara ClusterIP y acceso frontend mediante túnel loopback; no se ha levantado ni probado otro clúster en FIN-03B. Un ClusterIP no bloquea otros pods y kind no acredita enforcement de NetworkPolicy: para esta propuesta el clúster debe ser dedicado y confiable. Terraform/AKS son diseños futuros; no validación cloud.

**Aprobación técnica como propuesta dentro de este análisis; aceptación formal del responsable aún pendiente.** Debe aceptarse expresamente que cualquier cliente dentro del perímetro puede acceder a datos de otros identificadores o suplantarlos. Si se requiere participación de jugadores no confiables, la propuesta no satisface el objetivo y debe replantearse con autorización adicional. Una red privada no sustituye autorización individual.

La propuesta no garantiza por sí sola que cualquier página del navegador sea confiable: CORS abierto permite un origen arbitrario que alcance la API. Esa brecha queda confirmada abajo y se propone restringirla antes del cierre; la allowlist tampoco sustituirá identidad/CSRF o control de clientes fuera del navegador.

## 3. Matriz de acceso

| Flujo | Técnicamente posible | Permitido por perímetro propuesto | Control existente / evidencia | Riesgo residual | Resultado esperado y observado |
|---|---|---|---|---|---|
| Navegador→frontend | Sí en loopback | Operador local supervisado | Compose publica solo127.0.0.1; GET /200 real | Otro proceso local confiable comparte acceso; no hay login |200 para operador, observado; no se afirma bloqueo por identidad |
| Frontend→backend | Sí, /api por Nginx y red interna | Sí | Proxy y servicio interno, GET /api/health200 | Todo cliente de frontend puede usar /api | Proxy funcional observado; ocultar puerto backend no limita sus rutas vía frontend |
| Backend→PostgreSQL | Sí, credencial técnica app | Sí dentro de red de datos | Rol app separado, PGUSER/PGPASSWORD, SQL parametrizado | Rol compartido no aísla jugadores, administrador Docker controla datos | Lecturas/escrituras reales correctas |
| Cliente externo no autorizado→backend directo | No por puerto publicado en host; desde red Docker ajena bloqueado en ensayo | No | Backend sin PortBindings y red interna; probe externo independiente | Vía frontend puede acceder cualquier cliente que alcance el loopback/perímetro; otros pods/operadores no probados | Conexión TCP desde otra red sin éxito, observado; no401/403 inventado |
| Cliente externo→PostgreSQL | No por puerto publicado y desde red Docker ajena en ensayo | No | PG sin PortBindings, red interna | Host administrador y clientes dentro de red interna siguen siendo confiables | Conexión TCP5432 desde red ajena sin éxito; sin prueba física desde otra máquina LAN |
| Jugador A→partida B, lectura | Sí si conoce UUID; no token requerido | Identificadores sintéticos dentro de demo de operador, sin privacidad por jugador; prohibido atribuir aislamiento | GET filtra solución activa, no propietario | IDOR/lectura cruzada confirmada; UUID no es permiso |200 observado sin credencial, usuario ajeno visible; **control de autorización ausente**, no PASS de seguridad |
| Jugador A→partida B, escritura | Con A distinto de propietario,403; usando usuario_id de B, sí | Solo simulación sintética supervisada; sin garantía de identidad | Comparación de string game.py:74-76 | Suplantación confirmada |403/sin intentos con string distinto;200 y escritura con string de propietario suplantado. Este segundo resultado es **brecha**, no control exitoso |
| Jugador A→estadísticas B | Sí por ruta y ranking | Datos sintéticos de demo sin privacidad individual | Sin autorización en stats.py | Lectura cruzada y agregación de IDs visible |200 observado; no debe esperarse401/403 inexistente |
| Salud | Sí por frontend; backend directo solo interno | Operador/sondas del perímetro | /health sin datos y /healthz Nginx | Liveness200 no prueba DB | /api/health200 incluso al detener PG propio, observado |

## 4. Pruebas reales ejecutadas

Proyecto exclusivo **wordle-fin03b-168318a02d**, comprobado ausente antes del arranque y volumen nuevo. Se usó compose.yaml existente sin editarlo, con --env-file docker/postgres/.env.example y variables del proceso: nombre nuevo, puerto frontend0, DB/roles de prueba y dos passwords aleatorios distintos. Se construyeron Dockerfiles existentes y se arrancó con up --detach --wait. No se usaron los nombres/state/env/volúmenes persistentes PG-05/06.

Tres servicios healthy comprobados por inspect de campos concretos, sin Config.Env; red de datos internal:true. Backend/PG sin PortBindings; solo Nginx loopback, dirección asignada http://127.0.0.1:32774. Peticiones HTTP TCP desde Windows con urllib y proxies desactivados a /api, no TestClient ni mocks. Origen `https://untrusted.invalid` solo se envió como header; nunca se contactó ese dominio.

| Caso | Esperado como comprobación de control | Resultado observado | Evaluación |
|---|---|---|---|
| Crear partida sintética |200, sin solución en creación |200, UUID bd2d71c1-6129-4d55-b99d-c64a93ada6c5 | Funcional, no autenticación |
| AB,12345,ZZZZZ |400, cero filas de intentos | Tres400 y SQL count intentos0 | Control de validación PASS |
| UUID válido inexistente, GET y POST intento |404/sin writes |404/404; contador de intentos seguía0 | Control de existencia PASS |
| Usuario B distinto en intento de A |403/sin writes |403; SQL count intentos0 | Coherencia PASS, identidad no demostrada |
| GET partida de A como cliente sin identidad |Denegación si existiera privacidad por jugador |200, devuelve usuario de A; oculta solución activa | Privacidad individual **NO IMPLEMENTADA** |
| Cliente B declara usuario_id de A al intentar |Debería denegarse si existiera identidad verificable |200, se crea un intento; luego se completa la partida sintética si hace falta | Suplantación **CONFIRMADA**, no PASS de autorización |
| GET estadísticas de A sin credencial |Denegación si existiera privacidad |200, jugadas1 tras finalizar juego | Lectura cruzada **CONFIRMADA** |
| UUID malformado |Error sanitizado según contrato actual |500/detail Base de datos no disponible | Error sin detalles internos PASS; no se cambia el contrato a400 |
| CORS GET salud y stats con origen no confiable |Un origen fuera de allowlist debería carecer de ACAO permisivo en una demo restringida |200 y Access-Control-Allow-Origin:*; stats legibles | CORS restringido **NO CUMPLIDO** |
| CORS preflight POST intento |Origen no permitido debería rechazarse/no autorizarse |OPTIONS200 y ACAO:* para métodoPOST/header content-type | CORS abierto **CONFIRMADO** |
| Contenedor en otra red→IP interna backend8000/PG5432 |No conectar |Dos sockets con timeout2s sin conexión; probe termina correctamente comprobando ambos bloqueos | Separación entre las redes Docker del ensayo PASS |
| Detener únicamente PG propio y crear partida |500 sanitizado; salud sigue200 |500/detail genérico, /api/health200 | Manejo de fallo DB PASS |
| Logs/respuestas y passwords efímeros |No divulgar valores |Búsqueda local de ambos passwords generados: sin coincidencias en logs; respuestas verificadas no contienen credenciales y errores iguales al payload genérico | Resultado acotado, no certificación de todo historial/sistema |

El probe de red fue otro contenedor propio en red wordle-fin03b-168318a02d-outside, con Python del runtime recién construido y sin credenciales. Usó las dos IP exactas del entorno propio, no escaneo de red. No tiene publicación/privilegios/host network. Un timeout no es evidencia universal de firewall; unido a PortBindings vacíos y red separada demuestra solo el escenario probado. No se probó desde otra máquina física ni se tocó configuración Windows/firewall. No se promete aislamiento frente a administrador, otro pod interno o host comprometido.

Logs de los contenedores del proyecto se examinaron en memoria, sin volcarlos al informe ni imprimir valores. **Los IDs sintéticos sí aparecen en access logs**: no existe redacción general. No se cargaron credenciales personales/reales; comprobar los passwords de prueba no permite certificar que un despliegue productivo nunca filtre secretos. No hubo payloads con contraseñas en URL. La salud de DB no se deduce de /health.

## 5. Riesgos residuales y correcciones mínimas propuestas

| Prioridad | Corrección/decisión mínima pendiente | Criterio verificable posterior |
|---|---|---|
|1 | Ratificar por responsable demo privada de un operador/datos sintéticos y acceso solo loopback; mantener PG/backend sin puertos y clúster confiable. No hace falta cambiar la topología Compose ensayada | ADR aceptado, matriz de este informe y comprobación de los bindings del entorno que se vaya a mostrar; no afirmar denegación entre jugadores |
|2 | Autorizar allowlist CORS configurable para orígenes concretos de demo/desarrollo y pruebas positivas/negativas, manteniendo same-origin /api. No implementar ahora | Origen permitido funciona; origen no permitido no obtiene cabeceras permisivas/preflight de autorización. Clientes no navegador siguen dentro del modelo de confianza |
|3 | Mantener exclusivamente IDs/datos sintéticos en logs y no exportar raw logs/inspect/Secrets; si se comparten logs, autorizar redacción de query/path identificadores y notas de seguridad actualizadas | Comprobación de logs/respuestas con credenciales efímeras y payloads sintéticos sin divulgación, sin presentar un scan como garantía absoluta |
|4 | Documentar de forma vigente el acceso cruzado y la distinción health/DB, y la aceptación del riesgo del mismo usuario_id declarado | No usar «propietario autenticado», «partida privada» o «RLS por jugador» donde solo hay coherencia de string |

No se propone OAuth/JWT/cuentas, roles complejos, WAF, gestor cloud o infraestructura adicional. Si el responsable exige aislamiento real entre jugadores, los controles actuales no sirven y el alcance requerirá autorización nueva; no lo sustituye un token compartido ni CORS. Rate limiting y TLS público son decisiones futuras de exposición, no obligación automática para un operador local con datos sintéticos.

CI sigue con contents:read, publicación GHCR if:false y Terraform solo validaciones. La advertencia Node20/24 de PUB-06 permanece mantenimiento, sin vulnerabilidad confirmada; no hubo cambios/workflows nuevos en FIN-03B.

## 6. Criterios para cerrar FIN-03

1. Responsable acepta explícitamente la propuesta y el significado limitado de los negativos de acceso ajeno: se **demuestra su posibilidad y se acepta solo dentro del perímetro sintético**, no se certifica una denegación que no existe. Si el criterio original requiere denegar entre jugadores, FIN-03 no puede cerrarse bajo esta propuesta.
2. Resolver o aceptar expresamente el riesgo CORS con evidencia apropiada; recomendación: corrección mínima de allowlist bajo autorización separada antes del cierre. No elevar un CORS200 inseguro a PASS de seguridad por coincidir con código.
3. Mantener evidencia de exposición y matriz/roles/logs limitada al escenario real mostrado; notas de seguridad no deben seguir atribuyendo estados antiguos a FIN-01/02 o CI.
4. Conservar los negativos actuales con sus resultados verdaderos y referenciar las pruebas previas de transacciones/concurrencia; no repetir suites por defecto.

**FIN-03B PASS** acredita que la propuesta y los negativos previstos quedaron documentados y ejecutados. **FIN-03 no está completado ni listo para aprobar seguridad multiusuario.** El permiso formal y las correcciones mínimas anteriores siguen pendientes. No se inicia FIN-03C.

## 7. Reproducción, limpieza y Git

La prueba fue un harness inline temporal, no una modificación de scripts del proyecto. Secuencia repetible bajo nueva autorización: nombre/proyecto aleatorio ausente → secretos aleatorios solo por entorno → docker compose --env-file docker/postgres/.env.example --project-name <nuevo> -f compose.yaml config --quiet/build/up --wait → identificar frontend con compose port → peticiones HTTP anteriores y SQL count en postgres propio → probe en red nueva separada → detener PG del proyecto y comprobar fallo → revisar logs en memoria → retirar únicamente IDs/proyecto propios. No ejecutar esta secuencia sobre nombres persistentes conocidos.

Se ejecutó down --volumes solo para el proyecto nuevo cuyo volumen se comprobó ausente inicialmente y cuyos contenedores se verificaron por etiqueta; no es una instrucción de limpieza de PG-05/06. Contenedores, probe, redes y volumen propios eliminados; ausencia final de contenedores/redes/volumen confirmada. Se conservaron únicamente dos tags locales nuevos wordle-fin03b-168318a02d-backend:v1-local y wordle-fin03b-168318a02d-frontend:v1-local; no publicación, prune ni borrado de imágenes ajenas. No credenciales guardadas en archivos de proyecto, no entorno Compose privado previo leído.

Único archivo creado: este informe, sin seguimiento. HEAD/refs/índice y todos los archivos previos conservados; doce informes históricos y FIN-03A intactos byte a byte. Sin cambios de código/configuración, commits, push, merge/rebase, despliegue Azure, Supabase ni operaciones sobre PG-05/PG-06. No se repitieron las55/11 pruebas como parte de esta revisión; se realizaron los casos focalizados descritos.
