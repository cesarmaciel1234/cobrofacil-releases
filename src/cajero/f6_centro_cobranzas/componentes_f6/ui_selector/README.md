# Selector Cobranza

Qué hace: botones de medio y los lienzos (`LienzoEfectivo`, `LienzoQr`, `LienzoTarjeta`, `LienzoTransferencia`, `LienzoMixto`).

QR, tarjeta y transferencia cierran solos cuando Mercado Pago aprueba el importe. F9 es emergencia, no el camino normal. Mixto reparte y después corre esos lienzos en cola: cada uno espera su plata y recién entonces asienta.

Qué función: `PanelSelectorCobranza` en `panel_selector.py`

Cómo funciona: Agrupa visualmente el `cont_botones` y `cont_lienzos`. Se instancia en `PanelFiadoCobro` y expone sus atributos para que el orquestador conecte las señales (ej. `listo`, `volver`) de los lienzos a la lógica de pago.

Qué devuelve cuando falla: Son widgets visuales de PyQt.

Qué no debe cambiar una mejora futura: Los nombres de los atributos expuestos (`cont_botones`, `btn_efectivo`, `cont_lienzos`, `lienzo_efectivo`, etc.) para no romper el mapeo en `PanelFiadoCobro`.
