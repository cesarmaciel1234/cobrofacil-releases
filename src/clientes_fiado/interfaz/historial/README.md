# Historial

Ventana compartida de cuenta corriente: movimientos crudos, detalle de ticket/cobro e impresión.

## Qué hace

`DialogoHistorialCliente` — lista cargos y abonos sin filtro de período. Clic en fila → panel inferior (ticket de venta, cobro COB o cargo sin ticket). Botón Imprimir manda el historial a la tiketera.

`DialogoAlcanceImpresionCuenta` — selector espacioso para tickets de cuenta: permite elegir entre imprimir solo la deuda viva acumulada desde el último saldo en $0.00 o el historial completo, evitando recortes de botones.

`PanelDetalleTicket` — desglose abajo.

`HiloMovimientos` — lee `oficina/consulta_historial` fuera del hilo de UI.

## Quién lo abre

- Admin cartera (clic en fila)
- F6 Centro de Cobranzas → **Ver / Imprimir**

`modo="cajero"` oculta Editar, Saldo+ y Eliminar. `modo="admin"` deja todo.

## Cómo

```python
from src.clientes_fiado.interfaz.historial import DialogoHistorialCliente
DialogoHistorialCliente(cliente_id, parent, modo="cajero")
```
