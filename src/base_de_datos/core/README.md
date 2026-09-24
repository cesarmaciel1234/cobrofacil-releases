# Núcleo de la base

Acá se abre la conexión y se ejecutan las consultas. La pantalla no llama estos métodos: pasa por `db_manager`.

## connection.py

`ConnectionMixin.get_connection(caer_si_maestra_caida=True)` devuelve SQLite o MariaDB.

Si esta PC es esclava (`is_master` falso y `_host_tienda()` trae IP) y el puerto 3306 no contesta, llama `reconectar_local()` y devuelve el `punpro.db` local. No pone `is_master` en true. Prende `_forced_local_offline`.

Si el puerto parecía abierto y el conector tira red caída (`error_indica_maestra_caida`), hace lo mismo. El texto del circuit breaker (`unreachable` / `cooldown`) entra en esa lista. Un `access denied` no: la maestra está, la clave no.

`caer_si_maestra_caida=False` no cambia de motor. Lo usa `sync_venta_to_master` para no dar por subida una venta que solo se escribió en el respaldo.

`reconectar_local()` arma el path local, deja `db_engine_type` en `sqlite`, borra `mariadb_engine`, crea tablas y migra. Si ya está adentro (`_reconectando_local`), sale sin repetir. Al terminar anota `_last_master_try` para no volver a golpear la maestra en el mismo instante.

`_puerto_maestra_vivo(host)` usa `puerto_mariadb_abierto` con 0,6 s. Si responde, lo recuerda 8 s en `_maestra_viva_hasta` para no frenar cada lectura.

`reconectar_mariadb(host)` solo pisa el motor si el ping funciona.

## executor.py

`QueryExecutorMixin.execute_query`, `execute_non_query`, `execute_many` y `execute_scalar`.

Antes de leer, si hay maestra configurada, llama `asegurar_lectura_tienda()`. Si la consulta falla con marca de caída y esta PC es esclava, `_caer_a_sqlite_si_maestra_caida` pasa a SQLite y reintenta esa consulta una vez (`_reintento=True`). La segunda falla ya no cambia de motor: devuelve `[]`, `False` o `None`.

## mariadb_probe.py

`puerto_mariadb_abierto(host, timeout)` hace `connect_ex` al 3306. `False` si no hay host o si el sistema rechaza.

`error_indica_maestra_caida(err)` mira el texto: lost connection, can't connect, timeout, circuit breaker, unreachable, cooldown, 2003, 2006, 2013, 10060, 10061.

## red_rol.py

`leer_rol_red_desde_config(config_data)` devuelve `(es_esclava, host_remoto)`. Esclava si `is_master` es false, si `carteleria_is_slave` trae IP, o si `db_host` / `preferred_master_ip` / `carteleria_master_ip` apuntan a otra PC.

## db_path.py

`normalize_db_path` deja el archivo SQLite junto a la app.

## Qué no debe cambiar

No promover la esclava a maestra al caer la red. No borrar `ventas` ni `productos`. No tratar el circuit breaker como un error de SQL que se traga y devuelve vacío. No hacer que `sync_venta_to_master` escriba en el SQLite local y marque la cola como subida.
