# Lógica del terminal

Carrito, stock, ofertas, movimientos de caja y cierre remoto. No pinta la pantalla.

`TerminalController.__init__` recibe la vista y arma cuatro servicios: `CarritoService`, `StockOfertasService`, `MovimientosCajaService`, `CierreRemotoService`.

`CarritoService.buscar_productos` y `buscar_producto_exacto` leen `productos` con `db_manager.execute_query`. `procesar_codigo_escaneado` usa `BarcodeParser.parse_scan_text`.

`StockOfertasService.resolver_precio` delega en `MotorOfertas.resolver_precio_venta` (mayoreo → relámpago con cupo → oferta → lista). Las consultas de precio traen columnas de relámpago. `stock_disponible` usa el stock del diccionario; si no es número, el `except` desnudo devuelve `0.0`. `obtener_combos` guarda 15 s. No se agrega un `ProductoRepository` al lado.
