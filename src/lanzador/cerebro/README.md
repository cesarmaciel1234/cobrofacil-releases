# Cerebro del lanzador

Qué hace: arma el comando `--role` y lanza el perfil (`process_spawner.py`), y evalúa si un perfil caído debe relanzarse hasta Login o quedarse en reposo (`watchdog_perfiles.py`).

Qué función: `spawn_role_process`, `build_role_command`, `ensure_hub_services`, `build_launcher_command`, `decidir_accion_perfil_terminado`.

Cómo funciona: cajero, admin, jefe y contabilidad son **un PID por PC** (`perfil_{rol}.lock`). Arquitectura empresarial diferenciada por rol: el perfil `cajero` opera en **Modo Kiosco** (si se cierra voluntariamente con `exit_code` en `{0, 888}` o cae, se relanza automáticamente de inmediato para que la terminal de cobro nunca quede desatendida). Los perfiles administrativos (`admin`, `jefe`, `contabilidad`) respetan el cierre voluntario del usuario devolviendo `"reposo"`. Ante caída inesperada (`exit_code != 0`) sin actualización en curso (`apply_guard=False`), cualquier perfil permite hasta 3 relanzados dentro de una ventana de 60 segundos (`"relanzar"`) y luego pausa por seguridad (`"pausado"`). Cartelería no usa bloqueo único de terminal.
