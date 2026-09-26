# Plano — promedios

## Frente

Carne, cerdo y pollo. Kilos, merma, precio y la tabla de cortes. Columnas de volumen: **P. mayoreo** y **Cant. may.** Exportar / sincronizar pide la clave del jefe.

## Fondo

`VistaPromediosMixin` pinta. `MotorPromedios.calcular_media_res` saca merma y costo por kilo.

Exportar → `MotorMayoreo.aplicar_desde_promedios` (rama `src/motor_descuentos/mayoreo/`). Escribe `precio`, `costo`, `cant_mayoreo`, `precio_mayoreo`.

Sincronizar → `MotorMayoreo.obtener_por_nombre`.

Ya no usa `precio_oferta_promedio`. Oferta de cartelería se carga en Ofertas (admin).

Si el texto no es un número, queda `0` y esa fila no sale si precio y mayoreo siguen en cero.

## Qué no cambiar

No cambiar esos `except` por un log que invente un precio. El tema de los botones sale de `PAL`, el tema global. No de `theme_pro.py`.
