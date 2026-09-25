# Mixto en la pantalla de cobro

Se ve en la misma hoja del monto, solo cuando el medio es Mixto. No abre un cuadro aparte.

`panel.py`, clase `PanelMixtoCobro`. `mostrar(total)` pinta efectivo, tarjeta, transferencia y QR. `ocultar()` lo saca. `valores()` es el reparto. Cada casillero entra por `_numero`, que llama `redondear_dinero`. `cubre()` es verdadero cuando esa suma, más `0.001`, alcanza el total ya redondeado. `cambio` avisa cada vez que se escribe. Si hay importe en un tercer medio, lo borra y `aviso` pide el cartel: el mixto admite solo dos.

El teclado de la derecha escribe en el casillero con foco. F1 imprime y F2 registra. Esos botones no viven acá.

Al confirmar, con la luz del TPV en verde, `confirmar.py` arma los pasos vivos: tarjeta, después transferencia, después QR. El efectivo no tiene paso. Si mientras espera la transferencia ese monto pasa al QR, suelta la escucha y muestra el código por el importe de QR. Con la luz en rojo, Enter no arma esos pasos: guarda la venta con el reparto escrito.

`widgets/pagos_mixtos.py` es la ventana vieja. El clic de Mixto ya no la abre.
