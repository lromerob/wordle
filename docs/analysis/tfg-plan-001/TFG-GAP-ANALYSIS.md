# TFG-GAP-ANALYSIS

Fecha: 08/11/2026. Propuesta para aprobación, sin implementación. Fuente principal: Procedimiento PF - DevOps, 7 páginas. Corte local a666b17680781a24889ea774778019995d3fca45. Consultar la [matriz](TFG-COMPLIANCE-MATRIX.md) para IDs, páginas y evidencias E01-E18.

## Resultado ejecutivo

58 obligaciones atomizadas: 14 CUMPLIDO (24,14 %), 21 PARCIAL (36,21 %), 23 PENDIENTE (39,66 %). Cálculo por número de filas, sin ponderación de importancia ni crédito parcial. No es una calificación oficial ni una estimación del porcentaje de esfuerzo restante. El redondeo suma 100,01 %. No se verificaron ejecuciones de GitHub ni recursos cloud actuales.

La base de desarrollo local es sólida, pero el TFG todavía no demuestra la cadena académica completa: infraestructura cloud -> despliegue automatizado -> Blue-Green/rollback -> observabilidad integrada -> aplicación persistente -> evidencias/memoria/defensa.

## Cinco brechas determinantes

1. **Aplicación persistente y reproducible (A01/A19/A50/A51).** Hay cliente Supabase y tests MemoryDB, pero no esquema SQL, migraciones, RLS, datos sintéticos persistentes ni restauración probada. No puede deducirse el esquema real de los diccionarios Python. Hay que verificar tipos, claves, defaults, usuario_id, índices, políticas y permisos antes de escribir migraciones. La identidad UUID del frontend no es autenticación. Una base accesible mediante una clave privilegiada no demuestra autorización segura.
2. **Cloud/CD e Ingress (A05/A06/A09/A12/A14/A18/A31).** Terraform prepara AKS y el workflow prueba kind; no despliega la aplicación en Azure. Faltan perfil AKS, controlador/recurso Ingress, secretos runtime, estado remoto operativo, identidad de pipeline y acceso de red. La publicación GHCR está programada, no demostrada por una run inspeccionada. El job Terraform es independiente: no bloquea publish-ghcr por dependencia; una decisión posterior sobre required checks es necesaria.
3. **Blue-Green y rollback automático (A20/A21/A47).** Recreate del backend no es Blue-Green. No hay versión candidata, conmutación, gates ni recuperación automática. Se debe verificar la versión antigua, provocar un fallo controlado de la nueva y demostrar restauración sin intervención manual. El PDF exige ambos, no uno a elección.
4. **Observabilidad completa (A22-A30/A48).** Logs y probes son una base, no sustituyen Collector, Prometheus, Grafana, Loki, cAdvisor, Node Exporter ni alertas/notificaciones. Falta instrumentación y destino de trazas. El documento no impone una marca para ese destino: seleccionar una solución ligera o justificar una exportación inspeccionable, sin atribuir capacidades de trazas a Loki/Prometheus. Para una demostración convincente se recomienda poder consultar una traza completa, no solo mensajes en consola.
5. **Paquete académico y evidencia (A38-A58).** No existe memoria propia PDF, diagramas, dossier de runs/capturas ni vídeo verificable. La documentación técnica existente aporta material, no reemplaza los capítulos exigidos. El vídeo final depende de las tres preguntas del docente y dura como máximo 15 minutos.

## Niveles de evidencia observados

| Nivel | Hecho verificable | Límite |
|---|---|---|
| Código | React/FastAPI, contenedores, pruebas, Terraform y YAML presentes | No prueba ejecución o integración externa. |
| Configuración preparada | Siete jobs de Actions, GHCR, kind y backend azurerm parcial | No acredita runs verdes, paquetes o estado remoto activo. |
| Pruebas locales históricas | READMEs registran Docker/kind y fmt/init/validate; tests existen | No se repitieron y no hay logs originales versionados suficientes para todas las afirmaciones. |
| Integración real | Supabase/AKS se describen como pendientes | No se contactaron para comprobarlos. |
| Cloud demostrado | Sin evidencia encontrada en el repositorio inspeccionado | No se afirma que no haya recursos fuera del repositorio. |

Las 26 pruebas backend y 12 frontend son conteos estáticos de métodos/casos actuales; no 38 tests ejecutados hoy. El workflow actual ejecuta backend y build frontend, pero no Vitest. /health devuelve disponibilidad del proceso; no prueba acceso a Supabase. Los healthchecks no son dashboards ni alertas.

## Arquitectura conservada y decisiones pendientes

Se mantiene Terraform + AKS + Docker/GHCR + GitHub Actions + Supabase/PostgreSQL. No se propone Bicep ni otra plataforma de ejecución. Es la opción de menor retrabajo y satisface la elección AKS del PDF.

Decisiones necesarias antes de implementar:

- **D01 Datos y seguridad:** esquema real autorizado, modelo de identidad/propiedad, claves runtime de privilegio mínimo y RLS compatible. Elegir si la demo será solo de acceso controlado mientras se resuelve autenticación; no presentar un ID del cliente como seguridad. Un sistema de login nuevo requiere aprobación, no se introduce por este análisis.
- **D02 Red y CD:** identidad OIDC de alcance limitado, entorno protegido y conectividad al API AKS. IP variable de runner no justifica 0.0.0.0/0 ni autorizar todo Azure. Runner confiable con salida fija o conectividad privada son opciones a evaluar sin provisionarlas.
- **D03 Ingress y TLS:** controlador soportado en la fecha de implementación, compatible con AKS/Ingress y con el coste autorizado. No fijar por costumbre una distribución obsoleta; PDF pide Ingress Controllers, no un proveedor concreto. Resolver DNS/certificado para acceso público; alternativa de defensa restringida debe seguir demostrando el controlador.
- **D04 Promoción:** unidad Blue/Green de frontend+backend, selección del Service/Ingress, criterio de salud y rollback; datos compartidos y cambios de esquema compatibles hacia atrás. Los tests en memoria de réplicas independientes no prueban consistencia entre Blue y Green.
- **D05 Observabilidad:** destino de trazas, agente de logs, canal de notificaciones y retención. Secrets de receptores quedan externos, no en rules ni capturas. Definir umbrales y periodos medidos, no inventar requisitos numéricos del PDF.
- **D06 Coste y dimensionamiento:** región, versión AKS, SKU/cuota y RAM para aplicación más observabilidad. El ejemplo de dos D4s_v5 no es garantía de capacidad ni presupuesto aprobado. Ensayar localmente y medir antes de dimensionar.

## Ejecución Azure temporal: diseño, no implementación

**deploy-demo**, futuro workflow manual protegido: validar versión/artefactos y prerrequisitos -> inicializar estado remoto independiente -> revisar/aprobar plan -> aprovisionar -> configurar conectividad y secretos -> instalar Ingress/observabilidad -> desplegar una versión GHCR por digest -> migrar/sembrar DB dedicada -> probar E2E, señales y alertas -> guardar evidencias sanitizadas.

**destroy-demo**, futuro workflow manual protegido: comprobar respaldos restaurables, imágenes, estado y propiedad de recursos -> revisar/aprobar plan de retirada -> retirar solo recursos autorizados -> verificar nodos/discos/IP/balanceadores/PVC/snapshots remanentes -> registrar comprobación posterior de costes. No eliminar el backend remoto ni Supabase por defecto. Debe rechazar suscripción, nombres o etiquetas inesperados y serializar operaciones sobre el entorno; no confiar únicamente en el nombre del RG.

Fuera del entorno efímero: código, lock/provider y versiones, artefactos GHCR/digests, estado Terraform y copias, datos/semillas y respaldos, secretos y configuración privada, evidencias y manifiesto de versión. Las copias del estado/planes también son sensibles; no subirlos como artifacts públicos.

Entre periodos largos, preferir eliminar la ejecución AKS tras verificar recuperación. Durante la ventana de defensa, reconstruir al menos el día anterior y no retirarla hasta concluir la evaluación necesaria. Detener AKS conserva costes residuales y no garantiza capacidad de arranque; confirmar reglas actuales antes de decidir. Destruir crea identidades/endpoints nuevos al recrear: no conservar kubeconfigs ni IP como configuración inmutable.

**Estimaciones no medidas:** con automatización terminada, cuotas/permisos resueltos, imágenes ya publicadas y DB lista, reservar 45-90 minutos para reconstruir y verificar. Datos a restaurar, falta de capacidad, propagación RBAC y errores de red pueden añadir horas. No es un SLA; FIN-19 sustituirá la estimación por tiempos medidos. Preparación inicial y corrección de brechas se estiman en días de trabajo en el plan, no en esos minutos.

## Riesgos que comprometen la defensa

| Riesgo | Impacto | Prevención/evidencia requerida |
|---|---|---|
| Esquema/RLS desconocidos | La UI funciona con MemoryDB pero falla con Supabase | Restauración de BD limpia y pruebas persistentes antes de Azure. |
| Despliegue Azure no ensayado | Dependencia de permisos/cuotas el último día | Preflight y un ciclo completo de creación-retirada-recreación autorizado. |
| Blue-Green con datos incompatibles | La versión anterior no puede recuperar servicio | Migraciones compatibles y prueba de fallo funcional después de promoción. |
| Collector solo instalado, sin datos | Incumplimiento A22/A30 | Mostrar métrica y traza correlacionada de un intento real. |
| Exporters incompatibles/restringidos | Falta métrica de contenedor/nodo en AKS | Validar cAdvisor/kubelet y Node Exporter en AKS, no solo kind. |
| Presupuesto insuficiente/RAM escasa | OOM, alertas espurias y dashboard caído | Medición local, retención pequeña y sizing aprobado, sin prometer nodo mínimo universal. |
| Imágenes o secretos no recuperables | No se reconstruye la demo | Referencias por digest, retención y recuperación externa comprobada. |
| Sin evidencia capturada | Repetición de despliegues y costes | Capturar cada gate y exportar antes de destroy-demo. |
| Preguntas docentes no recibidas | Vídeo sin responder a evaluación real | Solicitarlas por canal académico y reservar tiempo posterior; no inventarlas. |

## Backlog y alcance

No se encontró archivo de backlog oficial en el repositorio. No se consultó ni alteró ninguna herramienta externa. FIN-01 a FIN-22 son propuestas nuevas en el [plan](TFG-COMPLETION-PLAN.md), pendientes de aprobación y correspondencia con el backlog oficial. No son tickets creados ni trabajo iniciado. Estos documentos no cambian estados académicos por sí mismos.
