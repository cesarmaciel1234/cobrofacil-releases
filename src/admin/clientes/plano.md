# Plano — cartera de clientes

La rama arranca en esta carpeta. `admin_clientes_main.py` es la pantalla; `componentes/` contiene los diálogos. La regla del crédito y sus datos viven en `src/clientes_fiado/`, no en la UI.

## Frente

La ficha del cliente abre `componentes/dialogo_historial_cliente.py`. En una fila `CARGO` con número de ticket, pulsar el número azul abre `componentes/dialogo_ticket.py` con el desglose de artículos. Los abonos y cargos manuales no abren un ticket.

## Fondo

El historial sale de `cerebro.movimientos()`. El clic de la columna Ticket valida que la fila sea `CARGO` y toma el `venta_id` guardado en el `UserRole` de la celda. `abrir_detalle_ticket()` crea el diálogo; un `QThread` pide los datos al lector independiente `src/clientes_fiado/oficina/ticket/motor.py::MotorTicket.detalle`.

El lector busca la venta en la base activa, la copia portable y la SQLite local pendiente. Solo consulta. Si no encuentra la venta, el diálogo lo informa; nunca altera el registro de deuda.

## Qué no cambiar

- No abrir tickets para abonos ni para cargos sin `venta_id`.
- No mover la consulta de venta al hilo de interfaz.
- No unir el lector de tickets con los motores que guardan ventas o deuda.


## Cartera: filtros y plazo

Frente: debajo del buscador, chips `Todos`, `🔴 Con deuda`, `🟢 Al día`, `🔵 Saldo a favor`, `⚡ Express`, cada uno con su contador. Las tarjetas de arriba siempre suman toda la cartera, no solo lo filtrado.

Fondo: `admin_clientes_main.py` (`_categoria`, `_pasa_filtro`, `_pintar_chips`). Deuda negativa se muestra como `+$X a favor` en azul. Sin deuda, la columna Días dice `Al día` y Recálculo queda en `—` (sin botón invisible).

Plazo: columna `clientes.plazo_dias` (0 = sin plazo). Se edita en `componentes/dialogo_editar_cliente.py` → `cerebro.actualizar_ficha(..., plazo_dias)`; queda en la auditoría (`CAMPOS_FICHA`).
- Sin plazo: Días = días corridos desde el último cargo.
- Con plazo: cuenta regresiva `⏳ N días` → `⚠ Vence hoy` → `🔴 -1 día`, `-2 días`… (vencido).
- `plazo_dias=None` en `actualizar_ficha` no toca el valor guardado.
