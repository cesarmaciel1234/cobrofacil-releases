# e2e — prueba contra una maestra de PRUEBA

`prueba_maestra.py` escribe en una MariaDB real y al final borra lo suyo. No lo levanta pytest (no empieza con `test_`).

```
python tests/e2e/prueba_maestra.py --host 192.168.0.13
```

Solo contra la maestra de prueba de la PC de programación. **Nunca contra la del negocio.**

## Qué recorre

1. Esquema: `_create_tables` + `_migrate_db` (lo que hace la maestra al arrancar) y `huella.tabla.asegurar` (columnas `uid`…, índice `ux_clientes_uid`, `clientes_auditoria`).
2. Cartera en la tienda con `cerebro.cuenta`: alta, ficha, límite, cargo manual, abono. Deuda y libro de eventos.
3. Cargado en casa: un SQLite con eventos `LOCAL` → `absorber.aplicar`. Primera vuelta 6 aplicados y 1 pendiente; segunda, 6 repetidos. Fusión por DNI, sin duplicados.
4. Una venta: la vitrina en vivo la ve.
5. `espejo.refrescar`: la vitrina sin red lee la copia (franja ámbar). `sincronizar_faltantes` a un pendrive temporal: ventas y modo DELETE.
6. Limpieza: clientes `PRUEBA E2E`, sus movimientos, eventos y la venta.

La copia y el pendrive van a una carpeta temporal: no tocan los de la PC.

## Ojo

Al conectar, `diario_ventas_externo` puede reinyectar en esa maestra los tickets del diario de AppData de esta PC (anti-wipe). Es lo de siempre del programa, no de la prueba. Sale en el log como «reinyectados N tickets».

Tablas dañadas en la maestra de prueba: se recrean vacías con sus columnas (`information_schema.columns`). Si queda un `.ibd` huérfano (errno 184), se crean con `innodb_file_per_table=OFF`.
