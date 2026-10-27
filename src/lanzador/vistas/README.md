# Hub del lanzador

Qué hace: `PerfilPantalla` en `hub_main.py`. Cinco tarjetas. Cajero, admin, jefe y contabilidad: un PID por PC; el clic trae la ventana. Si el usuario cierra, no se reabre solo. Cartelería sigue con reintento automático; el lanzador de TVs no se toca acá.

El renglón de arriba sale de `es_pc_maestra_local()`. En esta notebook dice «LANZADOR ESCLAVA — ESPEJO DE LA TIENDA». En la PC de la tienda sigue «LANZADOR MAESTRO». La ventana del espejo no se pinta acá: la abre el proceso `--server`, carpeta `src/central_red_global/servidor/ventana/`. El clic en «Espejo: activo» le pide al servidor que se muestre y después lo trae delante. Cada 15 segundos `_auto_ensure_server_if_offline` vuelve a pedirlo si el proceso no está.

Qué función: `_elegir`, `_lanzar_proceso_autonomo`, `_apply_locked_profiles_ui`.

Cómo funciona: `UN_SOLO_POR_PC` en `cerebro/process_spawner.py`. El candado es `perfil_{rol}.lock`.
