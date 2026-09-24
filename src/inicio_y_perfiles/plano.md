# Inicio y perfiles

## Frente

`LoginPantalla` es una ventana opaca. El fondo y la tarjeta se pintan en el propio diálogo. Si el tema global no carga, el login no queda transparente.

`PerfilPantalla` vive en `src/lanzador/vistas/hub_main.py`. En tema día el título es oscuro sobre marfil.

`AvisoCierreAutomatico` avisa el cierre de días anteriores. No abre la caja ni escribe la venta. El monto lo calcula `verificar_y_realizar_autocierre` antes de mostrar la ventana.

## Fondo

`logica/auth_controller.py` valida usuario y contraseña. Este plano no cambia esa validación.
