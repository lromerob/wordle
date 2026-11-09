# PG-05 — Traspaso para posible PG-06

> PUB-02 (09/11/2026): rutas personales sustituidas por `%LOCALAPPDATA%` y/o `<evidencias-privadas>` cuando existían. Las evidencias siguen fuera de Git; los nombres/UID de recursos de prueba se conservan como trazabilidad, no como requisitos para otro clon. Resultados, fechas, versiones y conteos originales no se actualizan.

Fecha: 09/11/2026. PG-06 no iniciado. No se cambian Kubernetes, Terraform, CI/CD o el plan FIN; FIN-01 no se declara completo.

## Estado entregado

Compose de tres servicios validado desde volumen vacío, PostgreSQL 16.15, baseline FIN-01B y fixture mínima. FastAPI Linux usa psycopg async/pool 0–4 sobre postgres:5432 con rol app separado del inicializador. Solo Nginx expone loopback y realiza proxy /api. El frontend/Nginx no necesitaron cambios.

Restart y recreación completa de contenedores mantuvieron idénticas las cuatro tablas. No se repitieron init scripts, seed ni creación de rol. Partidas y estadísticas de API/UI persistieron. 55 pruebas offline y 11 reales PG-04 aprobadas, además de smoke/UI/persistencia/restore y outage reutilizado. Sin commits/push.

Contenedores/redes PG-05 ya retirados. Se conserva expresamente wordle-pg05-7325afa8cc_postgres_data (~62.4 MiB asignados en PGDATA), imágenes locales y carpeta privada %LOCALAPPDATA%/WordlePG05/wordle-pg05-7325afa8cc/ con state.json, compose.env y pg05-demo.dump. No se han mostrado contraseñas ni se debe borrar el volumen como parte de PG-06.

## Recomendación

Tras revisar/aceptar PG-05, puede autorizarse PG-06 para un perfil Kubernetes de PostgreSQL compartido. Mantener el perfil memoria existente como tal. La validación Compose no demuestra todavía PVC, CSI, secretos Kubernetes o persistencia en AKS.

## Diseño a tratar en PG-06, no implementado

- Una instancia PostgreSQL mediante StatefulSet de una réplica, PVC y Service interno, fuera de colores Blue/Green. Sin replicación ni operador.
- Backend conecta al Service PG con el mismo protocolo transaccional/locks; nunca publicar DB mediante Ingress/LoadBalancer ni poner credenciales en VITE_.
- Inicialización única/serial sobre almacenamiento nuevo y verificación explícita de readiness. No copiar indiscriminadamente docker-entrypoint-initdb.d a un volumen que ya tenga datos ni aplicar CREATE TABLE desde workers web.
- Rol migrador/operativo, Secret y permisos/grants reproducibles. No copiar el archivo compose.env ni sus valores al repositorio; decidir provisión/autorización de secretos en la tarea correspondiente.
- Fuente de diccionario completa sigue pendiente; etiquetar este seed como fixture. No sumar palabras sin procedencia/licencia aprobada.
- Ensayo local autorizado con recreación de pod conservando filas, readiness/liveness, requests/limits y política de retención/limpieza del PVC. No borrar namespaces/PVC/volúmenes existentes para obtener un arranque limpio.
- Presupuesto de conexiones por worker/réplica y capacidad de disco/RAM. Una DB y Blue+Green futuros comparten estado; no duplicar base/PVC por versión ni implementar conmutación todavía.

## Recuperación y cuestiones pendientes

El pg_dump/pg_restore básico ha demostrado igualdad de tablas en una base nueva auxiliar, origen intacto y limpieza del destino de ensayo. --no-owner/--no-acl no conserva roles/passwords/grants; no demuestra recuperación completa sobre un clúster independiente. Ampliar en PG-08 con rol operativo, API y procedimiento autorizado, manteniendo copia fuera del entorno que se vaya a destruir.

La inicialización oficial solo actúa con PGDATA vacío. Una interrupción de primera inicialización no se autocorrige como si hubiese un historial de migraciones: preservar datos, diagnosticar y acordar recuperación; no limpiar el volumen automáticamente. Cambios futuros de esquema necesitarán un mecanismo forward-only explícito antes de promover versiones incompatibles.

Persisten límites de identidad usuario_id, autorización de GET, lecturas independientes, pérdida de conexión exactamente al COMMIT, cancelación/saturación real y despliegue multiproceso/Blue-Green. No se incorporaron funcionalidades empresariales ni servicios extra para ocultarlos. El alcance sigue siendo una demostración DevOps académica.

Esperar autorización para cualquier ejecución Kubernetes o nueva infraestructura. No iniciar PG-06, cloud, publicación de imágenes ni cierre FIN-01 por este documento.
