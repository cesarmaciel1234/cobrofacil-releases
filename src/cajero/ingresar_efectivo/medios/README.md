# Cobro del abono en F6

Esta hoja vive dentro de F6. No abre la venta.

## Flujo

1. Fiado confirma cliente y monto a abonar → `pagina.abrir`.
2. Saluda «Hola nombre» y pregunta el medio.
3. Efectivo: pregunta «¿Cuánto te dio en billetes?». El chip de arriba es lo que va a la cuenta. Falta: no cobra. Devolvé: Enter asienta el abono, no el billete. Vacío o texto raro no cobra.
4. Transferencia, tarjeta y QR: el clic pide PIN antes de iniciar el motor.
5. Transferencia: `pago_llegado`. Si llega el importe, asienta. F9 solo sin internet.
6. Tarjeta: Point; si FINISHED, asienta. F9 solo si la terminal no arrancó.
7. QR: `pago_aprobado`; si llega el importe, asienta. F9 solo en foto / sin TPV.
8. Mixto: reparte; corre los motores digitales en cola.
9. `cerrar_con_medio` → paso 5 / admin llaman `medios/cerrar.asentar`.
10. Si algo falla, aviso y la venta sigue.

## Piezas

`pagina.py`, `PaginaCobroAbono`. Orquesta PIN, cola y cierre. No importa `Paso6Cobro`.

`efectivo/lienzo.py`. Pregunta los billetes. Chip «Va a la cuenta». Si falta, el botón Cobrar queda apagado. Si alcanza, dice Devolvé o Justo. Emite el abono, no el recibido. No abre el cajón ni registra.

`qr/lienzo.py`. Pide el código con `pedir_qr_pos`. Asienta el id del pago.

`tarjeta/lienzo.py`. `enviar_monto` + `detalle_orden`. F9 Manual.

`transferencia/lienzo.py`. Escucha como el cobro. Toast Asociar. F9 Manual.

`aviso.py`, `AvisoAbono`. El toast del cobro, centrado en F6.

F9 llega por `QShortcut` en `dialogo.py`. No pasa dos veces por `keyPressEvent`.
