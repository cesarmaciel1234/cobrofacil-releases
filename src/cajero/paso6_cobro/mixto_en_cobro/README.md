# Mixto en la pantalla de cobro

Se ve en la misma hoja del monto, solo cuando el medio es Mixto. No abre un cuadro aparte.

`panel.py`, clase `PanelMixtoCobro`. `mostrar(total)` pinta efectivo, tarjeta, transferencia y QR. `ocultar()` lo saca. `valores()` es el reparto. `cubre()` es verdadero cuando la suma alcanza el total. `cambio` avisa cada vez que se escribe. Si hay importe en un tercer medio, lo borra y `aviso` pide el cartel: el mixto admite solo dos.

El teclado de la derecha escribe en el casillero con foco. F1 imprime y F2 registra. Esos botones no viven acá.

Al confirmar, `confirmar.py` arma los pasos vivos: tarjeta, después transferencia, después QR. El efectivo no tiene paso. La pantalla llama a cada motor por su lado y, cuando terminan, el motor mixto guarda la venta una sola vez.

`widgets/pagos_mixtos.py` es la ventana vieja. El clic de Mixto ya no la abre.
