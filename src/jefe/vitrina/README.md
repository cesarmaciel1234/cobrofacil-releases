# vitrina — KPIs del home del jefe

`hilo.py` arma el paquete fuera de la ventana. `paquete(desde, hasta)` devuelve el diccionario que pinta el panel. Si una cuenta falla, esa queda en cero y las otras siguen. `HiloVitrina` emite `listo(generacion, paquete)`. La ventana no espera la consulta.

`metricas.py` es cada número.

# metricas — KPIs de la vitrina

Todas reciben `desde` / `hasta` ('YYYY-MM-DD', los dos días incluidos). Sin fechas = hoy. Cuentan ventas vigentes (`COMPLETADA` del turno + `CERRADA` después del Z) y filtran con rango (`fecha >= desde AND fecha < día siguiente a hasta`). Si la consulta falla, devuelven cero.

- `ganancia(desde, hasta)`: la de `reportes/financiero.kpis_rango`. `None` si no hay costo cargado.
- `redondeo_y_descuento(desde, hasta)`: `(F3, ofertas)`. Parte `ventas.descuento`.
- `redondeo(desde, hasta)`: F3 del cobro.
- `descuento(desde, hasta)`: ofertas del ticket (DES. TOTAL).
- `tickets(desde, hasta)`: `(cantidad, total vendido)`. La vista muestra `77 · $1.657.988,50` y abajo el promedio.
- `cancelaciones(desde, hasta)`: ventas `CANCELADA` por `fecha_cancel` (si falta, la fecha de la venta). Cuenta y suma en SQL y trae solo la última fila. `{'cant', 'monto', 'cuando', 'usuario'}`; `cuando` = 'YYYY-MM-DD HH:MM'.
- `pagos_clientes(desde, hasta)`: abonos de `cuenta_corriente`.
- `digitales(desde, hasta)`: `(sin_firmar, total)` solo QR/tarjeta/transferencia/Point. Fiado, Clientes y MasCredito no entran: son cuenta/DNI.
- `cobros_auditoria(desde, hasta)`: mismos montos que el monitor (`tickets_digitales`, `cliente`, `sin_firmar_monto`, `firmados`, `sin_ticket_monto`) más conteos. La vitrina muestra el `5/25` (no firmados / tickets digitales) y aparte MP sin ticket.

- `deuda_clientes()` e `inventario_costo()`: los mismos números que `cerebro.resumen_cuentas()` y `WorkerAnaliticaJefe`. El panel los usa sin maestra.

Los `*_del_dia(fecha)` quedan como atajo de un solo día.

`_db()` es `nodo_portable.espejo.fuente()`: con maestra, `db_manager`; sin maestra, la copia de la tienda de esta PC (o la del pendrive). La vista muestra entonces la franja ámbar `set_origen(leyenda())`. El libro de vínculos es archivo local.
