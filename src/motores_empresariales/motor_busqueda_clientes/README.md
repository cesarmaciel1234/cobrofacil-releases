# Motor de búsqueda de clientes

Qué hace: Sugiere clientes en el cobro (crédito y cobranza) sin trabar la UI.

Qué función: `MotorBusquedaClientes.buscar_texto`, `precargar`.

Cómo funciona: Al armar el cobro carga `id, nombre, dni` en un hilo. Cada tecla filtra esa lista en memoria. `cesar` pega el inicio del primer o segundo nombre, no el medio. DNI por prefijo. Desde 3 letras o 3 dígitos. Máximo 5 sugerencias. Si el índice aún no llegó, consulta con `LIKE 'cesar%'` y límite, también en hilo.

Qué no debe cambiar: no llamar `SELECT *` ni `LIKE '%texto%'` en el hilo de la pantalla.
