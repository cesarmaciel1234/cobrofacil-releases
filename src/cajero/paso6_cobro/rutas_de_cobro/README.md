# Rutas de cobro

Qué hace: Cada medio es un proceso aislado. ESC no mezcla uno con otro: suelta el activo y vuelve a la grilla.

Qué función: `salida/proceso.py` → `salir_a_metodos`. Cada carpeta tiene `entrar` / `salir`.

Cómo funciona: Al elegir un medio se entra a su proceso. ESC, Cancelar o «cambiar método» llaman `salir_a_metodos`: paran timers, sueltan Point/QR, reinician crédito y muestran la página 0. No consulta MariaDB ni recarga el config.

Qué no debe cambiar: ESC en la grilla (página 0) sigue saliendo al carrito (`reject`).
