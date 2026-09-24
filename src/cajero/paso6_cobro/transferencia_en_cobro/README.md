# Alias en la transferencia

Ocupa el lugar del monto. El importe sigue siendo el de arriba: lo cambian el redondeo y el recargo.

`panel.py`, clase `PanelAliasCobro`. Ocupa todo el recuadro. El lápiz queda arriba a la derecha. El alias va grande al centro y, debajo, el nombre completo con el mismo peso. El lápiz edita el alias en la misma hoja y lo guarda en `mp_alias`.

`cuenta.py`, `datos_cuenta()`. Lee el token del TPV. El nombre sale de `users/me`. El alias, de la cuenta de Mercado Pago. Si la API no lo trae, queda el que se escribió con el lápiz.
