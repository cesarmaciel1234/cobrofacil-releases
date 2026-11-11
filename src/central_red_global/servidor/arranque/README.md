# Servidor - Secuencia de Arranque

## Qué hace la carpeta
Coordina el levantamiento del proceso `--server`, el healthcheck (`proceso.py`) y la interfaz en bandeja de sistema (`bandeja.py`).

## Cómo funciona (`proceso.py` y `bandeja.py`)
- `proceso.py` inicia el proceso con `build_server_command(background=True)` (`--server --background`) usando `CREATE_NO_WINDOW`.
- `is_store_server_online()` valida PID vivo y además **readiness real**: en Maestra comprueba puerto MariaDB `3306` + endpoint `/health` (o puerto `8000`); en Esclava valida que `oficio-esclava` mantenga fresco `locks/esclava_heartbeat.txt`.
- `bandeja.py` arranca `run_store_server_app(app, background=...)`. Si `background=True` y la bandeja del sistema está disponible, inicia **oculto en la bandeja (`win.hide()`)** para vivir en segundo plano con Windows sin robar foco al cajero; el usuario puede abrir la ventana haciendo doble clic en el ícono o clic en la pastilla del Lanzador.
- `_watchdog` ejecuta sus chequeos de MariaDB y presencia LAN en un **hilo daemon separado** (`_watchdog_worker`) y emite por señal Qt (`_WatchdogSignals`) para no congelar la interfaz.

## Qué no debe cambiar una mejora futura
- Mantener la invocación a `db.reconectar_mariadb()`, `db._create_tables()` y `db._migrate_db()` cuando el Watchdog enciende MariaDB tras un arranque diferido (`arrancar_mysqld=False`).
- Mantener la cuarentena segura de `MariaDBController` (`corrupt_backup_*`) sin borrar datos automáticamente.
