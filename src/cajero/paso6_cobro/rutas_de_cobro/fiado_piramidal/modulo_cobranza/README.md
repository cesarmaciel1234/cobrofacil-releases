# Módulo de cobranza

Qué hace: Cobra un abono (carrito, deuda o ambos) con efectivo, tarjeta, QR, transferencia o mixto.

Qué función: `PanelCobranza.poblar` / `_iniciar_cobranza` / `MotorCobranzaMedios.finalizar`.

Cómo funciona: El casillero arranca en el **ticket**. Los digitales son los mismos que el cobro del ticket, en lienzos de `ingresar_efectivo/medios/` (esta hoja no abre F6):

- **QR:** `pedir_qr_pos` + `pago_aprobado` por el uuid de esta orden. Reloj 800 ms. Un cobro viejo del mismo importe no cierra. F9 a mano.
- **Transferencia:** `ultimo_libre` con ventana (después de abrir el medio, máx. 3 min). Enter espera el exacto. F9 asocia.
- **Tarjeta:** el mismo `enviar_monto` del Point. Cancelar suelta. F9 a mano.
- **Mixto:** solo dos medios. Cola Tarjeta → Transferencia → QR. Después asienta una vez.

`MotorCobranzaMedios` asienta el abono. El ticket lo cierra el orquestador con `pago_completado`.

`MotorCobranzaMedios` es intermediario: asienta el abono y da el ok. El motor real de la venta es `MotorPrincipalCobros`. No unificarlos.

PIN de cobranza y PIN de F9: aún no. Ver `paso6_cobro/decisiones.md`.

Qué no debe cambiar: el intermediario no cierra la venta; emite `abono_exitoso` y el orquestador manda `pago_completado`.
