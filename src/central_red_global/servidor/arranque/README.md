# Servidor - Secuencia de Arranque

## Qué hace la carpeta
Contiene los módulos encargados de coordinar el lanzamiento asíncrono y los vigilantes del "Servidor de Tienda" (proceso aislado en la maestra).

## Cómo funciona (andeja.py)
andeja.py contiene un_store_server_app(app) que inicia la interfaz del sistema en el tray (bandeja de Windows) de la PC Maestra.
Inicia los servicios base, pero retrasa el arranque de MariaDB para no congelar la carga de los iconos (rrancar_mysqld=False).

### El Watchdog
Un temporizador revisa cada ciertos segundos (_watchdog()) si MariaDB sigue activo. Si lo encuentra apagado al inicio, lo levanta (start_server()).
- **Punto crítico:** Debido a que el DatabaseManager del proceso principal pudo haberse rendido y asumido "Modo offline" (SQLite) si comprobó el estado de MariaDB antes de que el watchdog lo levantara, el watchdog ejecuta inmediatamente una reconexión forzada db.reconectar_mariadb() y lanza las migraciones/creación de tablas. Sin esta inyección, el Servidor operaría con un MariaDB vacío y los clientes perderían los usuarios predeterminados (como el cajero o admin).

## Qué no debe cambiar una mejora futura
- No quitar la invocación a _create_tables() y _migrate_db() en el evento de encendido exitoso del Watchdog para MariaDB. Es el pilar de sincronización cuando el arranque es diferido.
