# FIN-05/06/07 — Infraestructura integrada

Fecha: 10/11/2026. Rama `codex/pg01-07-consolidation`, HEAD preservado `774405e6b92c33b438509832c6722605fee7d289`. Sin commit ni push.

## Resultado y alcance

- **FIN-05 PARTIAL**: implementación/perfil y validación local satisfactorios. Terraform existente ya cubría RG, VNet/subred, AKS Free, pool System parametrizado, identidad/permisos y outputs; se reutiliza sin duplicar recursos. Nuevo overlay AKS usa runtimes GHCR por SHA, readiness SQL, backend ClusterIP y PostgreSQL 16.15 con una réplica y PVC managed-csi 8Gi. Falta resolver la dependencia FIN-04: publicación/disponibilidad/digests GHCR. No se exige Azure para la prueba inicial ni se afirma haber desplegado AKS; FIN-18 verificará el destino real.
- **FIN-06 PASS local**: Traefik 3.7.17 fijado por digest, RBAC y Service privado, Ingress host wordle.test y rutas / y /api. Prueba HTTP real a través del controlador, no directamente al frontend. Diseño DNS/TLS privado documentado; LB/TLS Azure no desplegados.
- **FIN-07 PASS local**: configuración externa explícita, contraseñas sintéticas distintas solo en entorno/Secret, referencias coherentes, frontend sin claves y recuperación externa comprobada con backend nuevo. Permisos, custodia y procedimiento de rotación/recuperación documentados; rotación SQL no ejecutada.

Ruta demostrada: navegador → port-forward loopback al controlador → Traefik/Ingress → Nginx → /api → FastAPI → PostgreSQL/PVC. Todos los Services son ClusterIP; no hay NodePort, LoadBalancer de aplicación ni exposición pública de PostgreSQL. La demo sigue siendo privada y supervisada; no existe autorización robusta por jugador.

## Validaciones realizadas

- Terraform **1.9.8**, imagen oficial temporal `hashicorp/terraform:1.9.8`, copia aislada: `fmt -check`, `init -backend=false -input=false`, `validate`: **exit 0**. Sin binario global, estado remoto, plan, credenciales o llamadas de administración Azure. Proveedor AzureRM fijado existente, sin modificar código Terraform. Se conservan dos D4s_v5 parametrizados; no se inventa un SKU más barato compatible ni una cuota regional disponible.
- Kustomize: `local` (6 objetos), `aks` y `demo-kind` (19 objetos cada uno), render correcto. Memoria solo en local; ambos perfiles nuevos usan backend real sin memory_server. Sin objetos Secret ni valores de contraseña en los renders; backend/PG usan secretKeyRef. Sintaxis Python correcta.
- Nueva demo reproducida desde cero en `wordle-fin0507-2a94fd1a`, Kubernetes **1.35.0**, PostgreSQL **16.15**, cuatro workloads Ready y PVC Bound. Admission/dry-run server y despliegue correctos. Contratos SQL del baseline ratificado y cinco palabras verificados.
- HTTP por Ingress: frontend 200, /api/health 200, host ajeno 404; partida creada, palabra inválida 400, solución activa oculta, victoria y un intento persistidos mediante SQL real. La prueba no usa mocks ni Supabase.
- Secret wordle-db eliminado y recreado con los mismos valores desde el entorno externo, sin leer sus datos desde Kubernetes. Backend reiniciado y nueva partida por HTTP: dos partidas comprobadas en SQL. Pod PostgreSQL recreado: mismo PVC, ambas partidas y victoria conservadas; lectura HTTP posterior correcta.
- Ejecución sin flag de autorización rechazada antes de acceder a Kubernetes. No se repiten las 87 pruebas de aplicación: no se modificó aplicación ni CI.
- Limpieza: eliminados los dos clústeres propios usados en la validación y sus ficheros temporales/port-forward; continúa únicamente el clúster preexistente wordle-pg06-00f26f1f. Imágenes/cachés locales permanecen. No se modificaron recursos PG-05/PG-06.

## Incidencias resueltas durante esta validación

1. GitHub anunciaba Traefik v3.7.18 pero el registro oficial no tenía ese tag. Se eligió v3.7.17 disponible, de la rama 3.7 soportada, con digest `sha256:f4bb143d1135a579b630ed491e17ec50f6f7c9c6a30585ff3d385471d2a86f5a`.
2. Importar por referencia digest desde Docker 29 produjo CreateContainerError en kind. El overlay local y el archivo de importación usan la etiqueta de la imagen ya descargada/verificada; AKS conserva digest. La segunda ejecución funcionó sin intervención manual.
3. En la primera ejecución, tras reiniciar backend apareció 504 transitorio antes de actualizarse la ruta. El ejecutor ahora espera recuperación mediante GET antes de un POST no idempotente, sin reintentar escrituras. Se limpiaron sus recursos antes de repetir la prueba integrada; la reproducción final terminó PASS. La disponibilidad continua no queda garantizada.

## Archivos y reproducción

Nuevos: `k8s/aks/{kustomization.yaml,controller.yaml,ingress.yaml}`, `k8s/demo-kind/{kustomization.yaml,run_demo.py}`, `scripts/configure_demo_secrets.py` y este informe.
Actualizados: `k8s/README.md` (comandos, permisos, secretos, DNS/TLS), `infra/terraform/README.md` (PostgreSQL actual/perfil) y plan FIN (estados locales). Baseline SQL, aplicación, Docker, CI, Terraform .tf y manifiestos PG-06/local permanecen intactos.

Desde la raíz con Docker, kind, kubectl y Python existentes:

```sh
python -B k8s/demo-kind/run_demo.py --run-disposable-kind
kubectl kustomize k8s/aks
```

En Windows: `.venv\Scripts\python.exe`. El ejecutor crea y elimina exclusivamente un clúster aleatorio propio. El procedimiento manual para un entorno nuevo autorizado y la recuperación del Secret están en `k8s/README.md`; requieren kubeconfig/contexto explícitos y WORDLE_DEMO_ADMIN_PASSWORD/WORDLE_DEMO_APP_PASSWORD externos. No se incorporan ejemplos con credenciales utilizables ni se almacenan contraseñas en Git/artifacts. Exclusiones existentes de .env, secrets/, claves y *.kubeconfig son suficientes: no se generan archivos privados en el repositorio.

## Pendiente y límites

GHCR sigue deshabilitado y no se han publicado imágenes. Azure sigue sin aprovisionar: faltan autorización, cuota/región/versión, revisión de coste, acceso Entra, paquetes accesibles y comprobación CSI real. Nodos, discos, IP/salida y almacenamiento de estado son facturables; Free no los elimina. El PVC local no prueba un disco Azure. HTTP local sin dominio/TLS real; cualquier futuro acceso de red exige DNS/TLS privado y revisión del perímetro. No hay HA, garantía de aislamiento entre jugadores ni NetworkPolicy comprobada: kind no se presenta como prueba de aislamiento de red. El controlador necesita leer Secrets en su namespace; limitar acceso administrativo y no compartirlo con cargas ajenas. No hay operadores, Key Vault, Helm, cloud extra ni Blue-Green.

Los doce informes históricos y la modificación local del informe FIN-04 se preservan byte a byte; índice vacío. `git diff --check` satisfactorio. La evidencia es local, no una nueva ejecución GitHub Actions.

Fuentes oficiales: [Traefik Ingress](https://doc.traefik.io/traefik/reference/install-configuration/providers/kubernetes/kubernetes-ingress/), [soporte de releases](https://doc.traefik.io/traefik/deprecation/releases/), [restricciones pool System AKS](https://learn.microsoft.com/en-us/azure/aks/use-system-pools).
