# Plano — nodo portable

El código está en `motor_nodo.py`. La función de entrada del catálogo es `importar_catalogo_desde_nodo`.

## Frente

La pantalla del jefe dispara la sync. No decide qué tablas viajan. Eso está fijo en el motor.

## Fondo

La maestra del negocio es dueña de las ventas. El nodo de casa es dueño de los cambios de catálogo.

Hacia el nodo viajan ventas, cierres, auditoría, detalle de venta y movimientos de caja. El nodo las lee. No inventa ventas.

Hacia la maestra viajan productos, proveedores, departamentos, categorías, combos y clientes. Al volver al negocio, el catálogo de la maestra se actualiza con lo hecho en casa.

No hay «importar ventas desde el nodo», salvo que ese nodo haya sido promovido porque cayó el servidor. Las ventas salen del negocio. El catálogo entra desde casa.

Los PNG de productos se sincronizan aparte, con los archivos de `Catalogos/png_productos`. No van dentro del upsert de la tabla.

## Qué no cambiar

No invertir las dos vías. Un choque de id deja las dos bases distintas.
