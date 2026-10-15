# QR del abono (F6)

Dibuja el código del abono. No abre la venta.

`lienzo.py`, clase `LienzoQr`. `arrancar(monto)` pide el mismo `pedir_qr_pos` del paso 6. `pago_aprobado` lee la orden del POS (no el índice lento de payments). Reloj 800 ms, una GET a la vez. `listo` emite el id de pago.

F9 marca `F9 MANUAL` y asienta el abono aunque el QR esté en vivo. Si Mercado Pago aprueba, cierra solo y no hace falta F9.
