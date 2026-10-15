# QR del abono (F6)

Dibuja el código del abono. No abre la venta.

`lienzo.py`, clase `LienzoQr`. Mismo nivel que el QR del ticket: `pedir_qr_pos`, `pago_aprobado` por esta referencia, precarga TLS, pintado `FastTransformation`, reloj 800 ms, una GET a la vez. Un cobro viejo del mismo importe no cierra. `listo` emite el id de pago. Lo usan COBRANZA del paso 6 y F6.

F9 marca `F9 MANUAL` y asienta el abono aunque el QR esté en vivo. Si Mercado Pago aprueba, cierra solo y no hace falta F9.
