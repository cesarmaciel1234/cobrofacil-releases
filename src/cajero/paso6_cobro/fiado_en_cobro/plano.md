# Plano: Interfaz Nativa de Cobro (F5) Integrada en el Panel Fiado

Frente:
- El cajero presiona F5 estando en Paso 6 (Fiado).
- El panel verde (PanelFiadoCobro) se transforma: oculta la búsqueda de clientes y muestra el monto a cobrar (Deuda Previa + Venta Actual).
- Ofrece botones rápidos (Efectivo, Transferencia, Tarjeta, QR) directamente en el panel verde.
- Si se aplican redondeos (F3) o recargos (F4), el panel verde recalcula en vivo el valor a cobrar.
- Al seleccionar un método (QR, Tarjeta, etc.), el lienzo nativo de cobro se embebe dentro del mismo panel verde, manteniendo visible la cabecera con los saldos.

Fondo:
- PanelFiadoCobro ahora alberga un QStackedWidget con los Lienzos de cobro (LienzoQr, LienzoTarjeta, etc.).
- Cuando un lienzo emite 'listo', el panel asienta el pago usando asentar() y registra los movimientos de caja.
- Luego, emite 'pago_listo', lo que indica a Paso6Cobro que finalice la venta como Fiado. 
- Matemáticamente, el cliente queda con saldo temporal a favor por el pago total, el cual es inmediatamente absorbido por la finalización de la venta actual, garantizando tickets y saldos precisos.