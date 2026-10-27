# historial_ventas/ — un motor, dos caras

Cajero oscuro (`paso8`) y jefe claro (`reportes/historial`) hablan con este motor.  
No copies SQL de tickets en las vistas.

```
historial_ventas/
  motor.py      fachada (importá esto)
  listar.py     tickets; jefe: todas las cajas
  acciones.py   detalle / cancelar / reimprimir
  auditoria.py  lee el rastro de cancelación
  desglose.py        artículos del lote, con unidad
  ticket_volumen.py  ticket de billetera (no es el de venta)
  caja.py            puente a HistorialController (no tocar paso8)
```

## Arrancar

- Listar o filtrar: `motor_historial.listar(...)`. Fechas con `iso_dia` / `periodo/sql.where_fecha`.
- Cancelar: `motor_historial.cancelar(id, usuario)`. La firma (quién / caja) la escribe `database.cancelar_venta_transaccional`.
- Mostrar rastro: `motor_historial.linea_cancel(venta)`.
- Esclava: el motor usa `db_manager` → tiene que ser la maestra, no `punpro.db`.
- Ticket de volumen: `armar_ticket_volumen` arma los bytes; `columnas_configuradas` lee `printer_paper_width_mm` (58 → 32, 80 → 48). `medida_de` dice `kg` o `un`. `Articulos` = cantidad de nombres. El mes entra por `listar_tickets(..., fecha_hasta=)`.

Cajero: no pases por este paquete si ya usa el controller. Jefe: siempre por `motor.py`.
