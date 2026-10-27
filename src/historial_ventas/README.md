# Historial de Ventas (Lógica Base)


### Novedades
- **notas_manager.py**: Mini-módulo para persistir notas/observaciones de tickets en una base local aislada (
otas_tickets.sqlite) sin romper el esquema ni la sincronización de la BDD principal.
- **listar.py (Filtros)**: Se añadieron lógicas condicionales para "REDONDEO" y "RECARGO", calculando los importes > 0 al vuelo en vez de ser un método de pago.
- **acciones.reimprimir**: Importa `controller` de `caja.py` antes de pedir la copia. Es el botón Imprimir copia del historial del jefe.
- **ticket_volumen.py**: Ticket del desglose para llevar en la billetera. Día o mes, ancho de `printer_paper_width_mm`. Nombre del comercio en letra doble arriba y otra vez al cierre. Cada producto en negrita; debajo, en letra chica, `kg` o `un`, el precio y la plata. Al pie: `TOTAL`, `Kilos`, `Unidades` y `Articulos` (cantidad de nombres). No toca el ticket de venta.
- **desglose.py**: Une `detalles_ventas` con `productos` para saber si el nombre se pesa o es unidad. Si ese join no está, vuelve a la suma solo por nombre.
