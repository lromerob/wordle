# Revisión focalizada del backend

Las pruebas usan únicamente MemoryDB y sustituyen get_supabase; no validan una conexión real, políticas RLS ni el esquema desplegado.

## Correcciones

- Se validan cinco letras A-Z/Ñ antes de convertir a mayúsculas. Se conservan espacios exteriores y minúsculas; se rechazan símbolos, dígitos y expansiones Unicode. La política de tildes queda restringida al alfabeto actual del juego.
- GET de partida solo permite devolver la solución en los estados finales conocidos ganada/perdida; otros estados la ocultan. Crear partida devuelve únicamente su identificador; un intento activo devuelve solución nula.
- Consultas de partida con limit(1) permiten devolver 404 sin depender de la excepción de single() para cero filas.
- El promedio se actualiza ponderando por victorias previas; las derrotas no lo alteran. No se reconstruyen estadísticas históricas que ya fueran incorrectas.

## Riesgos pendientes que requieren decisiones adicionales

- usuario_id procede del cliente y no acredita identidad. Su comparación solo detecta incoherencias; un atacante que conozca el identificador puede suplantarlo. GET de partidas y estadísticas carecen de autorización verificable. Se necesita acordar autenticación y vinculación con RLS antes de exposición pública; no se añade un sistema nuevo aquí.
- Insertar intento, actualizar partida y actualizar estadísticas son operaciones separadas. Concurrencia o fallos parciales pueden duplicar intentos, perder incrementos o dejar estadísticas inconsistentes. La solución requiere transacción/RPC en PostgreSQL y restricciones apropiadas; un bloqueo en memoria no protege varios procesos. No se cambia el esquema ni se promete atomicidad.
- La selección del diccionario y el acceso usan el cliente síncrono desde handlers async. CORS permite todos los orígenes. No hay limitación de solicitudes. Deben revisarse antes de producción.
- No se han inspeccionado credenciales, configuraciones sensibles ni políticas reales de Supabase. La integración con Supabase permanece pendiente.
