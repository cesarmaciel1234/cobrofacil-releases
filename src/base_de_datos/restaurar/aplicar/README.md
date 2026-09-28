# aplicar — a qué tienda va y cómo entra

## destino.py

- `destino_actual()`: con MariaDB conectada, `Destino("mariadb", host, servidor=@@hostname)` con los datos de conexión de `db_manager.mariadb_engine._connect_kwargs()`. Si la tienda es SQLite sola (maestra sin MariaDB), `Destino("sqlite", archivo=punpro.db)`.
- Lanza `SinTienda` si la PC es caja (`db_host` de otra PC o `is_master: false`) y no está conectada a la maestra: restaurar ahí escribiría la base de emergencia de la caja. También si la maestra no contesta.
- `Destino.conectar()`: conexión propia con transacción. MariaDB nunca cae a SQLite.
- `Destino.es_local`: la MariaDB es esta PC (localhost o una IP propia). El `.zip` solo se aplica así.

## motor.py

- `modo(fuente, destino)`: `suma` para la copia del jefe y para un `.db` sobre MariaDB; `reemplazo` para `.sql`, `.zip` y `.db` sobre SQLite.
- `revisar(fuente, destino)` → `(bloqueos, avisos)`.
  - Bloqueos: `.sql` / `.zip` sobre tienda SQLite; `.zip` desde otra PC; falta `mariadb_server\bin\mysql.exe` para un `.sql`.
  - Avisos: copia de otra maestra (su `servidor` distinto del `@@hostname` de la tienda); copia sin servidor anotado; copia parcial (pendrive viejo de 8 tablas); respaldo de solo ventas; datos de un día anterior; qué hace el modo; la foto `pre_restore`.
- `restaurar(fuente, destino=None, progreso=None)`: con un bloqueo lanza `RuntimeError` sin tocar nada. Suma: `_foto_antes` (`crear_snapshot_pre_restore`), `sumar`, `_respaldo_despues` (respaldo del día forzado). Reemplazo: `AutoBlindajeDB.restaurar_ultimo_backup_valido(backup_path=…, merge_today=True)`; si devuelve False, `RuntimeError`.

## sumar.py

`sumar(origen, destino, progreso)`: cada tabla de la copia que la tienda también tiene, con las columnas que tienen las dos. Productos, clientes y ventas primero; después el resto por nombre. `espejo_meta` y `terminales_activos` no entran.

- Con clave primaria: `INSERT IGNORE` (MariaDB) / `INSERT OR IGNORE` (SQLite). Lo que la tienda ya tiene no se toca: stock, precios y deudas de la tienda quedan.
- Sin clave: solo se llena si la tabla de la tienda está vacía.
- Ventas: mismo `request_id` = la misma venta, no entra. Mismo número con otro `request_id` = otra venta (la tienda siguió vendiendo después de perder datos): entra con número nuevo. Sus filas de detalle, `mp_pagos` y demás con `id_venta` / `venta_id` se pasan al número nuevo.
- Todo en una transacción, con `FOREIGN_KEY_CHECKS = 0` en MariaDB. Si una tabla falla, rollback: la tienda queda como estaba.
- Devuelve `{"tablas": {tabla: {"sumadas", "ya_estaban"}}, "sin_lugar": [...], "renumeradas": n}`. `sin_lugar`: tablas de la copia que la tienda no tiene (no se crean).

## Arreglos en autoblindaje_db.py que usa el reemplazo

- `.sql`: `mysql --host=<maestra>`. Antes iba sin host y desde una caja restauraba la base local. Revisa el código de salida; antes daba OK aunque fallara.
- `.zip` solo si la MariaDB es esta PC (`_host_es_esta_pc`).
- Un `.db` no reemplaza una MariaDB (antes pisaba `punpro.db` local).

## Qué no cambiar

- No usar `REPLACE` ni `ON DUPLICATE KEY UPDATE` en la suma: pisa deudas y stock con datos viejos.
- No sacar la transacción única.
- No crear en la tienda tablas que la copia trae y la tienda no: el esquema lo arma el migrador del sistema.
