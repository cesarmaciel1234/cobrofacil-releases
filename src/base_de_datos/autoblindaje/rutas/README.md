# rutas — las tres carpetas del .sql

`carpetas.py`, clase `Rutas`.

## Qué hace

Dice dónde se guarda el paquete y copia lo que ya existe para que las tres rutas no queden distintas.

`get_backup_directories()` devuelve, en este orden:

1. `{programa}/backups/db`
2. `%LOCALAPPDATA%\CobroFacil_PRO\backups\db`
3. `%USERPROFILE%\Documents\CobroFacil_Backups\db` — solo si se pudo crear

Crea las carpetas. Si Documentos no se puede crear, la lista queda en dos. La 2 es el origen de `replicar_espejo()`.

## Funciones

- `replicar_espejo()`: de cada archivo se queda con la copia más nueva y la reparte. No pisa una copia más nueva con una vieja. Un `.part` no se copia. Devuelve cuántos copió.
- `_targets_diario_hoy(engine)`: un path por carpeta, nombre `backup_diario_AAAA-MM-DD.sql` (MariaDB) o `.db` (SQLite).
- `_paths_backup_diario_hoy(engine)`: el primero, el de AppData y el nombre.
- `_fecha_hoy()`: `AAAA-MM-DD` del reloj de esta PC.
- `_backup_date_str(path)`: saca la fecha del nombre, o `None`.
- `detectar_unidades_usb()`: letras de pendrive. Sin unidades, lista vacía.
- `sincronizar_con_pendrives_usb()`: copia el diario de hoy a `{unidad}\CobroFacil_PRO_Backups`. Sin pendrive no hace nada.
- `limpiar_backups_antiguos(max_dias=30)`: borra archivos más viejos que ese tope en las tres carpetas. No toca el espejo SQLite del jefe.

## Qué no debe cambiar

- El orden de la lista. `replicar_espejo` y el estado del cerebro usan la carpeta 1 (AppData).
- No dejar Documentos como única copia: si esa carpeta falla, AppData sigue siendo el origen.
