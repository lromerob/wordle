# Backend — límites de seguridad vigentes

Actualizado documentalmente en PUB-02, 09/11/2026. FastAPI con PostgreSQL16,
psycopg3 async y pool 0–4 por proceso, no cliente Supabase. Una conexión prestada
por request, SQL parametrizado y cierre por lifespan. No carga automática de
.env, lecturas de secretos privados ni DDL desde workers. Plantilla:
[.env.example](.env.example); configuración Compose distinta en
[../docker/postgres/.env.example](../docker/postgres/.env.example).

## Protecciones existentes y su alcance

- Cinco letras A–Z/Ñ, validación antes de upper(), normalización de espacios
  exteriores/minúsculas y evaluación de letras repetidas en dos pasadas.
- Crear partida devuelve solo ID; GET activo o estado desconocido no revela
  palabra_secreta. GET final ganador/perdedor sí la conserva; POST intento solo
  la devuelve al perder, según el contrato vigente.
- Intento, partida y estadísticas se escriben en una transacción explícita sobre
  la misma conexión. FOR UPDATE serializa intentos de una partida; UNIQUE de
  usuario y lock de estadísticas coordinan su creación/actualización. PG-04
  prueba rollback real y concurrencia mínima, sin simular el motor.
- Rol app separado del inicializador: USAGE de esquema/secuencias y
  SELECT/INSERT/UPDATE de tablas. Ningún permiso de owner se entrega a FastAPI.
  Los errores de driver se traducen a 500 genérico sin DSN/password/SQL crudo.
- /health es proceso, no DB. Readiness Kubernetes PG-06 consulta DB de lectura
  mediante un proceso exec independiente: no certifica todas las escrituras ni
  salud del pool web. No se reintentan automáticamente escrituras/commits.

## Riesgos y garantías que no se ofrecen

- usuario_id lo proporciona el cliente; compararlo con la partida es coherencia,
  NO identidad verificada. Un usuario conocido puede suplantarse; GET/creación/
  stats/ranking no tienen autorización efectiva. No exponer a usuarios no
  confiables sin una decisión explícita de identidad/autorización.
- CORS permite todos los orígenes; no hay rate limiting. El rol app compartido
  no implementa aislamiento por jugador ni se afirma una política RLS efectiva.
- Lecturas independientes pueden observar estados de momentos distintos; una
  desconexión exactamente al COMMIT puede dejar resultado ambiguo. No se han
  demostrado carga, saturación/cancelación real, múltiples workers o Blue-Green.
- La fixture de cinco palabras no es un diccionario completo aprobado. El
  esquema conserva nulabilidad/constraints originales; no promete invariantes
  contra escrituras arbitrarias de un operador con permisos directos.
- Credenciales por entorno son visibles al administrador Docker/Kubernetes.
  Secret local no equivale a cifrado/gestor cloud. PGSSLMODE=disable se limita al
  entorno local aislado; no es una política cloud. Nunca usar passwords de CI
  en otros entornos ni transmitirlos al frontend, build args o Git.
- Inicialización oficial solo en almacenamiento vacío; una interrupción parcial
  requiere diagnóstico sin borrar volumen/PVC. Cambiar Secret/archivo no rota
  automáticamente passwords persistidos. Backup/restore independiente completo,
  HA y supervivencia a pérdida del nodo siguen pendientes.

## Evidencia y material histórico

PG-07 documenta 55 offline y once reales más outage aprobados **localmente**;
no se ha verificado el workflow remoto. Las unitarias usan get_repository y
MemoryDB, no prueban PostgreSQL; PG-04/07 sí usan el motor real. PUBLICAR código
no autoriza exponer la API o desplegar cloud.

El modelo Supabase/RLS allow_all pertenece al prototipo histórico descrito en
[../supabase/README.md](../supabase/README.md); no se ejecuta por Compose, kind o CI
actuales. No reactivarlo como hardening. FIN-01 sigue pendiente y no se introduce
ningún sistema de autenticación nuevo desde PUB-02.
