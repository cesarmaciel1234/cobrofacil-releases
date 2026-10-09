# Fiado en Paso 6 (Proceso Piramidal de Crédito)

La clase `PanelFiadoCobro` (`panel.py`) es el orquestador de un diseño piramidal donde los componentes visuales y lógicos están encarpetados en `componentes_fiado/` (Estado Crédito, Selector Cobranza y Motor).

## Un proceso: el normal
El cliente viene, pide fiado, y se carga a la cuenta.
1. `HojaCuentaCobro` busca al cliente.
2. Al seleccionarlo (Enter), el sub-módulo `estado_credito` muestra la confirmación verde (Crédito Aprobado).
3. Un último Enter emite `pago_listo` al sistema principal (`Paso6Cobro`).
4. El sistema cierra la venta como Fiado, incrementando la deuda del cliente por el valor del carrito.

## Otro proceso: F5 (Cobranza Integrada)
El cliente quiere pagar su deuda o abonar parte de ella en el mismo momento de la compra.
1. El cajero presiona F5, lo que activa el sub-módulo `selector_cobranza` mostrando botones de métodos de pago.
2. El monto sugerido suma la deuda previa y la venta actual, adaptándose en vivo a recargos o redondeos (F3/F4).
3. Al seleccionar un método, un lienzo nativo se embebe en el panel verde.
4. **Contabilidad en dos fases:**
   - **Recibo de Pago:** El sub-módulo `motor` llama a `asentar()` con el monto pagado, ingresando el dinero a caja y reduciendo la deuda (dejando saldo a favor si cubrió la venta actual).
   - **Ticket de Venta:** Inmediatamente emite `pago_listo`. `Paso6Cobro` procesa los artículos, cerrando la venta como "Fiado". Esto suma el total a la cuenta, contrarrestando el saldo a favor exacto.

## Qué no cambiar
- El flujo piramidal expone las variables de los submódulos (`self.estado`, `self.lienzo_qr`, etc.) directamente en `PanelFiadoCobro` para mantener compatibilidad total con el exterior. No se debe cambiar esta firma.
- El `MotorCobranza` nunca cierra la venta general; debe emitir `pago_listo` y dejar que `Paso6Cobro` lo haga. No restablezca validaciones de sobrepago.
