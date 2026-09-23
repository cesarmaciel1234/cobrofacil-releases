# Plano — reportes

## Frente

Las pantallas están en `src/jefe/reportes/`, entre ellas `vista_financiero.py`. También miran esta regla `reportes_main.py` y `jefe_reportes.py` cuando arman el rótulo.

No se muestra «Día 1», «Día 17» ni «Mes 2». El día se escribe con la abreviatura y la fecha, por ejemplo Lun 17. Sale de `weekday()` de esa fecha. El mes se escribe Ene, Feb, Mar.

## Fondo

El cálculo de la fecha vive en el motor del reporte. La vista solo cambia el texto que ve el gerente. No reescribe la fecha guardada en la venta.

## Qué no cambiar

No volver a un número de día o de mes pelado en la tabla ni en el gráfico.
