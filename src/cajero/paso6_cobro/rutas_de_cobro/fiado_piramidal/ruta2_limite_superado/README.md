# Ruta 2: límite superado

Qué hace: Bloquea el crédito si el carrito supera el disponible.

Qué función: `PanelLimiteSuperado`. PIN de supervisor (`quien_autoriza`) o botón COBRANZA (`solicita_cobranza`).

Cómo funciona: Cuatro dígitos conceden excepción en el cerebro. El botón abre `modulo_cobranza` sin PIN. F5 no entra acá.

Qué no debe cambiar: el PIN de excepción es de crédito, no de cobranza.
