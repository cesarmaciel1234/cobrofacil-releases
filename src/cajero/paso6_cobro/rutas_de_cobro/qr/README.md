# Proceso QR

Qué hace: Aísla el QR de Mercado Pago.

Qué función: `entrar` / `salir` en `proceso.py`. La UI está en `qr_en_cobro/`.

Cómo funciona: `salir` llama `panel_qr.ocultar`: para el polling y borra la orden en un hilo.

Qué no debe cambiar: el pedido del QR no corre en el hilo de la UI. Timeout corto. Sin `asegurar_pos_qr` en el cobro. Si «Buscando…» se queda, leé `paso6_cobro/reparacion.md`.
