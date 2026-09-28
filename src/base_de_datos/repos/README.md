# Repositorios

Acá está el acceso a las tablas. La pantalla no escribe SQL. El plano de la venta está en `src/base_de_datos/plano.md`.

## ventas.py

`VentasRepoMixin.guardar_venta_completa(venta_data, items, fiado)` guarda cabecera y detalle en una transacción.

Toma `venta_data['request_id']`. Si no viene, crea un UUID y lo deja en el diccionario.

En una esclava, si `db_engine_type` es mariadb y hay `mariadb_engine`, guarda en esa base y no usa la API. Si hay `api_url`, no hay MariaDB y `_puerto_maestra_vivo` es verdadero, hace POST a `{api_url}/api/guardar_venta` con bearer `config.token_api_lan()` y timeout 5 segundos. 200 y `status` success devuelve `id_venta`. Si esa API falla y el puerto sigue abierto, devuelve `None`. Si la maestra no contesta, no cancela: inserta en SQLite y encola con `offline_sync_manager.guardar_venta_offline`. Ese encolado avisa `VENTA_NUEVA` por UDP. No inventa `9999999`.

`sync_venta_to_master` sale enseguida con `False` si `_forced_local_offline` está prendido o no hay motor MariaDB. Así la cola no se borra creyendo que la venta ya está en la maestra. `get_connection(caer_si_maestra_caida=False)` en esa sync no cambia el motor.

`_buscar_por_request` hace `SELECT id FROM ventas WHERE request_id = ?`. Si encuentra fila, `guardar_venta_completa` devuelve ese id y no inserta de nuevo.

El insert nuevo incluye `request_id`. Si la columna no existe, el except cae al insert anterior, sin esa columna, para no frenar la caja. `_es_duplicado` reconoce unique, duplicate e `idx_ventas_request_id`.

`_aplicar_fiado` lee `deuda_actual` del cliente y la suma en la misma transacción. Si no hay cliente, lanza `ValueError`.

### Cancelar un ticket

Regla de la tienda: al cancelar, al cliente se le devuelve el total **en efectivo** y se descuenta del cierre del turno. Fiado y Clientes no devuelven efectivo: `_anular_cargo` baja la deuda.

`calcular_devolucion(venta, caja_accion)` (función suelta, sin base) decide cuánto sale del cajón:

- `a_devolver`: el total; 0 en Fiado y Clientes.
- `retiro`: lo que no sale solo del esperado. La parte en efectivo (`pago_efectivo − cambio`) de una venta `COMPLETADA` de la misma caja ya baja el esperado porque la venta cancelada deja de sumar. El resto es retiro: la parte digital (transferencia, QR, tarjeta, lo digital del mixto) o cualquier venta de un turno ya cerrado (`CERRADA`).
- `ingreso_origen`: si otra caja cancela una venta `COMPLETADA` con efectivo, ese efectivo sigue en la caja de origen y se le reingresa, para que su esperado no baje.

`cancelar_venta_transaccional(id_venta, username)` devuelve stock, anula el fiado, marca `CANCELADA`, graba la auditoría y, en la misma transacción, inserta el `RETIRO` «Devolución ticket #N (cancelación, método)» en la caja que cancela (y el `INGRESO` de la caja de origen si hace falta). Una venta ya cancelada no se toca de nuevo: no duplica el retiro.

`plan_devolucion(id_venta)` corre la misma cuenta sin escribir, para el aviso previo del historial.

El cierre (`cierre_caja_cerebro/procesos/totales.py`) suma esos retiros en `devoluciones_efectivo`. Ya están dentro de `salidas_efectivo` y del esperado (`get_efectivo_en_caja` resta todo RETIRO). Pruebas: `tests/test_cancelacion_devolucion.py`.

## stock_descuento.py

`descontar_stock(cursor, producto_id, cantidad)` no hace nada si el id es vacío o `000`.

Si `config` tiene `opt_stock_negativo` en verdadero, ejecuta `UPDATE productos SET stock = stock - ? WHERE id = ?`.

Si está apagado, el update además exige `stock >= cantidad`. Si `rowcount` es 0, lanza `SinStock` con el id del producto. Quien llama deshace la venta entera.
