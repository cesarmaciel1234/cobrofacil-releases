# Ruta 3: cliente nuevo

Qué hace: Alta exprés desde el cobro.

Qué función: `PanelClienteNuevo._procesar` llama `crear_cliente(nombre, "", limite=50000)`.

Cómo funciona: Enter crea y el orquestador evalúa margen o abre cobranza según el modo.

Qué no debe cambiar: el límite base de 50.000.
