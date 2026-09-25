# Libro de la cuenta

`motor.py`, clase `MotorCuenta`. No cobra la venta.

`identificar_dni` llama `ClienteRepository.verificar_y_crear_cliente`. `identificar_nombre` llama `verificar_y_crear_por_nombre`. El límite express sale de `fiado_express_limite`. El de nombre queda en 50000.

`alta_regular` inserta `tipo_cliente = regular`. `actualizar_existente` y `actualizar_ficha` escriben la ficha. `fijar_limite` cambia solo el cupo.

`buscar` es la lista de admin. `sugerir_nombres` arma el listado del cobro: pliega tildes y mayúsculas, y devuelve hasta 8 fichas con el DNI. `listar` es la lista corta del cobro.

`listar_con_deuda`, `ultimo_cargo` y `movimientos` son la mesa de por cobrar. `abonar` es la mesa de cobradas. `credito_disponible` y `limite_excedido` son la mesa de saldos.

`motores/cuenta/motor.py` reexporta la clase.
