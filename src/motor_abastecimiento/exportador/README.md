# Subcarpeta Exportador (Formato y Salida de Pedidos)

## Qué hace la carpeta
Convierte los cálculos matemáticos de faltantes en mensajes amigables, formateados y estructurados para ser enviados inmediatamente por WhatsApp, impresos o revisados por el comerciante.

## Qué función, con el nombre real
* `generar_texto_whatsapp(pedido_proveedor, nombre_comercio)`: Genera el texto con negritas y emojis estándar de WhatsApp listo para copiar al portapapeles.
* `generar_resumen_general(pedidos_agrupados)`: Agrega los totales globales de artículos a comprar y presupuesto estimado de inversión.

## Cómo funciona, en el orden en que corre
1. Recibe el diccionario de un proveedor con sus ítems calculados.
2. Formatea cada producto con su cantidad sugerida (`• 24x Aceite Girasol 1.5L`).
3. Calcula el total de bultos y, si hay costo, el subtotal con la moneda de la tienda (`texto`).
4. Añade pie de mensaje cordial solicitando confirmación de entrega.

## Qué devuelve cuando falla
* Si el diccionario de ítems viene vacío, genera un mensaje indicando que no hay productos faltantes para ese proveedor.

## Qué no debe cambiar una mejora futura
* Mantener la legibilidad en pantallas de celulares de los repartidores/distribuidores.
