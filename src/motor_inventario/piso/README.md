# Puente de piso y techo

Mini motor. La pantalla no escribe `productos`. Este puente graba solo `stock_minimo` y `stock_maximo`.

## Qué hace la carpeta
Recibe la lista que el operador confirmó y la deja en la ficha del producto. Después le pide a la planilla que relea. Si esa relectura falla, el piso ya quedó guardado.

## Qué función, con el nombre real
* `validar_piso_techo(filas)`: revisa números, negativos y techo debajo del piso. Si una fila está mal, no devuelve ninguna.
* `guardar_piso_techo(filas)`: `UPDATE productos SET stock_minimo = ?, stock_maximo = ? WHERE id = ?`. No escribe `stock`.
* `HiloGuardarPiso`: hilo de la pantalla. Llama a `guardar_piso_techo` y emite `(ok, mensaje)`. Si se cae, emite falso y el texto «El stock sigue igual».

## Cómo funciona, en el orden en que corre
1. El botón Guardar arma la lista y arranca `HiloGuardarPiso`. La ventana no espera el `UPDATE`.
2. El hilo valida. Si algo está mal, no escribe.
3. Graba piso y techo, producto por producto.
4. Llama a `MotorPlanilla.avisar()`. El hilo de la planilla es el que reescribe la hoja. Si el aviso falla, el piso igual quedó.

## Qué devuelve cuando falla
`(False, mensaje)`. No hay excepción hacia la ventana. La venta no se entera.

## Qué no debe cambiar una mejora futura
* No poner este `UPDATE` en la pantalla ni en `descontar_stock`.
* No escribir la columna `stock` desde acá.
