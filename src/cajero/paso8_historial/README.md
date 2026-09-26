# Paso 8 — Historial de caja (F3)

Turno actual: lista de tickets a la izquierda, detalle a la derecha.

```
paso8_historial/
  README.md
  __init__.py              exporta DialogoHistorialDia, fmt_moneda
  paso8_historial.py       facade (mismo import que antes)
  dialogo.py               ventana y acciones
  logica/                  consultas, formato, teclas
  ui/                      cabecera, lista, filtros
  componentes_paso8_historial/   panel detalle + sello
```

Desde el terminal:

`from src.cajero.paso8_historial import DialogoHistorialDia`

En `ui/filtros.py`, el combo de método empieza con el texto `TODOS`. Es un valor del filtro, no un comentario `TODO`. El filtro sigue siendo TODOS, EFECTIVO, TARJETA, TRANSFERENCIA y MIXTO.

F3 tapa la venta con el gris `#334155`. La hoja del historial queda clara al frente.
