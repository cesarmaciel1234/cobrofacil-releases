# grabar — escribir el paquete del día

`diario.py`, clase `Grabar`.

## Qué hace

Vuelca la base de quien dijo `host_vivo` a las tres carpetas. No elige la máquina: si el host viene vacío, no escribe.

`crear_backup_diario_si_corresponde` vuelca **toda** la base al archivo del día. Antes lee el id de la última venta. Si ese id no aparece en el volcado, no reemplaza el archivo. `sellar_media_hora` copia ese diario completo a `backup_periodico_AHORA`: es la misma base entera, marcada en esa media hora, con el último ticket adentro.

## Cómo corre el diario

`crear_backup_diario_si_corresponde(engine, host, force, min_interval_hours)`:

1. En MariaDB llama `host_vivo`. Si vuelve `""`, avisa y devuelve `False`.
2. Si no es `force` y el archivo de AppData es más nuevo que el intervalo (`_daily_needs_refresh`, de fábrica 30 minutos), solo corre `replicar_espejo` y devuelve `False`. Ese `False` es “no hacía falta”, no un fallo.
3. MariaDB: `_backup_mariadb`. SQLite: `_backup_sqlite`.
4. Si salió bien, replica y deja el log en la última carpeta.

`_backup_mariadb(targets, host, ticket_id)`:

1. Host vacío, o sin poder leer el último ticket: `False`. No toca el disco.
2. Sin `mysqldump.exe`: `False`. No comprime la carpeta en caliente.
3. `mysqldump` de toda `punpro_db`, `--default-character-set=utf8mb4 --single-transaction --quick`, tope 90 s. La salida se lee en bytes y se decodifica como UTF-8: en Windows, leerla como texto usa cp1252 y corta el archivo en el primer byte que esa tabla no tiene. Hace falta `Dump completed`, más de 500 bytes, y el id del último ticket dentro del texto. Recién ahí reemplaza el archivo. Si el volcado no es UTF-8, la copia anterior queda. Ese rechazo no se cura como si se hubiera caído la red.

## Las otras funciones

- `sellar_media_hora`: copia el diario recién grabado a `backup_periodico_FECHA_HORA`. No vuelve a volcar.
- `backup_incremental_tablas_venta`: llama al diario completo. No escribe un recorte de ventas.
- `crear_backup_cierre_turno` y `finalizar_backup_del_dia`: el sello al cerrar. Pasan por el mismo diario completo.
- `_backup_sqlite`: copia `punpro.db` entero. Si no está el archivo, `False`.

## Qué no debe cambiar

- No guardar un recorte de tablas de venta como si fuera la media hora. La media hora es la base entera.
- Sin `Dump completed` o sin el último ticket, el archivo anterior no se toca.
- No hacer zip de la carpeta MariaDB en caliente y darlo por `.sql` del día.
- Escribir al lado (`.part`) y reemplazar. Un corte a mitad no deja el diario truncado.
