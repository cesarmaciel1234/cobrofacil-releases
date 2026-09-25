# Aviso en la pantalla de cobro

Cartel grande sobre la hoja. No abre una ventana y no hay que apretar OK.

`toast.py`, clase `AvisoCobro`. `mostrar(mensaje)` lo pinta sobre la fila de redondeo y a los pocos segundos se va solo. El mouse lo atraviesa: el cajero sigue escribiendo. Si llega `accion`, aparece el botón «Asociar», Enter lo acepta y el cartel se queda hasta esa decisión. El texto, si el monto no es el del ticket, es que llegó ese importe y se puede asociar o esperar otro. `alarma(mensaje)` es el cartel rojo con el signo de alarma: Espere la transferencia, el QR o la tarjeta. Con el TPV apagado ese bloqueo no corre y Enter registra.

`EsperaPoint.esperar(token, device, monto)` es el cartel del Point, en la misma hoja, con margen y el botón Cancelar. No abre la ventana «Esperando Pago…». Mientras espera, Enter no registra. Cancelar suelta el cobro que ya está en la terminal. Si la terminal aprueba, devuelve verdadero.

Con la luz del TPV en rojo, Enter no espera: `_guardar_sin_tpv` guarda la venta. El cartel rojo de alarma y F9 solo aparecen con la luz en verde.

Si se espera un cobro, F1 avisa «Al pagar se imprime el ticket.», F2 avisa que la venta se cierra sola y sin ticket, y F10 avisa el ticket fiscal. El mismo clic no vuelve a mostrar el cartel.
