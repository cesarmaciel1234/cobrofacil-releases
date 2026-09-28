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

## Si la maestra cambia de IP

La IP es solo la dirección. Los datos de la tienda están en la MariaDB de la maestra y no se mueven.

- **Esclava cerrada cuando cambió.** Al arrancar no llega a la IP de `db_host` y queda en SQLite local. `NetworkDBService.boot` (`src/services/db_network_service.py`) manda `PUNPRO_DISCOVER` por broadcast al puerto UDP 37020. La maestra contesta desde `start_udp_discovery_server` (`src/central_red_global/lan_server.py`) con su `server_ip`. La esclava guarda `db_host`, `api_url` e `is_master: false` en `config.json` y engancha MariaDB en esa IP.
- **Esclava abierta cuando cambió.** Pierde la maestra y sigue vendiendo en SQLite y `offline_queue.json`. `asegurar_lectura_tienda()`, el reintento de 30 s y `auto_heal` prueban solo la IP guardada: no buscan la nueva. Hay que cerrar y abrir el programa en la esclava.
- Para que el aviso funcione: la maestra prendida con el Servidor de Tienda (`--server`), las dos PCs en la misma red y el firewall abierto en UDP 37020.
- Las ventas de ese rato quedan en `offline_queue.json`, en disco. Sobreviven a cerrar el programa y a apagar la PC. Cuando la esclava vuelve a ver la maestra, `OfflineSync` las sube cada 15 s, en orden, con el mismo `request_id`: no se duplican. Solo salen de la cola las que la maestra aceptó.
- Los clientes nuevos o editados en la esclava suben por la huella (`src/clientes_fiado/oficina/huella`). Cada evento tiene id propio: el reintento no duplica.
- Mientras tanto, la esclava ve el catálogo de la última bajada y el panel del jefe muestra la copia local con el aviso «datos de la tienda al …». La maestra no ve esas ventas hasta que suben.
- No borrar la carpeta del programa en la esclava con ventas sin subir: se pierde `offline_queue.json`.
- La copia del jefe reconoce la maestra por el nombre de la máquina (`@@hostname`), no por la IP. La huella identifica cada PC por su `pc_id`. Un cambio de IP no toca ninguna de las dos.

En el negocio conviene fijar la IP de la maestra en el router (reserva DHCP por MAC). Así no cambia ni tras un corte de luz.

## config.json (`src/config.py`)

Varios procesos (jefe, admin, cajero) guardan el mismo archivo. `save()` escribe un `.tmp` y hace `os.replace`: quien lee ve el viejo o el nuevo, nunca uno a medio escribir. `_leer_json()` reintenta 5 veces. Si aun así no se puede leer, queda `_no_guardar`: el próximo `save()` vuelve a leer el disco antes de escribir y, si sigue ilegible, no guarda. Antes, una lectura a medias volvía a valores de fábrica y el siguiente guardado borraba `jefe_nodo_path` y el resto.

## Copia de la tienda para el jefe

`src/jefe/nodo_portable/espejo` lee la MariaDB con su propia conexión pymysql, no con `db_manager`: `execute_query` se traga el error y puede cambiar a SQLite en medio de la copia. No escribe en `punpro.db`. Copia toda la tienda (menos `terminales_activos`).

## Restaurar

Un solo motor, `restaurar/`, para respaldos y para la copia del jefe. Restaurar va siempre a la tienda: la MariaDB de la maestra con su propia conexión, nunca la SQLite de emergencia de una caja. Una caja sin maestra no restaura ni exporta.

La tienda trabaja con MariaDB. Los `.sql` / `.zip` solo se aplican con el MariaDB del sistema, y la copia del jefe (SQLite de viaje) la lee el sistema y la vuelca a MariaDB. Quien quiera leer una copia tiene que instalar el sistema.
