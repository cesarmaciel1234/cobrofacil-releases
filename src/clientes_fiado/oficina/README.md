# Oficina

Acá se llevan los créditos. El paso 5 ya vendió y el paso 6 ya registró el medio. Esta carpeta no cobra esa venta.

```
oficina/
  cuenta/               MotorCuenta — libro clientes y cuenta_corriente
  consulta_historial/   lector para admin y F6
  ticket/               MotorTicket — desglose de venta
  cobradas/             abonos / planilla
  cobranza/             listado de deudores (no es F6)
  por_cobrar/           quién debe
  saldos/               cupo
  cartel/               saludo del cobro
  huella/               auditoría de ficha
```

`cuenta/motor.py` lee y escribe. `ultimos_cargos` va por lotes. `borrar_cargo` marca `BORRADO ·`. F3 cancela con `_anular_cargo` en `repos/ventas.py` y marca `CANCELADO ·`.

`consulta_historial/motor.py` arma las filas. Lo preguntan hilos de admin y de F6. Si uno se cae, el otro sigue.

`ticket/motor.py` solo consulta. Si no hay copia de la venta, informa; no toca la deuda.

`cobranza/consulta.py` no es F6: F6 tiene `f6_centro_cobranzas/consulta.py`.
