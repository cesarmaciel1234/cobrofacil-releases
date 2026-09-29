# Lector de tickets de clientes

`motor.py` contiene `MotorTicket`, lector de solo consulta que abre el detalle de la venta enlazada a un movimiento `CARGO`.

`detalle(ticket)` valida que el número sea positivo y busca la cabecera y sus renglones en la base activa, el espejo portable y, si existe, la SQLite local que puede contener una venta pendiente de sincronizar. Devuelve venta, artículos y origen; devuelve `None` si no encuentra el ticket. No modifica ventas, movimientos ni deuda.

El diálogo de admin ejecuta esta consulta en un `QThread`, no en el hilo de la interfaz. Mantener separado este lector de `MotorCuenta` y de las rutas que registran ventas.
