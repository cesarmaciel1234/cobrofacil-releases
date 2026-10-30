# Alarma de reposición

El inventario dice qué producto está en alarma. Solo la usa `MotorPlanilla.actualizar()`. Pedidos no llama acá: lee la planilla.

## Qué hace la carpeta
Lee `productos` y devuelve los que ya están en alarma.

## Qué función, con el nombre real
* `productos_con_alarma_reposicion()`: lista de dict con id, código, nombre, departamento, stock, stock_minimo, stock_maximo, costo, precio y `motivo`.

## Cómo funciona, en el orden en que corre
1. `SELECT` sobre `productos`. No hace `UPDATE` ni `DELETE`.
2. Entra si el stock es cero o negativo (`motivo` = `critico`). Es el mismo corte que el pie del catálogo llama «Stock crítico».
3. Entra si hay piso cargado (`stock_minimo` > 0) y el stock está en ese piso o debajo (`motivo` = `reposicion`). Si las dos cosas pasan, gana `reposicion`.
4. Deja afuera artículo común y venta libre.
5. Un stock bajo pero todavía positivo, sin piso cargado, no entra. El color de la grilla (menos de 5) no es una alarma de pedido.
6. Una fracción de un producto con fórmula no se pide suelta. Huevo, Mocho, Pecho, Media res, Cerdo, Pollo y Congelado entran una vez, como cajón o bulto, con ese nombre. Lo junta `formula/motores/bulto_pedido.py`.

## Qué devuelve cuando falla
Lista vacía. El error queda en el log `alarma_inventario`.

## Qué no debe cambiar una mejora futura
* La regla vive acá. Abastecimiento pregunta, no copia el `SELECT`.
* No escribir `productos` desde esta carpeta.
