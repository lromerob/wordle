# PG-06 — Traspaso para revisión y posible PG-07

> PUB-02 (09/11/2026): rutas personales sustituidas por `%LOCALAPPDATA%` y/o `<evidencias-privadas>` cuando existían. Las evidencias siguen fuera de Git; los nombres/UID de recursos de prueba se conservan como trazabilidad, no como requisitos para otro clon. Resultados, fechas, versiones y conteos originales no se actualizan.

Fecha: 09/11/2026. PG-06 preparado para revisión; no constituye autorización para PG-07. FIN-01 continúa pendiente y no se modifica el plan FIN.

## Estado entregado

Perfil PostgreSQL separado en k8s/postgres, heredando frontend/Nginx y controles de seguridad del perfil memoria intacto. FastAPI runtime con psycopg async, una réplica/worker, pool 0–4. PostgreSQL 16.15 StatefulSet una réplica y PVC 2Gi independiente de la aplicación. Roles owner/app separados y Secret efímero nuevo. Inicialización sobre almacenamiento vacío reutiliza baseline y fixture de cinco palabras PG-05, sin SQL nuevo ni migraciones en workers.

Validación real en kind 0.33.0/Kubernetes1.35.0/kubectl1.36.1: frontend/proxy/API, victoria/derrota, stats/ranking y SQL; UI victoria en dos intentos. Cambio de pod PostgreSQL preserva mismo PVC y todas las filas; rollouts app conservan datos. 55 offline +11 integración reales y outage PG-04 aprobados. Kustomize ambos perfiles y dry-run servidor correctos. Detalles e incidencias en PG-06-TEST-RESULTS.md. Sin commit/push.

## Recursos que NO deben eliminarse automáticamente

- Clúster wordle-pg06-00f26f1f, namespace wordle-pg06, StatefulSet postgres, PVC data-postgres-0 (UID d3052f65-80f4-4758-8e42-4b80fbd24a6a, PV homónimo con prefijo pvc-).
- Datos: 5 palabras/3 partidas/9 intentos/3 estadísticas; Secret wordle-db y ConfigMaps, ambos Deployments y tres Services.
- Imágenes locales PG-06; kubeconfig y state.json fuera del repo en %LOCALAPPDATA%/WordlePG06/wordle-pg06-00f26f1f/. No publicar kubeconfig/Secret ni extraerlos a Git.
- PG-05: volumen wordle-pg05-7325afa8cc_postgres_data, imágenes y backup privado de 7924 bytes intactos. No abrir/copiar compose.env.

Acceso de revisión: http://127.0.0.1:18086/ mientras permanezca el port-forward. Para volver a abrirlo usar la kubeconfig privada/contexto kind-wordle-pg06-00f26f1f y Service frontend del namespace wordle-pg06. Ejecutar verify con state propio para comprobaciones de lectura; smoke crea nuevas partidas. Detener solo port-forward no borra datos.

No usar delete -k del overlay como limpieza: incluye Namespace. Antes de borrar clúster/nodo/namespace/PVC, exportar los datos necesarios, comprobar que no haya trabajo adicional y pedir autorización expresa. El almacenamiento local-path no sobrevive a la eliminación de kind. Nunca prune global.

## Decisiones y riesgos pendientes

- Revisar/aceptar esta evidencia antes de PG-07. Un despliegue kind no valida AKS, CSI/discos cloud, autenticación Entra, permisos ni costes.
- Mantener PostgreSQL único y compartido por futuras versiones Blue/Green; no duplicar DB/PVC por color. Antes de promover versiones, acordar compatibilidad de esquema y migraciones forward-only. No implementado aquí.
- Mantener conexión/pool presupuestados por réplica y worker. Readiness añade una conexión independiente; una comprobación de lectura no prueba todas las escrituras ni representa el pool web. /health sigue siendo solo proceso.
- Init oficial solo vacío: si se interrumpe y queda parcial, conservar PVC/Secret y diagnosticar, no borrar para reintentar. Cambiar Secret no rota el password persistido. ConfigMap init es inmutable; futuras migraciones exigen estrategia explícita.
- No existe backup/restore Kubernetes validado ni supervivencia a fallo del nodo. Planificar una prueba autorizada de restauración independiente antes de destruir este entorno.
- usuario_id sigue siendo declarado por cliente, no autenticación efectiva; GET/estadísticas mantienen límites conocidos. No ampliar funcionalidades/autenticación desde esta tarea.
- Cinco palabras son fixture, no fuente definitiva. Solicitar diccionario aprobado/licenciado en su tarea correspondiente.
- Secret local no equivale a cifrado/gestión de secretos cloud; kind estándar no garantiza NetworkPolicy. No se certificó aislamiento egress general. No introducir credenciales Supabase.
- Ingress definitivo, CD, rollback, observabilidad, HA y recursos Azure no se han implementado ni quedan autorizados por este documento.

Esperar revisión y autorización de la tarea siguiente. No realizar commits/push ni declarar FIN-01 completo.
