# Oficina

Acá se llevan los créditos. El paso 5 ya vendió y el paso 6 ya registró el medio. Esta carpeta no cobra esa venta.

`cuenta/motor.py`, clase `MotorCuenta`, es el libro. Lee y escribe `clientes` y `cuenta_corriente`.

Tres mesas, sobre ese mismo libro:

- `por_cobrar/` mira quién debe.
- `cobradas/` anota el abono.
- `saldos/` dice si el cupo alcanza, y el garante lo consulta antes del ok.
- `cartel/` llena el saludo de la confirmación. Si el nombre no está, deja `Sin datos`.

El cargo de una venta fiada no se escribe acá. Lo escribe `_aplicar_fiado`, en la misma transacción que el ticket.
