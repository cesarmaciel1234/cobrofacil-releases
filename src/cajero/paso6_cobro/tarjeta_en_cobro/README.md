# Tarjeta en la pantalla de cobro

El medio Tarjeta deja el hueco de `PanelTarjetaCobro` (mismo contenedor que QR). El cobro lo espera el cartel `EsperaPoint` **dentro de esa caja**, el mismo envío que usa el paso de tarjeta del mixto, solo si hay token y `mp_device_id`. Tener solo el QR no manda el Point. Al aprobar, cierra **solo** (sin F9) y el id queda para el ticket. Con la luz en rojo no se manda el Point: Enter guarda la venta. Si se cancela en el cartel o en la terminal, la hoja vuelve a la página de métodos.

`panel.py`, clase `PanelTarjetaCobro`. `mostrar(monto)` sigue pudiendo mandar el importe. Un fallo no cancela el cobro que ya quedó en la terminal.

El fondo del Point está en `envio/`: `mandar.enviar_monto`, `estado.detalle_orden` y `soltar.cancelar_intent`. El detalle de cada función está en `envio/README.md`. La terminal pide apoyar la tarjeta y no ofrece QR. El cartel consulta cada 1 s desde que el Point tomó el monto, y no apila GETs. El panel consulta cada 800 ms. Cancelar sin `en_terminal` no baja un cobro que ya se ve en el Point. El botón Cancelar del cartel sí pasa `en_terminal=True`.

Si la terminal no toma el monto, el cartel avisa y Enter registra la venta igual.

## Orden creada y el Point en blanco

`at_terminal` es el envío logrado. `created` se cancela y vuelve como `motivo: "otra_cuenta"`: el Point está abierto con otra cuenta que el token. El detalle del caso está en `paso6_cobro/decisiones.md`.
