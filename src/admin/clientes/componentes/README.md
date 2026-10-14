# Componentes de cartera de clientes

Esta carpeta contiene los diálogos de la pantalla de cartera.

`dialogo_historial_cliente.py` pide los movimientos al hilo `consulta/hilo.py`. El ticket se ve abajo (`PanelDetalleTicket`). Un abono muestra `COB-{id}`. Eliminar marca `BORRADO`. Cancelar en F3 llega como `CARGO · CANCELADO` y `TICKET CANCELADO`. `dialogo_recalculo_fiado.py` simula precios y %; no escribe.

`dialogo_cobros.py` es la planilla. **Ticket cobro** = `COB-{cuenta_corriente.id}`. **Id de pago** = Mercado Pago, `F9 MANUAL` o `Caja` si fue efectivo. Filtro Hoy/Semana/Mes/Año. Si dos cobros coinciden en cliente, monto, medio y minuto, la fila se marca en ámbar: no se ocultan, cada una tiene su COB.

`dialogo_auditoria_clientes.py` usa las mismas claves (referencia COB o ticket, medio, id de pago). Un evento sin vía ya no dice «Sin llegar»: si nació en la tienda dice «En esta tienda». Acciones `Borrado` y `Anulación` entran al filtro Borrados.

`dialogo_ticket.py` es el panel de lectura. Consulta en un `QThread` a `src/clientes_fiado/oficina/ticket/motor.py`. Si falla, informa; no cambia ni el ticket ni la deuda.

No mover la lectura de base de datos al hilo de interfaz ni conectar el diálogo a los motores que guardan ventas o deuda.
