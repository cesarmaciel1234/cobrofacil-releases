# Servicio Nativo de Windows (Session 0)

Qué hace: ejecuta el proceso `--server` (`MariaDB`, red LAN `:8000`/`:37020`, `CerebroBackup`, cartelera TV o espejo esclava) como un servicio nativo del Service Control Manager (SCM) de Windows (`CobroFacil_ServidorTienda`), activo desde el arranque antes de iniciar sesión de usuario y con recuperación automática ante fallos (`restart/5s/15s/30s`).

Qué función: `CobroFacilStoreService`, `run_windows_service`, `estado_servicio_windows`, `instalar_servicio_windows`, `desinstalar_servicio_windows`, `iniciar_servicio_windows`, `detener_servicio_windows`, `instalar_servicio_con_uac`.

Cómo funciona:
- `main.py` intercepta `--winservice` al principio sin cargar PyQt6 ni WebEngine, cambiando `cwd` al directorio real de la tienda (`--service-root` / `get_base_path()`).
- Si falta privilegio Admin al activar `Win: ON` en una sesión estándar, el autostart conserva el respaldo por Tarea Programada + acceso directo, y el botón de estado del servidor ofrece activar Session 0 vía UAC (`ShellExecuteW(..., "runas")`).
- `candados.py` consulta `QueryServiceStatusEx` (permitido para usuarios estándar) para no intentar duplicar ni borrar candados de un proceso `LocalSystem`.
