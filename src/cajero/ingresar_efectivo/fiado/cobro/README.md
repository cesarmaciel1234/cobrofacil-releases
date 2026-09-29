# Cobro del abono en F6

Esta hoja vive dentro de F6. No abre la venta.

## Flujo

1. Fiado confirma cliente y monto a abonar → `pagina.abrir`.
2. Saluda «Hola nombre» y pregunta el medio.
3. Efectivo: el monto a abonar ya está definido; pide aparte el efectivo recibido y muestra el vuelto. Al confirmar, pide PIN y, solo si se autoriza, abre el cajón y registra el abono. Si el PIN se cancela o falla, mantiene el recibido y no abre el cajón.
4. Transferencia, tarjeta y QR: el clic pide PIN antes de iniciar el motor.
5. Transferencia: EscuchaMP + toast Asociar; F9 = `F9 MANUAL`.
6. Tarjeta: Point; F9 suelta y asienta `F9 MANUAL`.
7. QR: `pedir_qr_pos` en esta hoja; F9 = `F9 MANUAL`.
8. Mixto: reparte; corre los motores digitales en cola.
9. `cerrar_con_medio` → paso 5 / admin llaman `medios/cerrar.asentar`.
10. Si algo falla, aviso y la venta sigue.

## Piezas

`pagina.py`, `PaginaCobroAbono`. Orquesta PIN, cola y cierre. No importa `Paso6Cobro`.

`lienzo_efectivo.py`. Solicita cuánto efectivo recibió el cajero y calcula el vuelto contra el monto a abonar; no vuelve a pedir el monto del abono, no abre el cajón ni registra. `pagina.py` pide PIN después de validar el recibido y abre el cajón únicamente al autorizar el abono. En Mixto, posterga la apertura hasta que los medios electrónicos hayan terminado correctamente.

`lienzo_qr.py`. Pide el código con `pedir_qr_pos`. Asienta el id del pago.

`lienzo_tarjeta.py`. `enviar_monto` + `detalle_orden`. F9 Manual.

`lienzo_transferencia.py`. Escucha como el cobro. Toast Asociar. F9 Manual.

`aviso.py`, `AvisoAbono`. El toast del cobro, centrado en F6.

F9 llega por `QShortcut` en `dialogo.py`. No pasa dos veces por `keyPressEvent`.
