# Motor

## Qué hace la carpeta
Calcula cuánto pedir para los días en que el proveedor no vuelve. Mira el stock, no las compras.

## Qué función, con el nombre real
* `feriados.de`: feriados nacionales del año. Un feriado no tiene reparto.
* `feriados.es`: dice si un día no reparte.
* `calcular.proyectar`: cajas o medias para cubrir desde el reparto hasta el día anterior al siguiente.
* `calcular.definir`: el pico viejo es la venta más alta. El mínimo y el máximo histórico salen del resto. Con menos de dos mediciones no define nada.
* `calcular.ritmo_de`: pide dentro del mínimo y el máximo históricos. Si la venta reciente es menor, baja hasta el mínimo. El pico no entra.
* `memoria.por_dia`: la baja de stock partida por los días del tramo. Una suba es una carga y no entra. La tabla guarda pollo, carne, cerdo, congelado y huevo. El pedido de este ciclo sigue en pollo y carne.
* `memoria.ventas`: las últimas de esa serie.

## Cómo funciona, en el orden en que corre
1. El reparto son los días marcados. El feriado se saltea.
2. La preparación es el último día que el local abre antes de ese reparto.
3. Se cubren los días abiertos hasta el próximo reparto. Un feriado o un día cerrado no se vende. El horario corrido de 8 a 20 es la jornada. Si llega a la tarde, cuenta media. El doble turno separa mañana y tarde. Un día con otro horario, si es más corto, pesa menos.
4. La cantidad es ese ritmo por los días, menos el stock que ya hay.
5. El pico viejo lo marca la venta más alta del historial y no entra en la cantidad. El mínimo y el máximo históricos son el resto de esas ventas.

## Qué devuelve cuando falla
Sin días marcados, `proyectar` pide 0 y lo dice. Si el archivo no se lee, los días vuelven a lunes, miércoles y viernes. Sin dos mediciones de stock no hay pico, mínimo ni máximo, y no se inventa esa banda.

## Qué no debe cambiar una mejora futura
No usar el pico viejo como cantidad. No guardar compras en el historial. Cerdo, huevo y congelado no pasan por acá.
