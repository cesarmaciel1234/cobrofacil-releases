# Proceso tarjeta

Qué hace: Aísla Point / tarjeta.

Qué función: `entrar` / `salir` en `proceso.py`. La UI está en `tarjeta_en_cobro/`.

Cómo funciona: `salir` llama `panel_tarjeta.ocultar` (para el reloj y cancela el intent en un hilo). No arranca Point.

Qué no debe cambiar: `_tpv_point_listo` sigue llamando `config._load_config` al entrar, no al salir.
