# Cerebro del lanzador

Qué hace: arma el comando `--role` y lanza el perfil. Si ese rol ya tiene candado en esta PC, enfoca la ventana y no crea otro proceso.

Qué función: `spawn_role_process`, `build_role_command`, `ensure_hub_services`.

Cómo funciona: cajero, admin, jefe y contabilidad son **un PID por PC**. Si el usuario cierra, el hub no los revive. Admin puede desanclar módulos en el mismo proceso. Cartelería no entra en esa regla (lanzador de TVs).