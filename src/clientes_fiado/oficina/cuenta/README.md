# Libro de la cuenta

`motor.py`, clase `MotorCuenta`. No cobra la venta.

`identificar_dni` llama `ClienteRepository.verificar_y_crear_cliente`. `identificar_nombre` llama `verificar_y_crear_por_nombre`. El límite express sale de `fiado_express_limite`. El de nombre queda en 50000.

`alta_regular` inserta `tipo_cliente = regular`. `actualizar_existente` y `actualizar_ficha` escriben la ficha. `fijar_limite` cambia solo el cupo.

`buscar` es la lista de admin. `sugerir_nombres` arma el listado del cobro: pliega tildes y mayúsculas, y devuelve hasta 8 fichas con el DNI. `listar` es la lista corta del cobro.

`listar_con_deuda`, `ultimo_cargo` y `movimientos` son la mesa de por cobrar. `abonar` y `cargar_manual` escriben la deuda y el movimiento en una sola transacción. Si la fila no entra, la deuda queda como estaba. `abonar` guarda medio, perfil y quién cobró. `pagos_del_dia` y `deuda_total` alimentan las tarjetas del jefe. `credito_disponible` y `limite_excedido` son la mesa de saldos.

`cuadre.py` busca ventas a crédito sin cargo. `emparejar` junta la venta con un cliente solo cuando el nombre coincide con uno. Si la venta quedó como `Express` más el DNI, la junta con la ficha que ya tiene ese DNI. `anotar` escribe ese cargo con la nota cuadre. `ventas_sin_cargo` y `anotar_faltante` salen por el cerebro.

`motores/cuenta/motor.py` reexporta la clase.
