# Monto en la pantalla de cobro

Efectivo, tarjeta y transferencia. El QR vive en `qr_en_cobro/` y el mixto en `mixto_en_cobro/`. Esta carpeta no los pinta.

`panel.py`, clase `PanelMontoCobro`. Dos marcos fijos: `zona_pago` (el casillero) y `zona_estado` (el vuelto o la escucha de Mercado Pago). El marco crece con la hoja. Lo de adentro conserva su alto y queda centrado, así no se estira ni se sale.

`ajustar(metodo, foto)` devuelve verdadero cuando el panel debe llenar el hueco del medio. En QR solo aparece, y bajo, si hay una foto cargada: el casillero del monto. En mixto no se muestra.
