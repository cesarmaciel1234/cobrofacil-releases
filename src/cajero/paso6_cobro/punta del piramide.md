# Punta de la pirámide — cobro

La ventana de cobrar. El gris tapa el paso 5. Esta carpeta no arma el ticket.

```
paso6_cobro/
  punta del piramide.md
  paso6_cobro.py           la ventana
  componentes_paso6_cobro/
    selector_metodo_pago/  tres tarjetas arriba y dos abajo
  mercadopago_core/        Point y QR, si el TPV está activo
  motor_pagos/             guarda la venta
  widgets/                 pago mixto, fiado y cliente
```

Si el TPV no está activo, tarjeta y QR se registran igual. La luz está en el encabezado: verde listo, roja sin terminal.
