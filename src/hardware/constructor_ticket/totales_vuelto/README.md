# Totales y Vuelto

**Qué hace:** Imprime la suma de la compra, medios de pago y vuelto.
**Qué función:** `generar_totales` en `generador.py`
**Cómo funciona:** Calcula el subtotal, resta descuentos y suma recargos si los hay. En caso de ser factura fiscal, agrega el desglose de IVA usando la función inyectada para el cálculo por tasas.
**Qué devuelve:** Un `bytearray` con comandos ESC/POS.
**Qué no debe cambiar:** La jerarquía de alineación (`ALIGN_CENTER` para subtotales, `ALIGN_LEFT` para pagos y vuelto).
