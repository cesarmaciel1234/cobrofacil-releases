# Fórmula

Por dónde, igual que en promedios del jefe. La receta original la escribe el jefe. Esta carpeta la acepta y no inventa otra.

| Si hay que… | Ir a |
|---|---|
| Crear la receta, los kilos, la merma y el código | `src/jefe/promedios/plano.md`. Carne, Cerdo y Pollo. La última columna es el código. Huevo no se toca. |
| Publicar esa receta | `src/jefe/promedios/motor_global_promedios.py`, `_publicar_orden`. Queda en `formula_orden`. |
| Leerla sin recalcular | `motores/orden.py`. `cortes` son los kilos. `codigos` es el producto. |
| Armar el remito | `motores/consulta.py`, `al_elegir`. Busca el código. Si el jefe no cargó código, usa el nombre exacto. |
| Escribir stock y costo | `motores/inventario.py`, `aceptar`. Con código, no adivina por el nombre. |
| Ver el enlace en la recepción | `motores/extension.py`. Copia stock y costo del original. Pollo entero suma los kilos útiles. El subtotal queda en cero y la fórmula no los cuenta. Carne y Cerdo usan este mismo método. |
| Avisar a la maestra | `motores/aviso.py`, `consultar`, en `HiloAviso`. No escribe stock y no baja el catálogo. Si la carga quedó en cola, el servidor la nutre. |
| Ver el nombre del original | Arriba: Este es el producto dice «760 es Suprema». El código sale de Promedios del jefe. Abajo solo Enlazar y Quitar. |
| Enlazar o quitar una oferta | Código a enlazar. Enlazar la agrega; si ya está, la marca en amarillo. Quitar dice «no existe» o «970 of. Pata Muslo quitado». El original no se borra: lo cambia el jefe en Promedios. El stock gris no entra en el total. Los kilos de la receta no van en la tabla: quedan abajo, por bulto. `motores/pieza.py` y `panel.py`. |
| Vender | `src/base_de_datos/repos/stock_descuento.py` pide `pieza.original_id` y descuenta solo ese producto. |

Qué hace: la tarjeta Fórmula del panel de proveedores. Compra predictiva está en `frontend/predictiva/plano.md`. En la lista de un corte, el texto de abajo dice que la info se extrae del promedio del jefe.

Qué función: `PanelFormula`. `inicio` muestra Carne, Cerdo, Pollo, Huevo y Congelado. `retroceder` vuelve un paso.

Cómo funciona: Carne abre Media res, Mocho y Pecho. Las tres usan el mismo stock de kilos. Abajo se ve la última carga, el stock y los kilos vendidos en vivo. El pedido sale al 60%. Si mocho y pecho llegan juntos, pide una media res. No escribe el inventario. Hay dos códigos: el del producto, que es el stock, y el que se enlaza. El enlace entra como fila debajo. Kilos, stock y vendido del corte no se mezclan con esa fila. Ahí se ve cuánto vendió ese código y a qué producto le resta. Pollo, cerdo y congelado tienen su propio stock. En Pollo ese stock es la suma de los cortes: la columna Stock del original se puede editar, la oferta copia el número y no entra en la suma, y el pedido de abajo sigue esa suma. El jefe deja los kilos y la merma; la fórmula los acepta y le manda al inventario el stock de cada corte y el costo. La merma no entra. El cajero vende el producto de la góndola. El pedido sale al 60%. En pollo, cerdo, carne y congelado el precio del cajón se divide por los kilos de la receta, sin la merma. Si en la recepción se borra menudos o carcasa, esos kilos pasan a merma, no entran al stock y el mismo precio se divide por menos kilos: sube el costo. El total de la compra no cambia. Huevo es otro módulo y no usa esta cuenta. Huevo abre el cajón y una tabla por fracción. Las tres tablas usan el nombre del producto. Arriba se ve cuánto queda de verdad y cuánto se vendió en el período. Vendido sale de las ventas, en un hilo. Si se vendió un maple, esa fila queda en Vendido y las otras se reajustan: 2 de huevo x 15, 3 de huevo x 10 y 5 de huevo x 6. El filtro es hoy, ayer, semana, semana pasada, mes, mes pasado, año o todo. El costo es el del cajón. No muestra el precio de venta.
