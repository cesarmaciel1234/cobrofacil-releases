# fuentes — qué copias hay y de cuándo son

`buscar.py`. No escribe nada: abre los SQLite en modo solo lectura.

## Funciones

- `buscar(*rutas)`: para cada carpeta recorre hasta 3 niveles (`PROFUNDIDAD`), como mucho 400 archivos `.sql` / `.zip` / `.db`. Saltea `Catalogos`, papelera, `.git`. Un archivo suelto se analiza solo. Devuelve `Fuente` ordenadas por fecha de datos, la más nueva primero (a igual fecha, la completa primero). La misma ruta no se repite, y dos archivos con el mismo nombre y tamaño (la maestra guarda cada respaldo en `backups/db` del programa y en AppData) se muestran una vez.
- `analizar(path)`: una `Fuente` o `None` si el archivo no es de la tienda.
- `lugares_de_esta_pc()`: las dos carpetas de respaldos (`backups/db` del programa y de AppData), la carpeta de la copia del jefe (`espejo_tienda`) y `jefe_nodo_path` de `config.json`.

## Qué reconoce

| tipo | archivo | fecha de los datos | completa |
|---|---|---|---|
| `sql` | volcado MariaDB (cabecera `MariaDB dump` / `CREATE TABLE` / `INSERT INTO`, más de 5 KB) | fecha y hora del nombre; si no tiene hora, la del archivo | sí; `*_ventas.sql` no (solo ventas y caja) |
| `zip` | `backup_*`, `pre_restore_*`, `respaldo_*` con carpeta `punpro_db/` adentro, más de 50 KB | igual que `sql` | sí |
| `copia` | SQLite con `espejo_meta`, o `nodo_negocio.db` | `ultima_copia` de `espejo_meta`; si no, `last_sync` de `nodo.json`; si no, la del archivo | si `espejo_meta.completa = 1` |
| `sqlite` | otro SQLite con tabla `ventas` (respaldo de una tienda SQLite) | igual que `sql` | sí |

Se descartan: nombres con `.bad_`, `.tmp`, `.nuevo`; SQLite sin `ventas` (por ejemplo `contabilidad_jefe.db`); zip sin `punpro_db/`.

La copia trae `servidor` (el `@@hostname` de la maestra de donde salió) para avisar si es de otra.

## Qué no cambiar

- Ordenar por la fecha de los datos, no por la del archivo: copiar al pendrive cambia la fecha del archivo.
- No abrir las copias con `db_manager`.
