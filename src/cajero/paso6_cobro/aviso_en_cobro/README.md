# Aviso en la pantalla de cobro

Cartel grande sobre la hoja. No abre una ventana y no hay que apretar OK.

`toast.py`, clase `AvisoCobro`. `mostrar(mensaje)` lo pinta sobre la fila de redondeo y a los pocos segundos se va solo. `pin(mensaje, marcas)` es el mismo cartel en rojo, con cuatro círculos, y se queda hasta que el cobro lo cierra: lo usa el fiado cuando el cupo no alcanza. El mouse lo atraviesa: el cajero sigue escribiendo. Si llega un importe distinto, el cartel pregunta si enlazar al ticket: **F9** asocia; **Enter no asocia** (sigue esperando el exacto). El botón del teclado dice «F9 Emergencia» y no se oculta. `alarma(mensaje)` es el cartel rojo: Espere la transferencia, el QR o la tarjeta. Con el TPV apagado ese bloqueo no corre y Enter registra.

`EsperaPoint.esperar(token, device, monto)` es el cartel del Point, en la misma hoja, con margen y el botón Cancelar. No abre la ventana «Esperando Pago…». Mientras espera, Enter no registra. Cancelar suelta el cobro que ya está en la terminal. Si la terminal aprueba, devuelve verdadero.

Con la luz del TPV en rojo, Enter no espera: `_guardar_sin_tpv` guarda la venta. F9 de emergencia cierra QR / tarjeta / transferencia a mano, o asocia una transferencia de otro monto. Enter no asocia.

Si se espera un cobro, F1 avisa «Al pagar se imprime el ticket.», F2 avisa que la venta se cierra sola y sin ticket, y F10 avisa el ticket fiscal. El mismo clic no vuelve a mostrar el cartel.
