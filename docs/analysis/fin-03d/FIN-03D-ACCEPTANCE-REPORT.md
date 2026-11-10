# FIN-03D — Integración CI y aceptación local

Fecha: 10/11/2026. **FIN-03D PASS**. **FIN-03: Completado** localmente para la demo privada aceptada por el responsable. Sin commit/push ni validación remota de este cambio. FIN-04 pendiente, no iniciada.

## Preflight y alcance

Rama codex/pg01-07-consolidation, HEAD bb35711a07d19f8944d52c1d5dfa1c9c2a31755b. Inicio: índice vacío; solo backend/app/main.py y backend/.env.example modificados por FIN-03C;16 archivos sin seguimiento previstos. Se leyeron informes FIN-03A/B/C, plan, workflow/suite CORS y configuraciones pertinentes. No modificaciones ajenas detectadas.

Archivos editados por FIN-03D:

- .github/workflows/ci.yml: solo backend-tests cambia, sin nuevos jobs.
- docs/analysis/tfg-plan-001/TFG-COMPLETION-PLAN.md: aceptación expresa, matriz y FIN-03 completado; FIN-04 pendiente.
- Nuevo este informe.

Se preservan sin editar los cambios main.py/.env.example, la suite CORS y los16 archivos previos sin seguimiento. Los informes históricos FIN-03A/B/C describen su estado anterior; no se reescribe su resultado ni su afirmación histórica de CI no integrado.

## Integración preparada

El mismo job backend-tests y el mismo paso de aislamiento ejecutan secuencialmente:

1. unittest.TestLoader().discover("backend/tests"):55 casos esperados.
2. Un loader nuevo para discover("backend/cors_tests"):9 casos esperados, evita reutilizar la ruta top-level del primer discovery.

Cada suite se ejecuta una sola vez y debe cumplir recuento exacto, cero omitidos y wasSuccessful(). Una suite CORS ausente, fallida o con skipped hace fallar el paso. Las guardas sockets/DNS/dotenv/psycopg cubren imports y ambas suites. WORDLE_CORS_ORIGINS se fija explícitamente a los dos orígenes locales en el env del job para que la configuración de los tests sea determinista. Los tests de configuración ejercitan overrides/vacío/inválidos y restauran entorno.

Los otros siete jobs, triggers, permisos, dependencias/lock, versiones de acciones y estrategia de publicación permanecen idénticos estructuralmente. postgres-integration conserva once casos en su propio servicio16.15 y sus guardas. GHCR sigue if:false/sin packages:write, Terraform solo validación; sin activación Azure. No se agregan dependencias ni se modifica la lógica del juego.

## Validación realmente ejecutada

| Comprobación | Resultado |
|---|---|
| Python exacto extraído del workflow editado |55 offline aprobadas, cero omitidas,1.230s;9 CORS aprobadas, cero omitidas,0.056s, dentro de las guardas globales reales del paso |
| PostgreSQL existente en destino desechable nuevo |11 aprobadas, cero omitidas,1.974s sobre PostgreSQL16.15; tipos/rollback/locks/errores/juego |
| Caída real del PG propio |500 sanitizado,/health200,pool cerrado; cero deadlocks y tres errores SQL de rollback esperados |
| Limpieza |Contenedor wordle-pg04-c22956b16a0e y red exclusivos retirados, ausencia verificada por runner. Sin volumen ni acceso a PG-05/06 |
| Workflow |YAML parseado con PyYAML existente; comparación estructural confirma cambio solo en backend-tests y ocho jobs en total; script Python compilado y ejecutado |
| Git/whitespace |git diff --check correcto y sintaxis Python del paso correcta; índice vacío |

No se afirma validación actionlint completa: no se instala una herramienta. La ejecución local del cuerpo Python no reproduce el orquestador de GitHub, la instalación de dependencias en un runner nuevo ni todos sus contextos. No se hizo push/dispatch ni se consultó un run que valide esta versión. PUB-06 verde pertenece al HEAD publicado anterior, sin las pruebas CORS integradas.

## Decisión de perímetro y matriz de aceptación

Aceptación expresa recibida del responsable en este encargo: **demo académica privada y supervisada; datos exclusivamente sintéticos; backend y PG sin exposición pública**. No usuarios reales/datos personales, servicio público sin controles adicionales o promesas de seguridad multiusuario.

| Criterio FIN-03 | Evaluación para el alcance aceptado | Evidencia |
|---|---|---|
| Identidad/propiedad y credencial decididas/revisadas |Satisfecho: no autenticación; rol app técnico separado de owner; riesgos aceptados |Orden FIN-03D, plan actualizado, FIN-03A/B y script de rol existente |
| Negativos de lectura/escritura ajena |Satisfecho como demostración honesta de límites, NO denegación entre jugadores |FIN-03B403 distinto usuario; lectura/suplantación200 confirmadas. Responsable acepta solo el escenario privado |
| Ninguna garantía falsa por usuario_id |Satisfecho |Matriz FIN-03B y aceptación de lectura cruzada/suplantación; CORS no es identidad |
| Exposición limitada hasta acuerdo |Satisfecho en escenario ensayado y aceptado |FIN-03B Compose propio:loopback frontend, backend/PG sin ports y red interna; cliente de otra red Docker no conecta |
| CORS restringido y errores sanitizados |Satisfecho local |FIN-03C TCP y suite9; errores SQL/DB genéricos en pruebas reales previas y actuales |
| Concurrencia y consistencia mínima |Satisfecho sin prometer HA |PruebasPG-04 reales y regresión11, no simulación de locks con mocks |
| ADR/matriz/resultados |Satisfecho local |Propuesta FIN-03B queda aceptada expresamente por FIN-03D; plan y este informe registran decisión, matriz y pruebas |

No se ha cambiado la API para denegar entre jugadores. El criterio se acepta en el significado limitado de demo privada que el responsable ha especificado ahora, conservando las pruebas de brecha y no inventando401/403. Si más adelante se exige aislamiento individual o exposición pública, ese alcance no está aprobado por este cierre y requiere nuevos controles.

Configuraciones disponibles compatibles: Compose solo frontend loopback; Kubernetes local ClusterIP/port-forward loopback sobre clúster dedicado/confiable. FIN-03D no reejecuta el entorno Compose o Kubernetes ni certifica aislamiento entre todos los pods, otros administradores o máquinas LAN. PostgreSQL sigue sin HA y CORS no afecta a clientes directos o peticiones simples ya enviadas.

## Riesgos residuales y límites

Se aceptan ausencia de autenticación/autorización robusta, lecturas cruzadas, suplantación de usuario_id y capacidad de clientes internos de llamar sin Origin. CORS limita lectura cross-origin/preflight en navegadores, no acceso SQL/API por identidad ni CSRF de forma general. Los logs contienen IDs sintéticos; no se permite introducir datos reales o exportar secretos/logs crudos. La advertencia de mantenimiento Node20/24 sigue sin corregir y no se clasifica como vulnerabilidad confirmada.

Notas anteriores de README/SECURITY-NOTES o informes conservan referencias de estado anteriores; para cierre actual prevalece el seguimiento FIN-03D, no una promesa de seguridad productiva. Este incremento no amplía el alcance a redactar todos los históricos. No se activó GHCR, Azure, Supabase o FIN-04.

## Git y próxima acción

Sin commits/add/push. Final: cuatro archivos versionados modificados en total (main.py/.env.example de FIN-03C más workflow/plan), suite CORS y cuatro informes FIN-03A/B/C/D junto a doce históricos:17 archivos sin seguimiento. Índice vacío; todos los archivos previos ajenos a workflow/plan se preservan byte a byte. No se modifica ningún informe previo sin seguimiento.

Próxima acción recomendada: revisar este cierre local y autorizar por separado la consolidación/publicación del conjunto CORS+suite+workflow y evidencias, para observar55+9 y11 en una ejecución remota real. FIN-04 es la siguiente tarea según plan, sin iniciarla automáticamente. No declarar verde remoto del nuevo workflow antes de esa ejecución.
