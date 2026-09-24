# Plano — promedios

## Frente

Carne, cerdo y pollo. Kilos, merma, precio y la tabla de cortes. Exportar al inventario pide la clave del jefe.

## Fondo

`VistaPromediosMixin` pinta. `MotorPromedios.calcular_media_res` saca merma y costo por kilo. `exportar_a_inventario` escribe `productos` por el nombre del corte. Si el texto no es un número, queda `0` y esa fila no sale si precio y oferta siguen en cero.

## Qué no cambiar

No cambiar esos `except` por un log que invente un precio. El tema de los botones sale de `PAL`, el tema global. No de `theme_pro.py`.
