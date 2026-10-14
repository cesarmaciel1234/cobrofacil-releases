# Paso 8 — Historial de caja (F3)

La nota de la rama es `punta del piramide.md` (frente y fondo).

```
paso8_historial/
  dialogo.py                 DialogoHistorialDia — ventana y acciones
  paso8_historial.py         facade: from src.cajero.paso8_historial import DialogoHistorialDia
  logica/                    get_ventas, cancelar, reimprimir, formato, Esc
  ui/                        cabecera, lista, filtros, armar
  componentes_paso8_historial/  PanelDetalle, StampLabel CANCELADO
```

Desde el terminal: `from src.cajero.paso8_historial import DialogoHistorialDia`.

En `ui/filtros.py`, el combo de método empieza con `TODOS`. Es el filtro, no un comentario TODO.

F3 tapa la venta con el gris `#334155`.

Cancelar: PIN de admin; `HistorialController.plan_devolucion` / `texto_devolucion`. Fiado no devuelve efectivo: anula deuda. El ticket queda CANCELADO. Cuenta corriente: `CANCELADO ·` + `Ticket cancelado #N (F3)`. Esta pantalla no escribe caja.

Notas: `src.historial_ventas.notas_manager` (SQLite `notas_tickets.sqlite`). Tickets con nota: naranja `#D97706`.
