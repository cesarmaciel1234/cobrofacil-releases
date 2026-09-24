# Tarjeta en la pantalla de cobro

Se ve cuando el medio es Tarjeta. No pide «paga con» y no abre el cuadro de Point.

`panel.py`, clase `PanelTarjetaCobro`. `mostrar(monto)` manda el importe a la terminal. Mientras espera, `bloquea_enter()` es verdadero: el cartel dice que no se toque nada. Si Mercado Pago aprueba, `pago_listo` cierra la venta.

`envio.py`: `enviar_monto` crea el cobro en la terminal. `estado_intent` mira si terminó. `cancelar_intent` suelta el anterior cuando cambia el redondeo o el recargo.

Si la terminal no toma el monto, el cartel avisa y Enter registra la venta igual.
