# PG-01 - Decisión de transición a PostgreSQL

Fecha: 08/11/2026. Documento de decisión y gates para revisión. No se modifica código, SQL, configuración ni plan FIN. [Contrato HTTP](PG-01-HTTP-CONTRACT.md) y [aceptación](PG-01-PG02-ACCEPTANCE.md).

## 1. Decisiones aprobadas por el propietario

- PostgreSQL 16 directo mediante psycopg 3 async y pool acotado como arquitectura objetivo.
- Una instancia PostgreSQL, sin replicación, HA u operador.
- Compose para desarrollo local y StatefulSet de una réplica con PVC en Kubernetes/AKS.
- Sin dependencia operativa futura de Supabase ni PostgREST para ejecutar Wordle.
- Base nueva: NO se migran partidas, estadísticas ni otros datos históricos de Supabase.
- No doble escritura ni sincronización entre las dos bases.
- Blue-Green solo para aplicación; dos versiones compatibles PG comparten la misma instancia/esquema.
- FIN-01 continúa pendiente. PG-01 no autoriza instalar, arrancar runtime o implementar PG-02.

Estas decisiones fijan objetivo, no describen un runtime ya existente. El backend actual sigue utilizando Supabase. La estructura SQL ya se probó en dos bases PG16 nuevas, no mediante el driver futuro; [FIN-01B](../fin-01b/FIN-01B-POSTGRES-VALIDATION.md) mantiene sus límites y procedencia.

## 2. Qué se conserva y qué cambia

Se mantienen frontend/proxy, cinco endpoints de datos más /health, cuerpos/códigos/errores controlados y reglas detalladas en el contrato. La evaluación de letras no cambia. No se añaden funcionalidades del juego, login, restricciones de esquema ni políticas de seguridad de usuarios.

Cambia únicamente la forma de persistir y su operación: cliente HTTP Supabase -> psycopg async/SQL parametrizado; IDs/datos con mapeo compatible; configuración de conexión privada; conexiones/transacciones y, en incrementos posteriores, contenedores/volumen/PVC y gates de CI. SQLAlchemy/ORM no forman parte de la decisión aprobada. No se crea un clon genérico de la API fluent del SDK como intermediario.

La baseline [initial_wordle.sql](../../../supabase/migrations/20261108000100_initial_wordle.sql) se reutiliza sin modificar. La ubicación supabase/ es histórica y no obliga al servicio. No duplicar/mover el baseline en PG-02 como cambio incidental. prototype/allow_all.sql reproduce un modelo Supabase opcional, no se aplica automáticamente a PG directo ni se recrean roles anon/authenticated/service_role sin una razón aprobada.

Los datos nuevos de demostración se generan desde fuente aprobada. El diccionario real no está disponible en el repositorio; prepare_dictionary.py es mecanismo, no fuente de palabras. Fixtures existentes permiten test local determinista, no cerrar FIN-02 ni sustituir el diccionario de demo. Con DB sin palabras, el contrato actual devuelve 500 controlado en nueva partida y /health sigue siendo de proceso.

## 3. Estrategia de transición, sin doble escritura

1. **Contrato/release de referencia:** conservar commit de backend y esquema/huellas FIN-01B. Identificar qué resultados provienen de tests en memoria y qué datos de respuesta real siguen no observados; no conectar a Supabase para completar muestras sin otra autorización.
2. **Implementación aislada posterior:** preparar PG-02/03 en rama autorizada con nuevas dependencias, tests y una DB nueva de ensayo. El frontend sigue consumiendo la misma API. No cambiar el backend activo ni sus secretos para ensayar.
3. **Reconstrucción nueva:** aplicar baseline una vez a un destino nuevo autorizado. Registro/serialización de migraciones y carga de diccionario son gates operativos posteriores; no reaplicar CREATE TABLE al arranque de cada web worker.
4. **Datos iniciales:** no copiar nada del proyecto Supabase, incluidos usuarios/estadísticas. Cargar solo fixtures de test o lista de vocablos aprobada según propósito; una fixture no es un dato histórico migrado.
5. **Verificación:** API con driver real, tipos JSON, errores conocidos, reglas de juego, conexiones y transacciones. La prueba SQL pasada no reemplaza este gate. El entorno local debe declararse limpio y no apuntar a un proyecto remoto.
6. **Cutover inicial controlado:** tras aceptación/autorización de despliegue posterior, publicar una primera release PostgreSQL y dejarla como referencia. No mezclar endpoints/rutas que envíen unas escrituras a Supabase y otras a PG. El propietario acepta comenzar sin historial; tampoco se importan después registros silenciosamente.
7. **Evolución Blue-Green posterior:** cuando las dos releases ya usan driver PG, ambas conectan al mismo DB Service y esquema compatible. La DB/PVC no recibe nombres de color, no se recrea al promover y queda fuera de selectores/rutas de conmutación.

No hay comandos ejecutados o workflows nuevos en este documento. Cada paso de implementación/runtime despliegue requiere su autorización correspondiente. No se elimina, detiene o modifica el proyecto Supabase existente por esta decisión; su retirada administrativa es independiente y no está autorizada aquí.

## 4. Reversión y alcance de compatibilidad

Antes del cutover, revertir código de una rama no exige tocar el servicio anterior ni borrar la DB de prueba. Después de que la nueva release escriba en PG, volver al SDK Supabase apuntaría a otra base y NO recuperaría los datos nuevos. No prometer esa operación como rollback automático sin pérdida de datos. La decisión de no migrar historial no autoriza eliminar nuevos datos creados en PG.

Para el Blue-Green futuro: Blue y Green deben ser dos aplicaciones PG compatibles con el mismo esquema. Gates previos y posteriores a promoción determinan el cambio de tráfico; rollback restaura la aplicación/ruta anterior, no deshace filas o DDL. Cualquier cambio posterior de esquema debe ser compatible durante ambas releases y su ventana de rollback, dejando retirada destructiva para una fase acordada. Una instancia de DB sigue siendo un punto único de fallo, aceptado para el TFG.

## 5. Decisiones técnicas mínimas antes de PG-02

| ID | Decisión | Estado y criterio de resolución |
|---|---|---|
| D01 | Driver async y distribución/versión estable; pool y lock | Arquitectura aprobada. Falta fijar versiones estables de psycopg/distribución binaria y psycopg_pool compatibles con Python 3.12/Linux y disponibilidad de wheels/hashes. No instalar en PG-01. |
| D02 | Tamaño, timeouts y lifecycle del pool | Debe ser por proceso, acotado, conexión prestada por operación/request, cerrado limpiamente. Fijar parámetros explícitos y sumar Blue+Green/workers; no usar una conexión global compartida ni conectar al importar. |
| D03 | Arranque y /health cuando DB no está disponible | Preservar liveness de proceso. Propuesta: pool abierto en lifespan con conexión diferida y fallo de datos controlado; confirmar que arranque no exige DB para responder health. No añadir readiness endpoint sin alcance posterior. |
| D04 | Configuración de conexión y rol técnico | Elegir nombres de variables, por ejemplo PGHOST/PGPORT/PGDATABASE/PGUSER y contraseña externa. Configuración privada, sin DSN en logs, rol de app separado del migrador. No reutilizar SUPABASE_KEY como contraseña por inferencia. |
| D05 | Entradas UUID malformadas y fallos de proveedor | No existe estado/detail estable específico en código actual. Decidir y documentar traducción mínima antes de afirmar compatibilidad. No introducir un 400/404/409/503 nuevo como si fuese contrato comprobado ni exponer excepción/SQL/DSN. |
| D06 | Serialización de filas | Conservar IDs str, resultado como lista JSON, números (incluido promedio fraccionario), campos/null de cada rama y fechas sin inventar zona. Fijar ejemplos sintéticos esperados; formato Supabase de fechas/errores sin muestra sigue incierto. |
| D07 | Frontera de transacción | Diseñar conexión compartida por unidad de intento y commit antes del éxito HTTP. PG-03 prueba atomicidad/concurrencia; PG-02 no puede declarar esa propiedad sin evidencia. |
| D08 | Interfaz mínima y adaptación de tests | Elegir pocas operaciones SQL de dominio o acceso pequeño, sin ORM y sin clon SDK. Adaptar dependencia HTTP/dobles y preservar evaluador; no sacrificar cobertura acoplada a AST solo por que falle tras el cambio. |
| D09 | Runtime y recursos de prueba | Autorización independiente para instalación/PG local nuevo. Las autorizaciones anteriores de contenedores finalizados no conceden permiso a arrancar otros en PG-01. Definir test DB/fixture y limpieza sin tocar bases existentes. |

Estas decisiones son gates de detalle de implementación, no una nueva evaluación de arquitectura. Si una definición exigiera cambiar comportamiento funcional documentado, detener esa parte y pedir aprobación concreta. No bloquear en cambio por decisiones rutinarias reversibles que ya estén comprendidas en la autorización futura.

## 6. Fuera del alcance y estado

No hay traslado de datos reales, nuevas funciones, nuevo sistema Auth, rediseño RLS, modificación SQL, cambios Compose/Kubernetes/Terraform/CI ni despliegue. El plan FIN-01..FIN-22 no se edita ahora. Sus referencias antiguas a Supabase se conservan como histórico hasta revisión documental autorizada.

PG-01 queda preparado para revisión junto con contratos y aceptación. FIN-01 sigue pendiente de integración y validaciones acordadas. No se inicia PG-02 por aprobación del objetivo arquitectónico solamente.
