# Tarjeta en cobranza

`lienzo.py`, clase `LienzoTarjeta`. Contenedor fijo (como el QR): pide pasar la tarjeta, muestra el monto y Cancelar.

`arrancar` manda el importe al Point una sola vez. Si ya está enviando o esperando el mismo monto, no vuelve a mandar. Cuando la terminal aprueba, emite `listo` y el panel asienta el abono. Cancelar suelta el cobro en el Point y vuelve a los medios. Un fallo se lee en el mismo contenedor: no se cierra solo.

F9 registra a mano si el Point no aprueba.
