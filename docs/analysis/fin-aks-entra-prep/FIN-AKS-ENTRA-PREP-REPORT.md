# FIN-AKS-ENTRA-PREP — Wordle TFG

Fecha: **16/11/2026**. Operaciones verificadas entre **17:53:58 y 17:54:07 UTC**. **PASS. Gate A GO; Gate B NO-GO; AKS NO-GO.**

## 1. Resumen ejecutivo

Se creó exclusivamente el grupo de seguridad **grp-wordle-aks-admins**, Object ID **f35832fa-d632-43b1-a83e-112d17cc8ccc**, y se incorporó como único miembro directo el usuario administrativo aprobado. Grupo estándar, sin correo, membresía asignada, no dinámica y no asignable a roles de directorio. No se añadieron propietarios; la consulta posterior devuelve cero. No se asignaron roles Azure, Entra o Kubernetes.

El requisito de existencia e incorporación inicial del administrador queda resuelto. Esto no configura todavía el grupo en AKS/Terraform ni concede acceso a un clúster inexistente. Gate B conserva los pendientes de configuración, red, presupuesto y autorizaciones.

## 2. Autorización y alcance

Adjunto FIN-AKS-ENTRA-PREP: crear un grupo con el nombre exacto, incorporar únicamente a la identidad humana actualmente autenticada y previamente aprobada, verificar propiedades/membresía y crear este informe. No cambios Azure RBAC, Terraform, infraestructura, políticas, permisos Graph, PIM o roles de directorio.

Se consultó FIN-AKS-GATE-B-READINESS-REPORT.md, particularmente su evidencia de grupo ausente, identidad y capacidad de administración. No se modifican ese informe ni decisiones anteriores.

## 3. Identidad y tenant verificados

Tenant actual confirmado: **aff0390f-c390-4edc-919f-77da2a811eb9**, coincide con la referencia autorizada. Azure CLI autentica un **user**. Microsoft Graph `/me?$select=id,userType` confirma el usuario aprobado y **userType=Member**; no se seleccionó invitado distinto, service principal, managed identity o cuenta alternativa.

Una consulta inicial `ad signed-in-user show` sin seleccionar explícitamente userType devolvió ese campo null; no se interpretó como invitado ni identidad ambigua. El GET explícito posterior recuperó Member antes de crear. El Object ID siempre coincidió exactamente con el aprobado. No se publican nombre, email o tokens.

## 4. Suscripción verificada

Suscripción activa **11306565…1bb5**, Enabled, coincidente con el destino personal Wordle. No se cambió cuenta, suscripción o tenant. El grupo es un objeto del directorio del tenant, no un recurso ARM regional ni un objeto contenido en el RG del backend; no se le asigna una región Sweden/West.

## 5. Resultado del preflight

- Nombre exacto consultado mediante filtro displayName='grp-wordle-aks-admins': **cero coincidencias**.
- Azure CLI user y Graph Object ID coincidentes; tenant/suscripción correctos.
- Lectura de roles transitivos del operador: **Global Administrator**; política authorizationPolicy: **allowedToCreateSecurityGroups=true**.
- No se identificó necesidad de roles nuevos, consentimiento adicional, activación PIM o cambios de política. Las lecturas de capacidad no se presentaron como garantía de escritura; la operación posterior acreditó aceptación real.
- Se repitió la comprobación de identidad y ausencia del grupo inmediatamente antes de crear.
- Se verificó que el informe de destino no existía para no sobrescribir documentación.

No auditoría general de grupos, Git o recursos ajenos. No se usó escritura como prueba de permisos antes de la operación autorizada.

## 6. Resultado de creación del grupo

**17:53:59.663669 UTC:** una única ejecución POST Microsoft Graph `https://graph.microsoft.com/v1.0/groups`, Azure CLI exit0, con respuesta que identifica el grupo creado. No se capturó un código HTTP independiente ni se inventa un status concreto a partir de exit0.

Cuerpo enviado:

```json
{
  "displayName": "grp-wordle-aks-admins",
  "description": "Administracion de AKS de Wordle TFG",
  "mailEnabled": false,
  "mailNickname": "grp-wordle-aks-admins",
  "securityEnabled": true,
  "groupTypes": [],
  "isAssignableToRole": false
}
```

mailNickname es una propiedad requerida por Graph, compatible con un grupo de seguridad sin correo; no crea un buzón. Se omitieron owners y members en la creación, para consultar el resultado y añadir después solo al miembro autorizado. No segundo grupo, duplicado o reintento.

## 7. Propiedades del grupo

GET explícito de propiedades, **17:54:00.555650 UTC**:

| Propiedad | Resultado |
|---|---|
| displayName | grp-wordle-aks-admins |
| securityEnabled | true |
| mailEnabled | false |
| groupTypes | [] |
| isAssignableToRole | false |
| membershipRule | null |
| membershipRuleProcessingState | null |
| mailNickname | grp-wordle-aks-admins |

groupTypes vacío y ausencia de regla dinámica corresponden a membresía **Assigned** de un grupo de seguridad estándar. No Microsoft 365, Unified o DynamicMembership. No se configuró un grupo privilegiado asignable a roles.

## 8. Object ID del grupo

**f35832fa-d632-43b1-a83e-112d17cc8ccc**.

La consulta final por displayName exacto devuelve un único grupo y ese mismo ID. Es el identificador operativo que podrá utilizarse posteriormente en `admin_group_object_ids` bajo una autorización de configuración separada. No se escribió en Terraform ni en archivos privados de variables en esta iteración.

## 9. Identidad del miembro autorizado

Usuario administrativo humano del propietario, tipo CLI user, Graph userType Member. Se recuperó otra vez `/me` después de crear el grupo y **antes de añadir membresía**, comprobando que el ID era el mismo del preflight.

No se dedujo pertenencia por nombre parecido, rol Storage o rol Global Administrator: la autorización actual identifica expresamente a este usuario como único miembro inicial.

## 10. Object ID del miembro

**b573130a-f09b-461b-865c-66fbd828a831**.

Coincide con el principal verificado en las iteraciones anteriores. Se documenta completo por autorización expresa como identificador operativo; no es token, contraseña ni credencial.

## 11. Resultado de la incorporación

Se consultaron los miembros del grupo recién creado antes de modificarlo: lista vacía y sin paginación. **17:54:03.408179 UTC:** único POST a `/groups/f35832fa-d632-43b1-a83e-112d17cc8ccc/members/$ref`, con:

```json
{"@odata.id":"https://graph.microsoft.com/v1.0/directoryObjects/b573130a-f09b-461b-865c-66fbd828a831"}
```

Operación satisfactoria, sin reenvíos. No otros miembros, grupos, propietarios o roles. Los dos cuerpos JSON se pasaron mediante archivos temporales nuevos externos al repositorio, eliminados en finally. No scripts persistentes ni credenciales locales nuevas.

## 12. Verificación de membresía

**17:54:04.302756 UTC:** GET `/groups/<ID>/members` devuelve **exactamente un miembro directo**, sin nextLink:

- ID: b573130a-f09b-461b-865c-66fbd828a831.
- @odata.type: **#microsoft.graph.user**.

El ID coincide con `/me` antes y después de crear. Se verifica la membresía almacenada en Graph; no se afirma que un token Kubernetes ya emitido incluya el nuevo grupo ni que exista acceso AKS efectivo. Eso se validará cuando se configure y cree el clúster autorizado.

## 13. Propietarios observados

**17:54:05.213011 UTC:** GET `/groups/<ID>/owners`: **cero entradas**, sin paginación. No se especificaron owners ni se añadió al operador como propietario mediante otra operación. No propietario automático observado.

La documentación Graph indica que un administrador que crea un grupo de seguridad sin owners no se añade necesariamente como propietario, a diferencia de otros casos. Resultado compatible con ese comportamiento. La administración futura puede realizarse mediante permisos de directorio existentes; no justifica añadir propietarios no autorizados.

## 14. Incidencias

Sin errores en creación, incorporación o consultas posteriores. Sin cambios de permisos, solicitudes de consentimiento, activación PIM o reintentos. La ausencia inicial de userType en una proyección fue resuelta con lectura explícita antes de escribir; no alteró la identidad seleccionada.

**17:54:06.111037 UTC:** consulta `/groups/<ID>/memberOf/microsoft.graph.directoryRole` devuelve cero roles, sin paginación. `isAssignableToRole=false` además confirma que no se habilitó como grupo asignable a roles. El rol Global Administrator del usuario miembro no se transfiere al grupo por esa pertenencia.

## 15. Recursos de identidad creados

Un único objeto grupo y una referencia de membresía directa al usuario aprobado. Sin propietarios añadidos, roles de directorio, Azure RBAC, identidades, aplicaciones, service principals, managed identities, credenciales o recursos ARM nuevos.

Verificación final **17:54:07.021911 UTC**: grupo exacto único, ID correcto, miembro directo único y propiedades verificadas. No limpieza automática: el grupo y la membresía autorizados se conservan.

## 16. Confirmación de ausencia de cambios fuera de alcance

El procedimiento solo ejecutó dos escrituras Graph: crear grupo y añadir miembro. Todas las demás llamadas fueron GET/listados o consultas CLI de contexto. No invocaciones ARM de escritura, role assignment, operaciones de otros grupos, owner-add, políticas, permisos, PIM, Terraform o Kubernetes.

Esta confirmación deriva de las operaciones ejecutadas y verificaciones dirigidas, **no de una auditoría global de cambios concurrentes de terceros**. No se asegura que nadie más haya actuado en el tenant durante la sesión. No es necesario ampliar el inventario del directorio para justificar el alcance propio.

Solo se crea este informe persistente local. Pendientes previos comprobados por SHA-256; índice y lista de cambios versionados conservados. Sin staging, commits, pushes o alteración del historial; no modificaciones de Terraform, documentos anteriores, backend, redes o recursos Azure. Temporales JSON eliminados.

## 17. Estado de Gate A

**GO mantenido.** Esta iteración no modifica la cuenta Storage, permisos Blob, firewall, retención, lifecycle ni contenido del backend. Se conserva la evidencia de bootstrap y lease anteriores; no se repiten esas pruebas ni se pretende nueva verificación funcional de Storage aquí.

## 18. Estado de Gate B

**NO-GO actual; requisito de identidad administrativa inicial resuelto.** Quedan configuración Sweden/versión/surge, incorporación del Object ID real a las variables, API /32 y aceptación de rangos externos, presupuesto/ventana y restantes prerrequisitos del informe Gate B.

El grupo aún no está asociado a un clúster ni existe AKS autorizado. No se otorgó Kubernetes RBAC mediante esta operación; el uso futuro de admin_group_object_ids requiere configuración/aprovisionamiento separado. **AKS permanece NO-GO.**

## 19. Próxima acción recomendada

Autorizar, en incremento separado, **configuración mínima de Terraform y sus ejemplos para Sweden Central**, usando el grupo f35832fa-d632-43b1-a83e-112d17cc8ccc, versión/surge aprobados y coordenadas del backend. Resolver en esa preparación las decisiones de API/IP y redes, sin ejecutar Terraform ni crear infraestructura por extensión.

Después, inicialización/plan y aplicación necesitan sus autorizaciones propias; esta operación de identidad no las concede. No se inicia otra fase automáticamente.

Fuentes oficiales consultadas16/11/2026: [creación de grupo y propiedades requeridas/owners](https://learn.microsoft.com/en-us/graph/api/group-post-groups?view=graph-rest-1.0), [incorporación de miembros](https://learn.microsoft.com/en-us/graph/api/group-post-members?view=graph-rest-1.0). Evidencia primaria: respuestas Graph y verificaciones dirigidas de esta sesión, sin tokens o credenciales.
