# QR en la pantalla de cobro

Se ve en la misma pantalla del monto, solo cuando el medio es QR. El código ocupa el alto libre de la hoja. No abre un cuadro aparte y no toca efectivo, tarjeta ni Point.

`panel.py`, clase `PanelQrCobro`. `mostrar(monto)` pide el código cuando la luz del TPV está verde. `ocultar()` lo saca. `bloquea_enter()` es verdadero mientras busca o espera el escaneo. `pago_listo` avisa el monto cuando Mercado Pago aprueba. Con la luz en rojo no pide el código en vivo: muestra la foto y Enter guarda la venta.

La luz verde del QR mira `mp_qr_pos_external_id` (el mismo que guarda Terminales TPV). Si ese dato no está, no pide el código en vivo: muestra la foto. Tener solo el Point no enciende el QR.

`pedido.py`: `pedir_qr_pos` arma la orden del POS con `mp_user_id` y `mp_qr_pos_external_id` (cache en memoria). Timeout 3,5 s. Session HTTP reusada. No llama `asegurar_pos_qr`. Si Mercado Pago bloquea esa orden, arma un cobro con el monto y el código sale de ese link. `precargar_conexion` abre TLS al armar el panel. Si se rompe, `paso6_cobro/reparacion.md`.

`pago_aprobado` no espera el índice de `/v1/payments/search` (ese listado llega tarde: el teléfono ya cobró y la caja seguía “esperando”). Primero lee la orden viva del POS (`url_orden_pos`, el mismo estado que ve el cliente). Si ya no está en el POS, busca `merchant_orders` por `external_reference`. `/payments/search` queda último, sin recorte de fecha. `pago_de_orden` arma el dict. Timeout 1,2 s.

El panel consulta cada 800 ms, arranca al pintar el código, y no lanza otra GET si la anterior sigue en vuelo. Si el importe llega, `pago_listo` cierra la venta **solo**, sin F9. F9 queda para emergencia (sin red). Ese cobro se anota en el monitor y queda el id para el ticket. Si no hay código, el panel dice «QR no disponible» y Enter registra la venta. «Cargar imagen de QR» muestra un archivo local: ahí vuelve el monto para escribirlo, y Enter registra. Redondeo y recargo rearman el código solo mientras está en vivo.

La terminal Point no entra acá. Sigue mandando el monto de tarjeta por F11.
