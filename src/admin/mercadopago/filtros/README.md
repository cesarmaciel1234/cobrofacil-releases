# Filtros de la auditoría

Qué hace: la lista que abre el botón **Filtros** y la regla que decide si una fila se ve.

Qué función:

- `panel.abrir(padre, ancla, cruce, cuenta, nombres, al_elegir, estilo_activo, estilo_idle)` pinta el popup y llama `al_elegir(cruce, cuenta)`.
- `clase.clase_cruce(fila)` devuelve `cruzado`, `ticket_sin_id` o `id_sin_ticket`.
- `clase.pasa(fila, cruce, cuenta)` dice si la fila entra en la grilla.
- `clase.entra_en_reparto(fila)` es verdadero solo si hay id de Mercado Pago.
- `clase.sumar_cuentas(filas)` devuelve `[(titular, monto_mp), …]` en el orden en que aparecen.
- `clase.texto_boton(cruce, cuenta)` es el texto del botón.

Cómo funciona: **Cruzados** tiene ticket e id. **Ticket sin id** es venta o cobro sin id de Mercado Pago; esa fila no lleva cuenta. **Id sin ticket** es un pago sin ticket. **Cuenta** solo aparece si hay más de un titular en el período. La suma de arriba no se esconde al filtrar el cruce: sigue siendo el total de cada token en lo que se está viendo.

Qué devuelve cuando falla: `clase_cruce` devuelve `""` si no hay ticket ni id. `sumar_cuentas` devuelve `[]`. El popup no consulta la red.

Qué no debe cambiar: no poner el token en esta carpeta. No sumar una fila sin id de pago a una cuenta. No volver a las casillas Firmados / Pendientes.
