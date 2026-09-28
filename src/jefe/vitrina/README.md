# metricas — KPIs de la vitrina

Todas reciben `desde` / `hasta` ('YYYY-MM-DD', los dos días incluidos). Sin fechas = hoy. Cuentan ventas vigentes (`COMPLETADA` del turno + `CERRADA` después del Z) y filtran con rango (`fecha >= desde AND fecha < día siguiente a hasta`). Si la consulta falla, devuelven cero.

- `ganancia(desde, hasta)`: la de `reportes/financiero.kpis_rango`. `None` si no hay costo cargado.
- `redondeo(desde, hasta)`: suma `ventas.descuento` (F3 redondeo + oferta en ticket).
- `tickets(desde, hasta)`: `(cantidad, total vendido)`. La vista muestra `77 · $1.657.988,50` y abajo el promedio.
- `cancelaciones(desde, hasta)`: ventas `CANCELADA` por `fecha_cancel` (si falta, la fecha de la venta). `{'cant', 'monto', 'cuando', 'usuario'}` de la última; `cuando` = 'YYYY-MM-DD HH:MM'.
- `pagos_clientes(desde, hasta)`: abonos de `cuenta_corriente`.
- `digitales(desde, hasta)`: `(sin_firmar, total)`. Sin firmar = digitales (QR, tarjeta, transferencia, MP, Point) cuyo `id` no está como ticket en `reportes/mp_vinculos.json` de esta PC ni en `mp_pagos` de la tienda (`motor_cobros_digitales.veredicto.conciliar.tickets_firmados(desde, hasta)`).

- `deuda_clientes()` e `inventario_costo()`: los mismos números que `cerebro.resumen_cuentas()` y `WorkerAnaliticaJefe`. El panel los usa sin maestra.

Los `*_del_dia(fecha)` quedan como atajo de un solo día.

`_db()` es `nodo_portable.espejo.fuente()`: con maestra, `db_manager`; sin maestra, la copia de la tienda de esta PC (o la del pendrive). La vista muestra entonces la franja ámbar `set_origen(leyenda())`. El libro de vínculos es archivo local.
