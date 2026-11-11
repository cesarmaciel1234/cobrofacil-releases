# Autostart de Windows (Servidor fantasma + Lanzador supervisor)

Qué hace: registra o quita los arranques automáticos en Windows al iniciar sesión para el daemon `--server --background` (`CobroFacil_ServidorTienda`) y para el Lanzador supervisor en bandeja (`CobroFacil_Lanzador`), completamente separados en procesos independientes.

Qué función: `set_windows_startup`, `is_windows_startup_enabled`, `startup_shortcut_path`, `launcher_startup_shortcut_path`, `_set_scheduled_task_item`, `asegurar_nombre_aviso`.

Cómo funciona: crea accesos directos en `Startup` (`*.lnk` vía COM `WScript.Shell` con fallback PowerShell) y Tareas Programadas `ONLOGON` con reinicio automático ante caídas. Valida la firma de ruta/argumentos en `_LNK_CACHE` para reparar rutas obsoletas al actualizar o mover de carpeta.
