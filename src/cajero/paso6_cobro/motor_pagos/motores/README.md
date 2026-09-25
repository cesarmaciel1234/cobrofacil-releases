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
