# Módulo cerdo
Contiene la vista y el motor matemático exclusivo para cerdo.
Al cargar la interfaz, solo se precargan los cortes y kilos por defecto. El resto de la tabla se inicializa en 0 o vacío para evitar cálculos fantasma.
Al editar cualquier celda de la tabla, su motor interno recalcula las 12 columnas en orden:
Corte | Kilos | Costo$/kg | Precio Venta | % Ganancia | P. Mayoreo | Desde kg | % Mayoreo | V. Total | V. Mayoreo | Ganancia | G. Mayoreo
La última columna es Código. No entra en esa cuenta. Es el producto de la góndola: si el nombre no coincide, el stock igual cae en ese código. Al guardar, esa receta es la que recibe la fórmula.

## Alta, baja y fórmula

`Alta corte` pide el nombre, los kilos y el código. `Baja corte` saca el corte elegido de la tabla. El nombre y los kilos también se cambian con doble clic. `Guardar nueva fórmula` no pide proveedor ni precio. Pide los kilos del bulto y un peso en cada corte que tenga nombre. Si un corte no tiene kilos, está repetido o la suma pasa el bulto, no guarda y dice el motivo. La receta queda en `formula_orden` y en `reportes/formula_receta.json` de esta PC. El precio sale de ahí: kilos del bulto por el precio del kilo, dividido por los kilos útiles, sin la merma. De 100 kg, cada corte conserva el peso cargado. `Repartir` recalcula la merma y no pisa esos pesos. Si todavía no hay fórmula guardada, la lista es Pechito, Bondiola, Matambre, Carré y Costillitas. Antes de escribir, `revisar` en `receta.py` frena el guardado. `MotorPromedios.guardar_formula` publica la orden. Al abrir, `MotorCerdo.receta` lee `orden.traer`.

## Método del bulto

El mismo que Pollo, con la receta de esta carpeta. El cerdo no entra en el libro de la carne ni en el del pollo. El precio del bulto se divide por los kilos de esta receta, sin la merma. Borrar un corte lo pasa a merma y sube el costo del kilo. El total sigue siendo bultos por precio.

El enlace de una oferta se ve debajo del corte, en gris. Copia el stock y el costo del original y el subtotal queda en cero. No entra en el libro de la fórmula. La pieza entera, si se agrega, va al lado de Pollo entero en `src/proveedor_global/frontend/formula/motores/extension.py`: recibe los kilos útiles y el costo real, y no suma al total. El ejemplo numérico que ya cuadró está en `pollo/README.md`.
