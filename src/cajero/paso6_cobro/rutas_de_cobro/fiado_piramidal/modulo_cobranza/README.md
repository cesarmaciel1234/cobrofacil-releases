# Módulo de cobranza

Qué hace: Cobra un abono (carrito, deuda o ambos) con efectivo, tarjeta, QR, transferencia o mixto.

Qué función: `PanelCobranza.poblar` / `_iniciar_cobranza` / `MotorCobranzaMedios.finalizar`.

Cómo funciona: El casillero arranca en el **ticket**. Si hay saldo a favor se muestra a favor y no se suma al cobro. Solo Deuda / Liquidar Todo aparecen si la deuda es positiva. Un importe ≤ 0 no arranca ningún medio: vuelve al ticket. Enter en el casillero arranca Efectivo. Mixto cobra primero lo digital y después asienta el total.

`MotorCobranzaMedios` es intermediario: asienta el abono y da el ok. El motor real de la venta es `MotorPrincipalCobros`. No unificarlos.

PIN de cobranza y PIN de F9: aún no. Ver `paso6_cobro/decisiones.md`.

Qué no debe cambiar: el intermediario no cierra la venta; emite `abono_exitoso` y el orquestador manda `pago_completado`.
