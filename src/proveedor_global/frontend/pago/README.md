# Pago

## Qué hace la carpeta
El pago centralizado de los fiados abiertos. La pantalla la arma `VistaProveedor._pago_centralizado` y esta carpeta guarda la nota del proceso.

## Qué función, con el nombre real
* `VistaProveedor._deudas_abiertas`: fiados con saldo, de la tienda y de esta PC.
* `VistaProveedor._pagar_proveedor`: un pago. Si el id empieza con `casa:`, no toca la deuda de la tienda.
* `MotorProveedor.pagar_proveedor` y `pagar_en_casa`.

## Cómo funciona, en el orden en que corre
1. La tarjeta abre los fiados y, debajo, el historial de pagos ya hechos.
2. El pago pide monto, forma (efectivo, transferencia, cheque o mixto), fecha de emisión y una nota.
3. Una cuenta de esta PC se anota en `punpro.db`. Una del negocio espera la tienda. El registro de la factura no se borra.

## Qué devuelve cuando falla
Si todas las elegidas son del negocio y no hay tienda, avisa y no marca ninguna.

## Qué no debe cambiar una mejora futura
No pagar un id local contra el mismo número en la tienda.
