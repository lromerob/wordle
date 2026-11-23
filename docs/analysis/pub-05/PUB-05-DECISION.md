# PUB-05 — Decisión

**CI NOT VERIFIED**. Publicación no realizada por condición preventiva expresa del apartado 3, no por un fallo de CI o autenticación.

El workflow no escucha push a la rama autorizada. Mantener sus triggers impide obtener ejecución automática mediante ese push. No se modifican workflows ni se elude la condición con PR/dispatch.

## Acción mínima propuesta, pendiente de autorización

Autorizar expresamente publicar la rama aunque no dispare CI y después lanzar workflow_dispatch sobre esa rama. Revalidar antes el estado local y la existencia/divergencia del destino remoto; no asumirlas verificadas. Esta alternativa conserva el workflow y no requiere commit correctivo. Si se prefiere ejecución automática por push, autorizar por separado un cambio mínimo del filtro de ramas y su commit; no se realiza aquí. PR sigue sin crear.

Riesgos pendientes: validación real del servicio PostgreSQL/Linux/Actions, instalaciones y builds del runner, smoke kind y limpieza, políticas de acceso Actions. No hay run ID ni SHA remoto confirmado. FIN-01 permanece pendiente, sin actualizar backlog. Los tres informes PUB-05 y el previo PUB-04 permanecen locales/sin seguimiento. Detenerse para revisión; no ejecutar correcciones, publicaciones o tareas posteriores.
