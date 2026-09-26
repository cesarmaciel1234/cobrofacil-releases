# Inicio y perfiles

`login_pantalla.py` abre `LoginPantalla`. El ingreso normal pinta su tarjeta blanca sobre `#F8FAFC`.

F11, desde el cajero, la abre con `fondo_gris=True`. El gris `#334155` tapa la venta y la tarjeta de usuario y contraseña queda al frente. El formulario se arma en `_setup_ui`, antes de pintar.

`perfil_pantalla.py` reexporta el hub de `src/lanzador/vistas/hub_main.py`.

`aviso_cierre_automatico.py` es el aviso grande cuando el cajero entra y ya se cerró un día anterior. Lo abre `main.py` antes de la apertura de caja.

La validación está en `logica/auth_controller.py`, función `authenticate`.
