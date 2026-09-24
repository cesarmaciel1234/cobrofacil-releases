# Widgets del cobro

Cliente y fiado son ventanas. `pagos_mixtos.py` es la ventana vieja del mixto: el cobro ya no la abre. El reparto en pantalla está en `mixto_en_cobro/`.

`cliente_express.py` y `fiado_express.py` disparan un `threading.Thread` daemon para el bip. No guardan la venta.

Los `while True` que abren estas ventanas están en `paso6_cobro.py`: el flujo de clientes y `_abrir_fiado_express_original`. Cancelar sale con `return`.
