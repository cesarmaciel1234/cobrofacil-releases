# Consulta historial

Motor de transporte de solo lectura. Lo preguntan los hilos de admin y de F6, cada uno en su carpeta.

`motor.py`, clase `MotorConsultaHistorial`, objeto `motor_consulta_historial`.

`movimientos(cliente_id)` pide el libro a `MotorCuenta.movimientos` y arma filas iguales para los dos perfiles: tipo, BORRADO, ticket de venta `#…` o ticket de cobro `COB-`. Si la base o el armado fallan, devuelve `[]`. No escribe, no borra, no llama a la UI.

Un cargo `BORRADO` (admin) o `CANCELADO` (F3, el cliente devolvió) sigue saliendo con el mismo `#ticket`. La anulación de F3 se etiqueta `TICKET CANCELADO`. Admin y cajero ven el mismo libro.

Qué no cambiar: no mezclar este lector con `borrar_cargo` ni con el cobro de F6.
