# Red LAN / Multicaja

## Qué hace

`red_lan_main.py` muestra el estado de conexión y permite cambiar el perfil de esta PC entre MAESTRA y ESCLAVA.

## Funciones principales

- `_actualizar_botones()`: refleja el rol activo y habilita la reparación a MAESTRA solo cuando `db_host` es una IP de esta PC y MariaDB local responde.
- `_convertir_maestra()`: pide confirmación y delega la validación del cambio a `MotorRed`; no cambia productos ni stock desde la pantalla.
- `_convertir_esclava()`: pide la IP y delega al motor, que valida identidad de tienda y conexión antes de guardar el enlace.

## Cómo funciona

Al reparar el rol local, el motor conecta a MariaDB por `localhost`, limpia los indicadores de esclava y reinicia el proceso `--server` para que arranque como titular. Si MariaDB no responde o la conexión falla, conserva el perfil anterior. Una IP propia no se toma como una maestra remota.

La pantalla consulta y configura el enlace; las ventas, el catálogo y su sincronización pertenecen a los servicios de base de datos y red.
