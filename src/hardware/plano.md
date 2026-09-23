# Plano — cajón

## Frente

La lámpara está en la cabecera del cajero, a la izquierda del nombre del negocio. La elige `src/notificaciones/motor/revisar.py`.

Si hay un aviso vivo con código `cajon`, `_alertas` arma una fila nivel `urgente`, detalle «Cajón abierto» y `en_franja` en falso. No escribe «CAJÓN ABIERTO» en la franja. No pinta el marco de la pantalla ni el título. El punto rojo es la lámpara urgente. Al pasar el mouse, el aviso puede decir «Cajón abierto».

## Fondo

`src/hardware/cash_drawer.py` habla con el cajón y publica el aviso antes de emitir la señal. `src/notificaciones` no abre el cajón: solo decide la lámpara.

Una venta solo en efectivo puede abrir el cajón. Tarjeta, transferencia y QR no tienen que abrirlo. El perfil cajero no debe ver el cajón abierto sin ese efectivo. Admin y jefe pueden probar el cajón: eso no es un robo en la franja.

## Qué no cambiar

No volver a pintar el perímetro, ni el cartel de cajón abierto, ni a poner ese texto en la franja.
