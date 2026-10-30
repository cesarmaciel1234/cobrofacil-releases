# Pedido

## Qué hace la carpeta
Arma el pedido de faltantes. Está partido en tres piezas para no dejar todo en un solo archivo.

## Qué función, con el nombre real
* `alta/dialogo.py`: `DialogoAltaProveedor`.
* `vincular/dialogo.py`: `DialogoVincularProveedor`.
* `pantalla/panel.py`: `PanelPedidosAutomaticos`.
* `reparto.py`: `dias` y `guardar`, el calendario del proveedor.
* `stock_memoria.py`: `anotar`, el stock de cada suelto. No guarda la compra.
* `sugerir.py`: `preparar` y `decidir`, la cantidad del suelto.
* `panel.py`: solo reúne esas tres para el resto del programa.

## Cómo funciona, en el orden en que corre
1. La tarjeta Realizar pedido abre `PanelPedidosAutomaticos`.
2. Asignar proveedor abre `DialogoVincularProveedor`.
3. Si el nombre no existe, ese cuadro abre `DialogoAltaProveedor`.

## Qué devuelve cuando falla
Cada pieza avisa en su cuadro. La pantalla no inventa faltantes.

## Qué no debe cambiar una mejora futura
Los imports de afuera siguen entrando por `pedido/panel.py`. No hace falta conocer las carpetas de adentro.
