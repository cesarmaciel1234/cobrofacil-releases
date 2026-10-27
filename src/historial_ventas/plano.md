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
- **desglose.py**: Agrupa los artículos de los tickets cerrados del filtro (`detalles_ventas` + `productos`). Una fila por nombre. Trae cantidad, plata, unidad y si es pesable.
- **ticket_volumen.py**: Arma el ticket de ese desglose para la billetera. No es el ticket de una venta y no lo modifica.
- **acciones.py**: Detalle, cancelar y reimprimir. Reimprimir llama a `caja.controller().reimprimir_ticket` (el mismo puente que cancelar). Sin ese import, el botón del jefe muestra `name 'controller' is not defined`.

### Ticket de volumen

Lo abre el jefe en Historial → Desglose de artículos → Imprimir. El filtro puede ser un día o el mes de la fecha elegida. Las ventas canceladas no entran.

`printer_paper_width_mm` decide el ancho en el momento de imprimir: 58 mm son 32 columnas, 80 mm son 48. Otro valor usa 58.

El papel, de arriba hacia abajo:

1. Nombre del comercio en letra doble y negrita. Vuelve a imprimirse, en negrita normal, debajo del total.
2. Saludo, dirección (`address` o `business_address`) y teléfono (`phone` o `business_phone`).
3. Título `VOLUMEN VENDIDO`, la fecha del filtro y la cantidad de clientes (tickets cerrados).
4. Cada producto: el nombre en negrita. Debajo, en letra chica, la cantidad con su medida, el precio y la plata de esa línea. Si el producto se pesa dice `kg`. Si se vende por unidad dice `un`.
5. `TOTAL` en plata. `Kilos` solo si hubo peso. `Unidades` solo si hubo unidades. `Articulos` es la cantidad de nombres de producto, no la suma de kilos ni de unidades.

La medida sale de `etiqueta_unidad`: pesable o unidad `KG` es kilo; si no, unidad. El departamento desempata cuando el producto no tiene la unidad cargada.

Quién imprime: `PosPrinter.imprimir_volumen_articulos` manda esos bytes a la tiketera configurada. El cajero y el ticket de venta no pasan por acá.

## Que no cambiar

- No cambiar la logica de `_get_db(ver_todo)` ni acoplarla estáticamente a MariaDB. Si se solicita `ver_todo=True` (Perfil Jefe), se debe enrutar la lectura al motor `espejo.fuente()` (SQLite espejo_tienda.db) cuando está offline. Si `ver_todo=False` (Perfil Cajero), se debe consultar el motor `db_manager` (SQLite punpro.db) local para permitir devoluciones sobre ventas hechas sin conexión. Esto garantiza el Aislamiento de Perfiles y Motores dictado en la raíz.
- No meter el ticket de volumen dentro del ticket de venta. `Articulos` cuenta nombres. No sumar kilos y unidades en el mismo renglón.
