# Salida a métodos

Qué hace: Esc un paso atrás. Cierra el cobro activo, **vacía ese medio** y deja la grilla.

Qué función: `salir_a_metodos(ventana)` en `proceso.py`. Lo llama `_esc_un_paso` (Esc, teclado «Esc», cuenta cancelada).

Cómo funciona: Para relojes, suelta Point, llama `salir` de efectivo, tarjeta, QR, transferencia, mixto y crédito. Vacía importes, cliente del combo, ids de Mercado Pago y el mixto. Marca Efectivo en la grilla y pone el stack en 0. Sin `set_metodo`, sin `cerebro`, sin `config._load_config`. Volver a entrar al mismo medio no trae el importe anterior.

Qué no debe cambiar: no volver a llamar `set_metodo` acá; eso reabría Point o leía el disco y congelaba. No dejes Esc en un casillero sin `_esc_un_paso`: el texto quedaba y se cobraba.
