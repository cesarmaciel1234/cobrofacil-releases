# Salida a métodos

Qué hace: Cierra el proceso de cobro activo y deja la ventana de selección de medio.

Qué función: `salir_a_metodos(ventana)` en `proceso.py`.

Cómo funciona: Para relojes, suelta Point, llama `salir` de efectivo, tarjeta, QR, transferencia, mixto y crédito, marca Efectivo en la grilla y pone el stack en 0. Sin `set_metodo`, sin `cerebro`, sin `config._load_config`.

Qué no debe cambiar: no volver a llamar `set_metodo` acá; eso reabría Point o leía el disco y congelaba.
