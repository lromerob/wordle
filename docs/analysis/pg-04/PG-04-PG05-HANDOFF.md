# PG-04 — Traspaso para posible PG-05

Fecha: 09/11/2026. PG-05 no iniciado. FIN-01 no se marca completo ni se modifica el plan FIN-01..FIN-22. Revisar y autorizar antes de continuar.

## Evidencia disponible

PostgreSQL 16.15 real, baseline FIN-01B intacta y catálogo validado. FastAPI/psycopg async funciona sobre DB nueva con rol operativo no superusuario. Once pruebas reales y outage aprobados; 55 pruebas offline preservadas/aprobadas. Rollback del servidor tras tres fallos SQL, bloqueos reales observados entre conexiones y estadísticas concurrentes coherentes en los escenarios académicos ensayados. Build runtime Linux por lock/hashes completado, sin cambiar Dockerfile.

Todos los datos fueron fixtures, sin migrar historia Supabase. Contenedores/redes propios e imagen temporal de build retirados; no se preserva ninguna DB de PG-04. El hecho de eliminar este tmpfs no proporciona evidencia de backup/restore o persistencia con volumen.

## Recomendación

Se recomienda aceptar PG-04 en su alcance local y considerar la autorización de PG-05: Compose con backend, frontend y una instancia PostgreSQL persistente. No se ha preparado ni modificado Compose en esta tarea. La configuración existente de producción todavía declara Supabase y no se presenta como funcional con PostgreSQL por haber validado el driver.

## Alcance propuesto para PG-05, sujeto a autorización

1. Una instancia PG16 con volumen exclusivo, Service privado dentro de Compose y healthcheck. La DB no necesita publicar un puerto del host para funcionar con el backend en otro contenedor.
2. Variables/secretos privados para credenciales DB, rol migrador separado de rol app; sin claves en frontend, imágenes o archivos versionados. Definir política de transporte adecuada al entorno; PG-04 usó sslmode=disable solo en el destino local desechable.
3. Migración inicial aplicada una sola vez a base nueva mediante mecanismo explícito, sin ejecutar CREATE TABLE desde cada web worker. Mantener baseline y sus hashes; no copiar allow_all.sql al flujo PG.
4. Semilla one-shot aprobada. Las cinco palabras de test no sustituyen el diccionario de demostración. Si no se aprueba otra fuente, etiquetar claramente el perfil de fixtures.
5. Comprobar Nginx /api, tráfico real entre contenedores y rol operativo; mantener el modo memoria separado de la integración persistente.
6. Validar primer arranque, segundo sin DDL repetido y recreación/reinicio conservando filas. No borrar un volumen existente para hacer pasar una prueba. Backup/restore y borrados necesitan sus propios gates y autorización.

No implementar Kubernetes/AKS, Terraform, CI nuevo, Blue-Green, observabilidad o CD dentro de PG-05 sin ampliar explícitamente su alcance. No desplegar en cloud ni trasladar datos históricos.

## Limitaciones que no se cierran con PG-04

- Backend/HTTP ejecutado en Windows ASGI con loop Selector, no como servidor TCP Linux dentro de la imagen; el build demuestra construcción/instalación, no todo el runtime desplegado.
- No persistencia después de reiniciar PG, volumen/PVC, backup/restore ni dimensionamiento de disco. PGDATA era tmpfs deliberadamente.
- No pérdida de conexión exactamente en COMMIT, cancelación de transacción real o saturación del pool; no prometer idempotencia ni retries. Se comprobó recuperación después de errores SQL y cierre después de caída.
- Dos requests concurrentes en un proceso con dos conexiones reales, no dos versiones desplegadas ni coordinación Blue-Green completa. Todos los escritores futuros deben mantener el protocolo transaccional/locks PG-03.
- READ COMMITTED verificado; no se prueban otros niveles. Mantener ese supuesto o revisar el tratamiento de SerializationFailure antes de cambiarlo.
- usuario_id no está autenticado y GET/estadísticas no implementan autorización. No presentar la comparación de usuario como control efectivo de identidad.
- Lecturas GET independientes conservan la semántica previa, sin snapshot global bajo carga. No se añaden garantías empresariales al TFG.
- RLS, roles definitivos, gestión de secretos, TLS remoto, diccionario definitivo, observabilidad, backups y evidencias académicas completas siguen sujetos a sus tareas correspondientes. FIN-01 requiere revisión de todos sus criterios antes de cerrarse.

## Reutilización de las pruebas

`backend/integration/run_pg04.py --run-disposable-postgres` sirve para futuras ejecuciones autorizadas/CI: siempre crea un destino propio, admite solo ese host/puerto/base en el driver, instala la baseline y limpia sus recursos. No reutilizarlo como migrador de desarrollo/producción ni añadir una DSN arbitraria. Las pruebas unitarias siguen en backend/tests y no arrancan Docker.

Los hooks de elección de palabra, fallo SQL y pausa tras lock viven exclusivamente en tests. No se añadieron endpoints de depuración ni mecanismos de fallo al runtime. Si el entorno Compose descubre un defecto concreto, informar y aplicar solo la corrección mínima autorizada; un rediseño de persistencia requiere revisión independiente.
