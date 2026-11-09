# PG-05 — Resultados verificables

> PUB-02 (09/11/2026): rutas personales sustituidas por `%LOCALAPPDATA%` y/o `<evidencias-privadas>` cuando existían. Las evidencias siguen fuera de Git; los nombres/UID de recursos de prueba se conservan como trazabilidad, no como requisitos para otro clon. Resultados, fechas, versiones y conteos originales no se actualizan.

Fecha: 09/11/2026. Docker Engine 29.9.2, Compose 5.6.1, PostgreSQL 16.15. Proyecto exclusivo wordle-pg05-7325afa8cc; no se reutilizaron volúmenes/DB existentes ni servicios Supabase/Azure.

## Ejecuciones y resultados

| Escenario | Resultado real |
|---|---|
| Compose build | Backend y frontend construidos correctamente con sus Dockerfiles existentes; imágenes locales del proyecto. Frontend npm ci/build ejecutados por su Dockerfile o reutilizados de caché válida; assets Vite servidos correctamente. |
| Arranque limpio | Volumen previamente inexistente, baseline original aplicada, cinco palabras cargadas y rol app creado. Tres servicios healthy. |
| Conectividad Windows | Frontend http://127.0.0.1:32768/ y /api/health 200 inicialmente. Tras recreación, puerto 32771 y consultas /api correctas. |
| Seguridad de red | postgres/backend sin PortBindings; una red internal:true para datos; solo Nginx añade ingress y publica loopback. No URLs Docker internas en el navegador. |
| Smoke API real | Nueva partida, palabra inválida 400 sin consumo, victoria de un intento, derrota de seis, GET, estadísticas y ranking; PostgreSQL consistente. |
| UI React real | Inicio, palabra incompleta, ZZZZZ inválida, teclado físico/virtual, amarillo/verde/gris, victoria en dos intentos, nueva partida y derrota en seis. |
| Rol/esquema | Catálogo FIN-01B PASS; app wordle_app no superusuario. No cambios de esquema ni baseline. |
| Restart | Snapshot completo de las cuatro tablas idéntico antes y después. |
| Down/up | Contenedores/redes recreados sobre el mismo volumen; snapshot idéntico; GET de partidas y stats coincide por /api. |
| Segundo arranque | Logs indican Skipping initialization; sin ejecución del esquema, duplicado de palabras ni reinicio de estadísticas. |
| Exportación/restauración | pg_dump custom sin owner/ACL, pg_restore a DB nueva auxiliar, tablas idénticas, origen intacto; DB auxiliar eliminada. Backup de 7924 bytes conservado fuera del repo. |
| Regresión offline | **55 tests aprobados, cero omitidos; 1.415 s**, DNS/sockets externos/.env/libpq bloqueados durante imports/ejecución. |
| Integración PG-04 reutilizada | **11 tests reales aprobados, cero omitidos; 1.811 s**, más outage real aprobado. Otro contenedor/tmpfs/red exclusivos, eliminados al finalizar. |
| Configuración Compose | Base y override memory config --quiet correctos. JSON de plantilla: solo backend/frontend activos en memoria, sin credenciales/dependencia DB y target memory-test. |
| Logs | postgres/backend/frontend revisados sin volcar valores privados; sin traceback Python o deadlock. No se observaron incompatibilidades de aplicación. |
| Assets públicos | Sin nombres de variables de credencial PGPASSWORD/WORDLE_DB_PASSWORD/SUPABASE_KEY en assets Nginx; ninguna credencial enviada como VITE_/build arg. |
| Cierre | down sin -v retira contenedores/redes del proyecto; volumen propio conservado, sin tocar recursos ajenos. |

Snapshots de persistencia comparados por valores de todas las filas ordenadas por id, no únicamente por counts: **5 palabras, 4 partidas, 15 intentos y 3 filas stats**. Incluyen las partidas de API y las de navegador; los rechazos no consumieron intento.

## Evidencia visual

Browser automatizado disponible. La victoria mostró CASAS como primer intento con amarillos/verdes y SACAS correcto al segundo. Otra partida terminó perdida tras seis PERRO, mostrando GATOS únicamente al finalizar. No se cambia el random de producción; el smoke API observa la solución de sus fixtures por SQL para preparar entradas deterministas. La UI ganó mediante sus pistas; para asegurar la derrota se eligió por lectura SQL una palabra válida diferente en el destino de pruebas.

Capturas fuera del repositorio:

- <evidencias-privadas>/pg05-ui-win.png
- <evidencias-privadas>/pg05-ui-loss.png

Una tanda larga de clicks alcanzó el timeout de la herramienta; se recuperó el estado visible, que estaba en el sexto intento con PE escrito, y se completó RRO una sola vez. No fue un timeout de FastAPI ni se repitieron intentos confirmados. La derrota final y el recuento de seis quedaron verificados.

## Incidencias y cambios mínimos

- Compose anterior seguía usando Supabase; se sustituyó solo su configuración por PG y un servicio persistente. Ningún cambio de lógica backend.
- El override de memoria heredaría postgres/credenciales/dependencia del nuevo base: se desactiva postgres por perfil y se usa !reset. Una comprobación auxiliar inicialmente esperaba ver el servicio de perfil inactivo en el JSON; Compose lo omite por defecto. Se corrigió la aserción para comprobar precisamente su ausencia. Las validaciones Compose reales no fallaron.
- LF en scripts fijado mediante .gitattributes local a docker/postgres para checkout Windows. La plantilla .env.example no queda ignorada por Git; las contraseñas reales se crean fuera del repo.
- No se detectó incompatibilidad de Nginx, driver o contratos que requiriera tocar aplicación, frontend o Dockerfiles.

## Reproducción y controles

Los comandos por etapas están en el informe de implementación. Las unitarias usan el wrapper offline de PG-04/PG-03; las reales se repiten con `python -B backend/integration/run_pg04.py --run-disposable-postgres`, cuyo aislamiento no comparte datos con PG-05.

El ejecutor PG-05 start comprueba ausencia del volumen antes de crear nada; las etapas siguientes validan etiqueta de proyecto del volumen antes de operar. Sus secretos se generan fuera del repo, nunca se imprimen ni se incluye config expandida en informes. stop no contiene una operación de eliminación de volumen.

Controles finales: compile() sin bytecode para el nuevo validador; git diff --check y whitespace; hashes de archivos históricos/SQL/app/infra; patrones de secretos sobre los candidatos y plantilla sin contraseñas. Los resultados concretos se incorporan al cierre antes de entregar.

## Límites

No se prueba backup empresarial, restauración de roles/permisos en un clúster nuevo, tolerancia a fallos o borrado de volumen. La demostración restaura tablas en DB nueva del mismo PG con admin y sin owner/ACL, no arranca la app sobre ese restore. No se prueba aún Kubernetes/PVC, Blue-Green, observabilidad, cloud o CI. El modo memoria se validó estáticamente y con las unitarias, no se levantó su Compose aquí.

usuario_id sigue sin autenticación; fixture de cinco palabras no es diccionario definitivo. Versiones de imagen por tag pueden moverse; las versiones reales de esta ejecución se documentan, sin prometer futura identidad de digest. El volumen y la copia local deben protegerse/mantenerse por su propietario. FIN-01 continúa pendiente.

Cierre ejecutado: únicamente compose.yaml y compose.test.yaml cambiaron frente al estado de entrada; todos los archivos previos restantes permanecen idénticos byte a byte. Diez archivos nuevos PG-05. Sintaxis del nuevo validador, whitespace, LF de scripts y patrones acotados de secretos: correctos, sin hallazgos; contraseñas vacías en plantilla. git diff --check correcto e índice vacío. Sin commit/push. Consultas finales por etiquetas: cero contenedores y redes PG-05; volumen wordle-pg05-7325afa8cc_postgres_data presente y con procedencia del proyecto verificada. No se abrió el archivo privado de credenciales.
