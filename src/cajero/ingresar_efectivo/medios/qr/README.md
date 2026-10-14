# QR del abono (F6)

Dibuja el código del abono. No abre la venta.

`lienzo.py`, clase `LienzoQr`. `arrancar(monto)` pide el mismo `pedir_qr_pos` del paso 6. `pago_aprobado` lee la orden del POS (no el índice lento de payments). Reloj 800 ms, una GET a la vez. `listo` emite el id de pago.

F9 marca `F9 MANUAL` solo en foto o sin TPV. Con QR en vivo no hace falta.
