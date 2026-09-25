# Motor clientes del cobro

`motor.py`, clase `MotorClientes`. `ejecutar` llama `cerebro.cobrar("Clientes", datos)`.

La autorización y la orden ok están en `src/clientes_fiado`. Si la orden no es ok, no se guarda la venta. Si es ok, `garante/despacho/despacho.py` llama `ejecutar_comun`: venta, stock y deuda en el mismo commit. Este motor no pregunta quién pagó.
