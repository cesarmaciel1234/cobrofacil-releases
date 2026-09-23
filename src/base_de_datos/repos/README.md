# Repositorios

Acá está el acceso a las tablas. La pantalla no escribe SQL. El plano de la venta está en `src/base_de_datos/plano.md`.

## ventas.py

`VentasRepoMixin.guardar_venta_completa(venta_data, items, fiado)` guarda cabecera y detalle en una transacción.

Toma `venta_data['request_id']`. Si no viene, crea un UUID y lo deja en el diccionario.

En una esclava, si `db_engine_type` es mariadb y hay `mariadb_engine`, guarda en esa base y no usa la API. Si hay `api_url` y no hay MariaDB, hace POST a `{api_url}/api/guardar_venta` con bearer `config.token_api_lan()` y timeout 5 segundos. 200 y `status` success devuelve `id_venta`. Cualquier otro caso devuelve `None`. No inventa `9999999`.

`_buscar_por_request` hace `SELECT id FROM ventas WHERE request_id = ?`. Si encuentra fila, `guardar_venta_completa` devuelve ese id y no inserta de nuevo.

El insert nuevo incluye `request_id`. Si la columna no existe, el except cae al insert anterior, sin esa columna, para no frenar la caja. `_es_duplicado` reconoce unique, duplicate e `idx_ventas_request_id`.

`_aplicar_fiado` lee `deuda_actual` del cliente y la suma en la misma transacción. Si no hay cliente, lanza `ValueError`.

## stock_descuento.py

`descontar_stock(cursor, producto_id, cantidad)` no hace nada si el id es vacío o `000`.

Si `config` tiene `opt_stock_negativo` en verdadero, ejecuta `UPDATE productos SET stock = stock - ? WHERE id = ?`.

Si está apagado, el update además exige `stock >= cantidad`. Si `rowcount` es 0, lanza `SinStock` con el id del producto. Quien llama deshace la venta entera.
