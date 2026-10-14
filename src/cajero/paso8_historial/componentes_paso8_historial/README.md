# Componentes del detalle F3

- `panel_detalle.py` — clase `PanelDetalle`. Folio, cajero, cliente, medio, ítems, totales. Título «Ticket N · CANCELADO» y sello si `estado` es CANCELADA. Botones Notas, Cancelar venta, Imprimir copia. `mostrar_venta(v, items)`.
- `stamp_label.py` — `StampLabel("CANCELADO")` encima del detalle.

Si no hay venta, el panel dice «Seleccione un Ticket». Cancelar deshabilitado en tickets ya cancelados. No escribe la base: llama los callbacks del diálogo.
