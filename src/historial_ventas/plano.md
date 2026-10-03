# Plano - Historial de Ventas

La rama arranca en esta carpeta. Modulo compartido para visualizar el registro historico de ventas en Cajero, Admin y Jefe.

## Frente

Muestra la lista de ventas completadas o anuladas (grilla). 
- Permite ver el desglose de cada ticket al seleccionarlo (lista de productos). 
- Permite realizar acciones mediante botones: anular ticket, reimprimir y cambiar medio de pago.
- Soporta funcionamiento offline transparente: si el Admin o Jefe pierden conexion, muestra la copia local (espejo_tienda.db); si es el Cajero en modo portable, lee su propio punpro.db.

## Fondo

El modulo centraliza las lecturas para evitar la duplicacion de codigo en las distintas pantallas de la app.

- **listar.py**: Ejecuta el `SELECT` principal a la tabla `ventas` (con paginacion y filtros). Utiliza `_get_db(ver_todo)` para acceder a MariaDB o enrutar de forma silenciosa al espejo/punpro.db segun la disponibilidad de red y perfil.
- **desglose.py**: Trae el detalle de los productos vendidos (`detalles_ventas`) asociados a un id de venta especifico, tambien usando `_get_db()`.
- **acciones.py**: Contiene los metodos para reimprimir y obtener el detalle crudo de un ticket (`_get_db()`).

## Que no cambiar

- No cambiar la logica de `_get_db(ver_todo)` ni acoplarla estáticamente a MariaDB. Si se solicita `ver_todo=True` (Perfil Jefe), se debe enrutar la lectura al motor `espejo.fuente()` (SQLite espejo_tienda.db) cuando está offline. Si `ver_todo=False` (Perfil Cajero), se debe consultar el motor `db_manager` (SQLite punpro.db) local para permitir devoluciones sobre ventas hechas sin conexión. Esto garantiza el Aislamiento de Perfiles y Motores dictado en la raíz.
