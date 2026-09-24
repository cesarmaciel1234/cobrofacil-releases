# Plano — venta e idempotencia

## Frente

La pantalla de cobro, `src/cajero/paso6_cobro/paso6_cobro.py`, crea un `request_id` al abrir el cobro. Si la red corta y el cajero reintenta, viaja el mismo id. No se inventa el ticket `9999999`. Si la maestra no contesta, la esclava cobra igual en el SQLite local y el ticket sale con el id de esa base. Si la maestra está en línea y la API LAN falla, el cobro se cancela. No se simula éxito.

## Fondo

`src/base_de_datos/repos/ventas.py`, método `guardar_venta_completa`.

Si el diccionario no trae `request_id`, el repo crea un UUID. En una esclava, si ya hay motor MariaDB y el puerto 3306 responde, guarda en esa base. La API LAN se usa solo si no hay MariaDB y `_puerto_maestra_vivo` dice que la maestra contesta. El post va a `/api/guardar_venta` con el token de `config.token_api_lan()`, timeout 5 segundos. Si responde 200 y `status` success, devuelve el id remoto. Si la maestra está en línea y la API no guarda, devuelve `None`. Si la maestra no contesta, no espera ese timeout: `guardar_venta_completa` inserta en `punpro.db` y `offline_sync_manager.guardar_venta_offline` deja la venta en `offline_queue.json`. En ese momento manda un UDP `VENTA_NUEVA` al puerto 37021, con `fuera_de_maestra` y el `request_id`, para que Nexus vea el ticket sin esperar la maestra. `is_master` sigue en false. Cuando el puerto vuelve, la cola sube con `sync_venta_to_master` y el mismo `request_id` no duplica. Nexus suelta ese monto de la pantalla en cuanto el `request_id` está en `ventas` de la maestra.

Antes del insert busca `ventas.request_id`. Si ya existe, devuelve ese id y no descuenta stock otra vez.

El insert nuevo lleva `request_id`. En una base vieja, si la columna todavía no está, el insert cae al formato anterior para no frenar la caja. La columna se agrega al arrancar, en el migrador. No hacer `ALTER TABLE` dentro de `guardar_venta_completa` ni de la sync a la maestra: en MariaDB el ALTER confirma la transacción solo y el ticket puede quedar a medias.

El índice único deja varios `NULL` en ventas viejas. No rellenar esas filas a la fuerza.

La llave entre cajas es `CLAVE_RED` (`1234`) en `src/config.py`. No sale de `local_pin` ni de `lan_api_token`. No hay pantalla para cambiarla.

`src/base_de_datos/repos/stock_descuento.py`, `descontar_stock`. Si `opt_stock_negativo` está apagado, el update exige `stock >= cantidad`. Si no afectó filas, lanza `SinStock` y la venta se deshace. Si está prendido, resta igual y el stock puede quedar negativo. El id `000` o vacío no descuenta.

## Qué no cambiar

No devolver `9999999`. No borrar `request_id` del cobro ni del motor. No ignorar `opt_stock_negativo`.
