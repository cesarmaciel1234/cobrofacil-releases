# Tarjeta en la pantalla de cobro

El medio Tarjeta no abre este panel ni la ventana «Esperando Pago…». El cobro lo espera el cartel `EsperaPoint` de `aviso_en_cobro/`, el mismo envío que usa el paso de tarjeta del mixto, solo si hay token y `mp_device_id`. Tener solo el QR no manda el Point. Al aprobar, el id del pago queda para el ticket. Con la luz en rojo no se manda el Point: Enter guarda la venta. Si se cancela en el cartel o en la terminal, la hoja vuelve a la página de métodos.

`panel.py`, clase `PanelTarjetaCobro`. `mostrar(monto)` sigue pudiendo mandar el importe. Un fallo no cancela el cobro que ya quedó en la terminal.

`envio.py`: `enviar_monto` manda el importe al Point solo como tarjeta (`credit_card`). La terminal pide apoyar la tarjeta y no ofrece QR: el código se ve en el sistema. El mínimo del Point es $15. `estado_intent` mira si terminó. `cancelar_intent` sin `en_terminal` no baja un cobro que ya se está viendo en el Point. El botón Cancelar del cartel sí pasa `en_terminal=True`.

Si la terminal no toma el monto, el cartel avisa y Enter registra la venta igual.
