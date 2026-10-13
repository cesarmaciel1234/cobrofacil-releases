# Ruta 1: margen aprobado

Qué hace: Pantalla verde cuando el disponible cubre el carrito.

Qué función: `PanelMargenAprobado.poblar` y señal `confirmado`.

Cómo funciona: Tras 350 ms acepta Enter y emite el id del cliente. No muestra deuda.

Qué no debe cambiar: el debounce. El mismo Enter del buscador no debe cerrar la venta.
