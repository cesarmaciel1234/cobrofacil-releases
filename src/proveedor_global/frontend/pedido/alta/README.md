# Alta

## Qué hace la carpeta
El cuadro para crear una ficha de proveedor.

## Qué función, con el nombre real
* `DialogoAltaProveedor`: pide nombre y teléfono y llama a `FichaProveedor.crear`.
* `DialogoAltaProveedor._crear`: guarda y cierra si la ficha salió bien.

## Cómo funciona, en el orden en que corre
1. El operador escribe el nombre y, si quiere, el teléfono.
2. Crear id llama a la ficha. El número lo pone la tienda.
3. Si no hay tienda, la ficha queda igual y el código interno no se muestra.

## Qué devuelve cuando falla
Un aviso y el cuadro sigue abierto.

## Qué no debe cambiar una mejora futura
No mostrar el código EN CASA. No inventar un id fijo en esta PC.
