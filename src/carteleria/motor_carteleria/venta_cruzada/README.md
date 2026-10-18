# Venta cruzada

Qué hace: cuenta cuántas veces dos productos van en el mismo ticket.

Qué función: `VentaCruzadaInteligente` en `motor.py`. `armar_slides` arma las preguntas de la TV. `obtener_relacionados_para_ticket` devuelve los acompañantes. `_matriz` lee `detalles_ventas` + `ventas`.

Cómo funciona: junta las líneas de cada venta no cancelada. Un ticket con un solo producto no cuenta. El peso baja con la antigüedad (30 días, 90, 365, más viejo). La matriz queda en memoria 15 minutos, o hasta que cambie la cantidad de ventas. Si no hay ningún ticket, `usar_relleno_catalogo` es verdadero y se puede completar con el rubro. Si la consulta falla, la matriz queda vacía y no se inventan pares.

Qué no debe cambiar: la tabla `detalles_ventas.nombre_producto` y `ventas.id`. No correr esta consulta en el hilo de la pantalla.
