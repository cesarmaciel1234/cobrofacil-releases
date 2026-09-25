# Widgets del cobro

Cliente y fiado son ventanas. `pagos_mixtos.py` es la ventana vieja del mixto: el cobro ya no la abre. El reparto en pantalla está en `mixto_en_cobro/`.

`cliente_express.py` y `fiado_express.py` reexportan los diálogos viejos. El cobro ya no los abre: Fiado y Clientes usan `HojaCuentaCobro`, en la misma hoja que la tarjeta. El bip sigue en un hilo. No guardan la venta.

El cobro no abre estas ventanas. Fiado y Clientes entran por `HojaCuentaCobro`. Cancelar vuelve a los medios.
