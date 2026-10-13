# Motor mixto

p1 efectivo / p2 otros. El cliente entra en p2. Una persistencia. El medio queda `Mixto (Cliente)` si hay resto a cuenta: el cajón igual mira el casillero de mixto.

La pantalla, antes de llegar acá, cobra la tarjeta en Point, escucha la transferencia y muestra el QR de esa parte. Si hay importe en cliente, `ejecutar` pide `cerebro.autorizar("Clientes", …)` por ese resto y después guarda. Este motor no abre la hoja.
