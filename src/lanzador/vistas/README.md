# Hub del lanzador

Qué hace: `PerfilPantalla` en `hub_main.py`. Cinco tarjetas. Cajero, admin, jefe y contabilidad: un PID por PC; el clic trae la ventana. Si el usuario cierra, no se reabre solo. Cartelería sigue con reintento automático; el lanzador de TVs no se toca acá.

Qué función: `_elegir`, `_lanzar_proceso_autonomo`, `_apply_locked_profiles_ui`.

Cómo funciona: `UN_SOLO_POR_PC` en `cerebro/process_spawner.py`. El candado es `perfil_{rol}.lock`.
