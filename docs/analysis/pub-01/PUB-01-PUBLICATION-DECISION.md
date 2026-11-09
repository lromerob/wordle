# PUB-01 — Decisión de publicación

Fecha: 09/11/2026. **READY WITH CONDITIONS**. No es autorización de commit/push. No se ha preparado el índice ni publicado nada.

## Justificación

El código, pruebas, SQL y automatización necesarios existen en disco; no se encontraron credenciales reales en los candidatos con el análisis acotado. Hay evidencia PG-07 de 55 offline y once reales más builds, que no se repitió en esta auditoría. El índice está vacío y los archivos privados identificados quedan fuera.

La publicación no está lista de forma incondicional: README/plantilla/notas técnicas contradicen PostgreSQL actual; nueve dependencias CI siguen sin seguimiento; siete informes contienen información de máquina que conviene sanear; históricos Supabase abiertos y documentos FIN/plan necesitan selección explícita. No hay evidencia de workflow remoto ni de clon limpio del conjunto propuesto.

## Condiciones antes de autorizar commit y push

1. **Documentación vigente:** autorizar una corrección pequeña de README.md, backend/.env.example y SECURITY-NOTES.md para describir PostgreSQL/psycopg async, variables vigentes, transacciones/locks y límites reales. Enlazar manuales PG-05/06/07 y etiquetar documentos Supabase históricos, sin modificar código o plan FIN en esta auditoría.
2. **Privacidad y selección:** revisar/sanear los siete informes PG-05/06/07-next indicados en el manifiesto; conservar originales privados si procede. Decidir inclusión histórica FIN/TFG y destino de allow_all/prototype_access/local_backend_smoke. No incorporarlos indiscriminadamente como configuración actual; no eliminarlos.
3. **Conjunto coherente:** revisar y autorizar las rutas VERSIONAR y las REVISAR resueltas, incluyendo nueve dependencias CI y recursos de inicialización/overlay; mantener secretos/cachés/backups/kubeconfigs/volúmenes fuera. El manifiesto enumera rutas concretas. Publicar solo workflow o solo archivos modificados rompería CI.
4. **Base y comprobación final:** en una tarea autorizada, actualizar referencias de GitHub y acordar rama de publicación preservando todos los cambios; no asumir que esta rama antigua sea main actualizado. Inspeccionar el futuro diff staged/listado exacto, secretos y whitespace antes del commit/push. No se ejecuta ninguna operación preparatoria aquí.

## Verificación posterior a publicación autorizada

El primer run real de GitHub es evidencia pendiente, no condición que pueda demostrarse sin publicar. Debe ejecutar 55 offline/once reales/cero omitidas, builds, Kustomize, kind memoria autorizado y Terraform; GHCR debe quedar skipped. Registrar SHA/enlace/run y fallos sin secretos. Publicar código no significa habilitar runtime público: identidad no verificada, CORS abierto, fixture mínima, backup independiente y tamaño/almacenamiento cloud siguen fuera de garantías.

No se requieren nuevas funcionalidades ni un refactor para resolver las condiciones documentales/de selección. Portabilidad Windows de los ejecutores PG-05/06 y tags móviles se documentan como límites; no impiden CI Linux PG-07 si se incluyen sus archivos correctos. El prototipo allow_all no es un hallazgo de password, pero debe quedar separado inequívocamente de instrucciones operativas.

## Qué cambiaría a BLOCKED

Un secreto real en candidatos/historial a publicar, una dependencia realmente ausente, pérdida/cambio no explicado de archivos, o necesidad de modificar datos/infraestructura para recuperar el estado exigiría detenerse y revisión específica. Ninguno de esos hechos se ha confirmado aquí. La ausencia de lectura de archivos privados o de auditoría de toda la historia no debe confundirse con una certificación universal de seguridad.

## Acciones realizadas y límite

Solo se crearon los tres informes PUB-01. Sin add/commit/push/reset/clean, cambio de rama, fetch, ejecución de tests/workflows, instalación, contenedores, despliegues o eliminación de recursos. Todo el trabajo PG previo debe permanecer idéntico. FIN-01 pendiente. Esperar autorización de la corrección documental/selección; no iniciar automáticamente publicación u otra tarea.
