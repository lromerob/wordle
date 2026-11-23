# FIN-AKS-MFA-POLICY-VALIDATION — 17/11/2026

## 1. Resumen ejecutivo

**PARTIAL. MFA CONDITIONAL.** Controles identificados y consultados nuevamente:
Azure Policy BuiltIn heredada, escritura Deny y eliminación DenyAction.
Contexto autorizado confirmado. Autenticación local Azure CLI compatible con
AzureRM 4.50.0 y backend Entra de Terraform 1.9.8.
**Cumplimiento de ambos controles: UNKNOWN**, no NON-COMPLIANT.
No existe prueba concluyente de MFA reconocido por ARM para futuras operaciones.
No recomendar aprovisionamiento facturable hasta preparar y acreditar la retirada.
Gate A GO; Gate B NO-GO; AKS NO-GO.

## 2. Alcance autorizado

GET Azure/Graph, lectura selectiva de configuración e informes y documentación
oficial. Único archivo creado: este informe. Sin pruebas mutativas, Terraform,
autenticación interactiva, renovación deliberada, cambios de sesión o permisos.
Sin extracción de tokens, decodificación JWT o acceso al estado remoto.

## 3. Estado inicial

Rama codex/pg01-07-consolidation; HEAD
4d56cf265cc5f0af8c72c64f2a93373660e8f122; índice vacío.
67 archivos pendientes preexistentes registrados por SHA-256.
Plan histórico: seis altas, cero cambios/borrados/reemplazos; no repetido hoy.
Terraform 1.9.8 / AzureRM 4.50.0 según configuración y evidencias anteriores.

## 4. Referencias revisadas

Informes DEPLOYMENT-BLOCKERS, TERRAFORM-PLAN, GATE-B-READINESS y
REMOTE-BACKEND-INITIALIZATION. providers.tf, versions.tf y únicamente campos
de autenticación de metadatos locales del backend; no estado remoto.
Las referencias antiguas a grupo ausente o backend sin inicializar son históricas,
no el estado vigente.

Fuentes oficiales consultadas:
- [MFA obligatorio: alcance ARM y fases](https://learn.microsoft.com/en-us/entra/identity/authentication/concept-mandatory-multifactor-authentication).
- [Azure Policy y MFA](https://learn.microsoft.com/en-us/azure/governance/policy/tutorials/mfa-enforcement).
- [Efecto DenyAction y excepciones](https://learn.microsoft.com/en-us/azure/governance/policy/concepts/effect-deny-action).
- [AzureRM 4.50.0: autenticación](https://raw.githubusercontent.com/hashicorp/terraform-provider-azurerm/v4.50.0/website/docs/index.html.markdown).
- [Backend Terraform 1.9.8](https://raw.githubusercontent.com/hashicorp/terraform/v1.9.8/internal/backend/remote-state/azure/backend.go)
  y [construcción de clientes/autorizadores](https://raw.githubusercontent.com/hashicorp/terraform/v1.9.8/internal/backend/remote-state/azure/arm_client.go).
- [Azure CLI con MSAL](https://learn.microsoft.com/en-us/cli/azure/msal-based-azure-cli).

## 5. Identidad y contexto Azure

17/11/2026 08:22:16 UTC: account show coincide exactamente con tenant,
suscripción e identidad aprobados; suscripción Enabled, tipo user.
Graph signed-in-user coincide con operador aprobado.
Identificadores sanitizados: suscripción 11306565…1bb5, tenant aff0390f…1eb9,
operador b573130a…a831. No contexto cambiado, login ni elevación.
Las consultas posteriores finalizaron exit 0.

## 6. Inventario de controles MFA

Ámbito común: tenant-root management group aprobado; herencia hacia suscripción
y futuros recursos Wordle. ID de asignación común:
`/providers/Microsoft.Management/managementGroups/<tenant-aprobado>/providers/Microsoft.Authorization/policyAssignments/<nombre>`.

| Nombre / displayName | Definición BuiltIn (ID después de /providers/Microsoft.Authorization/policyDefinitions/) | Efecto asignado |
| --- | --- | --- |
| sys.mfa-write / Microsoft Azure Multi Factor Authentication Enforcement for Resource Write Actions | 54f51f64-eaa5-44cf-8674-830bcfd14d21 | Deny |
| sys.mfa-delete / Microsoft Azure Multi Factor Authentication Enforcement for Resource Delete Actions | f69cd8b8-9a6e-46b4-be84-244e8b127944 | DenyAction |

Ambas: enforcementMode Default; definitionVersion 1.*.*;
definición recuperada versión 1.1.0, modo All.
No notScopes devueltos ni exclusiones visibles en asignaciones.
Exenciones atScope: cero devueltas, sin nextLink. Esto describe cobertura de la
consulta autorizada, no certifica ausencia universal de controles adicionales.

## 7. Clasificación del mecanismo de control

**Azure Policy**, dos asignaciones directas a definiciones BuiltIn; no iniciativas.
No son asignaciones RBAC condicionadas ni Conditional Access.
No se detecta clasificación errónea de estas dos en DEPLOYMENT-BLOCKERS.
RBAC concede acciones; Policy puede denegarlas aunque RBAC las permita.
Conditional Access puede imponer desafíos adicionales, pero su configuración
no se ha inventariado ni se presume ausente.

## 8. Definiciones y condiciones

GET assignments de suscripción con api-version=2023-04-01 y $filter=atScope():
tres heredadas, sin nextLink. GET de ambas definiciones con misma versión API.
GET exemptions con api-version=2022-07-01-preview y atScope(): sin resultados.

La condición allOf de ambas exige simultáneamente:
1. requestContext().identity contiene idtyp.
2. idtyp es user.
3. La lista separada por comas de
   http://schemas.microsoft.com/claims/authnmethodsreferences no contiene mfa.
4. La lista separada por comas de acrs no contiene p1.

Si coincide: escritura Deny; borrado DenyAction con actionNames=[delete].
Las definiciones permiten Audit/AuditAction/Disabled, pero sus defaults de
auditoría **no** son los efectos efectivos asignados.

Por lógica de la regla, mfa presente **o** p1 presente evita esta condición de
denegación; no garantiza aceptación por otros controles.
Se documentan claves del contexto del servicio, no se exige que un JWT tenga
exactamente esos nombres. No equiparar p1 a licencia Entra P1 ni a una garantía
genérica de sesión MFA. No se ha verificado la transformación de claims del token
al contexto ARM de esta identidad.

Tercera política: sys.blockwesteurope, distinta de MFA. No cambia el destino Sweden.
La consulta directa al management group falló en el diagnóstico anterior;
la consulta heredada atScope sí obtiene las asignaciones. No confundir ambas vías.

## 9. Evaluación de la sesión

| Condición | Evidencia de esta ejecución | Conclusión |
| --- | --- | --- |
| MFA configurado | No se enumeran métodos personales | UNKNOWN |
| MFA realizado | Sin evento de autenticación verificable consultado | UNKNOWN |
| MFA reconocido por ARM para write/delete | GET no lo acredita; sin operación protegida ni claims concluyentes | UNKNOWN |
| Desafío requerido en operación futura | Posible según contexto/expiración; no se provocó | UNKNOWN |

No se consultó get-access-token para evitar una adquisición/renovación deliberada.
No se abrió la caché de credenciales. El intento de inspeccionar únicamente código
de la biblioteca instalada mediante inspect.getsource devolvió OSError (paquete
sin fuente accesible); no se forzó una vía de extracción alternativa.
No se interpreta ausencia de evidencia o de amr como ausencia de MFA.

## 10. Autenticación Azure CLI

La CLI moderna utiliza MSAL y caché protegida en Windows; la identidad actual
es usuario, no servicio principal ni identidad administrada.
Puede reutilizar credenciales y adquirir tokens según audiencia y vigencia;
no se observó ni certificó qué token se seleccionaría en un futuro apply.
Se usó el intérprete oficial instalado -IBm azure.cli para GET, evitando problemas
del wrapper .cmd con filtros URL; sin configurar otra identidad.
No se solicitó login, logout, reauth, cambio de suscripción ni refresh intencionado.
La gestión interna normal de tokens de las lecturas no se instrumentó.

## 11. Autenticación Terraform

providers.tf fija tenant/subscription y resource_provider_registrations=none,
sin secreto, certificado, OIDC ni MSI explícitos.
Sin variables ARM_* o AZURE_* presentes en el proceso de inspección.
AzureRM 4.50.0 documenta use_cli=true por defecto y use_oidc/use_msi=false.
**Mecanismo local verificado por configuración: Azure CLI**, sujeto al entorno
efectivo de cualquier ejecución futura; no se ejecutó el proveedor hoy.

Backend azurerm inicializado: use_azuread_auth=true; tenant/subscription coinciden;
sin access_key, sas_token, client_secret, certificado u OIDC configurados en los
campos inspeccionados. En Terraform 1.9.8 Azure CLI está soportado por su builder;
el backend es independiente del proveedor AzureRM.
use_cli no es una opción del esquema de ese backend 1.9.8: null en metadatos no
equivale a desactivarlo. MSI/OIDC no habilitados.

Audiencias distintas: ARM management.azure.com (según entorno también identificador
management.core.windows.net), Storage storage.azure.com y Graph graph.microsoft.com.
El código 1.9.8 crea autorizadores ARM y Storage separados.
Misma cuenta no implica mismo token ni mismas condiciones de audiencia.
El workflow OIDC futuro es otra ruta de autenticación, no prueba de esta sesión.

Las políticas consultadas actúan sobre gestión ARM. No acreditan bloqueo MFA del
plano de datos Blob: lease/lectura/escritura del estado tienen controles propios
Entra/RBAC/firewall y posible CA. Las pruebas históricas de lease no prueban
cumplimiento de sys.mfa-write/delete en ARM; no se repiten hoy.

## 12. Requisitos para creación

| Operación prevista | Requisito / límite |
| --- | --- |
| Resource Group | ARM write: contexto MFA aceptable y permiso RG write |
| VNet y subnet | ARM write y permisos Network |
| User Assigned Identity | ARM write y permiso ManagedIdentity |
| Role assignment Network Contributor en subnet | ARM write y permiso roleAssignments/write |
| AKS | ARM write y permisos ContainerService; dependencias gestionadas tienen su propio contexto |

Las seis operaciones podrían quedar denegadas por sys.mfa-write cuando se cumpla
su condición. No se afirma que todos los trabajos internos AKS se ejecuten como
el usuario. Un plan exitoso no ensaya la admisión de todos estos PUT.

## 13. Requisitos para destrucción

DELETE explícitos de AKS, rol, identidad, subnet/VNet y RG pueden quedar sujetos a
sys.mfa-delete si su condición coincide. Se necesitan además permisos de borrado,
sesión vigente y acceso al backend para registrar progreso.
DenyAction documenta excepciones para ciertos tipos administrativos y diferencias
en borrados en cascada; modo All no acredita protección uniforme de los hijos
durante eliminación de RG. No se recomienda borrar el padre para eludir MFA.
La retirada de AKS y recursos gestionados tampoco queda certificada con una prueba
sobre RG vacío.

**No recomendar apply mientras la retirada no tenga operador disponible,
autenticación recuperable y procedimiento autorizado.** No utilizar fuerza,
exenciones o cambios RBAC como solución automática.

## 14. Evidencias de cumplimiento

| Control | Resultado | Qué demuestra / qué no |
| --- | --- | --- |
| sys.mfa-write | UNKNOWN | Regla/efecto/ámbito verificados; MFA efectivo de futuras escrituras no acreditado |
| sys.mfa-delete | UNKNOWN | Regla/efecto/ámbito verificados; MFA efectivo de futuras eliminaciones no acreditado |
| Contexto y ruta de autenticación local | VERIFIED como configuración, no como cumplimiento MFA | Identidad y configuración coinciden; no ensayo de operación protegida |

No evidencia NON-COMPLIANT. LIKELY describiría compatibilidad arquitectónica, no
debe sustituir UNKNOWN sobre sesión. Lecturas, RBAC y plan histórico no dan VERIFIED.

## 15. Limitaciones

No tokens/claims ni registros de inicio de sesión inspeccionados; no CA enumerado.
Sin evaluación write/delete, fecha de expiración ni garantía de desafío futuro.
Versión asignada flotante 1.*.*: puede cambiar el comportamiento antes del despliegue.
No se ejecuta validación ARM mutativa, simulación ni Terraform de ningún tipo.
Los métodos de MFA y una autenticación exitosa por sí solos tampoco cerrarían
la incertidumbre sobre el contexto reconocido por una operación concreta.

## 16. Riesgos y mitigaciones

| Riesgo | Probabilidad / impacto | Evidencia | Mitigación propuesta | Residual |
| --- | --- | --- | --- | --- |
| Apply denegado, quizá parcialmente | No determinada / alto | Deny confirmado; sesión UNKNOWN | Acreditar MFA antes, revisar operación futura autorizada | Otros controles/admisión |
| Destroy bloqueado y cargos continúan | No determinada / crítico si no hay recuperación | DenyAction confirmado, no fallo observado | Preparar reautenticación y responsable de retirada antes de crear | Expiración/cambios de política |
| Sesión expira durante demo | Posible / alto | Credenciales temporales; vigencia no inspeccionada | Reservar margen y operador disponible | Desafío adicional |
| Confundir RBAC con MFA | Evitable / alto | Mecanismos independientes | Checklist separado de permiso/contexto | Denies adicionales |
| Cambio de definición/herencia | Posible / alto | Asignación 1.*.* | Relectura focalizada antes de operación autorizada | Cambios posteriores |
| Backend falla con otro contexto/audiencia | Posible / alto | Token Storage independiente | Conservar procedimiento de recuperación y backend | CA/red/RBAC no probados hoy |

Son riesgos, no incidentes confirmados. No hay probabilidad numérica ni certeza de
que la sesión actual falle.

## 17. Propuesta de prueba futura, si procede

**No ejecutada; requiere autorización independiente, incluida creación y borrado.**

Primero priorizar evaluación oficial sin provisión (validación de plantilla ARM).
Puede detectar errores, pero no se presume que reproduzca la condición MFA de un
PUT ni un DELETE: un validate exitoso no cerraría por sí solo esta incertidumbre.

Si sigue sin evidencia concluyente, propuesta mínima:
- Confirmar misma cuenta/contexto y autorizar reautenticación interactiva solo
  si se requiere. Responsable disponible para recuperación antes de empezar.
- Crear un RG Wordle de prueba único y vacío en Sweden Central, previa comprobación
  de inexistencia; no usar RG de app, nodos o backend ni recursos ajenos.
- Permisos mínimos RG read/write/delete; no cambiar RBAC/políticas.
- Leer resultado y eliminar exactamente ese RG, comprobando antes que continúa
  vacío y que sus etiquetas corresponden a la prueba; confirmar ausencia final.
- Evidencia: tiempos, identidad sanitizada, resultado/código de ARM, IDs de
  correlación sanitizados y ausencia final. Sin tokens ni salida de depuración.
- Éxito: creación y borrado aceptados con la identidad aprobada; solo evidencia
  para esos tipos/instante, no certificación global de AKS.
- Coste previsto del RG vacío: sin cómputo/discos/IP; no crear dependencias facturables.
- Recuperación: si MFA bloquea borrado, detener creación adicional; reautenticación
  del mismo operador mediante autorización futura expresa y repetir solo la
  eliminación aprobada. Si no basta, escalar al administrador autorizado;
  no elevar roles ni cambiar políticas automáticamente. RG vacío remanente se
  registra como incidencia sin cómputo, con responsable y seguimiento de limpieza.
  No iniciar sin recuperación disponible.
- Si el tipo RG no permite acreditar ambos controles, no ampliar a VMs/AKS:
  reevaluar evidencia y autorización. La semántica de cascada no es una prueba
  de que se pueda destruir toda la infraestructura.

## 18. Recomendación MFA

**MFA CONDITIONAL**: ruta compatible, sin incumplimiento confirmado.
No MFA READY; falta acreditar contexto aceptado y recuperación de retirada.
No se recomienda desplegar aceptando sin más el riesgo crítico de destroy.
Nueva autenticación podría ser necesaria, no demostrada ni ejecutada.

## 19. Recomendación Gate B

Mantener **NO-GO**. Resolver evidencia MFA/recuperación mediante próxima
autorización independiente y revisar las demás condiciones ya identificadas
(costes, Run Command) sin reabrir auditoría general.
MFA CONDITIONAL no autoriza creación ni cambia el gate.

## 20. Estado Gate A

**GO**, histórico mantenido; backend/lease no consultados ni modificados.

## 21. Estado Gate B

**NO-GO**, sin modificación automática.

## 22. Estado AKS

**NO-GO**, sin despliegue autorizado ni ejecutado.

## 23. Integridad del repositorio

Único archivo creado: este informe. Sin modificar los 67 pendientes preexistentes,
HEAD, índice, archivos Terraform, lock ni caché/metadatos locales del backend:
comparación SHA-256 y listado final. git diff --check: PASS, exit 0, sin errores de whitespace. Advierte conversión
LF a CRLF en cuatro archivos preexistentes (informe FIN-04, plan FIN y scripts
observability/run_observability.py y validation.py); no se modifican ni normalizan. Verificación final: 68
archivos pendientes (67 preexistentes intactos y este informe nuevo).
No staging, commits, push ni limpieza.
No terraform plan/apply/destroy/init/import/refresh/state/force-unlock.
No recursos Azure creados/modificados/eliminados; no cambios Entra/Policy/RBAC,
credenciales, backend o estado remoto. Solo lecturas autorizadas.

## 24. Próxima acción recomendada

Revisar este PARTIAL y autorizar separadamente, si se acepta, la prueba mínima y
su recuperación/autenticación. No iniciar apply ni fase siguiente automáticamente.
