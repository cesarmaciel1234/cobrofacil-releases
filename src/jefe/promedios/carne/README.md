# Módulo carne
Contiene la vista y el motor matemático exclusivo para carne.
Al cargar la interfaz, solo se precargan los cortes y kilos por defecto. El resto de la tabla se inicializa en 0 o vacío para evitar cálculos fantasma.
Al editar cualquier celda de la tabla, su motor interno recalcula las 12 columnas en orden:
Corte | Kilos | Costo$/kg | Precio Venta | % Ganancia | P. Mayoreo | Desde kg | % Mayoreo | V. Total | V. Mayoreo | Ganancia | G. Mayoreo
La última columna es Código. No entra en esa cuenta. Es el producto de la góndola: si el nombre no coincide, el stock igual cae en ese código. Al guardar, esa receta es la que recibe la fórmula.

## Método del bulto

El mismo que Pollo, con la receta de esta carpeta. Mocho, Pecho y Media res no se mezclan en el remito: se carga la que se elige. El precio del bulto se divide por los kilos de esa receta, sin la merma. Borrar un corte lo pasa a merma y sube el costo del kilo. El total sigue siendo bultos por precio.

El enlace de una oferta se ve debajo del corte, en gris. Copia el stock y el costo del original y el subtotal queda en cero. No entra en el libro de la fórmula. El libro de kilos de la carne sigue siendo uno solo para Mocho, Pecho y Media res. Los kilos de una no se suman a los de otra como si fueran otro animal.

La pieza entera, si se agrega, va al lado de Pollo entero en `src/proveedor_global/frontend/formula/motores/extension.py`: recibe los kilos útiles y el costo real, y no suma al total. El ejemplo numérico que ya cuadró está en `pollo/README.md`. Las recetas están en `mocho/`, `pecho/` y `media_res/`.
