# Lógica del terminal

Carrito, stock, ofertas, movimientos de caja y cierre remoto. No pinta la pantalla.

`TerminalController.__init__` recibe la vista y arma cuatro servicios: `CarritoService`, `StockOfertasService`, `MovimientosCajaService`, `CierreRemotoService`.

`CarritoService.buscar_productos` pide 3 letras y solo pega el inicio de la 1.ª o 2.ª palabra (`asa` → ASADO, CARNE ASADA; no masa). El código de barras busca id/código exacto, sin LIKE al nombre. `procesar_codigo_escaneado` usa `BarcodeParser.parse_scan_text`. No volver a `LIKE '%texto%'` en el hilo de la UI.

`StockOfertasService.resolver_precio` delega en `MotorOfertas.resolver_precio_venta` (mayoreo → relámpago con cupo → oferta → lista). Las consultas de precio traen columnas de relámpago. `stock_disponible` usa el stock del diccionario; si no es número, el `except` desnudo devuelve `0.0`. `obtener_combos` guarda 15 s. No se agrega un `ProductoRepository` al lado.
