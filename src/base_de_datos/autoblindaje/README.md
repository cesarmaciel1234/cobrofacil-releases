# autoblindaje — el .sql del negocio

La puerta que ya usa el programa sigue siendo `src/base_de_datos/autoblindaje_db.py`. Ahí no hay lógica: importa `AutoBlindajeDB` de `puerta.py`.

Esto no es la copia SQLite del jefe. Esa vive en `src/jefe/nodo_portable/espejo/` y se refresca cada minuto. Acá se graba el volcado `.sql` completo cada minuto. Las dos copias tienen que existir. Si falta el `.sql`, el espejo no lo reemplaza.

## Orden

1. `quien/maestra.py` `host_vivo` dice de qué máquina se copia. Si esta PC es maestra y el puerto 3306 local responde, devuelve `127.0.0.1`. Si es esclava, manda `PUNPRO_DISCOVER` al UDP 37020 y usa la IP que la maestra anuncia en ese momento. No lee `db_host` ni otra IP guardada. Si nadie contesta, devuelve vacío.
2. `grabar/diario.py` `crear_backup_diario_si_corresponde` escribe el archivo del día en las tres carpetas de `rutas/carpetas.py`. Si `host_vivo` vino vacío, no escribe y devuelve `False`.
3. `rutas/carpetas.py` `replicar_espejo` toma lo que ya está en AppData y lo copia a las otras dos rutas si ahí falta o el tamaño no coincide.
4. `sanar/integridad.py` `verificar_y_respaldar_diario` corre al arrancar: si no hay maestra, solo replica lo ya guardado y no toca la base. Si hay maestra, revisa, repara o restaura, y después pide el diario.

El reloj es otro módulo: `src/cerebro_global/backup_cerebro/`. Cada minuto llama a esta rama y vuelca toda la base. Cada 30 minutos sella una copia con hora. El diario de hoy no se borra. De los días anteriores quedan diez: ayer pesa un poco menos que hoy, y mañana un poco más, porque cada archivo es la tienda entera más lo de ese día. La más antigua se va sola. De las de media hora quedan las diez más nuevas. Si el disco es chico, el jefe borra a mano y puede dejar la de ayer. Un fallo deja `last_ok` en falso y no mueve la fecha del último `.sql` bueno.

## Qué no debe cambiar

- No elegir una IP guardada por encima del anuncio de la red.
- No comprimir la carpeta MariaDB de una esclava y llamarla respaldo de la tienda. El zip físico solo si el host es esta PC y `mysqldump` falló.
- No dar por bueno un `.sql` de 500 bytes o menos.
- No borrar la puerta `autoblindaje_db.py`: el cajero, el arranque y el restaurar importan desde ahí.
- AppData es la carpeta 1 de `get_backup_directories`. `replicar_espejo` copia desde ahí.
