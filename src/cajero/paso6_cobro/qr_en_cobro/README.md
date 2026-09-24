# QR en la pantalla de cobro

Se ve en la misma pantalla del monto, solo cuando el medio es QR. No abre un cuadro aparte y no toca efectivo, tarjeta ni Point.

`panel.py`, clase `PanelQrCobro`. `mostrar(monto)` pide el código. `ocultar()` lo saca. `bloquea_enter()` es verdadero mientras busca o espera el escaneo. `pago_listo` avisa el monto cuando Mercado Pago aprueba.

`pedido.py`: `pedir_qr_pos` arma la orden del POS con `mp_user_id` y `mp_qr_pos_external_id`. Si Mercado Pago bloquea esa orden, arma un cobro con el monto y el código sale de ese link. `pago_aprobado` mira si ese `external_reference` ya está pago. Si no hay código, el panel dice «QR no disponible» y Enter registra la venta. «Cargar imagen de QR» muestra un archivo local: ahí vuelve el monto para escribirlo, y Enter registra. Redondeo y recargo rearman el código solo mientras está en vivo.

La terminal Point no entra acá. Sigue mandando el monto de tarjeta por F11.
