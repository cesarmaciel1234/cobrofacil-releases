# Motores

Cada medio tiene carpeta. Validan, consultan, piden persistir.

| Carpeta        | Medio            |
|----------------|------------------|
| efectivo       | Efectivo         |
| tarjeta        | Tarjeta          |
| mixto          | Mixto            |
| transferencia  | Transferencia    |
| fiado          | Fiado. Solo `cerebro.cobrar("Fiado", datos)` |
| clientes       | Clientes. Solo `cerebro.cobrar("Clientes", datos)` |
| qr             | QR y Mercado Pago |

`REGISTRO` en `__init__.py` además apunta crédito y débito a `MotorTarjeta`, y mercadopago a `MotorQR`.

## Ejecución Común (_comun.py)
Contiene la lógica core (ejecutar_comun). Se encarga de guardar en DB (síncrono, ultrarrápido) y deriva la impresión, factura AFIP, cajón y nube a un **hilo secundario** (post_cobro). Esto evita el congelamiento de la UI por desconexiones o bloqueos de red.
