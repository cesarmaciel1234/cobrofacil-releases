# UI del historial F3

Qué hace: arma la hoja clara sobre el gris.

- `armar.py` — `setup_ui`: cabecera + lista + filtros + `PanelDetalle`. Conecta Cancelar e Imprimir.
- `cabecera.py` — título HISTORIAL DE CAJA y Salir.
- `lista_tickets.py` — buscador y tabla Folio, Arts, Hora, Total, Redondeo, Cliente. `dialogo.cargar_ventas` tacha las filas `CANCELADA`.
- `filtros.py` — fecha, Hoy, Actualizar. El combo de método incluye `TODOS`.

Qué no cambiar: no mezclar esta UI con la cartera de admin. El folio de la tabla es solo el `ventas.id` (número), para que Cancelar lea el id.
