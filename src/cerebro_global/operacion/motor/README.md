# Motor del cerebro operativo

## Qué hace la carpeta

Convierte las señales de abastecimiento y compra predictiva en un único borrador de acciones priorizadas.

## Qué función, con el nombre real

* `analizar(db=None)`: consulta los motores existentes y devuelve el panorama.
* `evaluar(predictiva, resumen, hoy=None)`: función pura que unifica las propuestas entregadas por esas fuentes.
* `preparar_plan(db=None)`: construye y guarda un plan en estado `BORRADOR`.

## Cómo funciona

1. Toma la proyección de Pollo y Carne hasta el próximo reparto.
2. Toma las líneas ya calculadas por `MotorAbastecimiento`.
3. Agrupa por fórmula y unidad. Si coinciden, elige la cantidad mayor para no quedar corto y conserva ambas explicaciones.
4. Ordena primero las acciones que deben prepararse hoy, luego las de stock crítico y finalmente las programadas.
5. Si se llama `preparar_plan`, el plan pasa por `planificacion/` y `ejecucion/`, y queda auditable en la base.

## Qué devuelve cuando falla

Cada fuente puede faltar sin invalidar la otra. Devuelve `acciones` vacía y una lista `fuentes_fallidas` cuando no hay datos disponibles.

## Qué no debe cambiar una mejora futura

No envía pedidos, no escribe inventario y no decide el precio. Toda acción queda en `borrador` con `requiere_revision=True`.
