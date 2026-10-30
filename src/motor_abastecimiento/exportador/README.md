# Subcarpeta Exportador (Formato y Salida de Pedidos)

## Qué hace la carpeta
Convierte los cálculos matemáticos de faltantes en mensajes amigables, formateados y estructurados para ser enviados inmediatamente por WhatsApp, impresos o revisados por el comerciante.

## Qué función, con el nombre real
* `generar_texto_whatsapp(pedido_proveedor, nombre_comercio)`: Genera el texto de un proveedor. No imprime el código interno EN CASA.
* `mensaje_general(pedidos, nombre_comercio)`: Un solo texto para Todos, con los artículos y sin nombre de proveedor.
* `generar_resumen_general(pedidos_agrupados)`: Cuenta las fichas de proveedor, sin el grupo sin asignar, y suma el presupuesto. Si no hay costo, ese presupuesto es el precio de venta por la cantidad.

## Cómo funciona, en el orden en que corre
1. Recibe el diccionario de un proveedor con sus ítems calculados.
2. Escribe cada producto con la cantidad (`*10 a 12x* Caja de pollo`). Sin el motivo ni los que no se piden.
3. Añade el pie de confirmación de entrega.

## Qué devuelve cuando falla
* Si el diccionario de ítems viene vacío, genera un mensaje indicando que no hay productos faltantes para ese proveedor.

## Qué no debe cambiar una mejora futura
* Mantener la legibilidad en pantallas de celulares de los repartidores/distribuidores.
