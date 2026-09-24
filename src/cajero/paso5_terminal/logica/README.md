# Lógica del terminal

Carrito, stock, ofertas, movimientos de caja y cierre remoto. No pinta la pantalla.

`TerminalController.__init__` recibe la vista y arma cuatro servicios: `CarritoService`, `StockOfertasService`, `MovimientosCajaService`, `CierreRemotoService`.

`CarritoService.buscar_productos` y `buscar_producto_exacto` leen `productos` con `db_manager.execute_query`. `procesar_codigo_escaneado` usa `BarcodeParser.parse_scan_text`.

`StockOfertasService.stock_disponible` usa el stock que ya vino en el diccionario del producto. Si ese valor no es un número, el `except` desnudo devuelve `0.0`. `obtener_stock_db` sí consulta la tabla. `obtener_combos` guarda el resultado 15 segundos en la instancia del servicio. `combos_para_ticket` devuelve esa misma lista ya parseada. No se borra ese recuerdo para «forzar frescura» en cada escaneo. Si la lista está vacía, el terminal no recorre las filas.

La puerta de la base es `db_manager`. No se agrega un `ProductoRepository` al lado.
