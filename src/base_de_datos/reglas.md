# Base de datos — esclava lee a la maestra

Vale para **cualquier perfil**: cajero, jefe, admin, cartelería, lanzador.

## Regla

Si `config.json` dice esclava (`is_master: false` o `db_host` de otra PC):

- Toda lectura y toda venta van a MariaDB de esa IP (`3306`).
- `punpro.db` local **no** es la tienda. Guarda la venta de ese rato. Clientes, admin y ventas digitales se leen de la copia (`espejo`) mientras la maestra no responde. Al volver, esa copia se deja y la cola sube a la maestra.
- Si el puerto 3306 no contesta, o MariaDB tira circuit breaker / timeout / unreachable, la esclava pasa a ese SQLite. `is_master` no pasa a true.
- La venta de ese rato se guarda en local y en `offline_queue.json`. No se cancela ni se espera el timeout de la API. Al encolar, avisa a Nexus con un UDP `VENTA_NUEVA` en el puerto 37021.
- Cuando la maestra vuelve, `asegurar_lectura_tienda()` deja SQLite y engancha otra vez. En ese instante, en segundo plano, sube la cola y baja catálogo, clientes, ventas y la copia. No espera el turno de 15 segundos. La cola de tickets sube con el mismo `request_id`.
- `offline_queue.json` se reemplaza entero (archivo al lado, `fsync`, `os.replace`). Un corte de luz deja la cola anterior. Si el archivo no se puede leer, no se vacía. La caja espera el candado de la subida antes de agregar un ticket, así una venta no pisa a la otra.
- Cada ticket sube en una sola transacción. Si las líneas no coinciden con la cabecera, se deshace y el ticket sigue en la cola. No queda una parte en la maestra. Sale de la cola cuando la reserva lo tiene en el espejo (`en_titular` hasta el acuse). Si esta PC ya es la titular, sale al confirmarse el guardado.

## Dónde está el gancho

`database.py`: `get_connection`, `execute_query`, arranque en `main.py`, cada cambio de pantalla en `main_window.switch_tab`.

No abras `punpro.db` a mano en un perfil esclavo. Usá `db_manager`.

## Si la maestra cambia de IP

La IP es solo la dirección. Los datos de la tienda están en la MariaDB de la maestra y no se mueven.

- **Esclava cerrada cuando cambió.** Al arrancar no llega a la IP de `db_host` y queda en SQLite local. Al reconectar, `asegurar_lectura_tienda()` busca por UDP 37020 en un hilo. La maestra anuncia `server_ip` y un `store_id` estable. La esclava enlaza solo si la MariaDB tiene `productos` y la identidad coincide; actualiza `db_host` y `api_url` y engancha MariaDB en segundo plano. Si la identidad no se había aprendido antes, no salta automáticamente a otra IP.
- **Esclava abierta cuando cambió.** Pierde la maestra y sigue vendiendo en SQLite y `offline_queue.json`. La reconexión de `asegurar_lectura_tienda()` busca por UDP 37020 en un hilo, verifica el `store_id` y cambia la conexión cuando encuentra esa misma tienda. No hace falta cerrar la caja. Si no encuentra la misma identidad, permanece offline y conserva la cola.
- Para que el aviso funcione: la maestra prendida con el Servidor de Tienda (`--server`), las dos PCs en la misma red y el firewall abierto en UDP 37020.
- Las ventas de ese rato quedan en `offline_queue.json`, en disco. Sobreviven a cerrar el programa y a apagar la PC. Cuando la esclava vuelve a ver la maestra, `OfflineSync` las sube cada 15 s, en orden, con el mismo `request_id`: no se duplican. Solo salen de la cola las que la maestra aceptó.
- Los clientes nuevos o editados en la esclava suben por la huella (`src/clientes_fiado/oficina/huella`). Cada evento tiene id propio: el reintento no duplica.
- Mientras tanto, la esclava ve el catálogo de la última bajada y el panel del jefe muestra la copia local con el aviso «datos de la tienda al …». La maestra no ve esas ventas hasta que suben.
- La reserva aprende el `store_id` al consultar la titular. Si se promueve, continúa anunciando la misma identidad; las demás esclavas pueden enlazarse sin confundirla con otra tienda. Un reemplazo nuevo debe conservar el `store_id` de la tienda en su `config.json`.
- No borrar la carpeta del programa en la esclava con ventas sin subir: se pierde `offline_queue.json`.
- La copia del jefe reconoce la maestra por el nombre de la máquina (`@@hostname`), no por la IP. La huella identifica cada PC por su `pc_id`. Un cambio de IP no toca ninguna de las dos.

## Auditorías de stock sin conexión

Si una esclava ajusta stock offline, el producto actualizado y el evento de auditoría se conservan en `offline_cambios.json`. La auditoría lleva un `sync_id` estable; la maestra lo usa para reconocer reintentos y no duplicar el registro. El evento sale de la cola solo después de comprobar que quedó registrado en la maestra. Luego el espejo copia completa `auditorias_inventario`. La maestra sigue siendo la fuente de verdad: la esclava no escribe directamente en MariaDB.

No borrar ni reconstruir `offline_cambios.json` mientras tenga pendientes. Si el archivo está ilegible, no se sobrescribe y la sincronización debe informar el error.

Las recepciones offline llevan un `sync_id` estable. En SQLite, el journal `offline_recepciones` se escribe en la misma transacción que el remito, los ítems, el stock/costo y el gasto; así se reconstruye el outbox si el proceso se corta antes de escribir el JSON. En la maestra, esos mismos efectos deben confirmar en una sola transacción; si falla una parte, la cola conserva la recepción completa. El journal local solo se borra después de guardar el acuse del outbox. No quitar la recepción hasta confirmar el remito con ese mismo `sync_id`. No usar «último id de la tabla» para asociar el remito: usar el `lastrowid` de la inserción.

En el negocio conviene fijar la IP de la maestra en el router (reserva DHCP por MAC). Así no cambia ni tras un corte de luz.

## config.json (`src/config.py`)

Varios procesos (jefe, admin, cajero) guardan el mismo archivo. `save()` escribe un `.tmp` y hace `os.replace`: quien lee ve el viejo o el nuevo, nunca uno a medio escribir. `_leer_json()` reintenta 5 veces. Si aun así no se puede leer, queda `_no_guardar`: el próximo `save()` vuelve a leer el disco antes de escribir y, si sigue ilegible, no guarda. Antes, una lectura a medias volvía a valores de fábrica y el siguiente guardado borraba `jefe_nodo_path` y el resto.

## Copia de la tienda para el jefe

`src/jefe/nodo_portable/espejo` lee la MariaDB con su propia conexión pymysql, no con `db_manager`: `execute_query` se traga el error y puede cambiar a SQLite en medio de la copia. No escribe en `punpro.db`. Copia toda la tienda (menos `terminales_activos`).

## Restaurar

Un solo motor, `restaurar/`, para respaldos y para la copia del jefe. Restaurar va siempre a la tienda: la MariaDB de la maestra con su propia conexión, nunca la SQLite de emergencia de una caja. Una caja sin maestra no restaura ni exporta.

La tienda trabaja con MariaDB. Los `.sql` / `.zip` solo se aplican con el MariaDB del sistema, y la copia del jefe (SQLite de viaje) la lee el sistema y la vuelca a MariaDB. Quien quiera leer una copia tiene que instalar el sistema.
