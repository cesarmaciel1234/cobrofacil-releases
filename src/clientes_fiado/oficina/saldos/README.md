# Saldos

El cupo. Las funciones están en `oficina/cuenta/motor.py`.

`credito_disponible` resta `deuda_actual` de `limite_credito`. `limite_excedido` dice si el monto de la venta no entra en ese disponible. Sin cliente, `limite_excedido` devuelve verdadero y `credito_disponible` devuelve `0.0`.

El garante llama estas dos antes de armar la orden ok. La hoja del cobro las muestra como Saldo y Disponible. No guardan la venta.
