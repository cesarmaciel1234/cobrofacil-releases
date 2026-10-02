# Fiado en Paso 6

`panel.py`, clase `PanelFiadoCobro`, contiene la selección del cliente y confirma que la compra actual se cargue a su cuenta. `HojaCuentaCobro` conserva el flujo normal: elegir cliente, revisar saldo y presionar Enter. Ese Enter muestra la confirmación verde. El siguiente Enter cierra la venta con `pago_listo`.

## Cobranza Integrada (F5)

Cuando un cliente quiere pagar su deuda o no tiene crédito suficiente, F5 transforma el panel verde en una interfaz de cobro.
- Muestra el monto sugerido: **Deuda Actual + Venta Actual**.
- El panel verde embebe los lienzos nativos de cobro (`LienzoQr`, `LienzoEfectivo`, etc.) sin abrir ventanas de diálogo externas.
- El panel reacciona en vivo a los cambios de F3 (Redondeo) y F4 (Recargo) de la ventana principal, ajustando el monto sugerido automáticamente.

### Contabilidad y Cierre ("Cuenta Corriente Mercantil")

Si el cliente paga este monto, el sistema opera en dos fases:
1. **Recibo de Pago**: `PanelFiadoCobro` llama a `asentar()`, reduciendo la deuda del cliente (generando un saldo temporal a favor si paga la deuda más la venta actual) y registrando el ingreso de caja.
2. **Ticket de Venta**: Inmediatamente se emite `pago_listo`, y `Paso6Cobro` procesa los artículos del carrito cerrando la venta como "Fiado". Esto suma el total del carrito a la cuenta del cliente, contrarrestando el saldo a favor y dejando la deuda exacta, al mismo tiempo que imprime un ticket fiscalmente válido detallando los artículos, recargos y redondeos.

## Qué no cambiar

- El motor de cobranza dentro de `PanelFiadoCobro` asienta el pago mediante `asentar()`. Nunca debe llamar al cierre de la venta general; debe emitir `pago_listo` y dejar que `Paso6Cobro.finalizar()` lo haga en su propio flujo de Fiado.
- No restablezca las validaciones de sobrepago, el saldo a favor temporal es el mecanismo central de este diseño.
