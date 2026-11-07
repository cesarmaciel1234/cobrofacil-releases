# Planificación operativa

## Qué hace la carpeta

Convierte el panorama de señales en un plan identificable y listo para revisión.

## Qué función, con el nombre real

* `construir(panorama, politica)`: crea el contenido inmutable de un plan.

## Cómo funciona

Toma las acciones ordenadas por prioridad, conserva la versión de política usada y genera un identificador único. No modifica las cantidades que ya calcularon las fórmulas.

## Qué devuelve cuando falla

Devuelve un plan vacío pero válido, que se puede guardar como borrador sin bloquear al resto del negocio.

## Qué no debe cambiar una mejora futura

No convertir acciones en compras reales: eso pertenece a `ejecucion/` y requiere un cambio explícito de estado.
