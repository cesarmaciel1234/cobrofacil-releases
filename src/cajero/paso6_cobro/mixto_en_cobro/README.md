# Mixto en la pantalla de cobro

Se ve en la misma hoja del monto, solo cuando el medio es Mixto. No abre un cuadro aparte.

`panel.py`, clase `PanelMixtoCobro`. `vaciar()` borra todos los casilleros. `mostrar(total)` vacía y pinta efectivo, tarjeta, transferencia, QR y cliente. Volver a los medios, elegir otro o abrir otra venta no deja el mixto anterior. `ocultar()` lo saca. `valores()` es el reparto. Cada casillero entra por `_numero`, que llama `redondear_dinero`. `cubre()` es verdadero cuando esa suma, más `0.001`, alcanza el total ya redondeado **y** el excedente, si hay, está en efectivo. Sobrar en tarjeta, transferencia, QR o cliente no cubre. `cambio` avisa cada vez que se escribe. Si hay importe en un tercer medio, lo borra y `aviso` pide el cartel: el mixto admite solo dos. El cliente cuenta como uno de esos dos. Si ya hay un medio con plata y se toca otro casillero vacío, `_completar_falta` pone el resto. No escribe solo en redondeo ni recargo.

El teclado de la derecha escribe en el casillero con foco. F1 imprime. Enter registra. Esos botones no viven acá.

Enter, con el total cubierto, cierra el reparto y cobra solo. Lo más rápido primero: Point, palomita en tarjeta, y si hay efectivo abre el cajón. Después queda en escucha de transferencia o muestra el QR, o pide el cliente. Ese paso no cambia el medio a Fiado. Esc un paso atrás: grilla de medios y mixto vacío. Volver a Mixto no trae el reparto ni las palomitas. Con la luz en rojo, Enter guarda el reparto escrito, si `cubre()` y no es solo cliente.

F11 cubierto con parte de tarjeta entra al mismo flujo que Enter.

`widgets/pagos_mixtos.py` es la ventana vieja. El clic de Mixto ya no la abre.

## Cómo funciona el cobro vivo

`confirmar.py`: `pasos_vivos` arma tarjeta, transferencia y QR. El cliente lo agrega `paso6_cobro._entrar_mixto`. `PointService` usa `valores_mixtos["tarjeta"]`. `_anotar_point` anota ese mismo importe. `MotorMixto` persiste una sola venta; si hay resto a cuenta pide `cerebro.autorizar` por `fiado_parcial` y exige cliente.
