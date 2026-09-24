# Comandos

Escritura. Un cobro = un comando `persistir_cobro`.

- `persistir_cobro.py` — venta + stock (+ fiado si corresponde). Llama `db_manager.guardar_venta_completa`. Si no hay id, el cobro no sigue.
- `post_cobro.py` — cajon, ticket, cola diario

En producción esta escritura no se parte. El plano de la venta está en `src/base_de_datos/plano.md`.
