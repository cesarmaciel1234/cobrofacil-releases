# Componentes de cartera de clientes

Esta carpeta contiene los diálogos de la pantalla de cartera.

`dialogo_historial_cliente.py` muestra los movimientos de cuenta corriente. En un movimiento `CARGO` que tiene venta asociada, el número de Ticket queda como enlace azul; al pulsarlo llama a `_abrir_ticket()` y abre `dialogo_ticket.py`. Abonos y cargos manuales no tienen un detalle de venta que abrir.

`dialogo_ticket.py` consulta de forma asíncrona el lector `src/clientes_fiado/oficina/ticket/motor.py` y presenta fecha, medio, estado, artículos, cantidades, precios, importes y origen. Si la lectura falla o no encuentra copia, informa en el diálogo; no cambia ni el ticket ni la deuda.

No mover la lectura de base de datos al hilo de interfaz ni conectar el diálogo a los motores que guardan ventas o deuda.
