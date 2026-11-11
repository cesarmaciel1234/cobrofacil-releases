# Servidor de Tienda

## Qué hace

`src/central_red_global/lan_server.py` publica la API HTTP para las cajas (`/health`, `/api/ping`, sync) y el descubrimiento UDP para encontrar la maestra. Esta carpeta organiza el arranque, el rol (maestra/esclava), la presencia, el autoarranque en Windows (`autostart/windows.py`) y la ventana del proceso `--server`.

## Funciones principales

- `init_lan_server()`: inicia una sola supervisión para HTTP (`8000`) y UDP (`37020`).
- `GET /health` y `/api/health`: endpoint de readiness que verifica HTTP + estado de MariaDB local (devuelve `200 ok` o `503 degraded`).
- `is_os_autostart_enabled()` / `set_os_autostart(True)`: verifica ruta exacta del acceso directo en `Startup\CobroFacil_ServidorTienda.lnk` y registra la Tarea Programada `CobroFacil_ServidorTienda` (`ONLOGON`, reinicio automático ante fallo, sin límite de tiempo).
- `servidor/oficio/agente.py`: mantiene `esclava_heartbeat.txt` en cada vuelta del espejo.

## Cómo funciona

La maestra expone su API en TCP 8000 y escucha descubrimientos en UDP 37020. Al iniciar desde Windows o desde el watchdog del Lanzador, el proceso `--server --background` corre silencioso en la bandeja del sistema. Incluso en PCs esclavas, `auto_heal` conserva `auto_start_store_server` habilitado para mantener vivo el espejo.

## Qué no debe cambiarse

- No anunciar como maestra un puesto esclavo ni una base SQLite.
- No borrar colas offline ni carpetas de datos (`punpro_db`) automáticamente ante un fallo de arranque.
- Mantener acotada la concurrencia del servidor HTTP (`_HTTP_WORKERS = 32`).
