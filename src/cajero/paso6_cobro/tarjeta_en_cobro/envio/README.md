# Envío al Point

Manda el importe, mira si el equipo lo tomó y cancela la orden si hace falta. No pinta nada. La pantalla está en `aviso_en_cobro/` y en `panel.py`.

## mandar.py

`enviar_monto(token, device_id, monto)` arma `POST /v1/orders`. El monto va como texto con dos decimales. Solo tarjeta (`credit_card`). El mínimo es $15.

Devuelve `{"ok": False, "motivo": ...}`:

- `sin_terminal`: falta token, device o el monto es cero.
- `minimo`: menos de $15.
- `red`: no hubo respuesta.
- `ocupada`: HTTP 409.
- `rechazo`: otro HTTP o la orden no trajo id.
- `cancelo`: la orden ya venía cancelada.
- `otra_cuenta`: siguió en `created`.

`ok: True` trae `intent`, `token` y `device`. Eso solo pasa si el estado ya es `at_terminal` o `processed`.

`_esperar_point` mira la orden al toque. Si sigue en `created`, consulta cada 0,4 s, hasta 8 vueltas. La primera no espera. Cada consulta corta a los 0,8 s. Si nunca sale de `created`, llama `cancelar_intent` y devuelve `otra_cuenta`.

## estado.py

`clasificar_estado` traduce el status de Mercado Pago: `processed` → `FINISHED`, `at_terminal` y `action_required` → `AT_TERMINAL`, `created` y `processing` → `CREATED`, `failed`, `canceled`, `expired`, `refunded` → `CANCELED`.

`detalle_orden(token, intent_id)` hace `GET /v1/orders/{id}`. Devuelve `(estado, pago)`. El pago, si hay, trae `id` y `transaction_amount`. Si la red falla, devuelve `("", None)`. El cartel usa un tope de 1,2 s. La espera del envío usa 0,8 s.

`estado_intent` devuelve solo el estado.

## soltar.py

`cancelar_intent(token, device_id, intent_id, en_terminal=False)` hace `POST /v1/orders/{id}/cancel`. Sin `en_terminal` no baja un cobro que ya se ve en el Point. El botón Cancelar del cartel pasa `en_terminal=True` y manda la cabecera `x-allow-cancelable-status: at_terminal`. `clave()` es la `X-Idempotency-Key` de cada POST.

## Qué no cambiar

El importe sigue siendo string. No mandar QR en esta orden. No dar por enviado un HTTP 201 con status `created`.
