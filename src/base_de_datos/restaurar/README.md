# restaurar — un solo motor para cualquier copia

Restaura la tienda desde un respaldo del admin o desde la copia del jefe (pendrive o la copia local de una PC). Es el mismo camino para las dos. Quien guarda no sabe de esto:

- Respaldos (`autoblindaje_db.py`, `CerebroBackup`): la maestra guarda `.sql` / `.zip` cada 30 minutos, como siempre.
- Jefe (`src/jefe/nodo_portable/espejo`): la PC copia toda la tienda a un SQLite cada 5 minutos; el pendrive es una copia de ese archivo.

Lo abre Configuración → Mantenimiento → Respaldo → «Importar / Restaurar Respaldo» (`src/admin/configuracion/componentes/dialogo_restaurar.py`).

```
restaurar/
  __init__.py     buscar, analizar, lugares_de_esta_pc, destino_actual, revisar, modo, restaurar
  fuentes/        qué copias hay en una carpeta y de cuándo son sus datos
  aplicar/        a qué tienda va, cómo se aplica (reemplazo o suma) y los avisos
```

## Orden

1. `buscar(carpeta o archivo)` lista las copias, de la más nueva a la más vieja por la fecha de sus datos. La pantalla deja marcada la primera; se puede elegir otra.
2. `destino_actual()` dice a qué tienda va: la MariaDB de la maestra (con su `@@hostname`) o el `punpro.db` si la tienda es SQLite sola. Una caja sin maestra no restaura.
3. `revisar(fuente, destino)` devuelve bloqueos (no se puede) y avisos (otra maestra, copia parcial, fecha vieja, qué va a pasar).
4. `restaurar(fuente, destino, progreso)`:
   - Respaldo `.sql` / `.zip` (o `.db` sobre tienda SQLite): **reemplazo**. Usa `AutoBlindajeDB.restaurar_ultimo_backup_valido`: guarda las ventas de hoy, saca la foto `pre_restore`, aplica el respaldo y vuelve a cargar lo de hoy.
   - Copia del jefe (o un `.db` sobre tienda MariaDB): **suma**. Foto `pre_restore`, agrega lo que falta sin borrar ni pisar, y sella el respaldo del día.

## Quién puede leer las copias

La tienda trabaja con MariaDB. Para leer o restaurar cualquier copia hay que tener el sistema instalado:

- `.sql` y `.zip`: son de MariaDB. Sin el MariaDB del sistema (`mariadb_server/`) no se aplican ni se leen.
- Copia del jefe (`nodo_negocio.db`, `espejo_tienda.db`): es un SQLite de viaje. El sistema la lee (panel del jefe) y la vuelca a MariaDB con este motor. Para levantar una tienda desde el pendrive: instalar el sistema, que arma su MariaDB, y restaurar la copia.
- La copia del jefe lleva usuarios y configuración. Cualquier visor de SQLite la abre: el pendrive se guarda como una llave del negocio. Restaurar pide la clave del jefe.

## Qué no cambiar

- No hacer que el respaldo o el jefe llamen a este motor: cada uno guarda por su lado.
- No reemplazar la tienda con una copia del jefe: siempre suma.
- No restaurar sin la foto `pre_restore` antes.
