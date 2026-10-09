# Motor Cobranza

Qué hace: Mueve la lógica de `_finalizar_cobranza_con_motor` fuera del panel.

Qué función: `MotorCobranza` en `motor_cobranza.py`

Cómo funciona: Recibe una referencia al panel y maneja el asentamiento en caja y base de datos (con `asentar`), y luego emite las señales de `abono_registrado` y `pago_listo`.

Qué devuelve cuando falla: Cancela la operación y vuelve al lienzo de cobro mediante `panel._volver_de_lienzo()`.

Qué no debe cambiar una mejora futura: El contrato de `finalizar` (monto, metodo, detalle).
