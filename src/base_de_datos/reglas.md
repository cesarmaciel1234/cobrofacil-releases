# Base de datos — esclava lee a la maestra

Vale para **cualquier perfil**: cajero, jefe, admin, cartelería, lanzador.

## Regla

Si `config.json` dice esclava (`is_master: false` o `db_host` de otra PC):

- Toda lectura y toda venta van a MariaDB de esa IP (`3306`).
- `punpro.db` local **no** es la tienda. Es solo respaldo si la maestra no responde.
- Si el puerto 3306 no contesta, o MariaDB tira circuit breaker / timeout / unreachable, la esclava pasa a ese SQLite. `is_master` no pasa a true.
- La venta de ese rato se guarda en local y en `offline_queue.json`. No se cancela ni se espera el timeout de la API. Al encolar, avisa a Nexus con un UDP `VENTA_NUEVA` en el puerto 37021.
- Cuando la maestra vuelve, `asegurar_lectura_tienda()` deja SQLite y engancha otra vez. La cola sube con el mismo `request_id`.

## Dónde está el gancho

`database.py`: `get_connection`, `execute_query`, arranque en `main.py`, cada cambio de pantalla en `main_window.switch_tab`.

No abras `punpro.db` a mano en un perfil esclavo. Usá `db_manager`.
