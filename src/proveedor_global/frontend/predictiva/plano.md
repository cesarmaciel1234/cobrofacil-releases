# Compra predictiva

## Frente
Se abre en Fórmula, tarjeta Compra predictiva. El centro muestra la cantidad de este ciclo y el historial de stock, sin el texto de la cuenta. La tuerca abre la configuración: días de reparto y, en cada día, horario corrido o doble turno con el segundo horario al lado. Después del domingo figura el feriado, que no abre. El pedido de este ciclo sigue siendo solo pollo y carne. El producto suelto no se carga acá: sus días están en el proveedor.

## Fondo
`motor/calcular.py` cuenta los días abiertos hasta el próximo reparto y resta el stock. `calendario/jornada.py` dice qué días abre el local, el horario y si la carga llega a la mañana o a la tarde. `motor/feriados.py` saltea el feriado nacional. `motor/memoria.py` guarda los días de cada fórmula y el stock en `reportes/compra_predictiva.json`. El mínimo viejo sigue en el archivo y la pantalla no lo pide. `consultar.py` anota el stock de hoy y arma el texto. El pico viejo, el mínimo histórico y el máximo histórico los define el stock. El pico es el día que más se vendió y no se compra. Con menos de dos mediciones el sistema todavía no los define.

## Qué no romper
La carga de un bulto sigue sumando stock. Huevo no usa esta cuenta. El pie del WhatsApp no se cambia.
