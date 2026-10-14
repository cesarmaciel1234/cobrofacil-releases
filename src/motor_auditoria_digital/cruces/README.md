# Cruces

Qué hace: junta las consultas en filas de auditoría. No cobra.

Qué función: `snapshot.armar(desde, hasta)` y `totales.de_filas(filas)` (montos + `n_sin_firmar` / `n_tickets` para el 5/25).

Cómo funciona: pide pagos MP, vínculos, tickets, cobranzas F6 y F9. Concepto: `Venta QR` o `Cobranza QR · nombre`. ID de pago solo si hay MP o F9 de verdad. Ticket venta y ticket cobro van separados. Firmado / Sin firmar / F9 / Sin ticket / Cobranza.

Qué devuelve cuando falla: lista parcial o `[]`. Nunca lanza.

Qué no debe cambiar: no escribir `ventas` ni `mp_pagos`. No abrir EscuchaMP.
