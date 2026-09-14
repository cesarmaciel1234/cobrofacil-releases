# Cajero — reglas del servidor

El terminal no decide el puesto ni despierta MariaDB.

Al encender: usa lo que el lanzador / `--server` ya levantó (maestra) o la IP guardada (esclava). El cobro no toca Win/Auto ni el proceso de bandeja.

**Esclava:** cobra y consulta en la maestra (`db_host`). La SQLite local no es la caja. Ver `src/base_de_datos/reglas.md`.
