# Inicio y perfiles

`login_pantalla.py` abre `LoginPantalla`. Pinta su propia tarjeta blanca y no usa fondo transparente.

`perfil_pantalla.py` reexporta el hub de `src/lanzador/vistas/hub_main.py`.

`aviso_cierre_automatico.py` es el aviso grande cuando el cajero entra y ya se cerró un día anterior. Lo abre `main.py` antes de la apertura de caja.

La validación está en `logica/auth_controller.py`, función `authenticate`.
