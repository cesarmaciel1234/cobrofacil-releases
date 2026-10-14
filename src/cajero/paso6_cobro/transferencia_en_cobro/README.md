# Alias y escucha de transferencia

Ocupa el lugar del monto. El importe sigue siendo el de arriba: lo cambian el redondeo y el recargo.

`panel.py`, clase `PanelAliasCobro`. Ocupa todo el recuadro. El lápiz queda arriba a la derecha. El alias va grande al centro y, debajo, el nombre completo en gris oscuro. El lápiz edita el alias en la misma hoja y lo guarda en `mp_alias`. Con la luz del TPV en rojo, Enter no espera la transferencia: guarda la venta por el importe de arriba.

`cuenta.py`, `datos_cuenta()`. Lee el token del TPV. El nombre sale de `users/me`. El alias, de la cuenta de Mercado Pago. Si la API no lo trae, queda el que se escribió con el lápiz.

`escucha.py`, `pago_llegado` / `ultimo_libre` / `texto_enlazar`. Si el importe es el del ticket, cierra solo. Si llega otro monto, el toast pregunta si enlazar: F9 emergencia, o esperar el exacto. Enter no enlaza.
