# Ruta 1: Margen Aprobado (Pantalla Verde)

## ¿Qué hace?
Es la pantalla minimalista que aparece cuando el cliente tiene suficiente saldo a favor en su cuenta corriente para llevarse el carrito actual sin superar su límite.

## ¿Qué función cumple en el negocio?
Garantizar velocidad y privacidad. El cajero no necesita leer cuánto debe el cliente ni hacer cuentas. Simplemente ve un cartel verde gigante con el texto "CRÉDITO APROBADO" y aprieta ENTER para confirmar la transacción, permitiendo despachar la fila en segundos.

## ¿Cómo funciona?
- **`panel_aprobado.py`**: Es un `QFrame` con fondo degradado verde. No tiene lógica contable.
- Solo espera el atajo de teclado `[ ENTER ]` para emitir la señal que finaliza la venta.
- Si el cliente decide pagar su deuda histórica, el cajero puede presionar `[ F5 ]`, lo que cede el control temporalmente al puente de cobranza en la Ruta 2.
