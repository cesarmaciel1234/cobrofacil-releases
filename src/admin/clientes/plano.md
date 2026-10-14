# Plano — cartera de clientes

La rama arranca en esta carpeta. El crédito vive en `src/clientes_fiado/`.

```
admin/clientes/
  plano.md
  admin_clientes_main.py     pantalla
  theme.py
  consulta/                  HiloMovimientosAdmin
  componentes/               diálogos
```

## Frente

**Abonar** abre F6 con `perfil=Admin`. El cobro se asienta una sola vez. Sin deuda deja saldo a favor.

**Límite** cupo. **Editar** ficha. **Recalcular** simula precios de hoy y un % de financiación (no escribe).

La ficha abre `componentes/dialogo_historial_cliente.py`. El ticket se ve abajo. Eliminar marca `BORRADO`. Un ticket cancelado en F3 se ve `CARGO · CANCELADO` y `TICKET CANCELADO`. Planilla y auditoría: ticket de venta, `COB-`, id de pago o `F9 MANUAL`.

## Fondo

El historial lo pide `consulta/hilo.py` (`HiloMovimientosAdmin`) a `src/clientes_fiado/oficina/consulta_historial`. Si ese hilo falla, la ficha sigue. El ticket va por otro hilo (`PanelDetalleTicket` → `MotorTicket`). F6 tiene su propio hilo (`f6_centro_cobranzas/consulta_historial`). Los dos leen el mismo libro: un BORRADO de admin o una anulación del cajero quedan en ambos. Borrar escribe solo por `cerebro.borrar_cargo`.

El lector busca la venta en la base activa, la copia portable y la SQLite local pendiente. Solo consulta. Si no encuentra la venta, el panel lo informa; nunca altera el registro de deuda.

## Qué no cambiar

- No abrir otra ventana para ver el ticket.
- No borrar físicamente un cargo ni su ticket: se marca `BORRADO`.
- No abrir desglose de venta para abonos ni para cargos sin `venta_id`.
- No mover la consulta de venta al hilo de interfaz.
- No unir el lector de tickets con los motores que guardan ventas o deuda.


## Cartera: filtros y plazo

Frente: debajo del buscador, chips `Todos`, `🔴 Con deuda`, `🟢 Al día`, `🔵 Saldo a favor`, `⚡ Express`, cada uno con su contador. Las tarjetas de arriba siempre suman toda la cartera, no solo lo filtrado.

Fondo: `admin_clientes_main.py` (`_categoria`, `_pasa_filtro`, `_pintar_chips`). Deuda negativa se muestra como `+$X a favor` en azul. Sin deuda, la columna Días dice `Al día`. Recalcular sigue visible.

Plazo: columna `clientes.plazo_dias` (0 = sin plazo). Se edita en `componentes/dialogo_editar_cliente.py` → `cerebro.actualizar_ficha(..., plazo_dias)`; queda en la auditoría (`CAMPOS_FICHA`).
- Sin plazo: Días = días corridos desde el último cargo.
- Con plazo: cuenta regresiva `⏳ N días` → `⚠ Vence hoy` → `🔴 -1 día`, `-2 días`… (vencido).
- `plazo_dias=None` en `actualizar_ficha` no toca el valor guardado.
