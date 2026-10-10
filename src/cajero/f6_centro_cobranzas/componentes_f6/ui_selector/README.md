# Selector Cobranza

Qué hace: Mantiene los botones de métodos de pago (Efectivo, Tarjeta, etc.) y el stack de lienzos (`LienzoEfectivo`, `LienzoQr`, etc.).

Qué función: `PanelSelectorCobranza` en `panel_selector.py`

Cómo funciona: Agrupa visualmente el `cont_botones` y `cont_lienzos`. Se instancia en `PanelFiadoCobro` y expone sus atributos para que el orquestador conecte las señales (ej. `listo`, `volver`) de los lienzos a la lógica de pago.

Qué devuelve cuando falla: Son widgets visuales de PyQt.

Qué no debe cambiar una mejora futura: Los nombres de los atributos expuestos (`cont_botones`, `btn_efectivo`, `cont_lienzos`, `lienzo_efectivo`, etc.) para no romper el mapeo en `PanelFiadoCobro`.
