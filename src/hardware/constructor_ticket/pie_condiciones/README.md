# Pie y Condiciones

**Qué hace:** Imprime información de crédito, mensajes extra, código QR/CAE (AFIP), corta el papel y abre el cajón.
**Qué función:** `generar_pie` en `generador.py`
**Cómo funciona:** Evalúa si hay saldos de cuenta corriente para imprimir. Si hay `factura_electronica_data`, emite el pie legal; sino, un agradecimiento simple. Envía los comandos `CUT_PAPER` y opcionalmente los pulsos para abrir el cajón portamonedas.
**Qué devuelve:** Un `bytearray` con comandos ESC/POS de finalización.
**Qué no debe cambiar:** El final del flujo: debe incluir espacios en blanco (saltos de línea) antes del `CUT_PAPER` para que el papel salga del rodillo correctamente.
