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

## Cancelar un ticket

`dialogo.cancelar_venta_accion`: el cajero pide PIN de admin (el admin no). Antes de confirmar, `HistorialController.plan_devolucion` y `texto_devolucion` arman el aviso: «DEBERÁ DEVOLVER $X EN EFECTIVO al cliente. Se descontará del cierre al finalizar el turno.» En fiado y clientes dice que no se devuelve efectivo y se anula la deuda. El mismo aviso sale al terminar, y la franja de notificaciones muestra «⛔ COBRO CANCELADO — ticket N · devolver $X en efectivo».

La cuenta y el retiro los hace la base (`src/base_de_datos/repos/README.md`, «Cancelar un ticket»). Esta pantalla no escribe movimientos de caja.

## Tabla Principal
Las 6 columnas (se sumó la columna Cliente para exponer cuentas corrientes) están proporcionadas dinámicamente (Stretch). La columna **Redondeo** obtiene los datos asíncronos y admite manejo fallback offline sin crashear (sqlite3.Row compat).

### Sistema de Notas (Desacoplado)
- El historial integra un botón de **Notas** (panel_detalle.py).
- Utiliza src.historial_ventas.notas_manager (SQLite independiente: 
otas_tickets.sqlite) para no alterar el esquema de MariaDB ni afectar la sincronización offline_sync.
- **UI Feedback:** En dialogo.py, al cargar ventas, los tickets con nota se pintan con texto naranja oscuro (#D97706).

### Tabla Detalle
- Formato dinámico: No se restringe en altura.
- 4 Columnas: Cantidad, Descripción, Precio, Importe.
