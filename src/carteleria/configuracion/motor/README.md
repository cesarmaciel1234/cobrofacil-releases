# Motor de configuración TV

Qué hace: lee y guarda negocio, zócalo y tema. No pinta.

Qué función: `leer_local` / `leer_db` en `cargar.py`. `persistir_memoria` / `persistir_local` / `persistir_db` en `guardar.py`. `HiloCargar` / `HiloGuardar` en `hilo.py`.

Cómo funciona: la pantalla pinta con `leer_local` al toque. `HiloCargar` pide MariaDB y, si llega, pisa los campos. Guardar: memoria TV + `config.json` en el hilo de la UI; REPLACE `carteleria_config` en `HiloGuardar`. Si MariaDB falla, `revertir_memoria`.

Qué devuelve cuando falla: `leer_db` → `None`. `persistir_db` → `(False, error)`. El hilo no tira excepción al panel. Fila sqlite (`sqlite3.Row`) se lee por nombre de columna, no `.get`.

Qué no debe cambiar: no SELECT/REPLACE en el hilo de la UI. No tocar `src/cajero`.
