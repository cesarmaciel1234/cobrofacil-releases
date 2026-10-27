# Subcarpeta Detector (Detección de Faltantes y Quiebre de Stock)

## Qué hace la carpeta
Copia la planilla. No calcula la cantidad.

## Qué función, con el nombre real
* `obtener_productos_bajo_minimo()`: llama a `preguntar_alarma()` y copia `cantidad_sugerida`. No tiene otra cuenta.

## Cómo funciona, en el orden en que corre
1. Llama a `preguntar_alarma()`, que lee `planilla_reposicion`. No importa el catálogo ni consulta `productos`. Si la fila trae `cantidad_sugerida`, usa esa.
2. Copia `cantidad_sugerida`. Cero significa que la fila se muestra y no se pide.
3. Multiplica la cantidad por `costo`. Si la cantidad es cero, el costo del renglón es cero. El `motivo` viaja con el ítem: `reposicion`, `critico` o `sin_piso`.

## Qué devuelve cuando falla
* Si el inventario no contesta, registra el error y devuelve `[]`. La pantalla queda en cero, no se traba.

## Qué no debe cambiar una mejora futura
* No volver a consultar `productos` desde acá. La alarma la responde `src/motor_inventario/alarma`.
* No escribir `productos`.
