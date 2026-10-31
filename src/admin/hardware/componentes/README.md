# Componentes de hardware

Qué hace: tarjeta de prueba reutilizable en el panel de diagnóstico.

Qué función: `HardwareCard` en `hardware_card.py`.

Cómo funciona: el panel arma una card por dispositivo. El clic dispara la prueba local. Si el puerto no existe, la card lo dice y el resto sigue.

Qué no debe cambiar: no abrir el terminal de ventas ni tocar `qt_dpi`.
