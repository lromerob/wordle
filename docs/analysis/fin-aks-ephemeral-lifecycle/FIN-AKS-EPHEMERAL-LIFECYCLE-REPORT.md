# FIN-AKS-EPHEMERAL-LIFECYCLE — Wordle — 16/11/2026

## 1. Resumen ejecutivo

**PASS documental; AKS NO-GO.** Ciclo propuesto: DEPLOY → VALIDATE → EVIDENCE → DESTROY → REDEPLOY → DESTROY. Cada operación externa mantiene autorización separada; no se ejecuta ningún comando de ese ciclo hoy. No es una plataforma permanente: eliminar AKS/red/discos/LB/IP exclusivos después de cada sesión, conservar estado/backend temporalmente con aprobación, y custodiar fuentes, imágenes, backups sintéticos y evidencia externamente.

Hechos: Terraform y overlays/scripts existen; FIN-AKS-QUOTA-REQUEST acredita DSv5=16/regional=26. Propuestas no aprobadas: Entra/grupo, rangos externos, /32, backend Storage, AKS1.35.9 y surge1, presupuesto. Configuración operativa sigue null en versión y sin surge explícito. Las evidencias kind/CI no acreditan AKS. Este informe no convierte nombres definidos en recursos existentes.

Fuentes inspeccionadas: FIN-AKS-CONFIG-VALIDATION, informes de cuota/configuración; infra/terraform; k8s/aks-full/images.lock.json; ci.yml; scripts azure_supervised/azure_release/aks_run; guía docs/operations/azure-demo.md. No consulta a Azure ni prueba de runtime hoy. Tarifas conservadas de consulta oficial15/11/2026, no revalidadas16/11.

## 2. Inventario y clasificación

A=efímero, B=persistente temporal con autorización y fecha de revisión, C=artefacto de reproducción/documentación. No eliminar recursos preexistentes/compartidos. Clasificación propuesta, no permiso de borrado.

| Elemento | Clase | Creación y responsable | Retirada futura | Coste residual/dependencia de reconstrucción |
|---|---|---|---|---|
| RG Wordle aplicación | A | Terraform/operador, exclusivo | Plan destructivo revisado | RG no cobra por sí; contenido debe quedar inventariado |
| AKS/pool2nodos y surge | A | Terraform + recursos gestionados AKS | Helper ejecuta plan de retirada autorizado | VM/discos/capacidad mientras existan; requiere Entra, cuota, región y fuentes |
| RG de nodos/VMSS | A | AKS, no añadir recursos ajenos | AKS durante retirada; comprobar ausencia | No asumir que desapareció por exit0 |
| VNet/subred | A | Terraform/operador | Plan propio, tras dependencias | Sin peering/recursos compartidos; direcciones aprobadas necesarias al reconstruir |
| LB/IP de salida y recursos red gestionados | A | AKS/servicio Azure | Retirada AKS y verificación ARM | IP/LB/egreso pueden continuar facturando si quedan huérfanos |
| PostgreSQL StatefulSet/PVC/disco | A | Kubernetes + CSI, DB compartida por colores | Eliminación del clúster/disco bajo autorización, después de backup validado | PVC no equivale a backup; comprobar discos/PV/reclaim real, no asumir borrado |
| Identidad control-plane y roleAssignment subred | A | Terraform | Plan revisado | Sin coste propio declarado; verificar roles huérfanos y no borrar identidades externas |
| Identidad kubelet | A | AKS en RG nodos | AKS y comprobación de remanentes | Recurso gestionado, no identidad humana ni del backend |
| Namespaces/app/Ingress/observabilidad | A | aks_run y Kustomize | Clúster efímero | Métricas/logs/trazas emptyDir desaparecen; exportar primero |
| Grupo Entra dedicado/membresía | B | Administrador autorizado, no módulo principal | Solo decisión expresa tras defensa | Conservar para redeploy; no eliminar grupo compartido ni roles ajenos |
| RG/Storage/contenedor/backend | B | Bootstrap externo autorizado | Limpieza final independiente, nunca antes que recursos gestionados | Blob/versiones/operaciones facturables; acceso/clave/lineage indispensables |
| Estado actual, versiones y backup de estado | B | Terraform/Storage, custodia operador | Retención/aprobación posterior | Sensible aunque DB sintética; nunca artefacto público; no borrar para reparar errores |
| Variables aprobadas, kubeconfigs/secretos demo | B | Custodia privada externa | Rotar/retirar tras aceptación | Kubeconfig nuevo por clúster; secretos no van en C público |
| Backups DB sintéticos y metadata/hash | B hasta aceptación, luego C privado si procede | pg_dump/helper con pausa de escritores | Retención/eliminación expresas | Restauración independiente SQL+HTTP antes de confiar en ellos |
| Imágenes GHCR por digest/lock | C | CI publicador existente, sin ACR Azure | Mantener tags/digests; no limpiar por destruir AKS | Pull debe seguir disponible; dependencia externa y política GHCR por revisar |
| Fuentes/lock Terraform/manifests/scripts | C | Repositorio + paquete azure_release verificado | No borrar con infraestructura | HEAD no contiene toda preparación local: snapshot/hash necesario antes de ejecutar |
| Evidencias sanitizadas/informes/video/diagramas | C | Operador fuera de AKS | Conservar para TFG/defensa | Copia independiente del portátil/clúster, integridad y accesos revisados |

## 3. Arquitectura del ciclo de vida

Sesión1 nueva → desplegar → aceptar juego/observabilidad/promoción/rollback → exportar pruebas y backup → verificar restauración independiente → retirada autorizada → comprobar remanentes. Entre sesiones: solo B aprobado y C conservados. Defensa: fuentes/config aprobadas + imágenes idénticas + backend/secretos externos → nueva infraestructura → DB nueva vacía sin escritores → restaurar → SQL/HTTP → demo → nuevo backup/evidencias si interesa → retirada autorizada.

Se reutiliza una DB por instalación, no una por color. Reconstrucción secuencial evita mantener dos clústeres de pago; la cuota no autoriza solapamientos. Cambios no destructivos de aplicación son distintos de upgrade de plataforma y recuperación de datos. No se prometen HA, ausencia de interrupción ni recuperación histórica de señales emptyDir.

## 4. Procedimiento reproducible: comandos FUTUROS, NO ejecutados

Variables PowerShell de ejemplo: `$Private` carpeta privada externa, `$Work/$DestroyWork` carpetas NUEVAS vacías, `$Kubeconfig` ruta externa nueva, `$Context` contexto exclusivo. Suscripción/tenant/grupo/CIDR/backend aprobados se introducen en variables.json/backend.json privados, sin claves/SAS. PATH solo sesión para herramientas instaladas. Los comandos debajo no sustituyen autorizaciones.

| Fase | Acción futura reutilizada | Resultado/gate esperado |
|---|---|---|
| 1 Preflight | azure_preflight.py y revisar cuota/parche/capacidad, identidad, CIDR, presupuesto | Detener si algún gate esencial falta; no login/registro implícito |
| 2 Bootstrap backend | Crear RG/Storage/container/RBAC por procedimiento autorizado aparte | RG externo; Entra, firewall, versiones/retención; no backend ficticio |
| 3 Configuración | Aprobar variables, snapshot de fuentes y lock; fmt/validate sin remoto donde proceda | Coordenadas y hashes coherentes; pruebas locales existentes no repetidas por rutina |
| 4 Plan | azure_supervised prepare y plan con permiso de init/lease específico | Plan privado legible y hash revisado, sin recursos ajenos/replacements inesperados |
| 5 Aprovisionar | execute con CREATE, presupuesto y hash | AKS real, inventario y tiempos registrados |
| 6 Acceso | aks_run credentials | Kubeconfig de usuario nuevo, kubelogin, contexto/FQDN correctos; no --admin |
| 7 Imágenes | Obtener GHCR por digest de lock, verificar revisión/plataforma | No rebuild/publicación innecesaria; ninguna etiqueta latest como despliegue |
| 8 Kubernetes | aks_run deploy (o restore-deploy en reconstrucción) | Secretos externos sintéticos, probes/rollouts/PVC/Service privados |
| 9 Funcional | aks_run verify | HTTP/SQL reales y persistencia; no solo /health |
| 10 Pruebas | aks_run acceptance con autorización de averías | Promoción, rollback post-promoción, señales/alertas y datos íntegros |
| 11 Evidencias | Exportar directorios externos, video/capturas sanitizadas y hashes | Evidencia fuera de infraestructura efímera, revisada antes de destruir |

Comandos existentes de reproducción, siempre con autorización de la fase:

```powershell
python -B scripts/azure_release.py create --directory "$Private/release"
python -B scripts/azure_release.py verify --directory "$Private/release"
python -B scripts/azure_supervised.py prepare --workdir "$Work" --variables "$Private/variables.json" --backend "$Private/backend.json"
# GATE: init/plan/lease autorizados, no ejecución hoy
python -B scripts/azure_supervised.py plan --workdir "$Work" --confirm "PLAN rg-wordle-academic/aks-wordle-academic"
# GATE CREATE: plan/hash/coste aprobados
python -B scripts/azure_supervised.py execute --workdir "$Work" --confirm "EXECUTE rg-wordle-academic/aks-wordle-academic" --approve-intent "CREATE rg-wordle-academic/aks-wordle-academic" --budget-approved --plan-sha256 "<HASH_REVISADO>"
$aksArgs = @('--variables', "$Private/variables.json", '--kubeconfig', "$Kubeconfig", '--context', "$Context")
python -B scripts/aks_run.py credentials @aksArgs --evidence "$Private/evidence/credentials" --confirm "CREDENTIALS rg-wordle-academic/aks-wordle-academic"
python -B scripts/aks_run.py deploy @aksArgs --evidence "$Private/evidence/deploy" --confirm "DEPLOY rg-wordle-academic/aks-wordle-academic" --ack-costs
python -B scripts/aks_run.py verify @aksArgs --evidence "$Private/evidence/verify" --confirm "VERIFY rg-wordle-academic/aks-wordle-academic"
# GATE: solo instalación sintética; acceptance espera Blue activo inicialmente
python -B scripts/aks_run.py acceptance @aksArgs --evidence "$Private/evidence/acceptance" --confirm "ACCEPTANCE rg-wordle-academic/aks-wordle-academic"
python -B scripts/aks_run.py backup @aksArgs --directory "$Private/backups/run1" --evidence "$Private/evidence/backup" --confirm "BACKUP rg-wordle-academic/aks-wordle-academic"
```

El backup integrado conserva réplicas/selector y reanuda en finally; no mezclar metadata antigua del helper SQL básico con la del ejecutor integrado. Antes de retirada comprobar dump/hash y **restauración real en PostgreSQL16 desechable independiente con SQL+HTTP**, autorizada en su fase futura; el ensayo FIN-02B histórico no valida automáticamente este dump nuevo. Puede hacerse localmente sin levantar un segundo AKS: usar pg_restore y backend temporal con herramientas existentes, guardar receipt. No se afirma que run_fin02b.py acepte un dump externo: su flujo actual genera su propia fixture. Preparar ese ensayo concreto al llegar al backup, sin añadir automatización ahora.

Para reconstrucción tras infraestructura nueva, reutilizar mismo backend/clave con lineage preservado y variables aprobadas. Tras credentials con kubeconfig NUEVO, sustituir deploy por:

```powershell
python -B scripts/aks_run.py restore-deploy @aksArgs --evidence "$Private/evidence/restore-deploy" --confirm "RESTORE-DEPLOY rg-wordle-academic/aks-wordle-academic" --ack-costs
python -B scripts/aks_run.py restore @aksArgs --directory "$Private/backups/run1" --evidence "$Private/evidence/restore" --confirm "RESTORE rg-wordle-academic/aks-wordle-academic"
```

restore-deploy deja escritores a cero y PG vacío; restore comprueba versión/hash/datos/secuencias, restaura permisos y réplicas/selector, valida HTTP/escrituras y emite recibo solo tras éxito. No forzar acceptance que exige Blue si la restauración conserva Green; aprobar escenario separado o limitar defensa a verify y evidencia histórica de rollback. Secretos deben corresponder a bootstrap y reconstrucción externa, nunca copiar Secret desde clúster al informe.

## 5. Estado Terraform: protección y retirada

Bootstrap separado del módulo de aplicación; Entra/data-plane y Storage Blob Data Contributor acotado. TLS/firewall de salida aprobada; contenedor privado, versiones y soft delete7d propuestos. Backend no debe contener recursos ajenos. Inicialización futura solo después de aprobar coordenadas; no usar -migrate-state/-force-copy o un estado nuevo vacío para ocultar recursos existentes. Backend lock nativo mediante lease y -lock-timeout del helper; ante bloqueo, comprobar propietario/proceso y detener; force-unlock solo con autorización y prueba de bloqueo huérfano.

El estado puede contener datos sensibles; snapshots/planes privados, no Git/artifacts públicos. Conservar copia autorizada versionada antes y después de cambios, con fecha/hash/lineage/serial revisados; no manipular serial/lineage. Tras retirada, estado todavía conserva metadatos/linaje aunque no tenga recursos. **Nunca borrar estado antes de comprobar que todos sus recursos y dependencias AKS se eliminaron.**

Para reconstrucción preferir mantener B hasta defensa, no el clúster. Si se decide retirar backend antes, primero completar destrucción/ausencia ARM y exportar copia privada verificada; aprobación independiente para borrar cuenta/contenedor/versiones, registrar retención y copia. Reconstruir Storage y reubicar ese estado es recuperación/migración controlada futura, no procedimiento rutinario ni init a ciegas. Final de defensa: aplicar las mismas verificaciones y una fecha explícita de expiración de B; borrar copias/secretos/versiones solo bajo política aprobada, conservando C sanitizado. Soft delete/lifecycle pueden retener datos/coste; no prometer purga inmediata de versiones.

## 6. Imágenes y reproducción

No crear ACR. CI ya publica en GHCR por SHA tras siete gates, únicamente main y excepción de rama autorizada. `k8s/aks-full/images.lock.json` fija11digests; app source_commit4d56cf265cc5f0af8c72c64f2a93373660e8f122 y revisiones históricamente verificadas. Conservar ambas imágenes y todas las dependencias de observabilidad/PG/Traefik por digest entre sesiones; no borrar paquetes porque se destruya AKS. GHCR no forma parte del estado Azure, costes/política propios no cotizados aquí.

Rebuild desde Dockerfiles/locks no garantiza digest idéntico (bases, herramientas, tiempo/dependencias). Preferir pull de referencias verificadas. Como contingencia futura autorizada, guardar archivos OCI/Docker de imágenes verificadas con hash y manifests fuera del clúster; AKS necesitaría distribución por registro accesible, no docker load del portátil como sustituto de un registrypull. No se crean/exportan imágenes hoy ni se publica registro alternativo. Si desaparece un digest, reconstruir es una nueva release identificada y validada, no afirmar equivalencia binaria. El paquete azure_release preserva fuentes/configs/hashes, **no sustituye archivo de imágenes ni backup/secretos/estado**. Conservar snapshot de los cambios locales porque HEAD solo no los reproduce; consolidación Git requiere autorización distinta.

## 7. Matriz de evidencias

Toda evidencia se guarda en `$Private/evidence/<sesion>/<ID>` fuera de Azure efímero, con inventario SHA-256 y segunda copia privada independiente. Sanitizados para TFG pueden copiarse a carpeta C de entrega, nunca originales de planes/estado/kubeconfig. M=metadata/red/identificadores internos; S=secreto/estado/credencial que debe excluirse; D=datos sintéticos que no justifican publicar logs crudos.

| ID | Objetivo y procedimiento futuro | Esperado | Formato | Momento | Riesgo/control |
|---|---|---|---|---|---|
| E01 | Snapshot fuentes/lock/digests + hashes | Reproducción exacta de materiales | JSON/tar/diagrama | Antes deploy y defensa | M: versiones, no archivos secretos |
| E02 | fmt/validate, plan revisado y receipt | Sin errores, cambios propios esperados | TXT privado/JSON hash | Antes CREATE | S: plan puede contener secretos; solo resumen público |
| E03 | execute e inventario ARM limitado | AKS propio aprovisionado, tiempos | JSON sanitizado | Tras CREATE | M: ocultar IDs completos |
| E04 | Entra/CIDR/localaccounts/RBAC | Acceso permitido y exposición limitada | JSON/TXT revisado | Tras acceso | S: jamás kubeconfig/token/Secret |
| E05 | kubectl get nodes | Nodos Ready y versión efectiva | TXT/captura | Antes demo | M: ocultar IP/nombres personales |
| E06 | get ns/deploy/pods/svc/PVC | Ready/ClusterIP/Bound | TXT/JSON | Deploy y restore | M/D: no describir Secret |
| E07 | verify/runtime imageID/OCI | Commit-digest-runtime concordantes | images.json/result.json | Tras rollout | M: solo refs públicas |
| E08 | Navegador y HTTP/SQL juego | Frontend/API, válido/inválido, victoria/derrota, persistencia | JSON/video/capturas | Antes avería | D: no solución activa ni credenciales |
| E09 | Técnica DB reinicio/backup/restore | SQL/FK/secuencia y HTTP correctos | JSON/hash/receipt | Backup y reconstrucción | S: dump privado, no adjuntar filas crudas |
| E10 | acceptance promoción/fallo/rollback | Color activo, fallo postpromoción y recuperación automática | events.json/HTTP/timestamps/video | Ensayo autorizado | M/D: no afirmar cero interrupción |
| E11 | Queries métricas/logs/trazas/Grafana | Datos reales, dashboard y firing/resolved | JSON/PNG/video | Durante ensayo, antes destroy | S/D: sanitizar consultas/logs, no cabeceras |
| E12 | plan de retirada e inventario aprobado | Solo recursos propios | Receipt/hash/JSON privado | Antes DESTROY | S: plan privado, conservar estado |
| E13 | execute retirada y comprobación ARM | Destrucción confirmada y remanentes clasificados | JSON/TXT | Tras retirada | M: no borrar ajenos por coincidencia de nombre |
| E14 | Cost Management/inventario posterior | Residuales/cargos explicados | Captura/CSV sanitizado | Cierre y revisión posterior | M: no publicar facturación ajena; retrasos posibles |
| E15 | Redeploy+restore+verify | Nuevo AKS reproducido, datos y HTTP | JSON/video/tiempos | Predefensa | S: nuevos kubeconfigs privados |
| E16 | Segundo DESTROY+revisiónB | Sin infraestructura efímera, retención aprobada | Checklist/receipt | Fin defensa | S: eliminar B solo autorizado |

Matriz define obtención futura; **ninguna captura, éxito AKS o prueba se ha producido hoy**. La documentación histórica se enlaza como antecedente fechado, no como E03–E16 ejecutadas. Antes de destruir abrir evidencias y validar hashes/segunda copia, no solo comprobar que existe una carpeta.

## 8. Defensa y contingencia

A vivo: reservar como propuesta **2 horas de preparación técnica antes de la presentación**, dentro de la ventana aprobada de4h de recursos, y usar una ventana anterior para el ensayo completo. No es un SLA de creación; permisos/capacidad o restore pueden requerir más. Si no cabe, nueva autorización de duración/coste o modalidadB; no dejar AKS días encendido para evitar prepararlo. Antes de presentar: nodos/Pods/PVC, SQL+HTTP, versión activa, señales, backups y forwards solo loopback. No improvisar cambios de permisos durante exposición. Anotar la versión/release y tener comandos de lectura preparados.

B contingencia: video de un ensayo real AKS previamente capturado, capturas, logs sanitizados, diagramas, plan/receipt resumido, evidencia de promoción/rollback/restore/destrucción y resultados fechados. Mantener copia local offline y otra copia segura. Marcar reproducción como grabación y explicar el fallo actual; no confundir vídeo kind con AKS. Esta modalidad no sustituye el cumplimiento de las pruebas reales exigidas antes de entregar. Si nunca se probó AKS, FIN-18 permanece pendiente.

## 9. Presupuesto por escenarios

Se reutilizan precios oficiales consultados15/11/2026 en FIN-AKS-CONFIG-VALIDATION (USD, westeurope, Consumption, sin impuestos/descuentos). Son referencia fechada, no cotización nueva16/11. Revalidar antes de aprobar gasto. VM0.23/h por nodo; OS supuesto P6LRS64GiB11.2272/mes, PG supuesto E2LRS8GiB0.60/mes, unaIPv4Standard0.005/h; prorrateo orientativo730h/mes.

Por sesión4h con2nodos: VM1.84 + OS0.12304 + PG0.00329 + IPv40.02 = **1.98633 USD subtotal condicional**. Añadir LB/reglas/datos, egreso, operaciones discos, estado/retención y tiempo extra/arranque/surge. No es coste total. Un surge1h añade0.23 VM + disco temporal/red; DB no se duplica por promoción. Cargos de mount de discos compartidos no se incluyen porque no se usa shared disk.

| Escenario | Cuantificado bajo supuestos | Desconocido/residual |
|---|---|---|
| 1 Primera sesión4h | 1.98633 USD | LB, tráfico, I/O, estado, tiempo real/restore |
| 2 Entre sesiones, AKS retirado | VM/discos/IP exclusivos deberían0 una vez verificada retirada | Backend GB+versiones/operaciones, backups/GHCR/almacenamiento de evidencia; remanentes fallidos no0 |
| 3 Defensa4h | 1.98633 USD | Mismos medidores y reconstrucción/aceptación |
| 4 Contingencia adicional4h | 1.98633 USD | Mismos medidores y eventual surge |

Subtotal tres sesiones **5.95898 USD**, **no presupuesto integral**. Periodo de espera D días: Blob HotLRS0.0196 USD/GB-mes × GB efectivos incluyendo versiones ×D/30, más operaciones.1GB/30d equivale0.0196 solo capacidad; writes/list0.054/10K, reads/other0.0043/10K, según tarifas previas. D, bytes/versiones y operaciones no definidos. Soft delete7d no hace caducar versiones automáticamente; lifecycle/retención requieren aprobación.

Si no se eliminan, dosP6+E2 equivalen23.0544USD/mes y unaIP3.65USD/mes, más LB/otros; parar nodos no demuestra que cesen esos cargos. Observabilidad autogestionada usa nodos/OS/red, no LogAnalytics/AzureMonitor premium declarados; retener/exportar señales fuera añade almacenamiento cuyo importe depende del destino. No hay ACR/NATGateway nuevo. GHCR público ya previsto, no se presume precio/retención garantizados sin revisar condiciones.

**Presupuesto monetario integral pendiente de aprobación:** no se dispone de cota fiable para medidores faltantes ni duración entre sesiones; no inventar techo de10/20USD ni usar1.99 como presupuesto. Propuesta de control operativo: hasta tres sesiones, cada una máximo4h de vida de recursos, con responsable/hora de inicio/límite/retirada, revisión al inicio y antes de la última hora; no ampliar ni crear sesión extra sin autorización. Revisar Cost Management al cierre y después por latencia; alertas de50/80/100% de un presupuesto futuro aprobado son informativas, **no detienen gasto automáticamente**. No se configuran alertas hoy ni se añade automatismo destructivo.

Fuentes: [Retail API](https://prices.azure.com/api/retail/prices), [precios AKS](https://azure.microsoft.com/en-us/pricing/details/kubernetes-service/), [discos](https://azure.microsoft.com/en-us/pricing/details/managed-disks/), [LB](https://azure.microsoft.com/en-us/pricing/details/load-balancer/), [Storage](https://azure.microsoft.com/en-us/pricing/details/storage/blobs/), [alertas coste](https://learn.microsoft.com/en-us/azure/cost-management-billing/costs/cost-mgt-alerts-monitor-usage-spending).

## 10. Checklist de desmontaje futuro

1. Confirmar ensayos terminados y responsable de cierre; no hay otra sesión usando esos recursos.
2. Evidencias E01–E11 exportadas, sanitizadas, legibles, hashes y segunda copia verificados; backup SQL+HTTP independiente comprobado.
3. Registrar RG/cluster/discos/IP/identidades exclusivos e inventario actual con IDs privados; parar ante cualquier recurso ajeno. Backend fuera de ambosRG.
4. Preparar workspace externo NUEVO con mismas variables/backend; autorización separada de plan de retirada/lease. Revisar recursos/deltas e inventario y hashes, no destruir basándose solo en tag.
5. Obtener aprobación DESTROY expresa. El helper aplica un plan guardado de destrucción, no un destroy libre:

```powershell
python -B scripts/azure_supervised.py prepare --workdir "$DestroyWork" --variables "$Private/variables.json" --backend "$Private/backend.json"
python -B scripts/azure_supervised.py plan-destroy --workdir "$DestroyWork" --confirm "PLAN-DESTROY rg-wordle-academic/aks-wordle-academic"
# GATE: plan + inventory revisados y autorización de retirada
python -B scripts/azure_supervised.py execute --workdir "$DestroyWork" --confirm "EXECUTE rg-wordle-academic/aks-wordle-academic" --approve-intent "DESTROY rg-wordle-academic/aks-wordle-academic" --plan-sha256 "<HASH_REVISADO>" --inventory-sha256 "<HASH_INVENTARIO>"
```

6. Guardar salida/receipt y comprobar estado gestionado sin recursos esperados, sin editarlo. Exit0 no es única evidencia.
7. Lecturas futuras: az resource list en RG aplicación y nodos; comprobar RG ausentes o vacíos según plan, discos/IP/LB e identidades exclusivas retiradas. Resultado vacío debe distinguirse de error403/404 esperado/no visibilidad. Evitar get/delete de recursos ajenos. Si quedan restos, registrar y pedir autorización puntual; no usar borrado masivo genérico.
8. Revisar costes residuales y latencia de facturación, exportar E12–E14; no afirmar coste0 porque ARM ya esté vacío.
9. Mantener B solo según fecha/presupuesto; jamás eliminar estado antes de completar6–8. Tras defensa, aprobación separada de eliminación de backend/versiones/roles o retención de copia privada mínima. Nunca borrar grupo compartido.
10. Registrar cierre con recursos eliminados, pendientes, responsable, próxima revisión de costes y retención. Repetir al fin de defensa/contingencia, sin autorización implícita para otra sesión.

## 11. Riesgos y mitigaciones

Capacidad/versión pueden variar entre sesiones: preflight y margen, no mantener nodos como reserva. CIDR dinámico puede bloquear acceso: confirmar ruta antes, no0/0. Identidades/ACL del estado pueden expirar: comprobar acceso antes de plan. Pérdida de portátil/registro: copia externa deC, backup privado y refs; hashes no sustituyen copia. Estado/plan sensible: acceso mínimo y separación de entrega pública. Dump corrupto: restore independiente previo y SQL/HTTP posterior. Fallo de destroy: conservar estado y pedir intervención, no borrar referencia. PG y señales sinHA: demo explícita, no producción. Ningún procedimiento se prueba contra PG-05/06.

## 12. Bloqueos y decisiones pendientes

Se conservan: grupo Entra/miembros/permisos; /32 estable/autorizado; no solapamientos externos; backend/permisos/lease; presupuesto completo; aprobación de1.35.9/surge1. Gates añadidos por ciclo efímero: custodia y retenciónB/C con fecha hasta defensa; disponibilidad futura de todos los digests; snapshot íntegro de preparación no publicada; ensayo de restauración del dump concreto antes de destrucción; autorización diferenciada de cada CREATE/DESTROY y revisión de remanentes/costes; tiempo real de reconstrucción todavía no medido. Son decisiones/pasos futuros, no nuevos servicios necesarios.

## 13. Próxima iteración recomendada y preservación

Aprobar primero matriz de configuración y política de custodia/retención, responsables/ventanas y presupuesto completo; después autorizar de manera acotada grupo/miembros/CIDR y bootstrap del backend. No iniciar más análisis generales ni crear automatizaciones nuevas; reutilizar ejecutores existentes y preparar el primer plan solo al cerrar gates y autorizarlo.

Única creación hoy: este informe. No init/plan/apply/destroy, Kubernetes, Azure/Entra/RBAC, publicación, cuotas, commits/push ni cambios de scripts/manifests/configuración/documentos anteriores. Archivos pendientes previos preservados por SHA-256; no auditoría general de ramas. AKS NO-GO, esperar revisión del propietario.
