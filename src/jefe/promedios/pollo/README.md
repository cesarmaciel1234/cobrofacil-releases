# Módulo pollo
Contiene la vista y el motor matemático exclusivo para pollo.
Al cargar la interfaz, solo se precargan los cortes y kilos por defecto. El resto de la tabla se inicializa en 0 o vacío para evitar cálculos fantasma.
Al editar cualquier celda de la tabla, su motor interno recalcula las 12 columnas en orden:
Corte | Kilos | Costo$/kg | Precio Venta | % Ganancia | P. Mayoreo | Desde kg | % Mayoreo | V. Total | V. Mayoreo | Ganancia | G. Mayoreo
La última columna es Código. No entra en esa cuenta. Es el producto de la góndola: si el nombre no coincide, el stock igual cae en ese código. Al guardar, esa receta es la que recibe la fórmula.

## Método del bulto

Este es el que ya corre en recepción y el que usan Carne y Cerdo.

Un bulto son 17,5 kg útiles: Suprema 5, Pata Muslo 8, Alitas 2, Menudos 1, Carcasa 1,5. La merma no entra. El costo del kilo es el precio del bulto dividido por esos kilos. Con 2 bultos a $70.000 el total es $140.000 y el kilo sale $4.000. Las cantidades son 10, 16, 4, 2 y 3 kg. Los subtotales $40.000, $64.000, $16.000, $8.000 y $12.000 suman $140.000.

La oferta del corte se ve debajo, en gris. Lleva la misma cantidad y el mismo costo, y el subtotal queda en cero. Al confirmar, ese producto copia el stock y el costo del original. Pollo entero lleva los kilos útiles de la carga (35 kg en ese ejemplo) al mismo costo, y tampoco suma. El resumen cuenta 5 artículos y 2 bultos. La fórmula solo guarda los cortes reales.

Si se borra menudos o carcasa, esos kilos pasan a merma, el costo del kilo sube y el total del remito no cambia. El código de cada corte sale de esta pantalla. La recepción no recalcula la receta: está en `src/proveedor_global/frontend/formula/motores/consulta.py` y `extension.py`.

## Pedido

La cuenta está en `src/proveedor_global/frontend/formula/motores/caja_pollo.py`. El día vende de 3 a 5 cajas. Deciden suprema y pata y muslo, que son los cortes que generan ganancia. Las alitas no cuentan y no se piden. Menudos y carcasa van adentro de la caja y tampoco se piden solos. La merma no entra.

Con 3 cajas o menos en alguno de los dos cortes, si están parejos (menos de 3 cajas de diferencia) y los dos tienen stock, el pedido es pollo entero, en cajas, hasta que el que más tiene llegue a 5. Si uno de los dos no queda, las cajas suben hasta que el que todavía tiene stock llegue a 6, y los kilos que falten de ese corte vacío se piden aparte para completar 6. Suprema en 2 cajas y pata en cero piden 4 cajas y 16 kg de pata y muslo. Si Suprema y Pata Muslo ya tienen más de 3 cajas, esta vuelta no se compra, aunque las alitas estén en cero. Cuando entre los dos hay 3 cajas o más de diferencia, no se pide la caja porque agrandaría el desnivel: se inyectan solo los kilos del corte menor hasta completar 6 cajas de ese corte.

El stock de la fórmula es la suma de los cortes en la tabla, no la última carga menos lo vendido. En la columna Stock se puede cambiar el original a mano: eso escribe el producto, la oferta copia el mismo número y el pedido de abajo se recalcula. La oferta no entra en la suma.

Para una mejora futura: un corte empieza a decidir cuando `_rol` lo marca como plata. El piso, el techo de bultos y el techo de corte son las constantes del día. Cerdo y carne no pasan por acá.
