# PUB-03 — Evaluación de conflictos por lectura

Fecha: 09/11/2026. No se ejecuta merge/rebase, tampoco de prueba; no se usa merge-tree que pueda escribir objetos. No se modifica el árbol de trabajo.

## Comparación confirmada

HEAD a666b17680781a24889ea774778019995d3fca45 es el ancestro común con origin/main86cbf8936dc04abc39b8bee26c37767328db13df. Main tiene un commit adicional de merge PR#5; HEAD no tiene commits exclusivos. La referencia main anterior a fetch era ed6b45bd7e827c9714f6d0978ac81b42e82af749.

`git diff --name-status -M HEAD origin/main` y el diff ancestro común..main no devuelven rutas. Ambos árboles son cf8c64542e1e1a79dd581415d41c22161141a89a. Igualdad de árboles/objetos confirma ausencia de diferencias de contenido en el estado inspeccionado, más fuerte que no encontrar nombres coincidentes.

| Categoría | Resultado |
|---|---|
| Archivos remotos modificados desde el ancestro | 0 |
| Altas remotas | 0 |
| Bajas remotas | 0 |
| Renombrados remotos | 0 |
| Rutas remotas que coinciden con las81 candidatas locales | 0 |
| Nuevos archivos remotos que colisionen con las65 rutas sin seguimiento | 0 |
| Conflicto de contenido confirmado | Ninguno |
| Divergencia de commits lateral | No: HEAD ancestro de main, 0/1 |

No se ha aplicado ni simulado integración; no se garantiza una futura operación si main o los archivos cambian. La conclusión se limita al fetch de PUB-03 y a los81 candidatos actuales. Una ruta no coincidente por sí sola nunca acreditaría integración funcional; aquí se comprobó además identidad de los árboles base.

## Dependencias y riesgos potenciales

No hay cambios remotos que puedan sustituir app/repository.py, lock/tests, baseline/seed o recursos Compose/kind. La migración y scripts todavía locales deben acompañar al workflow en el primer commit, según PUB-02; publicar solo la parte ya versionada sí produciría un checkout incompleto, aunque Git no dé conflictos.

Los históricos allow_all/roles abiertos siguen fuera de bootstrap; incluirlos solo con la nota de alcance no crea conflicto Git, pero exige mantener su separación semántica. El literal de CI es público/desechable, no una credencial del entorno conservado.

La rama antigua ya se integró en main mediante PR#5. Reutilizarla permitiría un commit hijo de a666b17, pero conservaría una base de historial un merge por detrás aunque sus archivos coincidan. Es viable sin rebase y sin conflicto detectado; una rama nueva desde main actualizado ofrece trazabilidad más clara.

Un cambio futuro de main, una rama de publicación remota ya existente o archivos nuevos fuera del manifiesto requieren otra inspección. No forzar checkout, no stash automático, no overwrite/reset para resolverlos. Las imágenes, volúmenes PG-05 y clúster/PVC PG-06 no intervienen en este análisis y no se tocaron.

## Clasificación

Ausencia de colisiones detectadas y árboles base idénticos confirmados. **READY FOR COMMIT**, conforme a la estrategia propuesta y sujeto a autorización de las operaciones siguientes; no es autorización de commit/push ni afirmación de CI remoto aprobado. Tres informes nuevos adicionales deben aprobarse por separado si se pretende pasar de81 a84 rutas.
