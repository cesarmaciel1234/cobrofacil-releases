# Motor de cobros (paso 6)

Piramide. La UI solo llama a `MotorPrincipalCobros.iniciar_transaccion`.

```
motor_pagos/
  motor_principal.py     despacha por metodo
  consultas/             solo lecturas
  comandos/              escrituras (una transaccion)
  motores/               un motor por medio
  dtos/                  orden de cobro
```

Los motores **no se llaman entre si**. Hablan con `consultas` y `comandos`.
Fiado: venta + deuda + cuenta corriente en el mismo commit.
