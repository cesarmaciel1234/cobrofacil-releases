# Comandos

Escritura. Un cobro = un comando `persistir_cobro`.

- `armar_venta.py` — `armar_resultado_venta` pasa total, pagos, vuelto, redondeo, oferta y recargo por `redondear_dinero`. El vuelto solo queda en efectivo y en mixto.
- `persistir_cobro.py` — venta + stock (+ fiado si corresponde). Llama `db_manager.guardar_venta_completa`. Antes redondea los renglones con `redondear_items_carrito` y, si es fiado, el total de la deuda. Si no hay id, el cobro no sigue.
- `post_cobro.py` — cajon, ticket, cola diario

En producción esta escritura no se parte. El plano de la venta está en `src/base_de_datos/plano.md`.
