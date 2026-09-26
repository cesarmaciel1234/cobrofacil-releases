# Comandos

Escritura. Un cobro = un comando `persistir_cobro`.

- `armar_venta.py` — `armar_resultado_venta` pasa total, pagos, vuelto, redondeo, oferta y recargo por `redondear_dinero`. El vuelto solo queda en efectivo y en mixto.
- `persistir_cobro.py` — venta + stock (+ fiado si corresponde). Llama `db_manager.guardar_venta_completa`. Antes redondea los renglones. Después, si la línea fue `RELÁMPAGO`, `MotorOfertas.consumir_relampago_en_items` suma el cupo y puede apagar el flash (no tumba la venta si falla). Si no hay id, el cobro no sigue.
- `post_cobro.py` — cajon, ticket, cola diario

En producción esta escritura no se parte. El plano de la venta está en `src/base_de_datos/plano.md`.
