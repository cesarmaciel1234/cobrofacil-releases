# Hub del lanzador

Qué hace: `PerfilPantalla` en `hub_main.py`. Cinco tarjetas (`cajero`, `admin`, `jefe`, `carteleria`, `contabilidad`) en subprocesos `--role <rol>` aislados y un icono en bandeja (`ControladorBandejaLanzador`). Al cerrar con `✕` se oculta en bandeja sin cerrar perfiles ni detener el Servidor fantasma (`--server`); «Salir del Lanzador» en el menú de bandeja cierra solo el Lanzador. Con `--background` arranca directo en bandeja sin splash.

El renglón de arriba sale de `es_pc_maestra_local()`. En PCs esclavas dice «LANZADOR ESCLAVA — ESPEJO DE LA TIENDA»; en la PC maestra dice «LANZADOR MAESTRO». Cada 10 segundos `_auto_ensure_server_if_offline` (hilo daemon + señal `_server_checked`) verifica que el proceso `--server` siga activo en segundo plano y lo relanza si cayó.

Qué función: `_elegir`, `_lanzar_proceso_autonomo`, `_apply_locked_profiles_ui`, `ocultar_en_bandeja`, `ejecutar_en_bandeja`, `_salir_definitivo`.

Cómo funciona: `UN_SOLO_POR_PC` en `cerebro/process_spawner.py` y `decidir_accion_perfil_terminado` en `cerebro/watchdog_perfiles.py`. Si el usuario cierra un perfil administrativo limpiamente (`admin`, `jefe`, etc., `exit_code` `0`, `888`, `889`), pasa a reposo y no vuelve a abrirse (sin comportamiento tipo virus). Si el perfil es `cajero` (Modo Kiosco empresarial), se relanza de inmediato hacia la pantalla de Login para mantener la terminal siempre operativa. Si un subproceso cae con error real (`exit_code != 0`) y no hay actualización activa (`is_apply_guard_active()`), reabre `--role <rol>` hasta Login con Circuit Breaker de máximo 3 caídas en 60 segundos; al hacer clic manual se reinicia el contador.
