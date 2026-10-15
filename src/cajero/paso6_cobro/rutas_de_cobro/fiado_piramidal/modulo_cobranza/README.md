# Módulo de cobranza

Qué hace: Cobra un abono (carrito, deuda o ambos) con efectivo, tarjeta, QR, transferencia o mixto.

Qué función: `PanelCobranza.poblar` / `_iniciar_cobranza` / `MotorCobranzaMedios.finalizar`.

Cómo funciona: El casillero arranca en el **ticket**. QR, tarjeta y transferencia esperan el importe y asientan solos. Tarjeta usa un contenedor fijo con Cancelar; no se manda el Point dos veces. **F9** asocia una transferencia de otro monto o cierra a mano. **Enter no asocia**: espera el exacto. Mixto cobra primero lo digital y después asienta el total.

`MotorCobranzaMedios` es intermediario: asienta el abono y da el ok. El motor real de la venta es `MotorPrincipalCobros`. No unificarlos.

PIN de cobranza y PIN de F9: aún no. Ver `paso6_cobro/decisiones.md`.

Qué no debe cambiar: el intermediario no cierra la venta; emite `abono_exitoso` y el orquestador manda `pago_completado`.
