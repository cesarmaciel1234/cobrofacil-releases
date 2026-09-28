# bajada — de Mercado Pago a `mp_pagos`

`mp.py`, `ponerse_al_dia(token, desde=None)`.

1. Marca de arranque: `mp_historial_hasta` menos 2 horas. Sin marca, `mp_historial_desde`. Sin ninguna, el día 1 del mes (y lo anota en `mp_historial_desde`).
2. Pide `/v1/payments/search` con `range=date_last_updated` (altas, aprobaciones y devoluciones), un día por vez hasta ahora, 100 por página, hasta 10 páginas por día. Cada página se intenta tres veces.
3. Deja solo pagos de la cuenta del token (`users/me`) con monto mayor a 0 y los pasa a `libro.tabla.guardar`.
4. Los aprobados del mes también van al CSV del monitor (`historial/archivo.guardar`).
5. Después de cada día guardado corre `mp_historial_hasta`.

Devuelve cuántos guardó. Si MP no responde, corta: devuelve lo guardado o -1, y la próxima vuelta sigue desde la marca. Sin token, 0. Si ya hay una bajada corriendo en el proceso, 0.

Recuperar meses viejos: `ponerse_al_dia(token, desde=datetime(2026, 1, 1))`. No mueve la marca para atrás.

No cambiar: la marca solo avanza después de guardar. Sin `end_date` MP responde 400.
